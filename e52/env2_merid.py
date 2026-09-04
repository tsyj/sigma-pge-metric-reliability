#!/usr/bin/env python
"""统一探索环境 v2 —— 单一入口 env.step(action) → observation

三路对抗审查 C 队指出的问题（本文件修复其中三条）：
  · env.py 未覆盖 48×48 真值配置 → 本文件统一两类配置
  · truth_scan / config_sweep 各自重复实现 → 逻辑收敛到此处
  · 无随机种子控制 → action 支持 seed，写入 ledger

设计依据
  · EurekAgent (2606.13662) permissions engineering：真值与打分放在 Agent 工作区外
  · Agentic PDE (2604.09584) 四角色：Analyst 层确定性，LLM 不碰数值
"""
import os, re, sys, json, time, shutil, hashlib, subprocess
import concurrent.futures as cf
import numpy as np
from netCDF4 import Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mitgcm import read_field, iters
from sigma2z import roms_depths, to_z, rho_from_u
# --- 可移植性垫片：开发机行为不变；换台机器时自动改用仓库内的文件 ---
import os as _o, sys as _s
_H=_o.path.dirname(_o.path.abspath(__file__))
_R=_H if _o.path.isdir(_o.path.join(_H,'e44_tide')) else _o.path.dirname(_H)
for _d in (_o.path.join(_R,'scripts'), _o.path.join(_R,'e44_tide'), _R):
    if _o.path.isdir(_d) and _d not in _s.path: _s.path.insert(0,_d)
if not _o.path.isdir('/data/xinyuan/GOAI_ai4s_env'):
    # 评委机器：把开发路径重定向到仓库内
    _real_open=open
    def open(f,*a,**k):
        if isinstance(f,str) and f.startswith('/data/xinyuan/GOAI_ai4s_env/'):
            rel=f.replace('/data/xinyuan/GOAI_ai4s_env/','')
            for _b in (_R, _o.path.join(_R,'e44_tide')):
                _p=_o.path.join(_b,rel)
                if _o.path.exists(_p): return _real_open(_p,*a,**k)
                _p2=_o.path.join(_b,_o.path.basename(rel))
                if _o.path.exists(_p2): return _real_open(_p2,*a,**k)
        return _real_open(f,*a,**k)
# --- 垫片结束 ---

def rho_from_v(v):
    """ROMS v 点 (N, eta-1, xi) → rho 点 (N, eta, xi)，两端外推（E52 镜像 rho_from_u）。"""
    N, nym1, nx = v.shape
    r = np.empty((N, nym1 + 1, nx))
    r[:, 1:-1, :] = 0.5 * (v[:, :-1, :] + v[:, 1:, :])
    r[:, 0, :] = v[:, 0, :]
    r[:, -1, :] = v[:, -1, :]
    return r


ENV = "/data/xinyuan/GOAI_ai4s_env"
SRC = "/data/xinyuan/zpg_roms_dev/pge_test"
BASE = f"{ENV}/runs/r26_repro"
MIT = "/data/xinyuan/zpg_roms_dev/MITgcm/verification/seamount_roms/run_r29_wind_z13"
LEDGER = f"{ENV}/ledger/env2_merid_runs.jsonl"

# ---------------- 固定规则（不可探索）----------------
FIXED = {
    # ⚠ E33：此处原写 DJ_GRADPS —— 错的。实际编译进去的是 PRSGRD31
    #   （与用户原始科研 run 的 CPP_options 逐项相同）。环境不能谎报自己的求解器。
    "solver": "ROMS 3.9 (PRSGRD31 + RHO_SURF, SEAMOUNT_WIND)",
    "grid_hv": "48×48×13",
    "forcing": "E52 转 90°: 经向风应力 τ=0.1 N/m²，前 ~12 h tanh 爬升",
    "duration": "3 天（NTIMES=25920 × DT=10 s）",
    "stratification": "同一 T(z) 剖面，T∈[4.0, 25.9] °C，初始 u≡0",
    "conservation": "合法修正须落在反对称密度雅可比内（越界判非法）",
}

# ---------------- 动作空间 ----------------
BATHY = {
    "flat":     ("pge_grid_flat48_noN.nc", "ini_flat48_13.nc"),   # σ-PGE ≡ 0（对照）
    "mit":      ("pge_grid_mit.nc",        "ini_mit.nc"),          # 峰 107.7 m
    "r26steep": ("pge_grid_r26steep.nc",   "ini_r26steep13.nc"),   # 峰 80 m，有真值
}
ACTION_SPACE = {
    "bathy":   list(BATHY),                 # 地形（含零-PGE 对照）
    "VISC2":   (0.0, 2000.0),               # 横向黏性 m²/s
    "VISC4":   (0.0, 1e10),                 # 双谐波黏性
    "AKV_BAK": (1e-6, 1.0),                 # 背景垂向黏性
    "TNU2":    (0.0, 1000.0),               # 示踪物扩散
    "ntimes":  (1440, 25920),               # 运行长度（预算旋钮）
    "seed":    "int，写入 ledger 供复现（ROMS 本身确定性，seed 仅标识）",
}
# Agent 可见的观测键（其余隐藏）
PROXY_KEYS = ["u_max", "u_rms", "deep_rms_800", "surf_max",
              "temp_min", "temp_max", "valid", "crashed", "completion_ratio",
              "uv_ratio", "vu_ratio", "v_rms", "deep_rms_800_v"]

# ⭐ E40：抗刷分指标。全域 u 的 rms ÷ 全域 |v| 的均值。
#
# 为什么是它：三条刷分路径（换地形到 flat / 荒谬黏性 / 缩短积分）**共享同一机制
# —— 让一切变小**。而 u/v 是无量纲比值，对整体幅值缩放不变，分子分母同步缩小
# 比值不动，因此天然免疫这一整类刷分。
#
# 实测（E40，15376 个候选里穷举出来的）：
#   · 三条刷分路径逐一检验：1.151 / 1.012 / 2.729，全部 >1（指标变差＝抗刷分）
#     对比基线 deep_rms_800：0.010 / 0.049 / 1.232，被刷穿两条
#   · 全局排序前 8 名：6/8 落在有真值的实例上（基线 0/8），8/8 是完整积分（基线 1/8）
#   · 实例内与隐藏技巧评分秩相关 ρ = −0.923（基线 −0.963，只损失 4%）

# 求解器二进制。v4 相对 v1 只多编了 UV_VIS4 / TS_DIF4；
# 已验证在 VISC4=0、TNU4=0 时与 v1 **逐位一致**（u/v/temp/zeta/w 全场差 0），
# 因此 v1 时期的 59 个 run 与 v4 的新 run 可直接混用。
#   v1 sha256 479eca46aaa8b6216c7aa94f8dc7055015d45f8ed78ae5fff628a99fe295401a
#   v4 sha256 b50851d95ab35bc60a7545185eb5ec24f2aa9c3c0e36e70620b3e1b711436822
BIN = "coawstM_goai_merid"


def _bin_sha():
    """求解器二进制的 sha256，写进每条 ledger 记录。

    起因（E31）：clean 重建后，`truth_scan.json` / 两个 agent 轨迹 / 三个
    goodhart 扫描**都没重跑**，但图照画、数字自洽、无人报错 —— 整条链上
    没有任何一环能发现产物已经过期。
    **产物的有效性必须绑定到它依赖的二进制上，不能靠人记得。**
    """
    h = hashlib.sha256()
    with open(f"{ENV}/bin/{BIN}", "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_BIN_SHA = None

_TRUTH_CACHE = {}


# 真值目录：按垂向黏性 viscAz 索引。
# ⚠ 两处曾经的错配（E29 撤回 #6/#7），都已修在这里：
#   #6 ROMS 的 AKV_BAK 默认 1e-5，而官方真值 run 用 viscAz=1e-3 —— 差 100 倍。
#      在 Az=1e-5 下真值 |U|max 是 9.24 而非 6.05，此前把真值低估了约一半。
#   #7 `_truth(3.0)` 写死取真值第 3 天，而 ntimes=8640 的 ROMS run
#      （DT=10 s）只跑到**第 1 天** —— 拿第 1 天去比第 3 天。
# 现在两者都由调用方按实际配置传入。
# `hires_*` 是把 dumpFreq 从 43200 s（0.5 天）加密到 3600 s（1 小时）重跑的，
# 73 帧；已验证与原版在共同时刻**逐位一致**（加密输出不改变解）。
# 原来只有 0.5 天整数倍有真值，`ntimes=1440`（0.167 天）取不到 —— 短 run 无法评分。
TRUTH_BY_AKV = {   # E52 首轮: 仅 viscAz=1e-5 的转向真值; 其余 AKV 的评分标 N/A
    1e-5: f"{ENV}/truth/merid_1pEm5",
}
_RC = None


def _rc_truth():
    """MITgcm 的 z 层中心深度（负值向下）—— 全部真值目录一致。"""
    global _RC
    if _RC is None:
        _RC = read_field("RC", None, TRUTH_BY_AKV[1e-5]).ravel()
    return _RC


DT_ROMS = 10.0        # ocean_r26_dj10.in 的 DT
DT_MIT = 30.0         # MITgcm data 的 deltaT


def _truth(day, akv=1e-5):
    """取真值 U 场：按**垂向黏性**与**实际积分时长**双重匹配。"""
    if abs(np.log10(max(akv,1e-12)) - (-5.0)) > 0.3:
        return None   # E52 首轮: 非默认垂向黏性无转向真值
    d = TRUTH_BY_AKV[1e-5]
    if d not in _TRUTH_CACHE:
        _TRUTH_CACHE[d] = {round(i * DT_MIT / 86400, 3): read_field("V", i, d)
                           for i in iters("U", d)}
    return _TRUTH_CACHE[d].get(round(day, 3))


def _aid(action):
    return "e2_" + hashlib.sha256(
        json.dumps(action, sort_keys=True).encode()).hexdigest()[:12]


def _fmt(v):
    """转成合法的 Fortran 双精度字面量。

    Python 对 <1e-4 的浮点用 'e' 记法，直接拼 'd0' 会得到 `1e-05d0` —— 非法，
    ROMS 读不出来。必须把指数换成 d 记法。
    """
    s = repr(float(v))
    if "e" in s or "E" in s:
        m, e = s.lower().split("e")
        if "." not in m:
            m += ".0"
        return f"{m}d{int(e)}"
    return s + "d0"


def _nvals(body):
    """数出 == 右边原本有几个值，含 ROMS 的 `2*0.0d0` 重复记法。"""
    n = 0
    for t in body.split():
        m = re.match(r"^(\d+)\*", t)
        n += int(m.group(1)) if m else 1
    return max(n, 1)


def _patch(line, val):
    """把 `KEY == v1 v2  ! 注释` 里**所有**值都换掉。

    ROMS 的示踪物类参数是每示踪物一个值（`TNU2 == 50.0d0 50.0d0`）。
    只换第一个会造成「半生效」——温度扩散改了、盐度没改，而且不报错。
    """
    head, sep, rest = line.partition("==")
    body, hsh, comment = rest.partition("!")
    new = "  ".join([_fmt(val)] * _nvals(body))
    return f"{head}{sep} {new}" + (f"   {hsh}{comment}" if hsh else "\n")


class SigmaPGEEnv:
    """σ 坐标伪流探索环境。

    真值通道：仅 bathy='r26steep' 有 MITgcm z 坐标独立真解。
    这是刻意的 —— 真实科研中真值通常缺席，环境如实反映这一点。
    """

    def __init__(self, expose_truth=False, max_workers=12):
        self.expose_truth = expose_truth      # Agent 侧必须 False
        self.max_workers = max_workers
        self.n_calls, self.wall_total = 0, 0.0
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)

    # ---------- 单次交互 ----------
    def step(self, action):
        a = dict(action)
        bathy = a.pop("bathy", "r26steep")
        ntimes = int(a.pop("ntimes", 25920))
        seed = a.pop("seed", 0)
        if bathy not in BATHY:
            raise ValueError(f"bathy 须取自 {list(BATHY)}")
        grid, ini = BATHY[bathy]
        rid = _aid(action)
        rd = f"{ENV}/runs_merid/{rid}"
        os.makedirs(rd, exist_ok=True)
        for s, d_ in ((f"{SRC}/{grid}", grid), (f"{SRC}/{ini}", ini),
                      (f"{ENV}/bin/{BIN}", BIN)):
            if not os.path.exists(f"{rd}/{d_}"):
                shutil.copy2(s, f"{rd}/{d_}")
        os.chmod(f"{rd}/{BIN}", 0o755)

        lines = []
        for line in open(f"{BASE}/ocean_r26_dj10.in", errors="replace"):
            k = line.split()[0] if line.split() else ""
            if k == "GRDNAME":   line = f"     GRDNAME == {grid}\n"
            elif k == "ININAME": line = f"     ININAME == {ini}\n"
            elif k == "NTIMES":  line = f"      NTIMES == {ntimes}\n"
            elif k == "NHIS":    line = f"        NHIS ==  {min(4320, max(1, ntimes//4))}\n"
            elif k in ("HISNAME", "RSTNAME", "AVGNAME", "DIANAME"):
                line = f"     {k} == out_{k[:3].lower()}.nc\n"
            elif k in a:
                line = _patch(line, a[k])
            lines.append(line)
        open(f"{rd}/roms.in", "w").writelines(lines)

        # 配置回显自检 —— 教训见 E26：一个「跑完了、没报错、结果很干净」的
        # 扫描，可能因为替换根本没匹配上而什么都没扫。沉默的无效操作比崩溃危险。
        _seen = {}
        for line in open(f"{rd}/roms.in", errors="replace"):
            t = line.split()
            if t and t[0] in a:
                _seen[t[0]] = line.partition("==")[2].partition("!")[0].split()
        for k, v in a.items():
            got = _seen.get(k)
            if got is None:
                raise RuntimeError(f"动作键 {k} 在 ocean.in 里找不到对应行，未生效")
            want = _fmt(v)
            if any(g != want for g in got):
                raise RuntimeError(
                    f"{k} 写入不完整：期望全部为 {want}，实际 {got}")

        envv = dict(os.environ, PATH="/usr/bin:" + os.environ.get("PATH", ""),
                    LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:" +
                                    os.environ.get("LD_LIBRARY_PATH", ""))
        t0 = time.time()
        with open(f"{rd}/run.log", "w") as lg:
            subprocess.run([f"./{BIN}", "roms.in"], cwd=rd,
                           stdout=lg, stderr=subprocess.STDOUT, env=envv)
        wall = time.time() - t0
        self.n_calls += 1; self.wall_total += wall

        txt = open(f"{rd}/run.log", errors="replace").read()
        # ROMS 的爆栈信息实际写作 "Blows up"，不是 "BLOWUP"。
        # 原来只找 "BLOWUP"，导致炸掉的 run 被记成 crashed=False —— Agent
        # 分不清「崩了」与「因别的原因没完赛」，这是给它的错误信号。
        done = "ROMS/TOMS: DONE" in txt
        blow = ("Blows up" in txt or "BLOWUP" in txt or "exit_flag: 1" in txt)
        has_out = os.path.exists(f"{rd}/out_his.nc")
        obs, hidden = self._diagnose(rd, bathy, done and not blow and has_out,
                                     ntimes=ntimes, akv=a.get("AKV_BAK", 1e-5))
        obs["valid"] = bool(done and not blow and has_out)
        obs["crashed"] = blow
        if not has_out and done:
            obs["note"] = "完赛但无历史输出（NHIS > NTIMES？）"

        global _BIN_SHA
        if _BIN_SHA is None:
            _BIN_SHA = _bin_sha()
        rec = dict(run_id=rid, action=action, bathy=bathy, seed=seed,
                   obs=obs, hidden=hidden,
                   wall_s=round(wall, 1), ntimes=ntimes,
                   bin=BIN, bin_sha256=_BIN_SHA)
        with open(LEDGER, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        info = {"run_dir": rd, "wall_s": wall, "run_id": rid}
        if self.expose_truth:
            info["hidden"] = hidden
        return {k: obs.get(k) for k in PROXY_KEYS}, info

    # ---------- 确定性 Analyst 层（LLM 不碰数值）----------
    def _diagnose(self, rd, bathy, ok, ntimes=8640, akv=1e-5):
        obs, hid = {}, {}
        fn = f"{rd}/out_his.nc"
        if not ok or not os.path.exists(fn):
            obs["completion_ratio"] = 0.0
            obs["note"] = "run 未完赛；强度指标不可与完赛 run 比较"
            return obs, hid
        d = Dataset(fn)
        u = np.asarray(d["u"][-1]); v = np.asarray(d["v"][-1])
        T = np.asarray(d["temp"][-1])
        T0 = np.asarray(d["temp"][0]); h = np.asarray(d["h"][:])
        Cs = np.asarray(d["Cs_r"][:]); nfr = d.dimensions["ocean_time"].size
        d.close()
        elapsed_day = round(ntimes * DT_ROMS / 86400.0, 3)
        hu = 0.5 * (h[:, :-1] + h[:, 1:])
        depth = -Cs[:, None, None] * hu[None, :, :]

        # ⭐ E40 抗刷分指标（见 PROXY_KEYS 处的说明）
        _un = float(np.sqrt((u ** 2).mean()) * 100)
        _vd = float(np.abs(v).mean() * 100)
        obs["uv_ratio"] = (_un / _vd) if _vd > 1e-12 else None
        _vn = float(np.sqrt((v ** 2).mean()) * 100); _ud = float(np.abs(u).mean() * 100)
        obs["vu_ratio"] = (_vn / _ud) if _ud > 1e-12 else None   # E52 镜像指标
        obs["v_rms"] = _vn

        obs["u_max"] = float(np.abs(u).max() * 100)
        obs["u_rms"] = float(np.sqrt((u ** 2).mean()) * 100)
        obs["surf_max"] = float(np.abs(u[-1]).max() * 100)
        obs["temp_min"] = float(T.min()); obs["temp_max"] = float(T.max())
        obs["completion_ratio"] = 1.0
        for thr in (200, 400, 800, 1500):
            m = depth > thr
            obs[f"deep_rms_{thr}"] = (float(np.sqrt((u[m] ** 2).mean()) * 100)
                                      if m.any() else None)
        hv = 0.5 * (h[:-1, :] + h[1:, :]); depv = -Cs[:, None, None] * hv[None, :, :]
        mv = depv > 800
        obs["deep_rms_800_v"] = float(np.sqrt((v[mv] ** 2).mean()) * 100) if mv.any() else None

        over = np.clip(T - T0.max(), 0, None) + np.clip(T0.min() - T, 0, None)
        hid["temp_over_max"] = float(over.max())
        hid["temp_over_mean"] = float(over.mean())
        # 真值必须与本 run 的**实际积分时长**和**垂向黏性**对齐（见 TRUTH_BY_AKV 注释）
        U = _truth(elapsed_day, akv) if bathy == "r26steep" else None
        if U is not None:
            hid["truth_day"] = elapsed_day
            hid["truth_akv"] = akv
            # ⚠ E35 撤回 #8：此处原为 `u[..., :n] - U[..., :n]`，直接相减。
            #   但两个模式的垂向层序**相反**（ROMS k=0 是底层，MITgcm k=0 是面层），
            #   于是 ROMS 底层的伪流被配到了 MITgcm 表层的真流上。
            #   而且 σ 层随地形起伏、各列层深不同，仅仅翻转也不够 —— 必须逐列插值。
            zr = roms_depths(Cs, h)
            uz = to_z(rho_from_v(v), zr, _rc_truth())
            m = min(uz.shape[-2], U.shape[-2]); n = min(uz.shape[-1], U.shape[-1])
            A, B = uz[:, :m, :n], U[:, :m, :n]
            g = np.isfinite(A) & np.isfinite(B)
            err = A[g] - B[g]
            t_rms = float(np.sqrt((B[g] ** 2).mean()) * 100)
            hid["err_rms_vs_truth"] = float(np.sqrt((err ** 2).mean()) * 100)
            hid["err_max_vs_truth"] = float(np.abs(err).max() * 100)
            hid["truth_max"] = float(np.abs(B[g]).max() * 100)
            hid["truth_rms"] = t_rms
            # 技巧评分：以「恒输出零」为参照。0 = 与什么都不做持平，<0 = 更差。
            # 起因（E34）：原来的 err_rms 的退化最优就是一个什么都不产生的模型 ——
            # 接上真值挡住了代理指标失效，却没挡住「用消灭一切来降低误差」。
            hid["skill_vs_zero"] = float(
                1.0 - (hid["err_rms_vs_truth"] / max(t_rms, 1e-12)) ** 2)
        return obs, hid

    def step_batch(self, actions):
        with cf.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            return list(ex.map(self.step, actions))

    def budget(self):
        return dict(n_runs=self.n_calls, wall_total_s=round(self.wall_total, 1),
                    wall_per_run_s=round(self.wall_total / max(self.n_calls, 1), 1))

    def describe(self):
        return {"fixed_rules": FIXED, "action_space": ACTION_SPACE,
                "observable": PROXY_KEYS,
                "hidden": ["temp_over_*", "err_*_vs_truth", "truth_*"],
                "truth_available_for": ["r26steep"],
                "note": "真值仅一个配置有 —— 真实科研中真值通常缺席，环境如实反映"}


# ---------------- 隐藏评估器（Agent 不可访问）----------------
def grade(run_id, metric="err_rms_vs_truth"):
    for line in open(LEDGER):
        r = json.loads(line)
        if r["run_id"] == run_id:
            if not r["obs"].get("valid"):
                return {"score": None, "valid": False, "reason": "未完赛，不计分"}
            if metric not in r["hidden"]:
                return {"score": None, "valid": False,
                        "reason": f"该配置无 {metric}（真值仅 r26steep 可用）"}
            return {"score": r["hidden"][metric], "valid": True,
                    "metric": metric, "bathy": r["bathy"]}
    return {"score": None, "valid": False, "reason": "run_id 不存在"}


if __name__ == "__main__":
    e = SigmaPGEEnv()
    print(json.dumps(e.describe(), ensure_ascii=False, indent=1))
