/**
 * 主题：浅色（官网暖调，默认）/ 深色（原版冷色），手动切换后由本地存储记忆。
 * 与网站 localStorage「gdna-theme」同语义。
 */
const KEY = "gdna-theme";

const NAV = {
  light: { frontColor: "#000000", backgroundColor: "#faf9f5" },
  dark: { frontColor: "#ffffff", backgroundColor: "#0f1216" }
};

function current() {
  try {
    return wx.getStorageSync(KEY) === "dark" ? "dark" : "light";
  } catch (e) {
    return "light";
  }
}

function syncNavBar(t) {
  const c = NAV[t === "dark" ? "dark" : "light"];
  wx.setNavigationBarColor({
    frontColor: c.frontColor,
    backgroundColor: c.backgroundColor,
    fail: () => {}
  });
}

/** 页面 onShow 调用：同步页面 data.theme 与导航栏颜色 */
function applyToPage(page) {
  const t = current();
  if (page) page.setData({ theme: t });
  syncNavBar(t);
  return t;
}

/** 切换主题并同步所有在栈页面 + 各页的自定义 tabBar */
function toggle() {
  const next = current() === "dark" ? "light" : "dark";
  try {
    wx.setStorageSync(KEY, next);
  } catch (e) {}
  const pages = getCurrentPages();
  pages.forEach((p) => {
    p.setData({ theme: next });
    if (typeof p.getTabBar === "function" && p.getTabBar()) {
      p.getTabBar().setData({ theme: next });
    }
  });
  syncNavBar(next);
  return next;
}

module.exports = { current, applyToPage, toggle, syncNavBar };
