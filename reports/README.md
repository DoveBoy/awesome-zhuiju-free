# 验证与投诉记录

这里保存资源的历史记录，确保评分与下架决定可以被追溯。

## 文件

- `verifications.json`：每次人工或自动验证的结果，只追加、不覆盖历史。
- `availability.json`：GitHub Actions 每日生成的当前可访问性快照。
- `notices.json`：权利通知、安全投诉和其他正式处理记录。
- `navigation-sync.json`：导航后台的同步规则、当前站点基线和增删改操作历史。

## 记录原则

- 不记录与处理无关的个人信息。
- 未核实的投诉状态使用 `received`，不要直接写成事实。
- 资源被降级、暂停或下架时，应写明原因和关联记录。
- 投诉撤回或处理完成后保留历史，但更新处理状态。
- 自动可访问性检测只表示 GitHub Actions 节点当时能否访问，不替代人工验证。
- 每次修改导航后台前，先核对 `README.md`、`navigation-sync.json` 的 `current_state` 和后台实际数据。
- 导航后台操作完成后，更新 `current_state`，并向 `operations` 追加记录；历史记录不覆盖。

投诉状态：

- `received`：已收到，等待复核
- `reviewing`：正在复核
- `actioned`：已采取措施
- `rejected`：材料不足或不适用
- `withdrawn`：提交方撤回
