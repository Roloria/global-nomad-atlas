const communities = require("../../data/communities");
const meta = require("../../data/meta");
const fmt = require("../../utils/format");
const theme = require("../../utils/theme");

const SORTS = [
  { key: "score", label: "综合分" },
  { key: "capacity", label: "容量" },
  { key: "name", label: "名称" }
];

Page({
  data: {
    theme: "light",
    stats: [],

    search: "",
    regions: meta.COMM_REGIONS,
    region: "全部",
    types: ["全部类型"].concat(meta.COMM_TYPES),
    typeIndex: 0,
    sorts: SORTS,
    sortKey: "score",

    list: [],
    total: communities.length
  },

  onLoad() {
    this.buildStats();
    this.build();
  },

  onShow() {
    theme.applyToPage(this);
    if (typeof this.getTabBar === "function" && this.getTabBar()) this.getTabBar().sync(1);
  },

  buildStats() {
    const regionCounts = {};
    const typeCounts = {};
    communities.forEach((c) => {
      regionCounts[c.region] = (regionCounts[c.region] || 0) + 1;
      typeCounts[c.type] = (typeCounts[c.type] || 0) + 1;
    });
    const topRegion = Object.entries(regionCounts).sort((a, b) => b[1] - a[1])[0];
    const topType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0];
    const highest = [...communities].sort((a, b) => b.score - a.score)[0];
    this.setData({
      stats: [
        { l: "收录社区", v: String(communities.length), s: "5 大区域 + 全球线上" },
        { l: "最多区域", v: topRegion[0], s: topRegion[1] + " 个社区" },
        { l: "最多类型", v: topType[0], s: topType[1] + " 个社区" },
        { l: "综合最高", v: highest.score.toFixed(1), s: highest.name + " · " + highest.city }
      ]
    });
  },

  build() {
    const s = this.data;
    const q = (s.search || "").trim().toLowerCase();
    let pool = [...communities];
    if (s.region !== "全部") pool = pool.filter((d) => d.region === s.region);
    if (s.typeIndex > 0) pool = pool.filter((d) => d.type === s.types[s.typeIndex]);
    if (q) {
      pool = pool.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          (d.nameEn || "").toLowerCase().includes(q) ||
          d.city.toLowerCase().includes(q) ||
          d.country.toLowerCase().includes(q) ||
          (d.intro || "").toLowerCase().includes(q)
      );
    }
    if (s.sortKey === "score") pool.sort((a, b) => b.score - a.score);
    else if (s.sortKey === "name") pool.sort((a, b) => a.name.localeCompare(b.name, "zh"));
    else if (s.sortKey === "capacity") pool.sort((a, b) => b.capacity - a.capacity);

    const list = pool.map((d) => ({
      rank: d.rank,
      flag: d.flag,
      name: d.name,
      nameEn: d.nameEn,
      type: d.type,
      city: d.city,
      country: d.country,
      region: d.region,
      regionColor: fmt.REGION_COLORS[d.region],
      regionBg: fmt.REGION_BGS[d.region],
      intro: d.intro,
      price: d.price,
      capacityText: d.capacity >= 1000 ? currency_num(d.capacity) + "+" : String(d.capacity),
      policy: d.policy,
      scoreText: d.score.toFixed(1),
      hasUrl: !!(d.url && d.url !== "-"),
      hasEmail: !!(d.email && d.email !== "-"),
      hasSocial: !!(d.social && d.social !== "-"),
      url: d.url && d.url !== "-" ? d.url : "",
      email: d.email && d.email !== "-" ? d.email : "",
      social: d.social && d.social !== "-" ? d.social : ""
    }));

    this.setData({ list });
  },

  // ---------- 交互 ----------
  onSearch(e) {
    this.setData({ search: e.detail.value });
    this.build();
  },

  onRegion(e) {
    this.setData({ region: e.currentTarget.dataset.region });
    this.build();
  },

  onTypeChange(e) {
    this.setData({ typeIndex: Number(e.detail.value) });
    this.build();
  },

  onSort(e) {
    this.setData({ sortKey: e.currentTarget.dataset.key });
    this.build();
  },

  onShareAppMessage() {
    return {
      title: "牛马迁移指南 · 全球 60 个数字游民社区",
      path: "/pages/communities/communities",
      imageUrl: "/assets/icons/logo-badge.png"
    };
  },

  // 小程序内不能直接打开外链，统一复制到剪贴板
  onCopy(e) {
    const { kind, rank } = e.currentTarget.dataset;
    const item = this.data.list.find((x) => String(x.rank) === String(rank));
    if (!item) return;
    const labels = { url: "官网", email: "邮箱", social: "社群链接" };
    const value = kind === "url" ? item.url : kind === "email" ? item.email : kind === "social" ? item.social : "";
    if (!value) {
      wx.showToast({ title: "该社区未提供" + (labels[kind] || "此链接"), icon: "none" });
      return;
    }
    wx.setClipboardData({
      data: value,
      success: () => wx.showToast({ title: "已复制" + (labels[kind] || "链接"), icon: "success" })
    });
  }
});

function currency_num(n) {
  return Number(n || 0).toLocaleString();
}
