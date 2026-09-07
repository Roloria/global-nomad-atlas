# cloudfunctions/（云函数占位目录）

「牛马迁移指南」小程序当前为**纯前端版本**：榜单与社区数据内置于
`miniprogram/data/`，提交的数据暂存本机（`nomad_submissions`）。

后续接入微信云开发时，在此目录创建云函数（在微信开发者工具中
右键 `cloudfunctions/` → 新建 Node.js 云函数），建议的首批函数：

| 函数 | 用途 |
| --- | --- |
| `getLatestData` | 返回最新 cities / communities JSON（替代内置数据，实现与网站同步上线） |
| `getExchangeRate` | 拉取最新 USD→CNY 汇率（对应网站 GitHub Action 生成的 `data/exchange-rate.json`） |
| `submitContribution` | 接收提交表单数据 → 自动创建 GitHub Issue（对应网站的匿名提交 Worker，见 `api/README.md`） |

接入步骤概要：
1. 微信开发者工具 → 云开发 → 开通环境（记下 envId）
2. `miniprogram/app.js` 的 `onLaunch` 中 `wx.cloud.init({ env: "<envId>" })`
3. 将表单提交改为调用 `submitContribution`（见 `pages/submit/submit.js` 中 `STORE_KEY` 相关注释）
