#!/usr/bin/env python
"""从 ROMS 输出提取诊断量 —— env.step() 的观测端。

设计原则（EurekAgent「permissions engineering」）：
  - PROXY 层：Agent 可见的表层指标（含已知的陷阱指标）
  - TRUE  层：隐藏评估器用的体积加权/真值对照指标，不进 Agent 工作区

静止态 seamount 算例的真值恒等于 0（ANA_INITIAL，无强迫），
所以伪流强度可精确测量，无需外部真值。
"""
import os, re, json
import numpy as np
import netCDF4 as nc


def _rho_uv(u, v):
    """u(eta_u,xi_u), v(eta_v,xi_v) → rho 点上的 (u,v)，形状 (eta_rho,xi_rho)。"""
    nz, ny, nxu = u.shape
    nxr = nxu + 1
    nyr = v.shape[1] + 1
    ur = np.zeros((nz, nyr, nxr))
    ur[:, :, 1:-1] = 0.5 * (u[:, :, :-1] + u[:, :, 1:])
    ur[:, :, 0] = u[:, :, 0]
    ur[:, :, -1] = u[:, :, -1]
    vr = np.zeros((nz, nyr, nxr))
    vr[:, 1:-1, :] = 0.5 * (v[:, :-1, :] + v[:, 1:, :])
    vr[:, 0, :] = v[:, 0, :]
    vr[:, -1, :] = v[:, -1, :]
    return ur, vr


def diagnose(hisfile, logfile=None, ntimes_expected=None):
    """返回 dict(proxy=..., true=..., meta=...)。"""
    out = {"proxy": {}, "true": {}, "meta": {}}

    # ---- 完赛/崩溃检测 + 能量时间序列 ----
    # ROMS 每步打印:  STEP  YYYY-MM-DD hh:mm:ss.ss   KE   PE   TotalE   Volume
    STEPRE = re.compile(
        r"^\s*(\d+)\s+\d{4}-\d{2}-\d{2}\s+[\d:.]+\s+"
        r"([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)")
    crashed, done = False, False
    steps, ke_t, pe_t, te_t, vol_t = [], [], [], [], []
    if logfile and os.path.exists(logfile):
        txt = open(logfile, errors="replace").read()
        done = "ROMS/TOMS: DONE" in txt
        crashed = any(k in txt for k in
                      ("Blowing-up", "BLOWUP", "ABNORMAL TERMINATION",
                       "Abnormal termination", "MAX_SPEED"))
        for line in txt.splitlines():
            m = STEPRE.match(line)
            if m:
                try:
                    steps.append(int(m.group(1)))
                    ke_t.append(float(m.group(2)))
                    pe_t.append(float(m.group(3)))
                    te_t.append(float(m.group(4)))
                    vol_t.append(float(m.group(5)))
                except ValueError:
                    pass
    out["meta"].update(completed=done, crashed=crashed,
                       last_step=(steps[-1] if steps else None),
                       n_steps_logged=len(steps))

    # 能量时间序列衍生量（对应预注册文档的 g_K / 能量预算残差）
    if len(ke_t) >= 3:
        ke = np.asarray(ke_t); te = np.asarray(te_t); vo = np.asarray(vol_t)
        K0 = max(ke[0], 1e-30)
        out["proxy"]["KE_final"] = float(ke[-1])
        out["proxy"]["KE_max"] = float(ke.max())
        # 对数增长率 g_K：整段最小二乘斜率（1/步）
        lg = np.log(ke + K0)
        out["proxy"]["gK_logslope_per_step"] = float(
            np.polyfit(np.arange(len(lg)), lg, 1)[0])
        # 是否已进入"地板"（后 1/3 段增长率趋零 = seed-amplifier-floor 的 floor）
        tail = lg[int(len(lg) * 2 / 3):]
        out["proxy"]["gK_tail_slope"] = float(
            np.polyfit(np.arange(len(tail)), tail, 1)[0]) if len(tail) >= 3 else None
        # 守恒诊断（隐藏层）：总能量与体积漂移
        out["true"]["total_energy_drift_rel"] = float(
            abs(te[-1] - te[0]) / max(abs(te[0]), 1e-30))
        out["true"]["volume_drift_rel"] = float(
            abs(vo[-1] - vo[0]) / max(abs(vo[0]), 1e-30))
        out["meta"]["ke_series_head_tail"] = [float(ke[0]), float(ke[-1])]

    if not os.path.exists(hisfile):
        out["meta"]["error"] = "no history file"
        return out

    d = nc.Dataset(hisfile)
    if d.dimensions["ocean_time"].size == 0:
        out["meta"]["error"] = "empty history"
        return out

    pm = d["pm"][:]; pn = d["pn"][:]
    area = 1.0 / (pm * pn)                       # (ny,nx) m^2
    t_idx = -1                                   # 末帧
    z_w = d["z_w"][t_idx]                        # (s_w,ny,nx)
    Hz = np.diff(z_w, axis=0)                    # (N,ny,nx)
    dV = Hz * area[None, :, :]                   # (N,ny,nx) m^3
    Vtot = dV.sum()

    u = d["u"][t_idx]; v = d["v"][t_idx]
    ur, vr = _rho_uv(np.asarray(u), np.asarray(v))
    spd = np.sqrt(ur**2 + vr**2)                 # (N,ny,nx) m/s
    temp = np.asarray(d["temp"][t_idx])

    # ================= PROXY 层（Agent 可见）=================
    # 静止态真值 = 0，故 |u| 即伪流
    out["proxy"]["spurious_max_cms"] = float(spd.max() * 100)          # ← 全行业在用的指标
    out["proxy"]["spurious_rms_cms"] = float(np.sqrt((spd**2).mean()) * 100)
    out["proxy"]["temp_min"] = float(temp.min())
    out["proxy"]["temp_max"] = float(temp.max())

    # ================= TRUE 层（隐藏评估器）=================
    # 体积加权 —— 这才是"真"指标；单点极值会系统性高估收益
    ke = 0.5 * (spd**2)
    out["true"]["spurious_KE_volint"] = float((ke * dV).sum())
    out["true"]["spurious_rms_volwt_cms"] = float(
        np.sqrt((ke * 2 * dV).sum() / Vtot) * 100)
    for thr in (1e-4, 1e-3, 1e-2):               # m/s
        frac = float((dV * (spd > thr)).sum() / Vtot)
        out["true"][f"vol_frac_speed_gt_{thr:g}"] = frac
    # 温度超调的体积积分（对应 kill-test 的 I_u）
    T0min, T0max = float(np.asarray(d["temp"][0]).min()), float(np.asarray(d["temp"][0]).max())
    over_hi = np.clip(temp - T0max, 0, None)
    over_lo = np.clip(T0min - temp, 0, None)
    out["true"]["temp_overshoot_volint"] = float(((over_hi + over_lo) * dV).sum())
    out["meta"].update(T_init_min=T0min, T_init_max=T0max,
                       n_frames=int(d.dimensions["ocean_time"].size),
                       ocean_time_end=float(d["ocean_time"][t_idx]),
                       volume_m3=float(Vtot))
    d.close()
    return out


if __name__ == "__main__":
    import sys
    rd = sys.argv[1]
    r = diagnose(os.path.join(rd, "roms_his.nc"),
                 os.path.join(rd, "run.log") if os.path.exists(os.path.join(rd, "run.log"))
                 else os.path.join(rd, "smoke.log"))
    print(json.dumps(r, indent=2, ensure_ascii=False))
