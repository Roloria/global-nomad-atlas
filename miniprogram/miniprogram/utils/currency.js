/**
 * 货币显示（USD 默认 / CNY 折算）。
 * 汇率默认 7.20（与网站 DEFAULT_RATE 一致）；网站由 GitHub Action 每月自动更新
 * data/exchange-rate.json，小程序端稍后接入云开发后可用云函数拉取最新汇率，
 * 当前提供手动修改入口（数据存本地）。
 */
const DEFAULT_RATE = 7.2;
const KEY_CUR = "nomad_currency";
const KEY_RATE = "nomad_rate";

function current() {
  try {
    return wx.getStorageSync(KEY_CUR) === "CNY" ? "CNY" : "USD";
  } catch (e) {
    return "USD";
  }
}

function set(c) {
  try {
    wx.setStorageSync(KEY_CUR, c === "CNY" ? "CNY" : "USD");
  } catch (e) {}
}

function rate() {
  try {
    const v = parseFloat(wx.getStorageSync(KEY_RATE));
    if (isFinite(v) && v > 0) return Math.round(v * 100) / 100;
  } catch (e) {}
  return DEFAULT_RATE;
}

function setRate(v) {
  const n = parseFloat(v);
  if (!isFinite(n) || n <= 0) return false;
  try {
    wx.setStorageSync(KEY_RATE, String(Math.round(n * 100) / 100));
  } catch (e) {}
  return true;
}

function num(n) {
  return Number(n || 0).toLocaleString();
}

function symbol() {
  return current() === "CNY" ? "¥" : "$";
}

/** 月成本：按当前货币格式化 */
function formatCost(usd) {
  const v = Number(usd) || 0;
  if (current() === "CNY") return "¥" + num(Math.round(v * rate()));
  return "$" + num(v);
}

/** 月成本双币说明（详情区用） */
function formatDualCost(usd) {
  const v = Number(usd) || 0;
  if (current() === "CNY") return formatCost(v) + " ≈$" + num(v);
  return formatCost(v) + " ≈¥" + num(Math.round(v * rate()));
}

module.exports = { DEFAULT_RATE, current, set, rate, setRate, num, symbol, formatCost, formatDualCost };
