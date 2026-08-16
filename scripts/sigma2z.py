#!/usr/bin/env python
"""把 ROMS 的 σ 层剖面插到 MITgcm 的 z 层上 —— 逐场比较的前提。

⚠ E35 撤回 #8：此前 `_diagnose` 直接算 `u - U`，而两个模式的垂向层序**相反**：
    ROMS   k=0 是**底**层（Cs_r 从 -0.905 升到 -0.000）
    MITgcm k=0 是**面**层（RC 从 -9.7 降到 -2708.7）
  于是 ROMS 底层（12.33 cm/s 伪流）被配到了 MITgcm 表层（9.23 cm/s 真流）。
  `err_rms_vs_truth`（隐藏评估器的打分）从一开始就是错的。

仅仅翻转还不够：σ 层随地形起伏，各列的层深都不同，必须**逐列插值**。
"""
import numpy as np


def roms_depths(Cs_r, h, zeta=None):
    """ROMS rho 点各层深度（负值向下），形状 (N, eta, xi)。"""
    z = Cs_r[:, None, None] * h[None, :, :]
    if zeta is not None:
        z = z + zeta[None, :, :] * (1.0 + Cs_r[:, None, None])
    return z


def to_z(field, z_roms, z_target):
    """把 (N, eta, xi) 的 ROMS 场逐列插到 z_target（一维，负值向下）。

    ROMS 的 k=0 是底层 → 插值前按深度升序排（由深到浅本来就是升序，
    因为 z 是负数、底层最负）。目标层低于该列海底时置 NaN（不参与比较）。
    """
    N, ny, nx = field.shape
    out = np.full((len(z_target), ny, nx), np.nan)
    for j in range(ny):
        for i in range(nx):
            zc = z_roms[:, j, i]           # 由底(最负)到面(接近0)，单调升
            fc = field[:, j, i]
            bottom = zc[0]
            m = z_target >= bottom          # 目标层在海底以上才有意义
            if m.any():
                out[m, j, i] = np.interp(z_target[m], zc, fc)
    return out


def rho_from_u(u):
    """ROMS u 点 (N, eta, xi-1) → rho 点 (N, eta, xi)，两端外推。"""
    N, ny, nxm1 = u.shape
    r = np.empty((N, ny, nxm1 + 1))
    r[:, :, 1:-1] = 0.5 * (u[:, :, :-1] + u[:, :, 1:])
    r[:, :, 0] = u[:, :, 0]
    r[:, :, -1] = u[:, :, -1]
    return r
