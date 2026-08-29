#!/usr/bin/env python3
"""Manage Typecho posts and standalone pages through XML-RPC."""

from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import socket
import sys
import urllib.request
import xmlrpc.client
from http.client import HTTPException
from pathlib import Path
from typing import Any
from xml.parsers.expat import ExpatError


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / ".typecho.local.json"
MARKDOWN_MARKER = "<!--markdown-->"


class TimeoutSafeTransport(xmlrpc.client.SafeTransport):
    """HTTPS transport with a timeout and Typecho plain-text responses."""

    user_agent = "plain-text awesome-zhuiju-free-local-publisher/1.0"

    def __init__(self, timeout: float = 20.0) -> None:
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host: str):  # type: ignore[no-untyped-def]
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection

    def parse_response(self, response):  # type: ignore[no-untyped-def]
        """Ignore PHP deprecation warnings emitted around a valid XML response."""

        data = response.read()
        if response.getheader("Content-Encoding", "") == "gzip":
            data = gzip.decompress(data)

        data = re.sub(
            rb"<br\s*/>\s*<b>Deprecated</b>:.*?<br\s*/>\s*",
            b"",
            data,
            flags=re.DOTALL,
        )
        start = data.find(b"<?xml")
        closing = b"</methodResponse>"
        end = data.rfind(closing)
        if start >= 0 and end >= start:
            data = data[start : end + len(closing)]

        parser, unmarshaller = self.getparser()
        parser.feed(data)
        parser.close()
        return unmarshaller.close()


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"找不到本地配置文件：{path}")

    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法读取配置文件 {path}：{exc}") from exc

    missing = [key for key in ("endpoint", "username", "password") if not config.get(key)]
    if missing:
        raise RuntimeError(f"配置文件缺少字段：{', '.join(missing)}")
    if not str(config["endpoint"]).startswith("https://"):
        raise RuntimeError("XML-RPC 接口必须使用 HTTPS，避免账号密码明文传输")

    config.setdefault("blog_id", "1")
    return config


def create_client(config: dict[str, Any]) -> xmlrpc.client.ServerProxy:
    return xmlrpc.client.ServerProxy(
        str(config["endpoint"]),
        transport=TimeoutSafeTransport(),
        allow_none=True,
        use_builtin_types=True,
    )


def credentials(config: dict[str, Any]) -> tuple[int, str, str]:
    return (
        int(config["blog_id"]),
        str(config["username"]),
        str(config["password"]),
    )


def strip_markdown_marker(text: str) -> str:
    value = text.lstrip()
    while value.startswith(MARKDOWN_MARKER):
        value = value.removeprefix(MARKDOWN_MARKER).lstrip("\r\n")
    return value


def split_document(path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise RuntimeError(f"找不到 Markdown 文件：{path}")

    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    match = re.match(r"^#\s+(.+?)\s*(?:\n+|$)", content)
    if not match:
        raise RuntimeError("Markdown 第一行必须是一级标题，例如：# 页面标题")

    title = match.group(1).strip()
    body = strip_markdown_marker(content[match.end() :])
    if not body:
        raise RuntimeError("正文不能为空")
    return title, body


def make_excerpt(body: str) -> str:
    excerpt_source = body.split("<!--more-->", 1)[0]
    excerpt = re.sub(r"!?\[([^]]*)]\([^)]*\)", r"\1", excerpt_source)
    excerpt = re.sub(r"[`*_>#\[\]]", "", excerpt)
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    return excerpt[:240]


def build_content(args: argparse.Namespace, kind: str) -> dict[str, Any]:
    title, body = split_document(args.document.resolve())
    content: dict[str, Any] = {
        "title": args.title or title,
        "description": body,
    }

    if args.slug:
        content["wp_slug"] = args.slug
    if args.comments:
        content["mt_allow_comments"] = 1 if args.comments == "open" else 0
    if args.content_password is not None:
        content["wp_password"] = args.content_password

    if kind == "post":
        content["mt_excerpt"] = args.excerpt or make_excerpt(body)
        if args.category:
            content["categories"] = args.category
        if args.tag:
            content["mt_keywords"] = ",".join(args.tag)
        content["post_status"] = args.status
    else:
        if args.order is not None:
            content["wp_page_order"] = args.order
        if args.template is not None:
            content["wp_page_template"] = args.template
        content["page_status"] = args.status
    return content


def merge_post_metadata(content: dict[str, Any], existing: dict[str, Any]) -> None:
    defaults = {
        "categories": existing.get("categories", []),
        "mt_keywords": existing.get("mt_keywords", ""),
        "wp_slug": existing.get("wp_slug", ""),
        "wp_password": existing.get("wp_password", ""),
        "mt_allow_comments": existing.get("mt_allow_comments", 1),
    }
    for key, value in defaults.items():
        content.setdefault(key, value)


def merge_page_metadata(content: dict[str, Any], existing: dict[str, Any]) -> None:
    for key in (
        "wp_slug",
        "wp_password",
        "wp_page_order",
        "wp_page_template",
        "mt_allow_comments",
    ):
        if key in existing:
            content.setdefault(key, existing[key])


def remote_body(item: dict[str, Any], kind: str) -> str:
    body = str(item.get("description", ""))
    more_key = "mt_text_more" if kind == "post" else "text_more"
    more = item.get(more_key)
    if more:
        body = f"{body.rstrip()}\n\n<!--more-->\n\n{str(more).lstrip()}"
    return strip_markdown_marker(body)


def export_document(
    item: dict[str, Any], kind: str, output: Path, overwrite: bool
) -> None:
    destination = output.resolve()
    if destination.exists() and not overwrite:
        raise RuntimeError(f"文件已存在：{destination}；如需覆盖请加 --force")

    destination.parent.mkdir(parents=True, exist_ok=True)
    title = str(item.get("title") or "未命名")
    destination.write_text(
        f"# {title}\n\n{remote_body(item, kind).rstrip()}\n", encoding="utf-8"
    )
    print(f"已导出：{destination}")


def print_item(item: dict[str, Any], kind: str) -> None:
    id_key = "postid" if kind == "post" else "page_id"
    status_key = "post_status" if kind == "post" else "page_status"
    print(f"ID：{item.get(id_key, '')}")
    print(f"标题：{item.get('title', '')}")
    print(f"状态：{item.get(status_key, '')}")
    print(f"Slug：{item.get('wp_slug', '')}")
    print(f"链接：{item.get('link') or item.get('permaLink') or ''}")
    if kind == "post":
        print(f"分类：{', '.join(map(str, item.get('categories', [])))}")
        print(f"标签：{item.get('mt_keywords', '')}")
    else:
        print(f"顺序：{item.get('wp_page_order', '')}")
        print(f"模板：{item.get('wp_page_template', '')}")


def check_connection(client: xmlrpc.client.ServerProxy, config: dict[str, Any]) -> None:
    methods = client.system.listMethods()
    required = {
        "metaWeblog.newPost",
        "metaWeblog.editPost",
        "metaWeblog.getPost",
        "metaWeblog.getRecentPosts",
        "wp.newPage",
        "wp.editPage",
        "wp.getPage",
        "wp.getPageList",
    }
    missing = sorted(required.difference(methods))
    if missing:
        raise RuntimeError(f"接口不支持所需方法：{', '.join(missing)}")

    _, username, password = credentials(config)
    if "wp.getUsersBlogs" in methods:
        blogs = client.wp.getUsersBlogs(username, password)
    else:
        blogs = client.blogger.getUsersBlogs("", username, password)

    print(f"连接成功：接口支持 {len(methods)} 个方法，账号认证通过。")
    if isinstance(blogs, list) and blogs and isinstance(blogs[0], dict):
        print(f"博客：{blogs[0].get('blogName') or blogs[0].get('blogid', '')}")
    print("文章管理：可用；独立页面管理：可用。")


def fetch_post(
    client: xmlrpc.client.ServerProxy,
    blog_id: int,
    username: str,
    password: str,
    post_id: int,
) -> dict[str, Any]:
    try:
        return client.metaWeblog.getPost(post_id, username, password)
    except (xmlrpc.client.Error, OSError, ExpatError, HTTPException):
        client("close")()
        posts = client.metaWeblog.getRecentPosts(blog_id, username, password, 1000)
        for post in posts:
            if str(post.get("postid")) == str(post_id):
                return post
    raise RuntimeError(f"找不到文章，ID：{post_id}")


def parse_partial_xml_value(section: str, name: str) -> Any:
    pattern = (
        r"<member>\s*<name>"
        + re.escape(name)
        + r"</name>\s*<value>(.*?)</value>\s*</member>"
    )
    match = re.search(pattern, section, flags=re.DOTALL)
    if not match:
        return None
    value = match.group(1)
    for tag in ("string", "dateTime.iso8601"):
        typed = re.search(rf"<{tag}>(.*?)</{tag}>", value, flags=re.DOTALL)
        if typed:
            return html.unescape(typed.group(1))
    integer = re.search(r"<(?:int|i4)>(-?\d+)</(?:int|i4)>", value)
    if integer:
        return int(integer.group(1))
    boolean = re.search(r"<boolean>([01])</boolean>", value)
    if boolean:
        return boolean.group(1) == "1"
    return None


def fetch_partial_page(config: dict[str, Any], page_id: int) -> dict[str, Any]:
    blog_id, username, password = credentials(config)
    request_body = xmlrpc.client.dumps(
        (blog_id, username, password), methodname="wp.getPages", allow_none=True
    ).encode("utf-8")
    request = urllib.request.Request(
        str(config["endpoint"]),
        data=request_body,
        headers={"Content-Type": "text/xml"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()

    text = raw.decode("utf-8", errors="replace")
    fields = (
        "page_id",
        "page_status",
        "description",
        "title",
        "link",
        "permaLink",
        "text_more",
        "mt_allow_comments",
        "wp_slug",
        "wp_password",
        "wp_page_order",
        "wp_page_template",
    )
    for section in text.split("<value><struct>")[1:]:
        item = {field: parse_partial_xml_value(section, field) for field in fields}
        item = {key: value for key, value in item.items() if value is not None}
        if str(item.get("page_id")) == str(page_id):
            item["_partial_metadata"] = True
            return item
    raise RuntimeError(f"找不到独立页面，ID：{page_id}")


def fetch_page(
    client: xmlrpc.client.ServerProxy,
    config: dict[str, Any],
    page_id: int,
) -> dict[str, Any]:
    blog_id, username, password = credentials(config)
    try:
        return client.wp.getPage(blog_id, page_id, username, password)
    except (xmlrpc.client.Error, OSError, ExpatError, HTTPException):
        client("close")()
        try:
            pages = client.wp.getPages(blog_id, username, password)
        except (xmlrpc.client.Error, OSError, ExpatError, HTTPException):
            client("close")()
            return fetch_partial_page(config, page_id)
        else:
            for page in pages:
                if str(page.get("page_id")) == str(page_id):
                    return page
    raise RuntimeError(f"找不到独立页面，ID：{page_id}")


def handle_post(
    client: xmlrpc.client.ServerProxy,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    blog_id, username, password = credentials(config)

    if args.action == "list":
        posts = client.metaWeblog.getRecentPosts(blog_id, username, password, args.limit)
        print("ID\t状态\t标题")
        for post in posts:
            print(f"{post.get('postid', '')}\t{post.get('post_status', '')}\t{post.get('title', '')}")
        return

    if args.action == "get":
        post = fetch_post(client, blog_id, username, password, args.post_id)
        print_item(post, "post")
        if args.output:
            export_document(post, "post", args.output, args.force)
        return

    content = build_content(args, "post")
    should_publish = args.status == "publish"
    if args.action == "new":
        post_id = client.metaWeblog.newPost(
            blog_id, username, password, content, should_publish
        )
        action = "已发布" if should_publish else "已创建草稿"
        print(f"{action}，文章 ID：{post_id}")
        return

    existing = fetch_post(client, blog_id, username, password, args.post_id)
    merge_post_metadata(content, existing)
    result = client.metaWeblog.editPost(
        args.post_id, username, password, content, should_publish
    )
    if not result:
        raise RuntimeError(f"文章更新失败，ID：{args.post_id}")
    action = "发布" if should_publish else "草稿"
    print(f"文章 {args.post_id} 已更新并以{action}状态保存。")


def handle_page(
    client: xmlrpc.client.ServerProxy,
    config: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    blog_id, username, password = credentials(config)

    if args.action == "list":
        pages = client.wp.getPageList(blog_id, username, password)
        print("ID\t标题\t创建时间")
        for page in pages:
            print(f"{page.get('page_id', '')}\t{page.get('page_title', '')}\t{page.get('dateCreated', '')}")
        return

    if args.action == "get":
        page = fetch_page(client, config, args.page_id)
        print_item(page, "page")
        if args.output:
            export_document(page, "page", args.output, args.force)
        return

    if args.action == "delete":
        if str(args.confirm) != str(args.page_id):
            raise RuntimeError("确认值与页面 ID 不一致，已取消删除")
        result = client.wp.deletePage(blog_id, username, password, args.page_id)
        if not result:
            raise RuntimeError(f"页面删除失败，ID：{args.page_id}")
        print(f"独立页面 {args.page_id} 已永久删除。")
        return

    content = build_content(args, "page")
    should_publish = args.status == "publish"
    if args.action == "new":
        page_id = client.wp.newPage(
            blog_id, username, password, content, should_publish
        )
        action = "已发布" if should_publish else "已创建草稿"
        print(f"{action}，独立页面 ID：{page_id}")
        return

    try:
        existing = fetch_page(client, config, args.page_id)
    except (RuntimeError, xmlrpc.client.Error, OSError, ExpatError, HTTPException) as exc:
        if not args.force_without_metadata:
            raise RuntimeError(
                "当前服务器无法读取该页面的完整元数据。为避免覆盖 Slug、模板和排序，"
                "更新已停止；确认接受重置风险后可加 --force-without-metadata"
            ) from exc
        print("警告：未能读取原页面元数据，将仅使用本次命令提供的页面属性。")
    else:
        merge_page_metadata(content, existing)

    result = client.wp.editPage(
        blog_id, args.page_id, username, password, content, should_publish
    )
    if not result:
        raise RuntimeError(f"独立页面更新失败，ID：{args.page_id}")
    action = "发布" if should_publish else "草稿"
    print(f"独立页面 {args.page_id} 已更新并以{action}状态保存。")


def add_common_document_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("document", type=Path, help="Markdown 文件，第一行为 # 标题")
    parser.add_argument(
        "--status",
        choices=("draft", "publish"),
        required=True,
        help="明确指定保存为草稿或立即发布",
    )
    parser.add_argument("--title", help="覆盖 Markdown 第一行的标题")
    parser.add_argument("--slug", help="Slug")
    parser.add_argument(
        "--comments", choices=("open", "closed"), help="开启或关闭评论"
    )
    parser.add_argument("--content-password", help="文章或页面访问密码；空字符串表示清除")


def add_post_document_arguments(parser: argparse.ArgumentParser) -> None:
    add_common_document_arguments(parser)
    parser.add_argument("--excerpt", help="摘要；默认取 <!--more--> 前的正文")
    parser.add_argument("--category", action="append", help="分类，可重复传入")
    parser.add_argument("--tag", action="append", help="标签，可重复传入")


def add_page_document_arguments(
    parser: argparse.ArgumentParser, *, updating: bool = False
) -> None:
    add_common_document_arguments(parser)
    parser.add_argument("--order", type=int, help="页面排序数字")
    parser.add_argument("--template", help="页面模板文件名")
    if updating:
        parser.add_argument(
            "--force-without-metadata",
            action="store_true",
            help="服务器无法读取原元数据时仍继续更新，可能重置页面属性",
        )


def add_get_arguments(parser: argparse.ArgumentParser, id_name: str) -> None:
    parser.add_argument(id_name, type=int, help="Typecho 内容 ID")
    parser.add_argument("--output", type=Path, help="导出为本地 Markdown 文件")
    parser.add_argument("--force", action="store_true", help="允许覆盖导出文件")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="管理 Typecho 文章和独立页面")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"本地配置文件（默认：{DEFAULT_CONFIG.name}）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="只检查接口和账号，不修改博客")

    post_parser = subparsers.add_parser("post", help="管理文章")
    post_actions = post_parser.add_subparsers(dest="action", required=True)
    post_list = post_actions.add_parser("list", help="列出最近文章")
    post_list.add_argument("--limit", type=int, default=10, help="返回数量，默认 10")
    add_get_arguments(post_actions.add_parser("get", help="查看或导出文章"), "post_id")
    add_post_document_arguments(post_actions.add_parser("new", help="新增文章"))
    post_update = post_actions.add_parser("update", help="更新文章")
    post_update.add_argument("post_id", type=int, help="文章 ID")
    add_post_document_arguments(post_update)

    page_parser = subparsers.add_parser("page", help="管理独立页面")
    page_actions = page_parser.add_subparsers(dest="action", required=True)
    page_actions.add_parser("list", help="列出独立页面")
    add_get_arguments(page_actions.add_parser("get", help="查看或导出页面"), "page_id")
    add_page_document_arguments(page_actions.add_parser("new", help="新增独立页面"))
    page_update = page_actions.add_parser("update", help="更新独立页面")
    page_update.add_argument("page_id", type=int, help="独立页面 ID")
    add_page_document_arguments(page_update, updating=True)
    page_delete = page_actions.add_parser("delete", help="永久删除独立页面")
    page_delete.add_argument("page_id", type=int, help="独立页面 ID")
    page_delete.add_argument(
        "--confirm", required=True, help="必须再次输入相同的页面 ID"
    )

    # Backwards-compatible aliases from the first version of this script.
    legacy_new = subparsers.add_parser("new", help="新增文章（兼容旧命令）")
    add_post_document_arguments(legacy_new)
    legacy_update = subparsers.add_parser("update", help="更新文章（兼容旧命令）")
    legacy_update.add_argument("post_id", type=int, help="文章 ID")
    add_post_document_arguments(legacy_update)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config.resolve())
        client = create_client(config)
        if args.command == "check":
            check_connection(client, config)
        elif args.command == "page":
            handle_page(client, config, args)
        else:
            if args.command in ("new", "update"):
                args.action = args.command
            handle_post(client, config, args)
        return 0
    except (RuntimeError, OSError, socket.timeout, xmlrpc.client.Error, HTTPException, ExpatError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
