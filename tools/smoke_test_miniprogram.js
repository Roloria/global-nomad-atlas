#!/usr/bin/env node
/** 小程序逻辑冒烟测试：stub wx/Page/Component，加载页面模块并执行关键方法 */
const path = require("path");

const SRC = path.resolve(__dirname, "..", "miniprogram", "miniprogram");
let failures = [];

// ---- stubs ----
const storage = {};
global.wx = {
  getStorageSync: (k) => (k in storage ? storage[k] : ""),
  setStorageSync: (k, v) => (storage[k] = v),
  removeStorageSync: (k) => delete storage[k],
  setNavigationBarColor: () => {},
  showToast: () => {},
  showModal: (o) => o && o.success && o.success({ confirm: true, content: "7.3" }),
  setClipboardData: (o) => o && o.success && o.success(),
  switchTab: () => {},
  navigateTo: () => {},
  pageScrollTo: () => {},
  cloud: {}
};
global.getCurrentPages = () => [];
global.getApp = () => ({ globalData: { site: "s", repo: "r", sheet: "d", brand: "b", brandEn: "g" } });

let lastPage = null;
global.Page = (config) => {
  lastPage = config;
  const page = {
    data: JSON.parse(JSON.stringify(config.data || {})),
    setData(d) {
      // 支持 "a.b[0].c" 形式
      for (const [k, v] of Object.entries(d)) {
        if (k.includes("[") || k.includes(".")) {
          const m = k.match(/^(\w+)\[(\d+)\]\.(\w+)$/);
          if (m) this.data[m[1]][Number(m[2])][m[3]] = v;
        } else this.data[k] = v;
      }
    },
    getTabBar: () => null
  };
  for (const fn of ["onLoad", "onShow", ...Object.keys(config).filter((k) => typeof config[k] === "function")]) {
    if (typeof config[fn] === "function") page[fn] = config[fn].bind(page);
  }
  if (config.onLoad) page.onLoad();
  if (config.onShow) page.onShow();
  lastPage = page;
  return page;
};

let lastComponent = null;
global.Component = (config) => {
  lastComponent = config;
};

function run(name, fn) {
  try {
    fn();
    console.log("  ✓ " + name);
  } catch (e) {
    failures.push(name + ": " + e.message);
    console.log("  ✗ " + name + " → " + e.message);
  }
}

const load = (rel) => {
  lastPage = null;
  delete require.cache[require.resolve(path.join(SRC, rel))];
  require(path.join(SRC, rel));
  return lastPage;
};

console.log("== 自定义 tabBar ==");
run("attached + sync", () => {
  lastComponent = null;
  load("custom-tab-bar/index.js");
  const comp = { data: JSON.parse(JSON.stringify(lastComponent.data)), setData(d) { Object.assign(this.data, d); } };
  lastComponent.lifetimes.attached.call(comp);
  lastComponent.methods.sync.call(comp, 1);
  if (comp.data.selected !== 1) throw new Error("sync 未生效");
});

console.log("== 城市榜 ==");
run("onLoad/onShow 构建列表", () => {
  const page = load("pages/index/index.js");
  if (!page.data.list.length) throw new Error("列表为空");
  if (page.data.stats.length !== 5) throw new Error("统计卡应 5 张，实际 " + page.data.stats.length);
  if (page.data.countryOptions[0] !== "全部国家（40）" && !/全部国家/.test(page.data.countryOptions[0]))
    throw new Error("国家选项异常: " + page.data.countryOptions[0]);
  const item = page.data.list[0];
  if (item.dims.length !== 12) throw new Error("展开明细应为 12 维");
  if (!item.costText || !item.costDual) throw new Error("成本文本缺失");
});

run("区域筛选 → 欧洲只剩欧洲城市", () => {
  const page = load("pages/index/index.js");
  page.onRegion({ currentTarget: { dataset: { region: "欧洲" } } });
  if (!page.data.list.length || page.data.list.some((x) => x.region !== "欧洲")) throw new Error("混入非欧洲城市");
});

run("搜索中文「大理」与英文「Japan」均命中", () => {
  const page = load("pages/index/index.js");
  page.onSearch({ detail: { value: "大理" } });
  if (!page.data.list.some((x) => x.name === "大理")) throw new Error("中文未命中大理");
  page.onSearch({ detail: { value: "Japan" } });
  if (!page.data.list.some((x) => x.name === "东京")) throw new Error("英文未命中东京(国家英文名)");
  page.onSearch({ detail: { value: "不存在的城市xyz" } });
  if (page.data.list.length !== 0) throw new Error("无效关键词应返回空列表");
});

run("按综合分排序，首位应为里斯本 7.9", () => {
  const page = load("pages/index/index.js");
  page.onSort({ currentTarget: { dataset: { key: "综合分" } } });
  if (page.data.list[0].name !== "里斯本" || page.data.list[0].score !== 7.9)
    throw new Error("首位 " + page.data.list[0].name + " " + page.data.list[0].score);
});

run("展开/收起", () => {
  const page = load("pages/index/index.js");
  page.onToggle({ currentTarget: { dataset: { rank: 1 } } });
  if (page.data.expandedRank !== 1) throw new Error("未展开");
  page.onToggle({ currentTarget: { dataset: { rank: 1 } } });
  if (page.data.expandedRank !== null) throw new Error("未收起");
});

run("CNY 换算（汇率 7.2）", () => {
  const page = load("pages/index/index.js");
  page.onCurrencyCNY();
  const dali = page.data.list.find((x) => x.name === "大理");
  // 大理 850 USD → ¥6,120
  if (!dali.costText.includes("6,120")) throw new Error("大理 CNY 成本异常: " + dali.costText);
  page.onEditRate(); // modal stub confirm → 设为 7.3
  const dali2 = page.data.list.find((x) => x.name === "大理");
  if (!dali2.costText.includes("6,205")) throw new Error("改汇率后异常: " + dali2.costText);
});

run("TOP 20 筛选", () => {
  const page = load("pages/index/index.js");
  page.onTopChange({ detail: { value: 1 } });
  if (page.data.list.some((x) => x.rank > 20)) throw new Error("混入 TOP20 之外的城市");
});

console.log("== 社区地图 ==");
run("onLoad 构建列表 + 统计", () => {
  const page = load("pages/communities/communities.js");
  if (page.data.list.length !== 60) throw new Error("应为 60 社区，实际 " + page.data.list.length);
  if (page.data.stats.length !== 4) throw new Error("统计应 4 张");
});

run("类型筛选 + 排序", () => {
  const page = load("pages/communities/communities.js");
  page.onTypeChange({ detail: { value: 2 } }); // types[2] = 联合生活
  if (!page.data.list.length || page.data.list.some((x) => x.type !== "联合生活")) throw new Error("类型筛选异常");
  page.onSort({ currentTarget: { dataset: { key: "capacity" } } });
  const caps = page.data.list.map((x) => x.capacityText);
  if (caps.length && page.data.list[0].capacityText === undefined) throw new Error("容量缺失");
});

run("复制链接（未提供 → toast 不崩溃）", () => {
  const page = load("pages/communities/communities.js");
  page.onCopy({ currentTarget: { dataset: { kind: "url", rank: 8 } } }); // rank 8 是聚会社群，url 存在
  page.onCopy({ currentTarget: { dataset: { kind: "email", rank: 8 } } }); // email 为 "-" → toast 分支
});

console.log("== 共建页 ==");
run("onLoad 读取 globalData 链接", () => {
  const page = load("pages/about/about.js");
  if (!page.data.site || !page.data.repo || !page.data.sheet) throw new Error("链接未注入");
  if (page.data.dims.length !== 12 || page.data.faq.length !== 5) throw new Error("方法论/FAQ 数据异常");
  page.onFaqTap({ currentTarget: { dataset: { i: 2 } } });
  if (page.data.faqOpen !== 2) throw new Error("FAQ 未展开");
});

console.log("== 提交数据页 ==");
run("初始综合分应为 5.0", () => {
  const page = load("pages/submit/submit.js");
  if (page.data.overall !== 5) throw new Error("初始综合分 " + page.data.overall);
  if (page.data.formDims.length !== 12) throw new Error("滑杆应 12 条");
});

run("滑杆打分 → 综合分实时计算", () => {
  const page = load("pages/submit/submit.js");
  // 全部拉满 10 → 10 分
  page.data.formDims.forEach((d, i) => page.onSlider({ currentTarget: { dataset: { idx: i } }, detail: { value: 10 } }));
  if (page.data.overall !== 10) throw new Error("拉满应 10 分，实际 " + page.data.overall);
});

run("提交 → 本地存储 → Issue 文本", () => {
  const page = load("pages/submit/submit.js");
  page.setData({ city: "测试城", country: "测试国" });
  page.onSubmit();
  if (!page.data.submitted) throw new Error("未生成提交记录");
  if (page.data.savedCount !== 1) throw new Error("存储条数 " + page.data.savedCount);
  const text = page.buildIssueText(page.data.submitted);
  if (!text.includes("**城市**：测试城") || !text.includes("### 综合分（自动计算）")) throw new Error("Issue 文本格式异常");
  page.onCopyIssue();
  page.onDeleteSaved({ currentTarget: { dataset: { idx: 0 } } }); // modal stub confirm
  if (page.data.savedCount !== 0) throw new Error("删除失败");
});

console.log("");
if (failures.length) {
  console.error("✗ " + failures.length + " 项失败");
  process.exit(1);
} else {
  console.log("✓ 冒烟测试全部通过");
}
