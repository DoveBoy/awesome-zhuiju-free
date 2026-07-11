# 提交至 Awesome 列表清单

> 目标：将 awesome-zhuiju-free 加入其他知名 awesome 列表，获取持续被动流量和 Star。
> 提交方式均为 GitHub PR，按优先级排序执行。

---

## 第一梯队：强烈推荐（影响力大，匹配度高）

### 1. iptv-org/awesome-iptv
- 地址：https://github.com/iptv-org/awesome-iptv
- Stars：约 10k+
- 匹配理由：专门收录 IPTV 相关资源，项目收录了 IPTV 订阅源 + TVBox 配置地址，直接相关
- 提交位置：README 的 `Misc` 或 `Tools` 部分，描述定位为"中文追剧资源导航，含 IPTV 订阅源和每日可用性检测"
- PR 参考描述：
  ```
  Add awesome-zhuiju-free — a curated list of free Chinese streaming resources
  including IPTV subscriptions and TVBox configs, with daily automated availability checks.
  ```

### 2. OshekharO/awesome-entertainment
- 地址：https://github.com/OshekharO/awesome-entertainment
- Stars：活跃维护中
- 匹配理由：专收"娱乐相关 App 和网站"，有电影/电视流媒体分类，项目高度匹配
- 提交位置：`Movies & TV Shows` 或 `Tools & Resources` 部分
- 亮点：这个 list 本身受众就是找免费流媒体资源的用户，曝光转化率高

### 3. sindresorhus/awesome（终极目标）
- 地址：https://github.com/sindresorhus/awesome
- Stars：350k+，全球最大 awesome 元列表
- 匹配理由：awesome-zhuiju-free 本身是一个 awesome list，可作为独立条目提交进去
- 门槛说明：**要求极严格**，需满足：
  - 仓库有 awesome-list badge
  - 至少 30 天历史
  - 有合理的贡献说明（CONTRIBUTING.md ✅）
  - 内容质量高、分类清晰
  - README 格式规范
- 提交位置：`Miscellaneous` 或 `Entertainment` 分类
- 建议：等项目到 2000+ Star 再提交，成功率更高；先做其他 list 积累背书
- 贡献指南：https://github.com/sindresorhus/awesome/blob/main/contributing.md

---

## 第二梯队：值得尝试（中等影响力）

### 4. aliesbelik/awesome-free
- 搜索关键词：`github awesome-free awesome-freeware`
- 各类"免费资源"合集列表，直接匹配项目的"免费"属性
- 建议先搜索最近活跃的同类 list，找 CONTRIBUTING.md 存在的那些

### 5. andrew/ultimate-awesome
- 地址：https://github.com/andrew/ultimate-awesome
- 说明：自动聚合所有 awesome-list，每日更新；提交后会自动被收录
- 提交方式：直接提 PR，加入你的 list 链接

### 6. icopy-site/awesome-cn
- 地址：https://github.com/icopy-site/awesome-cn
- 说明：中文 awesome 列表合集，专门面向中文用户
- 匹配理由：项目是中文内容，受众完全重合
- 提交位置：新建一个 `docs/awesome/awesome-zhuiju-free.md` 翻译/介绍文件，提 PR

### 7. GitHubDaily/GitHubDaily
- 地址：https://github.com/GitHubDaily/GitHubDaily
- 说明：中文 GitHub 日报项目，专门分享高质量 GitHub 项目
- 提交方式：在 Issues 中推荐项目，或直接提 PR 补充到列表
- 注意：同时联系他们的微信公众号（见 blogger-pitch.md）

---

## 第三梯队：小众但精准

### 8. freemediatools.com 相关 GitHub 列表
- 搜索 `github awesome free media tools resources` 找近期活跃的列表
- 专门收录免费媒体工具的列表，项目有相当匹配度

### 9. 中文影视/TVBox 相关 GitHub 合集
- 搜索 `github TVBox config list awesome` 找同类导航型项目
- 在这类项目的 README 评论区或 Issues 推荐互相收录

---

## 模板一：英文 PR 描述（用于向英文 awesome 列表提 PR）

> 适用：iptv-org/awesome-iptv、OshekharO/awesome-entertainment、sindresorhus/awesome 等英文列表

```markdown
## Add awesome-zhuiju-free

**What is this?**
A manually curated list of free, ad-free Chinese streaming resources. Every resource is hand-picked — only free, genuinely ad-free content makes it in. Includes online video sites, video apps, TVBox/movie-warehouse config addresses, IPTV subscriptions, subtitle resources, and magnet/BT search tools.

**Why is it awesome?**
- Every resource is manually vetted — only free, ad-free content is accepted; paid or ad-heavy sites are excluded
- GitHub Actions runs daily availability checks on all listed resources — live status shown in README (🟢/🟡/🔴)
- Fully open source with structured JSON data and schema validation
- Community contribution via Issue templates, no Git knowledge required
- 1000+ GitHub Stars in the first week

**Links**
- GitHub: https://github.com/laoma2053/awesome-zhuiju-free
- Website: https://zhuiju.me
- Gitee (China mirror): https://gitee.com/laoma2053/awesome-zhuiju-free
```

---

## 模板二：中文 Issue 自荐（用于 GitHubDaily、中文社区平台）

> 适用：GitHubDaily/GitHubDaily Issues、HelloGitHub 投稿、中文 GitHub 社区推荐

**Issue 标题（直接复制）：**

```
【开源自荐】Awesome Zhuiju Free：免费无广告追剧资源导航，每日自动检测可用性
```

```markdown
项目地址：https://github.com/laoma2053/awesome-zhuiju-free

在线体验：https://zhuiju.me

追剧找资源，最烦的不是没有资源，而是"不知道今天哪个还能用"——收藏夹里十几个站，打开才发现一半挂了，剩下几个全是弹窗广告。

Awesome Zhuiju Free 专门解决这个问题。它是一份经过人工精选的免费无广告追剧资源导航——每一个收录的资源都经过维护者审核筛选，确保免费且无广告，劣质资源不会进来。最大的不同在于：GitHub Actions 每天早上自动检测所有收录资源是否可访问，结果实时标注在页面上，打开就知道今天哪些能用。

亮点：

1. **人工精选，仅收录免费无广告资源** — 每个资源都经过维护者审核，有广告、需要付费或质量差的资源不会被收录。
2. **每日自动可用性检测** — GitHub Actions 每天自动跑一遍，🟢可访问 / 🟡访问受限 / 🔴无法访问，不用自己逐一验证。
3. **覆盖全分类** — 在线影视、影视APP、网盘搜索、TVBox影视仓配置地址、磁力BT、字幕资源，60+ 个精选资源。
4. **结构化开源数据** — 资源数据存在 JSON 文件，有 Schema 验证，每个资源有评分和风险标注（版权/安全/隐私），如实填写不掩盖。
5. **社区驱动，零门槛贡献** — 普通用户通过 Issue 模板提交新资源，维护者审核后命令自动发布，不需要懂 Git。

适用人群：所有追剧的中文用户，特别是无广告在线观看用户、网盘追剧用户、TVBox/影视仓玩家、IPTV 用户。

开源协议：MIT

截图：
（附 README 截图或 zhuiju.me 网站截图）
```

---

## 执行清单

| 目标列表 | 优先级 | 状态 | PR 链接 |
|---|---|---|---|
| iptv-org/awesome-iptv | ⭐⭐⭐ | 待提交 | |
| OshekharO/awesome-entertainment | ⭐⭐⭐ | 待提交 | |
| andrew/ultimate-awesome | ⭐⭐ | 待提交 | |
| icopy-site/awesome-cn | ⭐⭐ | 待提交 | |
| GitHubDaily/GitHubDaily | ⭐⭐ | 待提交 | |
| sindresorhus/awesome | ⭐⭐⭐ | 等 2000+ Star 后再提 | |
