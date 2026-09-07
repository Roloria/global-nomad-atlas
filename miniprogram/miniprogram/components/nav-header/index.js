Component({
  properties: {
    theme: { type: String, value: "light" }
  },

  data: {
    statusBarHeight: 20
  },

  lifetimes: {
    attached() {
      try {
        const info = typeof wx.getWindowInfo === "function" ? wx.getWindowInfo() : wx.getSystemInfoSync();
        this.setData({ statusBarHeight: (info && info.statusBarHeight) || 20 });
      } catch (e) {}
    }
  }
});
