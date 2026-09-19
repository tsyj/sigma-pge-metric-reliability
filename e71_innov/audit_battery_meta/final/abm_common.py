# -*- coding: utf-8 -*-
"""abm_common.py — audit_battery_meta 共用件（PREREG_audit_battery_meta.md §2）。

封存门控、秩相关（metric_search 同式）、精确置换 p、Wilson、指针解析、run 集合装载、扩展基元。
真实模式只在封存后可用；--selftest 模式由调用方传入夹具根目录。
"""
import hashlib, itertools, json, math, os, re, sys, time
import numpy as np

FINAL = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(FINAL, 'PREREG_audit_battery_meta.md')
SHAF = os.path.join(FINAL, 'PREREG_audit_battery_meta.sha256')
ENV_REAL = '/data/xinyuan/GOAI_ai4s_env'
FIELDS = ("u", "v", "w", "temp", "zeta")
STATS = ("rms", "max", "mean_abs", "p95")
REGION_SPECS = [("all", None), ("d200", ("deeper", 200)), ("d400", ("deeper", 400)),
                ("d800", ("deeper", 800)), ("d1500", ("deeper", 1500)),
                ("s50", ("shallow", 50)), ("s200", ("shallow", 200))]
DEAD, PASS, EDGE, NA, UND = '死', '过', '边', '未', '待定'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def seal_gate(selftest=False):
    """真实模式：PREREG 与 .sha256 必须存在且匹配。selftest：不检查（只许读夹具）。"""
    if selftest:
        return None
    if not (os.path.exists(PREREG) and os.path.exists(SHAF)):
        sys.exit('[SEAL GATE] PREREG 或 .sha256 缺失 — 未封存，拒绝运行。')
    rec = open(SHAF).read().split()
    if not rec or rec[0] != sha256(PREREG):
        sys.exit('[SEAL GATE] PREREG sha256 与封存记录不匹配 — 拒绝运行。')
    return rec[0]


def code_sha(path):
    return sha256(os.path.abspath(path))


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')


# ---------------- 统计 ----------------
def spearman(a, b):
    """metric_search.py 同式：argsort-of-argsort 秩（并列按下标序破），std=0 返回 0.0。"""
    a = np.asarray(a); b = np.asarray(b)
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def spearman_avg(a, b):
    """平均秩版（敏感性列，不参与判定）。"""
    from scipy.stats import rankdata
    ra = rankdata(a); rb = rankdata(b)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


_PERM_CACHE = {}


def exact_p(a, b):
    """n≤8：argsort 秩下的全置换精确双侧 p（|ρ_π| ≥ |ρ_obs| − 1e-12 的比例）。"""
    a = np.asarray(a, float); b = np.asarray(b, float); n = len(a)
    rho = spearman(a, b)
    ra = np.argsort(np.argsort(a)).astype(float)
    if n not in _PERM_CACHE:
        _PERM_CACHE[n] = np.array(list(itertools.permutations(range(n))), dtype=float)
    P = _PERM_CACHE[n]
    ra_c = ra - ra.mean(); P_c = P - P.mean(axis=1, keepdims=True)
    num = P_c @ ra_c
    den = np.sqrt((P_c ** 2).sum(axis=1) * (ra_c ** 2).sum())
    rp = num / den
    return rho, float(np.mean(np.abs(rp) >= abs(rho) - 1e-12))


def wilson(k, n, z=1.959964):
    if n <= 0:
        return (float('nan'), float('nan'))
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


SEVERITY = {DEAD: 4, UND: 3, EDGE: 2, PASS: 1}


def worst(vs):
    vs = [v for v in vs if v in SEVERITY]
    if not vs:
        return NA
    return max(vs, key=lambda v: SEVERITY[v])


# ---------------- 电池判定规则（数值部分） ----------------
def v_A1_plain(B):
    if B is None or not np.isfinite(B):
        return NA
    return PASS if B >= 0.9 else (DEAD if B < 0.5 else EDGE)


def v_A1_trivalent(k, n):
    lo, hi = wilson(k, n)
    if not np.isfinite(lo):
        return NA
    if lo >= 0.9:
        return PASS
    if hi >= 0.9:
        return UND
    return DEAD if (k / n) < 0.5 else EDGE


def v_A8(rho, p):
    if rho is None or p is None or not (np.isfinite(rho) and np.isfinite(p)):
        return NA
    if rho >= 0.8 and p < 0.05:
        return PASS
    if rho < 0.6:
        return DEAD
    return EDGE


def v_A6(A, B):
    if A is None or B is None or not (np.isfinite(A) and np.isfinite(B)):
        return NA
    aok = A <= -0.7; bok = B >= 0.9
    if aok and bok:
        return PASS
    if A > 0 or (not aok and not bok):
        return DEAD
    return EDGE


# ---------------- 指针 ----------------
def resolve(ptr, env_root=ENV_REAL):
    """'<path>:<a.b.0.c>' → (ok, value)。path 相对 env_root 或绝对；键段为整数时按列表下标。"""
    if ptr.startswith('file:'):
        p = ptr[5:]
        p = p if p.startswith('/') else os.path.join(env_root, p)
        return os.path.exists(p), p
    if ptr.startswith('manual:'):
        return False, ptr
    path, _, keys = ptr.partition(':')
    path = path if path.startswith('/') else os.path.join(env_root, path)
    if not os.path.exists(path):
        return False, None
    try:
        cur = json.load(open(path))
    except Exception:
        return False, None
    if not keys:
        return True, '<file>'
    for k in keys.split('.'):
        if isinstance(cur, list) and re.fullmatch(r'-?\d+', k):
            i = int(k)
            if -len(cur) <= i < len(cur):
                cur = cur[i]
            else:
                return False, None
        elif isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return False, None
    return True, cur


# ---------------- ledger / run 集合 ----------------
def jl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def pair_key(a):
    return tuple(round(a.get(x, -1), 6) for x in ('VISC2', 'VISC4', 'AKV_BAK', 'TNU2'))


def load_regraded(env):
    reg = {}
    for r in jl(f'{env}/ledger/regraded_v2.jsonl'):
        reg[r['run_id']] = r
    return reg


def zonal_sets(env):
    """E57 wind_AB 同式：Z58 陡臂（regraded）、Zflat、Z32 配对（last-wins，键首次出现序）。"""
    reg = load_regraded(env)
    seen = {}; byp = {}
    for r in jl(f'{env}/ledger/env2_runs.jsonl'):
        if not (r['obs'].get('valid') and r['ntimes'] == 8640):
            continue
        seen[r['run_id']] = r['bathy']
        byp.setdefault(pair_key(r['action']), {})[r['bathy']] = r['run_id']
    z_steep = [k for k, v in seen.items() if v == 'r26steep' and k in reg]
    z_flat = [k for k, v in seen.items() if v == 'flat']
    pairs = [(v['r26steep'], v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    return dict(reg=reg, steep=z_steep, flat=z_flat, pairs=pairs,
                skill={k: reg[k]['skill_vs_zero'] for k in z_steep},
                err={k: reg[k]['err_rms'] for k in z_steep})


def other_wind_sets(env, ledger_name, runs_sub):
    """经向/45°：配对同式；truth 陡臂 = hidden.skill_vs_zero 非空（e67b 同式）。"""
    seen = {}; byp = {}; skill = {}
    for r in jl(f'{env}/ledger/{ledger_name}'):
        if not (r['obs'].get('valid') and r['ntimes'] == 8640):
            continue
        seen[r['run_id']] = r['bathy']
        if r['bathy'] == 'r26steep' and (r.get('hidden') or {}).get('skill_vs_zero') is not None:
            skill[r['run_id']] = r['hidden']['skill_vs_zero']
        byp.setdefault(pair_key(r['action']), {})[r['bathy']] = r['run_id']
    steep_truth = [k for k, v in seen.items() if v == 'r26steep' and k in skill]
    pairs = [(v['r26steep'], v['flat']) for v in byp.values() if 'r26steep' in v and 'flat' in v]
    return dict(runs_dir=f'{env}/{runs_sub}', steep_truth=steep_truth, skill=skill, pairs=pairs)


V7 = [(0.0, 'e2_266404276ec5'), (50.0, 'e2_04ac56d390ce'), (150.0, 'e2_8ece45ca0d8d'),
      (400.0, 'e2_3b79f788a4f1'), (800.0, 'e2_37506f16ae83'), (1500.0, 'e2_ce64784901eb'),
      (2747.0, 'e2_e6d68386cec3')]
ABSURD = dict(steep10000='e2_b82a21ff15fd', steep30000='e2_9e957e1b688e', flat30000='e2_710f227af49f')
ST_V = [0, 50, 150, 400, 800, 1500, 2747]
E60_RX = ['rx020', 'rx044', 'rx060', 'rx069']


def static_sets(env):
    st = json.load(open(f'{env}/e56/E56_BH93.json'))
    bytag = {r['tag']: r for r in st}
    umax = [bytag[f'bh93_r26steep_v{v}']['u_max'] for v in ST_V]
    ver = json.load(open(f'{env}/e56/E56_VERDICT.json'))
    ok = [float(a) == float(b) for a, b in zip(umax, ver['bh93_umax'])]
    return dict(flat=[f'{env}/e56/runs/bh93_flat_v{v}' for v in ST_V],
                steep=[f'{env}/e56/runs/bh93_r26steep_v{v}' for v in ST_V],
                umax=umax, umax_match_verdict=bool(all(ok) and len(ok) == 7))


def e60_pairs(env):
    return [(f'{env}/e60/runs/{rx}_steep_v{v}', f'{env}/e60/runs/{rx}_flat_v{v}') for rx in E60_RX for v in ST_V]


# ---------------- 扩展基元 ----------------
def ext_base_quantities(run_dir, frame=-1, scale=1.0):
    """metric_search.base_quantities 同运算序；frame 帧、深浅阈同乘 scale；另返回每键有限格点数 N。"""
    fn = f"{run_dir}/out_his.nc"
    if not os.path.exists(fn):
        return None, None
    import netCDF4 as nc
    try:
        d = nc.Dataset(fn)
        h = np.asarray(d["h"][:]); Cs = np.asarray(d["Cs_r"][:])
        out = {}; N = {}
        for f in FIELDS:
            if f not in d.variables:
                continue
            arr = np.asarray(d[f][frame])
            scl = 100.0 if f in ("u", "v", "w", "zeta") else 1.0
            arr = arr * scl
            if arr.ndim == 2:
                depth = np.zeros_like(arr)
            else:
                n = min(arr.shape[-1], h.shape[-1]); m = min(arr.shape[-2], h.shape[-2])
                arr = arr[..., :m, :n]
                depth = -Cs[:, None, None] * h[None, :m, :n]
                if arr.shape[0] != depth.shape[0]:
                    arr = arr[:depth.shape[0]]
            for rname, rspec in REGION_SPECS:
                if rspec is None:
                    msk = np.ones_like(depth, dtype=bool)
                elif rspec[0] == "deeper":
                    msk = depth > (rspec[1] * scale if scale != 1.0 else rspec[1])
                else:
                    msk = depth < (rspec[1] * scale if scale != 1.0 else rspec[1])
                v = arr[msk]
                v = v[np.isfinite(v)]
                if v.size == 0:
                    continue
                av = np.abs(v)
                out[f"{f}|{rname}|rms"] = float(np.sqrt((v ** 2).mean()))
                out[f"{f}|{rname}|max"] = float(av.max())
                out[f"{f}|{rname}|mean_abs"] = float(av.mean())
                out[f"{f}|{rname}|p95"] = float(np.percentile(av, 95))
                for s in STATS:
                    N[f"{f}|{rname}|{s}"] = int(v.size)
        d.close()
        return out, N
    except Exception:
        return None, None


def json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def clean(o):
    """递归把非有限 float 换成 None（JSON 合法）。"""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def dump(obj, path):
    with open(path, 'w') as f:
        json.dump(clean(obj), f, ensure_ascii=False, indent=1, default=json_default)
