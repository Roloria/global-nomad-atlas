#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字游民城市：腾讯文档(共建) ↔ GitHub 同步脚本
================================================
流程（双向，GitHub CSV 为唯一数据源）：
  腾讯文档(社区编辑) → 按 (城市,国家) 主键 diff → 校验(对齐 CI) → 建分支+更新 csv/xlsx/index.html + 开 PR(label=data) 等审核
  反向：GitHub CSV 变动 → 细粒度单元格回写腾讯文档（不改用户待审编辑、不删 TD 独有行）

模式：
  --mode dry-run  (默认) 仅输出双向 diff 报告，不触碰 GitHub
  --mode apply            有 TD→GitHub 变更则建 PR；并反向把 GitHub→腾讯文档 写回；重算派生视图
  --mode restore --version <tag>   把指定快照写回 GitHub(开PR) + 腾讯文档 + 重算派生视图
  --mode backfill         一次性：为腾讯文档『综合数据』补『最后更新』列并回填（P0/P4）

配置集中在 CONFIG 区。依赖：gh (已登录) + openpyxl + tencentdocs.py。
"""
import argparse, csv, json, subprocess, sys, os, base64, io, tempfile, datetime, re
from collections import defaultdict

# ============================ CONFIG ============================
REPO_OWNER = "Roloria"
REPO_NAME  = "global-nomad-atlas"
CSV_PATH   = "data/digital-nomad-cities.csv"
XLSX_PATH  = "data/digital-nomad-cities.xlsx"

TD_FILE_ID  = "DJiXDMEgpqtQ"
TD_SHEET_ID = "BB08J2"
# 全部 6 个子表（tab）的 sheet_id；其余 5 个由原 Excel 镜像而来
TD_SHEETS = {
    "综合数据": "BB08J2",
    "按区域": "yPJ03u",
    "专题排行": "GqzvWb",
    "签证政策": "yMEYl4",
    "按身份推荐": "j3bVD2",
    "数据说明": "Yiix0q",
}
# 仅这两个为「由 综合数据 派生」的视图，会在同步时自动重算；
# 签证政策/按身份推荐/数据说明 为静态策划内容，镜像一次后脚本不再改动。
DERIVED_SHEETS = {"按区域", "专题排行"}
REGION_ORDER = ["亚洲", "欧洲", "拉美", "非洲", "中东"]
def _find_tencentdocs_script():
    """定位腾讯文档 tencentdocs.py。
    优先 5.5.3+：该版本含 V2 MCP Gateway 凭据提供方，能在独立 Bash 子进程里
    从宿主本地网关注入拿到登录票据。旧版 1.0.0 只读 TDOC_* 环境变量，在 Bash
    子进程中无票 → ERROR:no_token（2026-09-01~09-05 连续失败的根因）。
    自动选最新插件目录，兼容插件后续升级。"""
    import glob as _glob
    base = "/Users/kevinwang/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin"
    cands = sorted(_glob.glob(os.path.join(base, "*", "skills", "tencent-docs", "tencentdocs.py")))
    prefer = [c for c in cands if "5.5.3" in c]
    if prefer:
        return prefer[-1]
    if cands:
        return cands[-1]
    # 兜底：旧硬编码路径（防插件目录结构变动）
    return "/Users/kevinwang/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin/1.0.0/skills/tencent-docs/tencentdocs.py"
TD_SCRIPT   = _find_tencentdocs_script()
PY          = "/Users/kevinwang/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
VENV_PY     = "/Users/kevinwang/.workbuddy/binaries/python/envs/default/bin/python3"
PROJECT     = "/Users/kevinwang/WorkBuddy/数字游民"
SNAP_DIR    = os.path.join(PROJECT, "snapshots")

EXPECTED_HEADERS = ["排名","区域","城市","国家","国家(英)","国旗","游民数","月成本 (USD)","货币类型",
    "网络","社群","生活","安全","英语","步行","空气","女性友好","LGBTQ+","夜生活","安静指数",
    "种族包容","年均气温 (°C)","最佳季节","签证","综合分","最后更新"]
SCORE_COLS = {"网络","社群","生活","安全","英语","步行","空气","女性友好","LGBTQ+","夜生活","安静指数","种族包容","综合分"}
WEIGHTS = {"网络":1.0,"社群":1.2,"生活":1.0,"安全":1.2,"英语":0.9,"步行":0.7,"空气":0.7,
    "女性友好":0.8,"LGBTQ+":0.6,"夜生活":0.5,"安静指数":0.6,"种族包容":0.6}
WSUM = sum(WEIGHTS.values())
VALID_REGIONS = {"亚洲","欧洲","拉美","非洲","中东"}
INT_COLS = {"游民数","月成本 (USD)","年均气温 (°C)","排名"}
DERIVED = {"排名","综合分","最后更新"}   # 派生/系统字段，不计入"用户改动"
REPO = f"{REPO_OWNER}/{REPO_NAME}"
# ===============================================================

def tdoc_call(service, tool, args):
    r = subprocess.run([PY, TD_SCRIPT, "tdoc_call", service, tool, json.dumps(args, ensure_ascii=False)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        # 腾讯文档脚本把 ERROR:xxx 写在 stdout（stderr 常为空），两路都回显才能定位 no_token
        detail = (r.stdout or "").strip() or (r.stderr or "").strip() or f"returncode={r.returncode}"
        if detail.startswith("ERROR:no_token"):
            raise RuntimeError(
                "腾讯文档登录票据失效 (ERROR:no_token)：请在 WorkBuddy 中重新授权「腾讯文档」连接器后重跑。")
        raise RuntimeError(f"tdoc_call {service}/{tool} 进程失败: {detail}")
    out = json.loads(r.stdout)
    if "error" in out and out["error"]:
        raise RuntimeError(f"tdoc_call {service}/{tool} 错误: {out.get('error')}")
    return out.get("result", {})

def read_tencent_docs():
    res = tdoc_call("sheet-mcp", "get_cell_data", {
        "file_id": TD_FILE_ID, "sheet_id": TD_SHEET_ID,
        "start_row": 0, "start_col": 0, "end_row": 300, "end_col": 26, "return_csv": True})
    text = res["content"][0]["text"]
    data = json.loads(text)
    lines = data["csv_data"].splitlines()
    reader = list(csv.reader(lines))
    header, start = None, 0
    for i, row in enumerate(reader):
        if row and row[0] == "排名":
            header, start = row, i + 1
            break
    if header is None:
        raise RuntimeError("腾讯文档中找不到 '排名' 表头行")
    header = header[:len(EXPECTED_HEADERS)]   # 去掉读取时可能多出的空列
    rows = []
    for row in reader[start:]:
        if not row:
            continue
        row = (row + [""] * len(EXPECTED_HEADERS))[:len(EXPECTED_HEADERS)]
        d = dict(zip(header, row))
        # 跳过残缺/残留行：真实城市必有「城市」名（腾讯文档空写不清除单元格，故以此过滤）
        if not d.get("城市", "").strip():
            continue
        rows.append(d)
    return header, rows

def read_github_csv():
    out = subprocess.run(["gh","api",f"repos/{REPO}/contents/{CSV_PATH}","--jq",".content"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"gh api 读取 CSV 失败: {out.stderr}")
    content = base64.b64decode(out.stdout.strip()).decode("utf-8")
    rows = list(csv.DictReader(content.splitlines()))
    return EXPECTED_HEADERS, rows

def recompute(rows):
    for r in rows:
        s = sum(float(r[h]) * w for h, w in WEIGHTS.items())
        ov = round(s / WSUM, 1)
        # 整数形式(如 7.0→"7")与开源 CSV 保持一致，避免 xlsx 读回 "7" 时校验 mismatch
        r["综合分"] = str(int(ov)) if ov == int(ov) else str(ov)
    order = sorted(range(len(rows)), key=lambda i: -float(rows[i]["综合分"]))
    for rank, i in enumerate(order, 1):
        rows[i]["排名"] = str(rank)
    rows.sort(key=lambda r: int(r["排名"]))

def validate(rows):
    errors, seen = [], set()
    for i, r in enumerate(rows, start=2):
        key = f"{r['城市']}|{r['国家']}"
        if key in seen:
            errors.append(f"第{i}行 城市+国家重复: {key}")
        seen.add(key)
        if r["区域"] not in VALID_REGIONS:
            errors.append(f"第{i}行 区域非法: '{r['区域']}' (应为 {VALID_REGIONS})")
        for col in EXPECTED_HEADERS:
            if str(r.get(col, "")).strip() == "":
                errors.append(f"第{i}行({r['城市']}) 字段'{col}'为空")
        for col in SCORE_COLS:
            try:
                v = float(r[col])
                if v < 0 or v > 10:
                    errors.append(f"第{i}行({r['城市']}) '{col}'={v} 超出 0–10")
            except ValueError:
                errors.append(f"第{i}行({r['城市']}) '{col}' 非数字: '{r[col]}'")
        for col in INT_COLS:
            try:
                int(r[col])
            except ValueError:
                errors.append(f"第{i}行({r['城市']}) '{col}' 非整数: '{r[col]}'")
    return errors

def diff(td, gh):
    gh_map = {(r["城市"], r["国家"]): r for r in gh}
    td_map = {(r["城市"], r["国家"]): r for r in td}
    added = [k for k in td_map if k not in gh_map]
    removed = [k for k in gh_map if k not in td_map]
    modified = []
    for k in td_map:
        if k in gh_map:
            changes = {}
            for col in EXPECTED_HEADERS:
                if col in DERIVED:
                    continue
                a = str(td_map[k].get(col, "")).strip()
                b = str(gh_map[k].get(col, "")).strip()
                if a != b:
                    changes[col] = (b, a)   # (旧, 新)
            if changes:
                modified.append((k, changes))
    return added, removed, modified

def save_snapshot(rows, tag):
    os.makedirs(SNAP_DIR, exist_ok=True)
    path = os.path.join(SNAP_DIR, f"nomad_{tag}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EXPECTED_HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in EXPECTED_HEADERS})
    return path

def build_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPECTED_HEADERS)
    w.writeheader()
    for r in rows:
        w.writerow({h: r.get(h, "") for h in EXPECTED_HEADERS})
    return buf.getvalue()

def _typed(v, h):
    if h in INT_COLS:
        return int(v)
    if h in SCORE_COLS:
        return float(v)
    return str(v)

def build_xlsx(rows):
    out = subprocess.run(["gh","api",f"repos/{REPO}/contents/{XLSX_PATH}","--jq",".content"],
                         capture_output=True, text=True)
    raw = base64.b64decode(out.stdout.strip())
    tf = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tf.write(raw); tf.close()
    import openpyxl
    wb = openpyxl.load_workbook(tf.name)
    ws = wb["综合数据"]
    hr = None
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 1).value == "排名":
            hr = r
            break
    if hr is None:
        raise RuntimeError("xlsx 中找不到 '排名' 表头行")
    ws.delete_rows(hr, ws.max_row - hr + 1)
    for c, h in enumerate(EXPECTED_HEADERS, 1):
        ws.cell(hr, c, h)
    for i, r in enumerate(rows, 1):
        for c, h in enumerate(EXPECTED_HEADERS, 1):
            ws.cell(hr + i, c, _typed(r.get(h, ""), h))
    buf = io.BytesIO()
    wb.save(buf)
    os.unlink(tf.name)
    return buf.getvalue()

# ---------- 派生视图（由 综合数据 计算） ----------
def _median(vals):
    s = sorted(vals); n = len(s)
    if n == 0:
        return 0
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2

def fmt_money(v):
    return f"${int(round(float(v))):,}"

def fmt_int(v):
    v = int(round(float(v)))
    return f"{v:,}" if v >= 1000 else f"{v}"

def fmt_score(v):
    v = float(v)
    return str(int(v)) if v == int(v) else str(v)

def build_region_rows(records):
    groups = defaultdict(list)
    for r in records:
        groups[r["区域"]].append(r)
    rows = [["🗺️ 按区域分组统计"], [],
            ["区域", "城市数", "月成本中位数", "月成本范围", "游民数中位数", "平均综合分"]]
    for reg in REGION_ORDER:
        rs = groups.get(reg, [])
        if not rs:
            continue
        # 仅聚合以美元计价的城市（货币类型=美元），避免混入人民币/欧元导致中位数失真
        costs = [int(r["月成本 (USD)"]) for r in rs if r.get("货币类型", "美元") == "美元"]
        nomad = [int(r["游民数"]) for r in rs]
        scores = [float(r["综合分"]) for r in rs]
        rows.append([reg, len(rs), f"${int(round(_median(costs)))}",
                     f"${min(costs)}-${max(costs)}", fmt_int(_median(nomad)),
                     round(sum(scores) / len(scores), 1)])
    return rows

def build_topic_rows(records):
    sections = [
        ("💰 最便宜 TOP 10（按月成本）", "月成本 (USD)", False, "最便宜", fmt_money),
        ("💎 最贵 TOP 10", "月成本 (USD)", True, "最贵", fmt_money),
        ("👥 最大社群 TOP 10", "游民数", True, "最大社群", fmt_int),
        ("🌐 网络最快 TOP 10", "网络", True, "网络最快", fmt_score),
        ("🛡️ 最安全 TOP 10", "安全", True, "最安全", fmt_score),
        ("🎉 生活品质 TOP 10", "生活", True, "生活品质", fmt_score),
        ("🗣️ 英语便利 TOP 10", "英语", True, "英语便利", fmt_score),
    ]
    rows = [["🏆 专题排行榜 TOP"], []]
    for title, metric, rev, label, fmt in sections:
        srt = sorted(records, key=lambda r: (float(r[metric]) * (-1 if rev else 1),
                                             -float(r["综合分"]), int(r["排名"])))
        rows.append([title]); rows.append([])
        rows.append(["排名", "城市", "国家", "区域", label])
        for i, r in enumerate(srt[:10], 1):
            rows.append([i, r["城市"], r["国家"], r["区域"], fmt(r[metric])])
        rows.append([])
    return rows

def write_td_rows(sid, rows):
    if not rows:
        return
    # 统一每行列数：腾讯文档 set_range_value_by_csv 要求每行列数一致，
    # 否则报 "wrong number of fields"。标题/空行用空串补齐到最大宽度。
    width = max(len(r) for r in rows)
    buf = io.StringIO()
    w = csv.writer(buf)
    for row in rows:
        w.writerow(list(row) + [""] * (width - len(row)))
    tdoc_call("sheet-mcp", "set_range_value_by_csv", {
        "file_id": TD_FILE_ID, "sheet_id": sid,
        "start_row": 0, "start_col": 0, "csv_data": buf.getvalue()})

def sync_td_derived(records):
    """把 综合数据 的派生视图（按区域 / 专题排行）重算并写回腾讯文档。"""
    write_td_rows(TD_SHEETS["按区域"], build_region_rows(records))
    write_td_rows(TD_SHEETS["专题排行"], build_topic_rows(records))
    print("✅ 已重算并写回腾讯文档派生视图（按区域 / 专题排行）")

def write_td_cell(row_idx, col_idx, value):
    """单格写回腾讯文档（反向同步细粒度用）。"""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([value])
    tdoc_call("sheet-mcp", "set_range_value_by_csv", {
        "file_id": TD_FILE_ID, "sheet_id": TD_SHEET_ID,
        "start_row": row_idx, "start_col": col_idx, "csv_data": buf.getvalue()})

def write_td_full_row(row_idx, record):
    """整行写入/追加（GitHub 新增城市回流用）。"""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([record.get(h, "") for h in EXPECTED_HEADERS])
    tdoc_call("sheet-mcp", "set_range_value_by_csv", {
        "file_id": TD_FILE_ID, "sheet_id": TD_SHEET_ID,
        "start_row": row_idx, "start_col": 0, "csv_data": buf.getvalue()})

def set_last_updated(td_rows, gh_map, modified_keys):
    """P0: 改动行 最后更新=今日；未改行保留 GitHub 原值（与仓库语义一致）。"""
    today = datetime.date.today().isoformat()
    for r in td_rows:
        key = (r["城市"], r["国家"])
        if key in modified_keys or key not in gh_map:
            r["最后更新"] = today
        else:
            cur = str(r.get("最后更新", "")).strip()
            r["最后更新"] = cur or gh_map[key].get("最后更新", "")

def sync_td_from_github(gh_rows, td_rows, modified):
    """P1: 细粒度反向同步 GitHub→腾讯文档。
    - GitHub 新增城市 → 整行追加（绝不删除 TD 独有行，那些是待审 PR）
    - 已存在城市 → 仅写回「GitHub 变 且 非用户待审编辑」的单元格
    """
    gh_map = {(r["城市"], r["国家"]): r for r in gh_rows}
    td_map = {(r["城市"], r["国家"]): r for r in td_rows}
    user_changes = {k: ch for k, ch in modified}
    td_index = {k: i for i, k in enumerate(td_map.keys())}
    # 当前布局：表头在 row 0，数据从 row 1 起（与 read_tencent_docs 的 start_row=0 一致）
    next_row = 1 + len(td_rows)
    write_cells, new_cities = 0, 0
    for k, gr in gh_map.items():
        if k not in td_map:
            write_td_full_row(next_row, gr)
            next_row += 1
            new_cities += 1
            continue
        di = td_index[k]
        skip = user_changes.get(k, {})
        for col in EXPECTED_HEADERS:
            if col in skip:
                continue
            if col in DERIVED:   # 排名/综合分/最后更新 为派生列，不从 GitHub 反向覆盖（GitHub 排名可能陈旧）
                continue
            gv = str(gr.get(col, "")).strip()
            tv = str(td_map[k].get(col, "")).strip()
            if gv != tv:
                write_td_cell(1 + di, EXPECTED_HEADERS.index(col), gv)
                write_cells += 1
    print(f"✅ GitHub→腾讯文档 反向同步：写回 {write_cells} 格，新增 {new_cities} 城")
    return write_cells, new_cities

_site_int = {"排名","游民数","月成本 (USD)","年均气温 (°C)"}
def _site_val(r, h):
    if h in _site_int:
        try: return int(float(r[h]))
        except: return r[h]
    if h in SCORE_COLS:
        try: return float(r[h])
        except: return r[h]
    return r[h]

def build_site_html(rows):
    """P4/P2: 由 rows 重生成 docs/index.html 的 CITIES_DATA 块（仅替换数据，不动交互/样式）。"""
    out = subprocess.run(["gh", "api", f"repos/{REPO}/contents/docs/index.html", "--jq", ".content"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"gh 读取 index.html 失败: {out.stderr}")
    raw = base64.b64decode(out.stdout.strip()).decode("utf-8")
    arr = [{h: _site_val(r, h) for h in EXPECTED_HEADERS} for r in rows]
    arr.sort(key=lambda x: int(x["排名"]))
    js = "const CITIES_DATA = " + json.dumps(arr, ensure_ascii=False) + ";"
    new_html, n = re.subn(r"const CITIES_DATA = \[.*?\];", js, raw, count=1, flags=re.DOTALL)
    if n == 0:
        raise RuntimeError("未在 index.html 中找到 CITIES_DATA 块")
    return new_html.encode("utf-8")

def backfill_td_last_updated():
    """P0/P4 一次性：为腾讯文档『综合数据』补『最后更新』列并回填（按主键对齐）。"""
    _, td_rows = read_tencent_docs()
    _, gh_rows = read_github_csv()
    gh_map = {(r["城市"], r["国家"]): r for r in gh_rows}
    today = datetime.date.today().isoformat()
    write_td_cell(3, 24, "最后更新")            # 表头（row idx 3, col idx 24 = Y）
    td_index = {(r["城市"], r["国家"]): i for i, r in enumerate(td_rows)}
    for k, gr in gh_map.items():
        if k in td_index:
            write_td_cell(4 + td_index[k], 24, gr.get("最后更新") or today)
    print(f"✅ 已为腾讯文档『综合数据』补『最后更新』列并回填（{len(td_index)} 城）")

def gh_put_content(path, content_bytes, message, branch, sha):
    data = {"message": message, "content": base64.b64encode(content_bytes).decode(),
            "branch": branch, "sha": sha}
    cmd = ["gh","api","-X","PUT",f"repos/{REPO}/contents/{path}","--input","-"]
    p = subprocess.run(cmd, input=json.dumps(data), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"gh 更新 {path} 失败: {p.stderr}")
    return json.loads(p.stdout)

def gh_get_sha(path):
    out = subprocess.run(["gh","api",f"repos/{REPO}/contents/{path}"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"gh 读取 {path} sha 失败: {out.stderr}")
    return json.loads(out.stdout)["sha"]

def open_bot_pr():
    """返回已有的开放同步 PR（head 分支前缀 sync/tencent-docs-），无则 None。"""
    r = subprocess.run(["gh","pr","list","--state","open","--json","headRefName,title"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout)
    except Exception:
        return None
    for p in prs:
        if str(p.get("headRefName", "")).startswith("sync/tencent-docs-"):
            return p
    return None

def push_to_github(rows, label="data"):
    existing = open_bot_pr()
    if existing:
        print(f"⏭️  已有开放同步 PR（{existing.get('headRefName')}），跳过新建避免刷屏；请先审核/合并既有 PR。")
        return False
    errors = validate(rows)
    if errors:
        print("❌ 校验失败，已中止（不会提交）：")
        for e in errors:
            print("  ", e)
        return False
    recompute(rows)
    main_sha = json.loads(subprocess.run(["gh","api",f"repos/{REPO}/git/ref/heads/main"],
                         capture_output=True, text=True).stdout)["object"]["sha"]
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"sync/tencent-docs-{ts}"
    subprocess.run(["gh","api","-X","POST","repos/{REPO}/git/refs".replace("{REPO}",REPO),
                    "--input","-"], input=json.dumps({"ref": f"refs/heads/{branch}", "sha": main_sha}),
                    capture_output=True, text=True, check=True)
    csv_sha = gh_get_sha(CSV_PATH)
    xlsx_sha = gh_get_sha(XLSX_PATH)
    new_csv = build_csv(rows).encode("utf-8")
    new_xlsx = build_xlsx(rows)
    gh_put_content(CSV_PATH, new_csv, f"data: sync from Tencent Docs ({ts})", branch, csv_sha)
    gh_put_content(XLSX_PATH, new_xlsx, f"data: regenerate xlsx from csv ({ts})", branch, xlsx_sha)
    # 网站随数据再生成（P4/P2）：同一 PR 内重刷 CITIES_DATA，Pages 自动发布
    try:
        html_sha = gh_get_sha("docs/index.html")
        new_html = build_site_html(rows)
        gh_put_content("docs/index.html", new_html,
                       f"website: regenerate CITIES_DATA ({ts})", branch, html_sha)
    except Exception as e:
        print("⚠️ 网站 index.html 重生成跳过：", e)
    # PR
    body = "本 PR 由腾讯文档共建表自动同步生成。\n\n变更已通过本地校验（对齐 CI validate_data.py）。请审核后 merge。"
    pr = subprocess.run(["gh","pr","create","--title",f"data: 同步腾讯文档共建数据 {ts}",
                         "--body",body,"--head",branch,"--base","main","--label",label],
                        capture_output=True, text=True)
    if pr.returncode != 0:
        raise RuntimeError(f"gh pr create 失败: {pr.stderr}")
    print("✅ 已开 PR：", pr.stdout.strip())
    return True

def push_to_tencent(rows):
    csv_data = build_csv(rows)
    tdoc_call("sheet-mcp", "set_range_value_by_csv", {
        "file_id": TD_FILE_ID, "sheet_id": TD_SHEET_ID,
        "start_row": 0, "start_col": 0, "csv_data": csv_data})
    print("✅ 已写回腾讯文档")

def print_report(added, removed, modified, gh_rows):
    print("=" * 50)
    print(f"📊 对比结果：GitHub 当前 {len(gh_rows)} 城 | 新增 {len(added)} | 删除 {len(removed)} | 修改 {len(modified)}")
    print("=" * 50)
    for k in added:
        print(f"  ➕ 新增城市: {k[0]} ({k[1]})")
    for k in removed:
        print(f"  ➖ 删除城市: {k[0]} ({k[1]})")
    for k, ch in modified:
        print(f"  ✏️  {k[0]} ({k[1]}):")
        for col, (old, new) in ch.items():
            print(f"       {col}: {old} → {new}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry-run","apply","pull","restore","backfill"], default="dry-run")
    ap.add_argument("--version", help="restore 模式下的快照 tag (文件名 nomad_<tag>.csv)")
    args = ap.parse_args()

    print("📥 读取腾讯文档共建表 …")
    _, td_rows = read_tencent_docs()
    print(f"   腾讯文档: {len(td_rows)} 行")
    print("📥 读取 GitHub 当前 CSV …")
    _, gh_rows = read_github_csv()
    print(f"   GitHub: {len(gh_rows)} 行")

    added, removed, modified = diff(td_rows, gh_rows)
    print_report(added, removed, modified, gh_rows)

    if args.mode == "dry-run":
        if not (added or removed or modified):
            print("\n✅ 无差异，无需同步。")
        else:
            print("\nℹ️  dry-run 模式：未提交任何变更。用 --mode apply 提交。")
        return

    if args.mode == "pull":
        # 纯拉取：GitHub → 腾讯文档（以 GitHub 为权威源，不推送 TD→GitHub）
        # 适用于「GitHub 更新了，把最新 CSV 同步回共建表」的场景。
        td_keys = {(r["城市"], r["国家"]) for r in td_rows}
        gh_keys = {(r["城市"], r["国家"]) for r in gh_rows}
        only_td = td_keys - gh_keys
        if only_td:
            print(f"⚠️ 中止 pull：腾讯文档有 {len(only_td)} 个 GitHub 没有的城市，pull 会丢弃它们：")
            for k in sorted(only_td):
                print("   -", k[0], k[1])
            print("   如需保留这些城市，请改用 --mode apply（会为它们建 PR）。")
            sys.exit(1)
        print(f"\n📥 拉取 GitHub 最新 {len(gh_rows)} 城写入腾讯文档『综合数据』…")
        push_to_tencent(gh_rows)
        sync_td_derived(gh_rows)
        print("✅ GitHub → 腾讯文档 同步完成。")
        return

    if args.mode == "restore":
        if not args.version:
            print("❌ restore 需要 --version <tag>")
            sys.exit(1)
        snap = os.path.join(SNAP_DIR, f"nomad_{args.version}.csv")
        if not os.path.exists(snap):
            print(f"❌ 快照不存在: {snap}")
            sys.exit(1)
        with open(snap, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        # 确保 最后更新 存在（旧快照可能只有 24 列）
        today = datetime.date.today().isoformat()
        for r in rows:
            if not str(r.get("最后更新", "")).strip():
                r["最后更新"] = today
        print(f"♻️  回滚至快照 {args.version} ({len(rows)} 行) …")
        # 回滚：写回 GitHub(PR) + 腾讯文档
        if push_to_github(rows):
            push_to_tencent(rows)
            sync_td_derived(rows)
        return

    if args.mode == "backfill":
        # P0/P4 一次性：为腾讯文档补『最后更新』列并回填
        backfill_td_last_updated()
        return

    if args.mode == "apply":
        gh_map = {(r["城市"], r["国家"]): r for r in gh_rows}
        modified_keys = {k for k, _ in modified}
        # 1) 腾讯文档 → GitHub（建 PR，等你审核）
        if added or removed or modified:
            save_snapshot(gh_rows, f"pre-{datetime.datetime.now():%Y%m%d-%H%M%S}")
            set_last_updated(td_rows, gh_map, modified_keys)
            print("\n🚀 提交至 GitHub（建分支 + PR，等你审核）…")
            push_to_github(td_rows)
            # 同步派生视图（按区域 / 专题排行）回腾讯文档，保持公开表一致
            sync_td_derived(td_rows)
        # 2) 反向同步 GitHub → 腾讯文档（细粒度，直接回写公开表）
        wc, nc = sync_td_from_github(gh_rows, td_rows, modified)
        if not (added or removed or modified) and wc == 0 and nc == 0:
            print("\n✅ 双向均无差异，跳过。")
        return

if __name__ == "__main__":
    main()
