# 牛马迁移指南 · 微信小程序（Global Nomad Atlas Mini Program）

复用榜单网站（`docs/index.html`）的核心功能与移动端视觉，原生微信小程序实现。
当前为**纯前端版本**：数据内置、提交暂存本机，暂未开通云开发与真实 appid，
后续在微信开发者工具中打开即可接入。

## 目录结构

```
miniprogram/
├── project.config.json        # 项目配置（appid 为 touristappid 占位，接入时替换）
├── miniprogram/               # 小程序源码（miniprogramRoot）
│   ├── app.js / app.json / app.wxss
│   ├── sitemap.json
│   ├── assets/icons/          # logo-badge.png（品牌徽章）+ tab 图标 4 配色变体（均由脚本生成）
│   ├── components/
│   │   └── nav-header/        # 自定义导航（三个 tab 页 navigationStyle=custom）：徽章 Logo + 加粗应用名
│   ├── custom-tab-bar/        # 图标 + 文字自定义 tabBar（城市榜 / 社区地图 / 共建）
│   ├── data/
│   │   ├── cities.js          # 80 城数据（自动生成，勿手改）
│   │   ├── communities.js     # 60 社区数据（自动生成，勿手改）
│   │   └── meta.js            # 评分维度/权重/公式/FAQ
│   ├── utils/
│   │   ├── theme.js           # 浅/深主题（与网站 gdna-theme 同语义；入口在「共建」页外观设置）
│   │   ├── currency.js        # USD/CNY 与汇率（默认 7.20，可手动改）
│   │   └── format.js          # tier 圆点 / 成本分档 / 区域配色
│   └── pages/
│       ├── index/             # 城市榜：搜索 + 区域/国家/TOP 筛选 + 排序 + 12 维展开明细
│       ├── communities/       # 社区地图：搜索 + 区域/类型筛选 + 排序 + 链接复制
│       ├── about/             # 共建：顶部标语 + 三大支柱 + 评分方法论 + 流水线 + FAQ + 外观设置
│       └── submit/            # 提交数据：12 维滑杆表单 + 综合分实时计算 + 本地存储 + Issue 文本
└── cloudfunctions/            # 云函数占位（接入云开发时使用，见其 README.md）
```

顶部设计约定：三个 tab 页使用自定义导航（`navigationStyle: "custom"`），
导航区只放品牌徽章 Logo + 加粗应用名；「你的下一座城，不该靠运气选。」
标语展示在共建页顶部；主题（浅/深）切换入口在共建页「外观」设置区。

## 与网站的功能映射

| 网站（docs/index.html） | 小程序 |
| --- | --- |
| 城市榜单 + 搜索/区域/国家/TOP 筛选 + 列排序 | 城市榜页 chips + picker + 卡片展开明细 |
| 行展开 12 维明细（tier 圆点 + 档位词 + 说明） | 卡片点击展开，视觉同源 |
| USD/CNY 汇率切换（默认 7.20，双击改汇率） | 货币分段器 + 点按汇率行弹窗修改 |
| 浅色（官网暖调）/深色主题切换 + 记忆 | 共建页「外观」设置切换，wx storage 记忆 |
| 社区地图（60 社区：类型/区域/排序/链接） | 社区页；外链改为「复制到剪贴板」 |
| 匿名提交表单（localStorage + GitHub Issue 预填） | 提交页滑杆表单，综合分同公式实时计算，Issue 文本一键复制 |
| 评分方法论 / FAQ / 共建流程 | 共建页原样移植 |

## 数据更新流程

1. 更新 `data/*.csv` → 同步至 `docs/index.html`（现有流程不变）
2. 运行 `node tools/build_miniprogram_data.js` 重新生成 `miniprogram/miniprogram/data/*.js`
3. 小程序端发版即可同步最新数据

## 后续接入清单

- [ ] 注册小程序，把 `project.config.json` 的 `appid` 从 `touristappid` 换成真实 appid
- [ ] 微信开发者工具导入 `miniprogram/` 目录（本仓库内），真机预览调整细节
- [ ] （可选）开通云开发，按 `cloudfunctions/README.md` 添加 `getLatestData` / `getExchangeRate` / `submitContribution`
- [ ] （可选）小程序搜索优化：为三个 tab 页配置页面收录与分享标题
