#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71G · prsgrd31 离线复刻库（纯函数，无 I/O，无副作用）。

复刻对象与公式出处（PREREG_mms_operator.md §1，全部 2026-09-17 源码走读核过）：
- set_scoord: Vstretching=4（Shchepetkin 2010 双重拉伸）；set_depth: Vtransform=2, zeta=0。
- rho_eos LINEAR_EOS: rho = R0 - R0*Tcoef*(T-T0) - 1000（Scoef=0），
  出处 build/work_rest/Build_roms/rho_eos.f90 L217-219。
- prsgrd31.h 标准密度 Jacobian（SDJ）逐字翻译：WJ_GRADP/ATM_PRESS/TIDE_GENERATING_FORCES/WET_DRY
  未定义；RHO_SURF **已定义**（run.log L235；prsgrd.f90 L219-222 保留其项），该项
  = (fac2+fac1*(rho_i+rho_{i-1}))*(z_w,N(i)-z_w,N(i-1))，zeta≡0 时 z_w,N≡0 逐点恒零，
  故按 zeta=0 合法略去（复刻数值不受影响）。
  加速度换算 a_u = -phix/dx（等价 ru/(0.5(Hz_i+Hz_{i-1})*om_u*on_u)，均匀网格）。
措辞红线：本库是「按 Song 1998 与 prsgrd31.h 复刻」，不是「即 ROMS 算子」。
约定：数组形状 (N, Ny, Nx)，k=0 为底、k=N-1 为面（ROMS k=1..N 的 0 基映射）。
"""
import numpy as np

G_ACC = 9.81          # m/s^2（ROMS mod_scalars g）
RHO0 = 1025.0         # kg/m^3（roms.in RHO0）
R0, T0, TCOEF = 1025.0, 14.0, 1.7e-4   # roms.in（Scoef=0）


def cs_v4(s, theta_s=7.0, theta_b=2.0):
    """Vstretching=4 的 C(s)，theta_s>0 且 theta_b>0 分支。"""
    s = np.asarray(s, dtype=np.float64)
    csur = (1.0 - np.cosh(theta_s * s)) / (np.cosh(theta_s) - 1.0)
    return (np.exp(theta_b * csur) - 1.0) / (1.0 - np.exp(-theta_b))


def s_levels(N):
    """s_rho(k)=(k-N-0.5)/N, k=1..N；s_w(k)=(k-N)/N, k=0..N。"""
    k = np.arange(1, N + 1, dtype=np.float64)
    kw = np.arange(0, N + 1, dtype=np.float64)
    return (k - N - 0.5) / N, (kw - N) / N


def set_depth_v2(h, N=13, theta_s=7.0, theta_b=2.0, hc=250.0):
    """Vtransform=2、zeta=0：z = h*(hc*s + h*C)/(hc + h)。返回 z_r(N,Ny,Nx), z_w(N+1,Ny,Nx), Hz。"""
    h = np.asarray(h, dtype=np.float64)
    s_r, s_w = s_levels(N)
    C_r, C_w = cs_v4(s_r, theta_s, theta_b), cs_v4(s_w, theta_s, theta_b)
    z_r = h[None] * (hc * s_r[:, None, None] + h[None] * C_r[:, None, None]) / (hc + h[None])
    z_w = h[None] * (hc * s_w[:, None, None] + h[None] * C_w[:, None, None]) / (hc + h[None])
    Hz = z_w[1:] - z_w[:-1]
    return z_r, z_w, Hz


def rho_linear_eos(T):
    """LINEAR_EOS（Scoef=0）：kg/m^3 - 1000。"""
    return R0 - R0 * TCOEF * (np.asarray(T, dtype=np.float64) - T0) - 1000.0


def prsgrd31_sdj(rho, z_r, z_w, Hz, dx=2000.0, dy=2000.0):
    """prsgrd31.h SDJ 逐字翻译。

    CPP 口径（逐一核过）：WJ_GRADP/ATM_PRESS/TIDE_GENERATING_FORCES/WET_DRY 未定义；
    RHO_SURF 已定义，其顶层项 ∝ (z_w,N(i)-z_w,N(i-1))，zeta≡0 下逐点恒零，故按 zeta=0 合法略去
    （prsgrd.f90 L219-222）。本函数只适用于 zeta≡0 的输入几何。

    返回 (a_u, a_v)：u/v 点的 PGF 加速度 [m/s^2]，形状 (N,Ny,Nx-1)/(N,Ny-1,Nx)。
    a_u = -phix/dx；ru(m^4/s^2) 可由 -0.5*(Hz_i+Hz_{i-1})*phix*dy 复原（不在此返回）。
    逐层递推顺序与源码一致：k=N 顶层初始化，k=N-1..1 向下累加（0 基：N-1 顶、N-2..0）。
    """
    fac1 = 0.5 * G_ACC / RHO0
    fac3 = 0.25 * G_ACC / RHO0
    N = rho.shape[0]

    def _dir(rho, z_r, z_w, axis):
        # axis=2: XI 向（u 点）；axis=1: ETA 向（v 点）。sl/sr 取相邻两列。
        sl = [slice(None)] * 3
        sr = [slice(None)] * 3
        sl[axis] = slice(0, -1)
        sr[axis] = slice(1, None)
        sl, sr = tuple(sl), tuple(sr)
        a = np.empty_like(rho[(slice(None),) + sl[1:]])
        # 顶层（源码 k=N）
        cff1 = (z_w[N][sr[1:]] - z_r[N - 1][sr[1:]] +
                z_w[N][sl[1:]] - z_r[N - 1][sl[1:]])
        phi = fac1 * (rho[N - 1][sr[1:]] - rho[N - 1][sl[1:]]) * cff1
        a[N - 1] = -phi / (dx if axis == 2 else dy)
        # 内层（源码 k=N-1..1）
        for k in range(N - 2, -1, -1):
            cff1 = (rho[k + 1][sr[1:]] - rho[k + 1][sl[1:]] +
                    rho[k][sr[1:]] - rho[k][sl[1:]])
            cff2 = (rho[k + 1][sr[1:]] + rho[k + 1][sl[1:]] -
                    rho[k][sr[1:]] - rho[k][sl[1:]])
            cff3 = (z_r[k + 1][sr[1:]] + z_r[k + 1][sl[1:]] -
                    z_r[k][sr[1:]] - z_r[k][sl[1:]])
            cff4 = (z_r[k + 1][sr[1:]] - z_r[k + 1][sl[1:]] +
                    z_r[k][sr[1:]] - z_r[k][sl[1:]])
            phi = phi + fac3 * (cff1 * cff3 - cff2 * cff4)
            a[k] = -phi / (dx if axis == 2 else dy)
        return a

    a_u = _dir(rho, z_r, z_w, axis=2)
    a_v = _dir(rho, z_r, z_w, axis=1)
    return a_u, a_v


# ---------- 柱平均（PREREG §5 A2/A2b/A2c 口径） ----------
def hz_u(Hz):
    """u 点层厚 0.5(Hz_i+Hz_{i-1})，形状 (N,Ny,Nx-1)。"""
    return 0.5 * (Hz[:, :, 1:] + Hz[:, :, :-1])


def hz_v(Hz):
    """v 点层厚 0.5(Hz_j+Hz_{j-1})，形状 (N,Ny-1,Nx)。"""
    return 0.5 * (Hz[:, 1:, :] + Hz[:, :-1, :])


def colmean(a, Hzx):
    """层厚加权柱平均 Σ_k Hzx·a / Σ_k Hzx（Σ_k Hz_u = 0.5(h_i+h_{i-1}) 即正压耦合的深度平均口径）。"""
    return np.sum(Hzx * a, axis=0) / np.sum(Hzx, axis=0)


# ---------- 制造场（PREREG §2，常数写死） ----------
MF = dict(rho_bar=25.0, dR=1.5, z0=-250.0, d=100.0, eps=0.05,
          kx=2.0 * np.pi / 20000.0, De=500.0)


def rho_manufactured(x, z, eps=None):
    """rho_m(x,z) = 25.0 - 1.5*tanh((z+250)/100) + eps*sin(kx*x)*exp(z/500)。（kg/m^3-1000）"""
    e = MF['eps'] if eps is None else eps
    return (MF['rho_bar'] - MF['dR'] * np.tanh((z - MF['z0']) / MF['d'])
            + e * np.sin(MF['kx'] * x) * np.exp(z / MF['De']))


def rho_reference_z(z):
    """参考态（仅 z 依赖部分）：25.0 - 1.5*tanh((z+250)/100)。"""
    return MF['rho_bar'] - MF['dR'] * np.tanh((z - MF['z0']) / MF['d'])


def a_x_true(x, z):
    """闭式真值：-(g/rho0)*eps*kx*cos(kx*x)*De*(1-exp(z/De))；a_y_true 恒 0。"""
    return -(G_ACC / RHO0) * MF['eps'] * MF['kx'] * np.cos(MF['kx'] * x) * \
        MF['De'] * (1.0 - np.exp(z / MF['De']))


# ---------- 误差范数（PREREG §2） ----------
def norms_u(a_num, a_tru, Hz, dx=2000.0, dy=2000.0):
    """u 向内点误差范数：两水平方向各去掉最外一圈；体积权 L2 与 L∞。"""
    err = (a_num - a_tru)[:, 1:-1, 1:-1]
    w = 0.5 * (Hz[:, :, 1:] + Hz[:, :, :-1])[:, 1:-1, 1:-1] * dx * dy
    L2 = float(np.sqrt(np.sum(w * err ** 2) / np.sum(w)))
    return L2, float(np.max(np.abs(err)))


def norms_v(a_num, Hz, dx=2000.0, dy=2000.0):
    """v 向（真值恒零）：同口径。"""
    err = a_num[:, 1:-1, 1:-1]
    w = 0.5 * (Hz[:, 1:, :] + Hz[:, :-1, :])[:, 1:-1, 1:-1] * dx * dy
    L2 = float(np.sqrt(np.sum(w * err ** 2) / np.sum(w)))
    return L2, float(np.max(np.abs(err)))


def rx0_of(h):
    """Beckmann-Haidvogel rx0 = max|Δh|/(2h̄)，双向取最大。"""
    h = np.asarray(h, dtype=np.float64)
    a = np.abs(h[:, 1:] - h[:, :-1]) / (h[:, 1:] + h[:, :-1])
    b = np.abs(h[1:, :] - h[:-1, :]) / (h[1:, :] + h[:-1, :])
    return float(max(a.max(), b.max()))


def gauss_seamount(Npt, dx, L, H0=3000.0, hmin=80.0, domain=96000.0):
    """解析高斯海山（PREREG §3 S2）：返回 h(Ny,Nx) 与 x_rho(Nx)。域中心对齐，Npt=48/96/192。"""
    x = (np.arange(Npt) + 0.5) * dx
    X, Y = np.meshgrid(x, x)
    r2 = (X - domain / 2.0) ** 2 + (Y - domain / 2.0) ** 2
    return H0 - (H0 - hmin) * np.exp(-r2 / L ** 2), x
