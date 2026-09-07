/**
 * 榜单元数据：评分维度、区域、社区类型与综合分公式。
 * 权重与公式与榜单网站（docs/index.html）完全一致，综合分人人可复算。
 */

const SCORE_FIELDS = [
  { key: "网络", weight: 1.0, label: "🌐 网络", help: "5G/光纤普及度、办公 Wi-Fi 速度" },
  { key: "社群", weight: 1.2, label: "👥 社群", help: "Meetup/Coworking/线下活动密度" },
  { key: "生活", weight: 1.0, label: "🎉 生活", help: "餐厅/娱乐/文化体验丰富度" },
  { key: "安全", weight: 1.2, label: "🛡️ 安全", help: "治安、夜间外出安全感" },
  { key: "英语", weight: 0.9, label: "🗣️ 英语", help: "日常英语沟通便利度" },
  { key: "步行", weight: 0.7, label: "🚶 步行", help: "步道/基础设施/便利" },
  { key: "空气", weight: 0.7, label: "🌬️ 空气", help: "PM2.5 / 综合污染指数" },
  { key: "女性友好", weight: 0.8, label: "👩 女性友好", help: "性别平等与女性安全感" },
  { key: "LGBTQ+", weight: 0.6, label: "🌈 LGBTQ+", help: "多元包容与社会氛围" },
  { key: "夜生活", weight: 0.5, label: "🌃 夜生活", help: "酒吧/俱乐部/夜间活力" },
  { key: "安静指数", weight: 0.6, label: "🤫 安静", help: "噪音/拥挤度/可专注性" },
  { key: "种族包容", weight: 0.6, label: "🤝 种族包容", help: "对外来人口接受度" }
];

const WEIGHT_SUM = SCORE_FIELDS.reduce((s, f) => s + f.weight, 0); // = 9.8

/** 综合分 = Σ(维度分 × 权重) / Σ权重 */
function overall(scores) {
  const sum = SCORE_FIELDS.reduce((s, f) => s + (Number(scores[f.key]) || 0) * f.weight, 0);
  return Math.round((sum / WEIGHT_SUM) * 10) / 10;
}

const REGION_LIST = ["全部", "亚洲", "欧洲", "拉美", "非洲", "中东"];
const COMM_TYPES = ["联合办公", "联合生活", "度假村", "聚会", "在线社群"];
const COMM_REGIONS = ["亚洲", "欧洲", "拉美", "非洲", "中东", "全球"];

const FORMULA =
  "overall = (网络×1.0 + 社群×1.2 + 生活×1.0 + 安全×1.2 + 英语×0.9 + 步行×0.7 + 空气×0.7 + 女性友好×0.8 + LGBTQ+×0.6 + 夜生活×0.5 + 安静×0.6 + 种族包容×0.6) / 9.8";

const FAQ = [
  {
    q: "评分是怎么来的？",
    a: "每座城市按网络、社群、生活、安全、英语、步行、空气、女性友好、LGBTQ+、夜生活、安静指数、种族包容共 12 个维度加权评分，月成本作为独立数据列呈现。权重与公式完全公开，综合分人人可复算。"
  },
  {
    q: "数据多久更新一次？",
    a: "没有强制周期，由社区持续维护。任何人都可以通过「共建」页提交更新，PR 合并后对应城市的「最后更新」会自动刷新；CI 数据保鲜哨兵会在数据停滞超 7 天时自动提醒社区。"
  },
  {
    q: "我不懂代码，能参与吗？",
    a: "能。打开腾讯文档共建表就能像编辑在线表格一样直接修改，改动会自动进入 GitHub 审核流程，全程不需要任何编程知识，无需实名与代码基础。"
  },
  {
    q: "数字游民签证怎么选？",
    a: "热门选项包括葡萄牙 D7/D8、西班牙数字游民签证、爱沙尼亚与捷克游民签证，常见门槛为月收入 2,000–3,500 美元与健康保险。榜单为每座城市标注了当前推荐签证类型，具体申请请以当地移民局官网为准。"
  },
  {
    q: "预算有限，可以去哪儿？",
    a: "河内、岘港、暹粒、开罗的月成本约 800 美元；大理 850 美元就能住进综合分 7.5 的城市。在城市榜按「月成本」排序即可找到适合预算的目的地。"
  }
];

module.exports = { SCORE_FIELDS, WEIGHT_SUM, overall, REGION_LIST, COMM_TYPES, COMM_REGIONS, FORMULA, FAQ };
