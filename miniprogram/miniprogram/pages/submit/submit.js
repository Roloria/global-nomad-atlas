const meta = require("../../data/meta");
const fmt = require("../../utils/format");
const theme = require("../../utils/theme");

const STORE_KEY = "nomad_submissions"; // 与网站 localStorage 同键名，稍后接入云开发可直接上传
const REGIONS = ["亚洲", "欧洲", "拉美", "非洲", "中东"];

function nowDate() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}

Page({
  data: {
    theme: "light",

    // 表单
    city: "",
    country: "",
    regions: REGIONS,
    regionIndex: 0,
    description: "",
    sources: "",
    today: nowDate(),

    // 12 维滑杆
    formDims: [],
    overall: 0,

    // 提交结果
    submitted: null,
    savedCount: 0,
    savedList: []
  },

  onLoad() {
    this.resetForm();
    this.refreshSaved();
  },

  onShow() {
    theme.applyToPage(this);
  },

  resetForm() {
    const formDims = meta.SCORE_FIELDS.map((f) => ({
      key: f.key,
      label: f.label,
      help: f.help,
      weight: f.weight,
      value: 5,
      cls: "m"
    }));
    const scores = {};
    formDims.forEach((d) => (scores[d.key] = d.value));
    this.setData({ formDims, overall: meta.overall(scores), submitted: null, city: "", country: "", regionIndex: 0, description: "", sources: "" });
  },

  refreshSaved() {
    let savedList = [];
    try {
      savedList = wx.getStorageSync(STORE_KEY) || [];
    } catch (e) {}
    // 倒序展示，最近提交在前
    this.setData({
      savedList: savedList.map((x, i) => ({ idx: i, city: x.city, country: x.country, region: x.region, overall: x.overall, time: x.timestamp })),
      savedCount: savedList.length
    });
  },

  // ---------- 表单交互 ----------
  onCity(e) { this.setData({ city: e.detail.value }); },
  onCountry(e) { this.setData({ country: e.detail.value }); },
  onRegion(e) { this.setData({ regionIndex: Number(e.detail.value) }); },
  onDescription(e) { this.setData({ description: e.detail.value }); },
  onSources(e) { this.setData({ sources: e.detail.value }); },

  onSlider(e) {
    const idx = Number(e.currentTarget.dataset.idx);
    const v = Math.round(Number(e.detail.value) * 10) / 10;
    const key = "formDims[" + idx + "].value";
    const clsKey = "formDims[" + idx + "].cls";
    const scores = {};
    const dims = this.data.formDims;
    dims[idx].value = v;
    dims.forEach((d) => (scores[d.key] = d.value));
    this.setData({
      [key]: v,
      [clsKey]: fmt.tier(v),
      overall: meta.overall(scores)
    });
  },

  collectScores() {
    const scores = {};
    this.data.formDims.forEach((d) => (scores[d.key] = d.value));
    return scores;
  },

  onSubmit() {
    const s = this.data;
    if (!s.city.trim() || !s.country.trim()) {
      wx.showToast({ title: "请先填写城市与国家", icon: "none" });
      return;
    }
    const scores = this.collectScores();
    const record = {
      type: "submission",
      timestamp: new Date().toISOString(),
      city: s.city.trim(),
      country: s.country.trim(),
      region: s.regions[s.regionIndex],
      description: s.description.trim(),
      sources: s.sources.trim(),
      scores,
      overall: meta.overall(scores),
      最后更新: nowDate()
    };

    let all = [];
    try {
      all = wx.getStorageSync(STORE_KEY) || [];
    } catch (e) {}
    all.push(record);
    try {
      wx.setStorageSync(STORE_KEY, all);
    } catch (e) {
      wx.showToast({ title: "本地保存失败", icon: "none" });
      return;
    }

    this.setData({ submitted: record });
    this.refreshSaved();
    wx.showToast({ title: "已保存到本地", icon: "success" });
  },

  onAnother() {
    this.resetForm();
    wx.pageScrollTo({ scrollTop: 0, duration: 200 });
  },

  // ---------- GitHub Issue 文本（与网站 showSuccess 生成的格式一致） ----------
  buildIssueText(r) {
    const lines = [];
    lines.push("## 数据提交");
    lines.push("");
    lines.push("**城市**：" + r.city);
    lines.push("**国家**：" + r.country);
    lines.push("**区域**：" + r.region);
    lines.push("");
    lines.push("### 描述");
    lines.push(r.description || "(无)");
    lines.push("");
    lines.push("### 数据来源");
    lines.push(r.sources || "(无)");
    lines.push("");
    lines.push("### 评分（满分 10）");
    meta.SCORE_FIELDS.forEach((f) => lines.push("- **" + f.label + "** (" + f.key + ")：" + r.scores[f.key]));
    lines.push("");
    lines.push("### 综合分（自动计算）");
    lines.push(String(r.overall));
    lines.push("");
    lines.push("---");
    lines.push("**最后更新**：" + r["最后更新"]);
    lines.push("");
    lines.push("提交时间：" + r.timestamp);
    lines.push("提交方式：微信小程序（匿名）");
    return lines.join("\n");
  },

  onCopyIssue() {
    const r = this.data.submitted;
    if (!r) return;
    wx.setClipboardData({
      data: this.buildIssueText(r),
      success: () =>
        wx.showModal({
          title: "Issue 文本已复制",
          content: "粘贴到 GitHub 仓库 Issues 新建工单即可进入审核；接入云开发后此步骤将自动完成。",
          showCancel: false,
          confirmText: "知道了"
        })
    });
  },

  onDeleteSaved(e) {
    const idx = Number(e.currentTarget.dataset.idx);
    wx.showModal({
      title: "删除这条提交？",
      content: "仅删除本机记录，不影响任何公开数据。",
      success: (res) => {
        if (!res.confirm) return;
        let all = [];
        try {
          all = wx.getStorageSync(STORE_KEY) || [];
        } catch (err) {}
        all.splice(idx, 1);
        try {
          wx.setStorageSync(STORE_KEY, all);
        } catch (err) {}
        this.refreshSaved();
      }
    });
  }
});
