#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""
community_metric_trial 验证阶段判定脚本（预注册冻结件之一）
============================================================
pilot_blur_metrics.py 的环境参数化版。口径逐字继承试点（见 PREREG §1），
新增：D_sym 对称伪流代理、Haldane OR、形状比谓词、双攻免疫幸存者、
P4 集合（纬向 S_A ∧ 经向两关）、BH93 静止负对照零响应检验。

用法：validate_envs.py {zonal|merid|diag45|bh93|all}
盲区纪律（硬断言）：merid/diag45/bh93 只有在 PREREG 已封存
（.sha256 存在、三件套不可写、逐文件哈希相符）后才允许运行。
zonal 属探索域，随时可跑（自检：S_A 必须复现 204）。
产出：final/VALIDATION_<env>.json, final/ARRAYS_<env>.npz, final/validate_<env>.log
"""
import hashlib, json, os, sys, time
from collections import defaultdict
import numpy as np
import netCDF4 as nc
from scipy.ndimage import gaussian_filter

ENV = "/data/xinyuan/GOAI_ai4s_env"
OUT = f"{ENV}/e71_innov/community_metric_trial/final"
PREREG = f"{OUT}/PREREG_community_metric_trial.md"
SEAL = f"{OUT}/PREREG_community_metric_trial.sha256"
sys.path.insert(0, f"{ENV}/scripts")

FIELDS = ("u", "v", "w", "temp", "zeta")
REGIONS = [("all", None), ("d200", ("deeper", 200)), ("d400", ("deeper", 400)),
           ("d800", ("deeper", 800)), ("d1500", ("deeper", 1500)),
           ("s50", ("shallow", 50)), ("s200", ("shallow", 200))]
SIGMAS = (1.0, 2.0, 4.0)
EPS = 1e-12
FLOOR = float(np.log(1.001))
ETA_ZONAL_FALLBACK = 0.025500820115274825   # PREREG §1.8 锁死

CFG = {
    "zonal":  dict(ledger=f"{ENV}/ledger/env2_runs.jsonl",        runs=f"{ENV}/runs",
                   labels="regraded", sweep=f"{ENV}/ledger/knob_sweep.json"),
    "merid":  dict(ledger=f"{ENV}/ledger/env2_merid_runs.jsonl",  runs=f"{ENV}/runs_merid",
                   labels="hidden",   sweep=f"{ENV}/ledger/knob_sweep_merid.json"),
    "diag45": dict(ledger=f"{ENV}/ledger/env2_diag45_runs.jsonl", runs=f"{ENV}/runs_diag45",
                   labels="hidden",   sweep=f"{ENV}/ledger/knob_sweep_diag45.json"),
}

np.seterr(all="ignore")
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
_LOG = [None]
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    if _LOG[0]:
        _LOG[0].write(s + "\n"); _LOG[0].flush()

# ---------------- 封存门（PREREG §0） ----------------
def require_seal():
    assert os.path.exists(SEAL), "拒绝：未找到 .sha256——留出环境只能在封存后读取"
    for p in (PREREG, os.path.abspath(__file__), f"{OUT}/score_prereg.py", SEAL):
        assert os.path.exists(p), f"拒绝：封存件缺失 {p}"
        assert not (os.stat(p).st_mode & 0o222), f"拒绝：{p} 仍可写（未 chmod 444）"
    listed = {}
    for line in open(SEAL):
        parts = line.strip().split()
        if len(parts) == 2 and len(parts[0]) == 64:
            listed[os.path.basename(parts[1].lstrip("*"))] = parts[0]
    assert listed, "拒绝：.sha256 无哈希行"
    for base, h in listed.items():
        hh = hashlib.sha256(open(f"{OUT}/{base}", "rb").read()).hexdigest()
        assert hh == h, f"拒绝：{base} 哈希与封存记录不符"
    # SEAL_INPUTS.txt：P4 判分输入（ARRAYS_zonal.npz / VALIDATION_zonal.json）物证链
    sinp = f"{OUT}/SEAL_INPUTS.txt"
    if os.path.exists(sinp):
        for line in open(sinp):
            parts = line.strip().split()
            if len(parts) == 2 and len(parts[0]) == 64:
                base = os.path.basename(parts[1].lstrip("*"))
                p = f"{OUT}/{base}"
                assert os.path.exists(p), f"拒绝：登记材料缺失 {base}（SEAL_INPUTS.txt）"
                hh = hashlib.sha256(open(p, "rb").read()).hexdigest()
                assert hh == parts[0], f"拒绝：{base} 与 SEAL_INPUTS.txt 登记哈希不符"
    return sorted(listed.items())

# ---------------- 场与基元（试点逐字口径） ----------------
def load_fields(run_dir):
    fn = f"{run_dir}/out_his.nc"
    if not os.path.exists(fn):
        return None
    d = nc.Dataset(fn)
    out = {"h": np.asarray(d["h"][:]), "Cs": np.asarray(d["Cs_r"][:]),
           "pm": np.asarray(d["pm"][:]), "pn": np.asarray(d["pn"][:])}
    for f in FIELDS:
        if f in d.variables:
            out[f] = np.asarray(d[f][-1])          # 原生 dtype（float32）
    if "temp" in d.variables:
        out["temp0"] = np.asarray(d["temp"][0])
    d.close()
    return out

def blur_uv(fl, sigma):
    g = dict(fl)
    for f in ("u", "v"):
        if f in g:
            g[f] = gaussian_filter(g[f], sigma=(0, sigma, sigma), mode="nearest")
    return g

def base_from_fields(fl):
    h = fl["h"]; Cs = fl["Cs"]; out = {}
    for f in FIELDS:
        if f not in fl:
            continue
        arr = np.asarray(fl[f])
        scale = 100.0 if f in ("u", "v", "w", "zeta") else 1.0
        arr = arr * scale
        if arr.ndim == 2:
            depth = np.zeros_like(arr)
        else:
            n = min(arr.shape[-1], h.shape[-1]); m = min(arr.shape[-2], h.shape[-2])
            arr = arr[..., :m, :n]
            depth = -Cs[:, None, None] * h[None, :m, :n]
            if arr.shape[0] != depth.shape[0]:
                arr = arr[:depth.shape[0]]
        for rname, rspec in REGIONS:
            if rspec is None:
                msk = np.ones_like(depth, dtype=bool)
            elif rspec[0] == "deeper":
                msk = depth > rspec[1]
            else:
                msk = depth < rspec[1]
            v = arr[msk]; v = v[np.isfinite(v)]
            if v.size == 0:
                continue
            av = np.abs(v)
            out[f"{f}|{rname}|rms"] = float(np.sqrt((v ** 2).mean()))
            out[f"{f}|{rname}|max"] = float(av.max())
            out[f"{f}|{rname}|mean_abs"] = float(av.mean())
            out[f"{f}|{rname}|p95"] = float(np.percentile(av, 95))
    return out

# ---------------- 社区指标基元（试点 11 个） ----------------
EXQ = ["spec_lo", "spec_mid", "spec_hi", "spec_slope", "hi_lo_ratio",
       "enstrophy_surf", "div_surf", "ke_total", "temp_drift",
       "budget_res_u", "budget_res_v"]

def exemplar_from_fields(fl):
    u = fl["u"]; v = fl["v"]
    dx = 1.0 / float(np.mean(fl["pm"])); dy = 1.0 / float(np.mean(fl["pn"]))
    ur = 0.5 * (u[:, :, :-1] + u[:, :, 1:])[:, 1:-1, :]
    vr = 0.5 * (v[:, :-1, :] + v[:, 1:, :])[:, :, 1:-1]
    su = ur[-1] - ur[-1].mean(); sv = vr[-1] - vr[-1].mean()
    F = np.fft.fft2(su); G = np.fft.fft2(sv)
    E2 = 0.5 * (np.abs(F) ** 2 + np.abs(G) ** 2) / (su.size ** 2)
    ny, nx = su.shape
    ky = np.fft.fftfreq(ny) * ny; kx = np.fft.fftfreq(nx) * nx
    KH = np.rint(np.sqrt(ky[:, None] ** 2 + kx[None, :] ** 2)).astype(int)
    Ek = np.bincount(KH.ravel(), weights=E2.ravel(), minlength=KH.max() + 1)
    lo = float(Ek[1:5].sum()); mid = float(Ek[5:11].sum()); hi = float(Ek[11:23].sum())
    kk = np.arange(2, 17); ek = Ek[2:17]; okm = ek > 0
    slope = float(np.polyfit(np.log(kk[okm]), np.log(ek[okm]), 1)[0]) if okm.sum() > 3 else 0.0
    dvdx = np.diff(v, axis=2) / dx; dudy = np.diff(u, axis=1) / dy
    ens = float(np.sqrt(((dvdx[-1] - dudy[-1]) ** 2).mean()))
    dudx = np.diff(u, axis=2) / dx; dvdy = np.diff(v, axis=1) / dy
    div = dudx[:, 1:-1, :] + dvdy[:, :, 1:-1]
    dvr = float(np.sqrt((div[-1] ** 2).mean()))
    ke = float(0.5 * np.mean(ur ** 2 + vr ** 2))
    td = abs(float(np.mean(fl["temp"])) - float(np.mean(fl["temp0"])))
    return dict(spec_lo=lo, spec_mid=mid, spec_hi=hi, spec_slope=slope,
                hi_lo_ratio=float(hi / max(lo, EPS)),
                enstrophy_surf=ens, div_surf=dvr, ke_total=ke, temp_drift=td)

def budget_from_dia(run_dir):
    fn = f"{run_dir}/out_dia.nc"
    out = {}
    if not os.path.exists(fn):
        return out
    try:
        d = nc.Dataset(fn)
        for c in ("u", "v"):
            acc = np.asarray(d[f"{c}_accel"][-1], dtype=float)
            s = np.zeros_like(acc)
            for t in ("cor", "hadv", "vadv", "hvisc", "vvisc"):
                s = s + np.asarray(d[f"{c}_{t}"][-1], dtype=float)
            r = acc - s
            out[f"budget_res_{c}"] = float(np.sqrt((r ** 2).mean()))
            out[f"_accel_rms_{c}"] = float(np.sqrt((acc ** 2).mean()))
            out[f"_sum_rms_{c}"] = float(np.sqrt((s ** 2).mean()))
        d.close()
    except Exception as e:
        log("  [dia fail]", run_dir, repr(e))
    return out

# ---------------- 排名与统计工具 ----------------
def rank0(X):
    return np.argsort(np.argsort(X, axis=0), axis=0).astype(float)

def spear_vec(X, y):
    rx = rank0(X); ry = np.argsort(np.argsort(y)).astype(float)
    rx = rx - rx.mean(0); ry = ry - ry.mean()
    sx = rx.std(0); sy = ry.std()
    out = np.zeros(X.shape[1])
    good = (sx > 0) & (sy > 0)
    if good.any():
        out[good] = (rx[:, good] * ry[:, None]).mean(0) / (sx[good] * sy)
    return out

def jstat(a, b):
    n11 = int((a & b).sum()); n10 = int((a & ~b).sum())
    n01 = int((~a & b).sum()); n00 = int((~a & ~b).sum())
    union = n11 + n10 + n01
    orr = (n11 * n00) / (n10 * n01) if n10 * n01 > 0 else None
    orh = ((n11 + .5) * (n00 + .5)) / ((n10 + .5) * (n01 + .5))   # Haldane（判分口径）
    return dict(n11=n11, n10=n10, n01=n01, n00=n00,
                jaccard=round(n11 / union, 4) if union else None,
                odds_ratio_raw=round(orr, 3) if orr else None,
                odds_ratio_haldane=round(orh, 3))

def sp_masked(a, b, msk):
    if msk.sum() < 10:
        return None
    ra = np.argsort(np.argsort(a[msk])); rb = np.argsort(np.argsort(b[msk]))
    return round(float(np.corrcoef(ra, rb)[0, 1]), 4)

# ================= 单环境全流程 =================
def run_env(env):
    cfg = CFG[env]
    _LOG[0] = open(f"{OUT}/validate_{env}.log", "w")
    te = time.time()
    log(f"== validate_envs [{env}] start", time.strftime("%F %T"))

    # ---- 账本（PREREG §1.2/1.3） ----
    reg = {}
    if cfg["labels"] == "regraded":
        for l in open(f"{ENV}/ledger/regraded_v2.jsonl"):
            r = json.loads(l); reg[r["run_id"]] = r["skill_vs_zero"]
    seen = {}; byp = {}
    for l in open(cfg["ledger"]):
        r = json.loads(l)
        if not (r["obs"].get("valid") and r["ntimes"] == 8640):
            continue
        seen[r["run_id"]] = r["bathy"]
        if cfg["labels"] == "hidden" and r["bathy"] == "r26steep" and \
           (r.get("hidden") or {}).get("skill_vs_zero") is not None:
            reg[r["run_id"]] = r["hidden"]["skill_vs_zero"]
        a = r["action"]
        k = tuple(round(a.get(x, -1), 6) for x in ("VISC2", "VISC4", "AKV_BAK", "TNU2"))
        byp.setdefault(k, {})[r["bathy"]] = r["run_id"]
    # 行序锁死 = 账本首次出现序（dict 插入序，与试点/e67b 逐字一致）：
    # argsort 双排名的并列打破依赖行序，改序会漂移含并列候选的 A/sgn（PREREG §1.1）
    r26 = [k for k, v in seen.items() if v == "r26steep" and k in reg]
    flat = [k for k, v in seen.items() if v == "flat"]
    PAIRS = [(v["r26steep"], v["flat"]) for v in byp.values()
             if "r26steep" in v and "flat" in v]

    # ---- 噪声尺 η_env（PREREG §1.8） ----
    dup = defaultdict(list)
    for l in open(cfg["ledger"]):
        r = json.loads(l)
        if r["obs"].get("valid") and r["ntimes"] == 8640 and r["bathy"] == "r26steep":
            dup[r["run_id"]].append(r["obs"])
    OBSF = ("u_max", "u_rms", "surf_max", "deep_rms_200", "deep_rms_400",
            "deep_rms_800", "deep_rms_1500")
    cvs = []
    for rid, rows in dup.items():
        if len(rows) < 3:
            continue
        for f in OBSF:
            vals = np.array([x[f] for x in rows
                             if x.get(f) is not None and x.get(f) > 0], float)
            if len(vals) >= 3:
                cvs.append(float(np.std(np.log(vals))))
    if cvs:
        eta_scalar = float(np.median(cvs)); eta_src = f"本环境账本重复行 n_cv={len(cvs)}"
    else:
        eta_scalar = ETA_ZONAL_FALLBACK;    eta_src = "无重复行，沿用纬向 η（PREREG §1.8 锁死）"
    thr = max(2 * eta_scalar, FLOOR)

    LAD = sorted([(e["val"], e["run_id"]) for e in json.load(open(cfg["sweep"]))
                  if e["knob"] == "VISC2" and e["bathy"] == "r26steep"])
    assert len(LAD) >= 5, f"VISC2 阶梯不足 5 档: {LAD}"
    log(f"[sets] ASET={len(r26)} flat={len(flat)} pairs={len(PAIRS)} "
        f"eta={eta_scalar:.6f} ({eta_src}) thr={thr:.6f} ladder={[v for v,_ in LAD]}")

    Fcache = {}
    def fields_of(rid):
        if rid not in Fcache:
            Fcache[rid] = load_fields(f"{cfg['runs']}/{rid}")
        return Fcache[rid]

    # ---- 自检 1（仅 zonal）：内存版基元 vs 官方逐位一致 ----
    if env == "zonal":
        from metric_search import base_quantities as bq_orig
        for rid in sorted(r26)[:3]:
            q1 = bq_orig(f"{cfg['runs']}/{rid}"); q2 = base_from_fields(fields_of(rid))
            assert set(q1) == set(q2), "key set mismatch"
            md = max(abs(q1[k] - q2[k]) / max(abs(q1[k]), 1e-30) for k in q1)
            log(f"[validate-bq] {rid} keys={len(q1)} max_rel_diff={md:.2e}")
            assert md < 1e-12

    # ---- 基元矩阵 ----
    need = sorted(set(r26) | set(flat) | set(x for p in PAIRS for x in p)
                  | set(r for _, r in LAD))
    Q = {}
    for i, rid in enumerate(need):
        fl = fields_of(rid)
        assert fl is not None, f"缺场文件: {cfg['runs']}/{rid}"
        Q[rid] = base_from_fields(fl)
        if (i + 1) % 40 == 0:
            log(f"  base {i+1}/{len(need)} ({time.time()-te:.0f}s)")
    keys = sorted(set.intersection(*[set(Q[r]) for r in need]))
    K = len(keys)
    log(f"[keys] {K} (expect 124)")

    key_dev = None
    if env != "zonal":
        zk = [str(x) for x in np.load(f"{OUT}/ARRAYS_zonal.npz", allow_pickle=True)["keys"]]
        if keys != zk:
            inter = sorted(set(keys) & set(zk))
            key_dev = dict(env_keys=K, zonal_keys=len(zk), inter=len(inter))
            log(f"[DEVIATION] 键集与纬向不一致 → 用交集 {len(inter)}（PREREG §1.14）")
            keys = inter; K = len(keys)

    def mat(rids):
        return np.array([[Q[r][k] for k in keys] for r in rids])

    M26 = mat(r26); S = np.array([reg[r] for r in r26]); MFL = mat(flat)
    P26 = mat([a for a, _ in PAIRS]); PFL = mat([b for _, b in PAIRS])

    # ---- 美颜后的基元（ASET steep） ----
    PB = {s: np.zeros((len(r26), K)) for s in SIGMAS}
    for i, rid in enumerate(r26):
        fl = fields_of(rid)
        for s in SIGMAS:
            qb = base_from_fields(blur_uv(fl, s))
            PB[s][i] = [qb[k] for k in keys]
        if (i + 1) % 20 == 0:
            log(f"  blur {i+1}/{len(r26)} ({time.time()-te:.0f}s)")

    # ---- 候选空间 ----
    NUM, DEN = [], []
    for i in range(K):
        NUM.append(i); DEN.append(-1)
        for j in range(K):
            if j != i:
                NUM.append(i); DEN.append(j)
    NUM = np.array(NUM); DEN = np.array(DEN); NCND = len(NUM)
    DENi = np.where(DEN < 0, K, DEN)

    def cvals(M):
        Me = np.concatenate([M, np.ones((M.shape[0], 1))], axis=1)
        return M[:, NUM] / Me[:, DENi]

    def colbad(M):
        return (np.abs(M) < EPS).any(axis=0)

    badden = colbad(M26) | colbad(MFL) | colbad(P26) | colbad(PFL)
    valid = np.ones(NCND, bool)
    rmask = DEN >= 0
    valid[rmask] &= ~badden[DEN[rmask]]
    V26 = cvals(M26); VFL = cvals(MFL)
    valid &= (V26 > 0).all(0) & (VFL > 0).all(0)
    valid &= np.isfinite(V26).all(0) & np.isfinite(VFL).all(0)

    A = -spear_vec(V26, S)
    iu = keys.index("u|all|rms"); iv = keys.index("v|all|rms")
    D_u = spear_vec(V26, M26[:, iu])
    D_sym = spear_vec(V26, np.sqrt(M26[:, iu] ** 2 + M26[:, iv] ** 2))   # PREREG §1.9
    B = (cvals(PFL) >= cvals(P26)).mean(0)
    SA = valid & (A >= 0.7) & (B >= 0.9)
    log(f"[gates] valid={int(valid.sum())}/{NCND}  S_A_env={int(SA.sum())}"
        + ("  (zonal expect 204)" if env == "zonal" else ""))
    if env == "zonal":
        assert int(SA.sum()) == 204, f"自检失败：纬向 S_A={int(SA.sum())} ≠ 204"

    # ---- 美颜 Δlog 与方向化改善 ----
    sgn = np.sign(A)
    LG0 = np.log(np.maximum(M26, EPS))
    blur = {}
    for s in SIGMAS:
        DL = np.log(np.maximum(PB[s], EPS)) - LG0
        DLe = np.concatenate([DL, np.zeros((DL.shape[0], 1))], axis=1)
        CD = DL[:, NUM] - DLe[:, DENi]
        imp = -sgn[None, :] * CD
        blur[s] = dict(med=np.median(imp, 0), frac=(imp > 0).mean(0))
        del CD, imp, DL, DLe

    eta = np.full(NCND, eta_scalar)
    thrv = np.maximum(2 * eta, FLOOR)

    # ---- 黏性阶梯 ----
    lvals = np.array([v for v, _ in LAD])
    LL = np.log(np.maximum(mat([r for _, r in LAD]), EPS))
    LLe = np.concatenate([LL, np.zeros((LL.shape[0], 1))], axis=1)
    CL = LL[:, NUM] - LLe[:, DENi]
    tend = -sgn * spear_vec(CL, lvals)
    veff = -sgn * (CL[-1] - CL[0])
    del CL

    # ---- 判定 ----
    oriented = valid & (sgn != 0)
    gb = {s: oriented & (blur[s]["frac"] >= 0.9) & (blur[s]["med"] > thrv) for s in SIGMAS}
    gv = oriented & (tend >= 0.7) & (veff > thrv)

    fld = [k.split("|")[0] for k in keys]
    isuv = np.array([f in ("u", "v") for f in fld])
    uvt = isuv[NUM] | (rmask & isuv[np.maximum(DEN, 0)])
    # 形状比谓词（PREREG §1.11）
    shape = np.zeros(NCND, bool)
    rr = np.where(rmask)[0]
    for i in rr:
        fn_, fd_ = fld[NUM[i]], fld[DEN[i]]
        shape[i] = (fn_ == fd_) or ({fn_, fd_} == {"u", "v"})

    def ndnum(msk):
        return len(set(int(x) for x in NUM[msk]))

    res = dict(
        env=env, stamp=time.strftime("%F %T"),
        prereg_sha_file=(open(SEAL).read() if os.path.exists(SEAL) else None),
        sets=dict(ASET=len(r26), flat=len(flat), pairs=len(PAIRS),
                  visc_ladder=[float(v) for v in lvals],
                  aset_run_ids=r26),
        keys=K, key_deviation=key_dev, n_candidates=NCND,
        n_valid=int(valid.sum()), n_oriented=int(oriented.sum()),
        S_A_env=int(SA.sum()),
        n_distinct_numerators_S_A_env=ndnum(SA),   # PREREG §9.3 双口径的机械指针
        eta=dict(eta_scalar_log=eta_scalar, source=eta_src, thr_log=float(thr),
                 floor_log=FLOOR),
        denominator_note="一切 frac_of_valid 分母=n_valid；名义分母 15376 双报（PREREG §9.11）",
    )

    res["blur_gameable"] = {}
    for s in SIGMAS:
        g = gb[s]
        res["blur_gameable"][f"sigma{s:g}"] = dict(
            n=int(g.sum()),
            frac_of_valid=round(float(g.sum() / max(valid.sum(), 1)), 4),
            frac_of_nominal_15376=round(float(g.sum() / NCND), 4),
            n_in_uv_touch=int((g & uvt).sum()),
            n_in_S_A_env=int((g & SA).sum()),
            frac_of_S_A_env=round(float((g & SA).sum() / max(SA.sum(), 1)), 4),
            n_distinct_numerators=ndnum(g),
            n_distinct_numerators_in_S_A_env=ndnum(g & SA),
            n_nonuv_hit=int((g & ~uvt).sum()),   # 攻击面自检：应为 0
            median_impr_pct_when_gameable=(round(float(np.expm1(np.median(blur[s]["med"][g])) * 100), 3)
                                           if g.any() else None))
    res["visc_gameable"] = dict(
        n=int(gv.sum()), frac_of_valid=round(float(gv.sum() / max(valid.sum(), 1)), 4),
        n_in_S_A_env=int((gv & SA).sum()),
        median_eff_x_when_gameable=(round(float(np.exp(np.median(veff[gv]))), 2) if gv.any() else None))

    # ---- 机理同构（P2/P3） ----
    iso = {}
    for s in SIGMAS:
        iso[f"table_sigma{s:g}"] = jstat(gb[s][oriented], gv[oriented])
    bm = blur[2.0]["med"]
    iso["rho_blur2_visc_all_oriented"] = sp_masked(bm, veff, oriented)
    iso["rho_blur2_visc_Apos"] = sp_masked(bm, veff, oriented & (A > 0))
    iso["rho_blur2_visc_uvtouch_Apos"] = sp_masked(bm, veff, oriented & (A > 0) & uvt)
    iso["rho_blur2_D_sym"] = sp_masked(bm, D_sym, oriented)      # P3 判分量
    iso["rho_blur2_D_u"] = sp_masked(bm, D_u, oriented)          # E65 连续性观察
    iso["rho_visc_D_sym"] = sp_masked(veff, D_sym, oriented)
    res["isomorphism"] = iso

    # ---- 阈值敏感性（PREREG §9.12 同表） ----
    sens = {}
    for mult in (1, 2, 3):
        for fr in (0.8, 0.9):
            t2 = np.maximum(mult * eta, FLOOR)
            g2 = oriented & (blur[2.0]["frac"] >= fr) & (blur[2.0]["med"] > t2)
            sens[f"mult{mult}_frac{fr}"] = dict(n=int(g2.sum()), n_in_S_A_env=int((g2 & SA).sum()))
    res["threshold_sensitivity_sigma2"] = sens

    # ---- 双攻免疫幸存者与形状比（P8） ----
    surv = SA & ~gb[2.0] & ~gv
    surv4 = SA & ~gb[4.0] & ~gv
    res["dual_immune"] = dict(
        n=int(surv.sum()), n_shape=int((surv & shape).sum()),
        shape_frac=(round(float((surv & shape).sum() / surv.sum()), 4) if surv.sum() else None),
        n_distinct_numerators=ndnum(surv),
        n_sigma4=int(surv4.sum()),
        composition=None)
    if surv.sum():
        comp = defaultdict(int)
        for i in np.where(surv)[0]:
            if DEN[i] < 0:
                comp[f"abs:{fld[NUM[i]]}"] += 1
            else:
                comp[f"{fld[NUM[i]]}/{fld[DEN[i]]}"] += 1
        res["dual_immune"]["composition"] = dict(sorted(comp.items(), key=lambda x: -x[1]))

    # ---- P4 集合（merid 判分；diag45 同式作观察）----
    # 键集偏差预案（PREREG §1.14）：用 ARRAYS_zonal.npz 的 keys/NUM/DEN 按
    # (分子键, 分母键) 名称把纬向 S_A 精确映射到交集候选索引（候选级 A/B 只依赖
    # 自身列，名称映射即精确重建）。任何异常只记 p4_unavailable，不拖死本环境落盘。
    if env != "zonal":
        try:
            z = np.load(f"{OUT}/ARRAYS_zonal.npz", allow_pickle=True)
            SAz_full = np.asarray(z["SA"], bool)
            assert int(SAz_full.sum()) == 204, \
                f"P4 自检失败：纬向 S_A={int(SAz_full.sum())} ≠ 204"
            if key_dev is None:
                assert len(SAz_full) == NCND, "P4：键集一致但候选数不一致（不应发生）"
                SAz = SAz_full
            else:
                zk = [str(x) for x in z["keys"]]
                zNUM = np.asarray(z["NUM"]); zDEN = np.asarray(z["DEN"])
                zidx = {}
                for c in range(len(zNUM)):
                    dk = zk[zDEN[c]] if zDEN[c] >= 0 else None
                    zidx[(zk[zNUM[c]], dk)] = c
                SAz = np.zeros(NCND, bool)
                for c in range(NCND):
                    dk = keys[DEN[c]] if DEN[c] >= 0 else None
                    SAz[c] = bool(SAz_full[zidx[(keys[NUM[c]], dk)]])
                log(f"[P4] 键集偏差→名称映射：纬向 S_A {int(SAz_full.sum())} "
                    f"→ 交集索引内 {int(SAz.sum())}（记 DEVIATIONS）")
            m88 = SAz & valid & (A >= 0.7) & (B >= 0.9)
            hit = m88 & gb[2.0]
            res["p4_zonalSA_cross_survivors"] = dict(
                n_set=int(m88.sum()), expect=(88 if env == "merid" else 140),
                n_zonal_SA_mapped=int(SAz.sum()),
                n_hit_blur2=int(hit.sum()),
                frac_hit=(round(float(hit.sum() / m88.sum()), 4) if m88.sum() else None),
                n_distinct_numerators_set=ndnum(m88), n_distinct_numerators_hit=ndnum(hit))
        except Exception as exc:
            log("[P4 unavailable]", repr(exc))
            res["p4_zonalSA_cross_survivors"] = dict(
                p4_unavailable=True, error=repr(exc),
                note="按 PREREG §1.14：P4 判 FAIL 并记 DEVIATIONS，其余判分输入照常落盘")

    # ---- 社区指标基元体检（P5） ----
    log("[exemplars] computing …")
    def exvec(rid):
        e = exemplar_from_fields(fields_of(rid))
        e.update({k2: v2 for k2, v2 in budget_from_dia(f"{cfg['runs']}/{rid}").items()})
        return e
    res["budget_closure_check"] = budget_from_dia(f"{cfg['runs']}/{sorted(r26)[0]}")
    EX26 = [exvec(r) for r in r26]
    EXB = {s: [exemplar_from_fields(blur_uv(fields_of(r), s)) for r in r26] for s in SIGMAS}
    EXP26 = [exvec(a) for a, _ in PAIRS]; EXPFL = [exvec(b) for _, b in PAIRS]
    EXL = [exvec(r) for _, r in LAD]

    ex_report = {}
    for q in EXQ:
        v26 = np.array([e.get(q, np.nan) for e in EX26])
        if not np.isfinite(v26).all():
            ex_report[q] = dict(note="missing values"); continue
        aq = -float(spear_vec(v26[:, None], S)[0])
        p26v = np.array([e.get(q, np.nan) for e in EXP26])
        pflv = np.array([e.get(q, np.nan) for e in EXPFL])
        sg = np.sign(aq) if aq != 0 else 0.0
        b_or = float(np.mean(pflv >= p26v)) if sg >= 0 else float(np.mean(pflv <= p26v))
        row = dict(A=round(aq, 3), B_raw=round(float(np.mean(pflv >= p26v)), 3),
                   B_oriented=round(b_or, 3), lower_is_better=bool(aq > 0))
        if q.startswith("budget_res"):
            row["blur_reachable"] = False
        else:
            for s in SIGMAS:
                vb = np.array([e.get(q, np.nan) for e in EXB[s]])
                if (v26 > 0).all() and (vb > 0).all():
                    rel = vb / v26 - 1.0
                else:
                    rel = (vb - v26) / np.maximum(np.abs(v26), EPS)
                imp = -sg * rel
                row[f"blur{s:g}_med_rel_pct"] = round(float(np.median(rel) * 100), 2)
                row[f"blur{s:g}_oriented_impr_pct"] = round(float(np.median(imp) * 100), 2)
                row[f"blur{s:g}_frac_improve"] = round(float(np.mean(imp > 0)), 3)
                row[f"blur{s:g}_max_absrel"] = float(np.max(np.abs(rel)))   # P5(b) 结构零判据
        vl = np.array([e.get(q, np.nan) for e in EXL])
        if np.isfinite(vl).all():
            row["visc_spearman"] = round(float(spear_vec(vl[:, None], lvals)[0]), 3)
            if (vl > 0).all():
                row["visc_eff_x_0toMax"] = round(float(vl[-1] / vl[0]), 3)
        ex_report[q] = row
    res["exemplars"] = ex_report

    # ---- 落盘 ----
    np.savez_compressed(
        f"{OUT}/ARRAYS_{env}.npz",
        keys=np.array(keys), NUM=NUM, DEN=DEN, valid=valid, A=A, B=B,
        D_u=D_u, D_sym=D_sym, eta=eta, uv_touch=uvt, shape=shape, SA=SA,
        blur_med_s1=blur[1.0]["med"], blur_med_s2=blur[2.0]["med"], blur_med_s4=blur[4.0]["med"],
        blur_frac_s1=blur[1.0]["frac"], blur_frac_s2=blur[2.0]["frac"], blur_frac_s4=blur[4.0]["frac"],
        visc_tend=tend, visc_eff=veff,
        gameable_blur_s1=gb[1.0], gameable_blur_s2=gb[2.0], gameable_blur_s4=gb[4.0],
        gameable_visc=gv, dual_immune=surv)
    res["elapsed_s"] = round(time.time() - te, 1)
    json.dump(res, open(f"{OUT}/VALIDATION_{env}.json", "w"), indent=1, ensure_ascii=False)
    log(f"[done {env}] {res['elapsed_s']}s -> VALIDATION_{env}.json")
    _LOG[0].close(); _LOG[0] = None

# ================= BH93 静止负对照（P7） =================
def run_bh93():
    _LOG[0] = open(f"{OUT}/validate_bh93.log", "w")
    te = time.time()
    log("== validate_envs [bh93] start", time.strftime("%F %T"))
    root = f"{ENV}/e56/runs"
    dirs = sorted(d for d in os.listdir(root)
                  if os.path.isdir(f"{root}/{d}") and os.path.exists(f"{root}/{d}/out_his.nc"))
    flats = [d for d in dirs if "flat" in d.lower()]
    method = "目录名含 flat"
    if not flats:
        j = json.load(open(f"{ENV}/e56/E56_BH93.json"))
        rows = j if isinstance(j, list) else j.get("runs", [])
        fm = {r["tag"] for r in rows if r.get("bathy") == "flat"}
        flats = [d for d in dirs if d in fm]
        method = "E56_BH93.json tag→bathy 回退"
    assert len(flats) >= 5, f"flat 静止 run 不足 5 个: {flats}（记 DEVIATIONS 后中止）"
    log(f"[bh93] dirs={len(dirs)} flats={len(flats)} ({method})")

    per_sigma = {f"sigma{s:g}": dict(dl_uv=[], dl_all=[]) for s in SIGMAS}
    uv_names = None
    for d in flats:
        fl = load_fields(f"{root}/{d}")
        q0 = base_from_fields(fl)
        ks = sorted(q0)
        if uv_names is None:
            uv_names = [k for k in ks if k.split("|")[0] in ("u", "v")]
        for s in SIGMAS:
            qb = base_from_fields(blur_uv(fl, s))
            for k in ks:
                dl = abs(float(np.log(max(qb[k], EPS)) - np.log(max(q0[k], EPS))))
                per_sigma[f"sigma{s:g}"]["dl_all"].append(dl)
                if k.split("|")[0] in ("u", "v"):
                    per_sigma[f"sigma{s:g}"]["dl_uv"].append(dl)
    res = dict(env="bh93", stamp=time.strftime("%F %T"),
               n_dirs=len(dirs), n_flat=len(flats), flat_runs=flats,
               classification=method, n_uv_primitives=len(uv_names),
               floor_log=FLOOR)
    for s in SIGMAS:
        d = per_sigma[f"sigma{s:g}"]
        uv = np.array(d["dl_uv"]); al = np.array(d["dl_all"])
        res[f"sigma{s:g}"] = dict(
            median_absdlog_uv=float(np.median(uv)), max_absdlog_uv=float(uv.max()),
            n_uv_cells=int(uv.size), n_uv_cells_gt_floor=int((uv > FLOOR).sum()),
            median_absdlog_all124=float(np.median(al)), max_absdlog_all124=float(al.max()))
    res["p7_pass_preview"] = bool(res["sigma2"]["median_absdlog_uv"] < FLOOR)
    res["elapsed_s"] = round(time.time() - te, 1)
    json.dump(res, open(f"{OUT}/VALIDATION_bh93.json", "w"), indent=1, ensure_ascii=False)
    log(f"[done bh93] {res['elapsed_s']}s -> VALIDATION_bh93.json")
    _LOG[0].close(); _LOG[0] = None

# ================= 入口 =================
def main():
    envs = sys.argv[1:] or ["all"]
    if envs == ["all"]:
        envs = ["zonal", "merid", "diag45", "bh93"]
    for e in envs:
        assert e in ("zonal", "merid", "diag45", "bh93"), f"未知环境 {e}"
        if e != "zonal":
            listed = require_seal()
            print("[seal-ok]", "; ".join(f"{b}={h[:12]}…" for b, h in listed))
            assert os.path.exists(f"{OUT}/ARRAYS_zonal.npz"), "先跑 zonal（P4/键集自检依赖）"
        if e == "bh93":
            run_bh93()
        else:
            run_env(e)
    print(f"ALL DONE {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()
