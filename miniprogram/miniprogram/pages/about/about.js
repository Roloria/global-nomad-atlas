const meta = require("../../data/meta");
const theme = require("../../utils/theme");

Page({
  data: {
    theme: "light",
    pillars: [
      { no: "01", icon: "👥", title: "开放共建", text: "拿到链接就能编辑，没有中心化运营。补一座城、改一个评分、加一条备注——每一个真正住过那里的人，都是数据源。" },
      { no: "02", icon: "👁️", title: "数据透明", text: "12 个维度加权合成综合分，权重与公式完全公开。不是黑箱评分，而是社区共识——人人可复算、可质疑、可讨论。" },
      { no: "03", icon: "🕘", title: "开源可追溯", text: "每次改动自动生成 GitHub 提交记录，git 历史就是一部「城市变迁编年史」。改错了？历史版本随时回滚。" }
    ],
    steps: [
      { no: "STEP / 01", title: "编辑", text: "打开腾讯文档，像用在线表格一样直接改。无需登录，拿到链接就能动手。" },
      { no: "STEP / 02", title: "同步", text: "同步脚本自动比对文档与开源仓库，你的改动生成一个 GitHub PR。" },
      { no: "STEP / 03", title: "校验", text: "CI 自动检查排名一致性、成本与气温合理区间；人工审核把最后一道关。" },
      { no: "STEP / 04", title: "上线", text: "合并后榜单即时更新，你的 GitHub 头像进入贡献者列表。" }
    ],
    dims: meta.SCORE_FIELDS,
    formula: meta.FORMULA,
    faq: meta.FAQ,
    faqOpen: 0,

    site: "",
    repo: "",
    sheet: "",

    pipeline: "腾讯文档 ⇄ 同步脚本 → GitHub PR → CI 校验 → 榜单网站 / 小程序"
  },

  onLoad() {
    const app = getApp();
    this.setData({
      site: app.globalData.site,
      repo: app.globalData.repo,
      sheet: app.globalData.sheet
    });
  },

  onShow() {
    theme.applyToPage(this);
    if (typeof this.getTabBar === "function" && this.getTabBar()) this.getTabBar().sync(2);
  },

  onThemeSwitch() {
    theme.toggle();
  },

  onFaqTap(e) {
    const i = Number(e.currentTarget.dataset.i);
    this.setData({ faqOpen: this.data.faqOpen === i ? -1 : i });
  },

  // 审核期间暂时下线：提交入口已在 about.wxml 注释、页面注册已从 app.json 移除，恢复时同步还原
  // onGoSubmit() {
  //   wx.navigateTo({ url: "/pages/submit/submit" });
  // },

  onShareAppMessage() {
    return {
      title: "牛马迁移指南 · 你的下一座城，不该靠运气选",
      path: "/pages/about/about",
      imageUrl: "/assets/icons/logo-badge.png"
    };
  },

  onCopyLink(e) {
    const key = e.currentTarget.dataset.key;
    const labels = { site: "榜单网站", repo: "GitHub 仓库", sheet: "腾讯文档共建表" };
    const value = this.data[key];
    if (!value) return;
    wx.setClipboardData({
      data: value,
      success: () => wx.showToast({ title: "已复制" + (labels[key] || "链接"), icon: "success" })
    });
  }
});
