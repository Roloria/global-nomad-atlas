/** 展示与计算辅助：tier、成本分档、区域配色（与网站一致） */

/** 评分分档：≥7 高分 g，≥5.5 中等 m，其余偏低 b */
function tier(v) {
  return v >= 7 ? "g" : v >= 5.5 ? "m" : "b";
}

function tierLabel(c) {
  return c === "g" ? "高分" : c === "m" ? "中等" : "偏低";
}

/** 综合分档位描述（详情用） */
function tierScore(score) {
  if (score >= 9) return "世界级";
  if (score >= 7.5) return "优秀";
  if (score >= 6) return "良好";
  if (score >= 4.5) return "一般";
  return "偏差";
}

/** 月成本分档配色：低 = 绿，中 = 橙，高 = 红 */
function costClass(usd) {
  const c = Number(usd) || 0;
  return c <= 1100 ? "cost-low" : c <= 2000 ? "cost-mid" : "cost-high";
}

const REGION_KEYS = {
  亚洲: "asia",
  欧洲: "europe",
  拉美: "latam",
  非洲: "africa",
  中东: "mena",
  全球: "global"
};

const REGION_COLORS = {
  亚洲: "#e8890c",
  欧洲: "#1971c2",
  拉美: "#d6336c",
  非洲: "#2f9e44",
  中东: "#7048e8",
  全球: "#0b7285"
};

/** pill 柔和底色（对应区域色 10% 透明度） */
const REGION_BGS = {
  亚洲: "rgba(232,137,12,0.12)",
  欧洲: "rgba(25,113,194,0.10)",
  拉美: "rgba(214,51,108,0.10)",
  非洲: "rgba(47,158,68,0.12)",
  中东: "rgba(112,72,232,0.10)",
  全球: "rgba(11,114,133,0.10)"
};

module.exports = { tier, tierLabel, tierScore, costClass, REGION_KEYS, REGION_COLORS, REGION_BGS };
