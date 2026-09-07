const cities = require("../../data/cities");
const meta = require("../../data/meta");
const fmt = require("../../utils/format");
const theme = require("../../utils/theme");
const currency = require("../../utils/currency");

// 排序入口：key 为数据字段名
const SORTS = [
  { key: "排名", label: "排名", dir: 1 },
  { key: "综合分", label: "综合分", dir: -1 },
  { key: "月成本", label: "月成本", dir: 1 },
  { key: "游民数", label: "游民数", dir: -1 }
];
const SORT_FIELD = { 排名: "排名", 综合分: "综合分", 月成本: "月成本 (USD)", 游民数: "游民数" };
const TOP_OPTIONS = ["全部排名", "TOP 20", "TOP 50"];
const QUICK_DOTS = [
  { key: "网络", label: "网" },
  { key: "社群", label: "群" },
  { key: "安全", label: "安" },
  { key: "空气", label: "气" }
];

Page({
  data: {
    theme: "light",
    cityCount: cities.length,
    commCount: 60,

    // 统计
    stats: [],

    // 筛选状态
    search: "",
    region: "全部",
    regions: meta.REGION_LIST,
    countryOptions: ["全部国家"],
    countryIndex: 0,
    topOptions: TOP_OPTIONS,
    topIndex: 0,
    sorts: SORTS,
    sortKey: "排名",
    sortDir: 1,

    // 列表
    list: [],
    expandedRank: null,

    // 货币
    currency: "USD",
    rateText: "7.20",

    freshness: ""
  },

  onLoad() {
    this.refreshCurrency();
    this.buildCountries();
    this.build();
  },

  onShow() {
    theme.applyToPage(this);
    if (typeof this.getTabBar === "function" && this.getTabBar()) this.getTabBar().sync(0);
    // 其他页改过货币时回到本页需重算
    if (currency.current() !== this.data.currency) {
      this.refreshCurrency();
      this.build();
    }
  },

  refreshCurrency() {
    this.setData({
      currency: currency.current(),
      rateText: currency.rate().toFixed(2)
    });
  },

  // ---------- 构建：统计 + 视图列表 ----------
  build() {
    const state = this.data;
    const cur = currency.current();

    // 统计卡
    const byCost = [...cities].sort((a, b) => a["月成本 (USD)"] - b["月成本 (USD)"]);
    const cheapest = byCost[0];
    const priciest = byCost[byCost.length - 1];
    const biggest = [...cities].sort((a, b) => b["游民数"] - a["游民数"])[0];
    const top = [...cities].sort((a, b) => b["综合分"] - a["综合分"])[0];
    const stats = [
      { l: "收录城市", v: String(cities.length), s: "亚洲/欧洲/拉美/非洲/中东" },
      { l: "最便宜(" + currency.symbol() + ")", v: currency.formatCost(cheapest["月成本 (USD)"]).slice(1), s: cheapest["城市"] },
      { l: "最贵(" + currency.symbol() + ")", v: currency.formatCost(priciest["月成本 (USD)"]).slice(1), s: priciest["城市"] },
      { l: "最大社群", v: currency.num(biggest["游民数"]), s: biggest["城市"] },
      { l: "综合最高分", v: String(top["综合分"]), s: top["城市"] }
    ];

    // 筛选
    const q = (state.search || "").trim().toLowerCase();
    let pool = [...cities];
    if (state.region !== "全部") pool = pool.filter((d) => d["区域"] === state.region);
    if (state.countryIndex > 0) pool = pool.filter((d) => d["国家"] === state.countryOptions[state.countryIndex]);
    if (state.topIndex > 0) pool = pool.filter((d) => d["排名"] <= parseInt(TOP_OPTIONS[state.topIndex].slice(4), 10));
    if (q) {
      pool = pool.filter(
        (d) =>
          d["城市"].toLowerCase().includes(q) ||
          d["国家"].toLowerCase().includes(q) ||
          (d["国家(英)"] || "").toLowerCase().includes(q)
      );
    }

    const field = SORT_FIELD[state.sortKey];
    const dir = Number(state.sortDir) || 1;
    pool.sort((a, b) => {
      const av = a[field];
      const bv = b[field];
      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });

    const list = pool.map((d) => ({
      rank: d["排名"],
      rankNo: String(d["排名"]).padStart(2, "0"),
      flag: d["国旗"],
      name: d["城市"],
      country: d["国家"],
      region: d["区域"],
      regionColor: fmt.REGION_COLORS[d["区域"]],
      regionBg: fmt.REGION_BGS[d["区域"]],
      nomadsText: currency.num(d["游民数"]),
      costText: currency.formatCost(d["月成本 (USD)"]),
      costCls: fmt.costClass(d["月成本 (USD)"]),
      costDual:
        currency.formatCost(d["月成本 (USD)"]) +
        "（" +
        (cur === "CNY" ? "≈$" : "≈¥") +
        currency.num(cur === "CNY" ? d["月成本 (USD)"] : Math.round(d["月成本 (USD)"] * currency.rate())) +
        "）",
      score: d["综合分"],
      temp: d["年均气温 (°C)"],
      season: d["最佳季节"],
      visa: d["签证"],
      updated: d["最后更新"],
      keyDots: QUICK_DOTS.map((f) => ({
        label: f.label,
        value: d[f.key],
        cls: fmt.tier(d[f.key])
      })),
      dims: meta.SCORE_FIELDS.map((f) => ({
        key: f.key,
        label: f.label,
        value: d[f.key],
        cls: fmt.tier(d[f.key]),
        tierWord: fmt.tierLabel(fmt.tier(d[f.key])),
        help: f.help
      }))
    }));

    // 数据新鲜度脚注
    const dates = cities.map((d) => d["最后更新"]).filter(Boolean).sort();
    const freshness = dates.length ? "数据更新：" + dates[dates.length - 1] + " · " + cities.length + " 城由社区共同维护" : "";

    this.setData({ stats, list, freshness, expandedRank: this.data.expandedRank });
  },

  // ---------- 交互 ----------
  onSearch(e) {
    this.setData({ search: e.detail.value });
    this.build();
  },

  onRegion(e) {
    const region = e.currentTarget.dataset.region;
    this.setData({ region, expandedRank: null });
    this.buildCountries();
    this.build();
  },

  onCountryChange(e) {
    this.setData({ countryIndex: Number(e.detail.value), expandedRank: null });
    this.build();
  },

  onTopChange(e) {
    this.setData({ topIndex: Number(e.detail.value), expandedRank: null });
    this.build();
  },

  onSort(e) {
    const key = e.currentTarget.dataset.key;
    if (key === this.data.sortKey) {
      this.setData({ sortDir: -this.data.sortDir });
    } else {
      const conf = SORTS.find((s) => s.key === key) || SORTS[0];
      this.setData({ sortKey: key, sortDir: conf.dir });
    }
    this.build();
  },

  onToggle(e) {
    const rank = Number(e.currentTarget.dataset.rank);
    this.setData({ expandedRank: this.data.expandedRank === rank ? null : rank });
  },

  noop() {},

  onShareAppMessage() {
    return {
      title: "牛马迁移指南 · 80 城数字游民榜单",
      path: "/pages/index/index",
      imageUrl: "/assets/icons/logo-badge.png"
    };
  },

  // ---------- 货币 ----------
  onCurrencyUSD() {
    currency.set("USD");
    this.refreshCurrency();
    this.build();
  },

  onCurrencyCNY() {
    currency.set("CNY");
    this.refreshCurrency();
    this.build();
  },

  onEditRate() {
    wx.showModal({
      title: "设置汇率",
      editable: true,
      placeholderText: "1 USD 等于多少 CNY？默认 " + currency.DEFAULT_RATE,
      content: String(currency.rate()),
      success: (res) => {
        if (!res.confirm) return;
        const v = (res.content || "").trim();
        if (!v) {
          try {
            wx.removeStorageSync("nomad_rate");
          } catch (e) {}
        } else if (!currency.setRate(v)) {
          wx.showToast({ title: "汇率无效，未修改", icon: "none" });
          return;
        }
        this.refreshCurrency();
        this.build();
        wx.showToast({ title: "汇率已更新", icon: "none" });
      }
    });
  },

  // 内部：按当前区域重建国家选项
  buildCountries() {
    let pool = cities;
    if (this.data.region !== "全部") pool = pool.filter((d) => d["区域"] === this.data.region);
    const cs = [...new Set(pool.map((d) => d["国家"]))].sort();
    this.setData({ countryOptions: ["全部国家（" + cs.length + "）"].concat(cs), countryIndex: 0 });
  }
});
