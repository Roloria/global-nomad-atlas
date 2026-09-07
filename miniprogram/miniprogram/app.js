const theme = require("./utils/theme");

App({
  globalData: {
    // 品牌信息
    brand: "牛马迁移指南",
    brandEn: "Global Nomad Atlas",
    repo: "https://github.com/Roloria/global-digital-nomad",
    site: "https://roloria.github.io/global-digital-nomad/",
    sheet: "https://docs.qq.com/sheet/DREppWERNRWdwcXRR"
  },

  onLaunch() {
    // 主题记忆（与网站 localStorage「gdna-theme」同键位语义）
    theme.syncNavBar(theme.current());
  }
});
