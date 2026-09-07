const theme = require("../utils/theme");

Component({
  data: {
    selected: 0,
    theme: "light",
    list: [
      { pagePath: "/pages/index/index", text: "城市榜", icon: "tab-city" },
      { pagePath: "/pages/communities/communities", text: "社区地图", icon: "tab-globe" },
      { pagePath: "/pages/about/about", text: "共建", icon: "tab-users" }
    ]
  },

  lifetimes: {
    attached() {
      this.setData({ theme: theme.current() });
    }
  },

  methods: {
    /** 页面 onShow 调用：同步选中项与主题 */
    sync(selected) {
      const t = theme.current();
      if (this.data.selected !== selected || this.data.theme !== t) {
        this.setData({ selected, theme: t });
      }
    },

    onTap(e) {
      const index = Number(e.currentTarget.dataset.index);
      const path = e.currentTarget.dataset.path;
      if (index === this.data.selected) return;
      wx.switchTab({ url: path });
    }
  }
});
