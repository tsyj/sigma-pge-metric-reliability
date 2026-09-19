# -*- coding: utf-8 -*-
"""
cert_gate.py —— 统计判决总账核心库（领域无关）
cert_stat_ledger / E71 正式版。冻结于 PREREG_cert_stat_ledger.md 封存之时。

约定（与 PREREG §0 一致，改动=偏离）：
  α=0.025 单侧；E*=1/α=40；门 p0=0.9；
  认证 e-过程：H0 p<=p0，分子先验 U(p0,1]（主）或点备择 q*（副）；
  判死 e-过程：H0 p>=p0，分子先验 U[0,p0)；
  数值积分：512 节点 Gauss–Legendre，log 域。
只依赖 numpy。
"""
import numpy as np

ALPHA = 0.025
E_STAR = 1.0 / ALPHA          # 40
P0 = 0.9
Z95 = 1.959964
GL_NODES = 512


def wilson_ci(k, n, z=Z95):
    """Wilson 双侧 95% CI。返回 (lo, hi)。"""
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    p = k / n
    z2 = z * z
    den = 1.0 + z2 / n
    ctr = (p + z2 / (2 * n)) / den
    hw = (z / den) * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return ctr - hw, ctr + hw


def _log_mix_table(i_max, j_max, lo, hi):
    """
    log ∫_{lo}^{hi} q^i (1-q)^j dq/(hi-lo)  的 (i_max+1)x(j_max+1) 表。
    Gauss–Legendre 512 节点，log 域 logsumexp。
    """
    x, w = np.polynomial.legendre.leggauss(GL_NODES)
    q = 0.5 * (hi - lo) * x + 0.5 * (hi + lo)
    lw = np.log(w * 0.5 * (hi - lo)) - np.log(hi - lo)   # 含先验密度 1/(hi-lo)
    lq = np.log(q)
    l1q = np.log1p(-q)
    jcol = np.arange(j_max + 1)[:, None]           # (j+1, 1)
    base_j = jcol * l1q[None, :]                   # (j+1, nodes)
    out = np.empty((i_max + 1, j_max + 1))
    for i in range(i_max + 1):                     # 逐 i 行，避免三维大数组
        m = lw[None, :] + i * lq[None, :] + base_j  # (j+1, nodes)
        mx = m.max(axis=1, keepdims=True)
        out[i, :] = (mx[:, 0] + np.log(np.exp(m - mx).sum(axis=1)))
    return out


class ETable:
    """log e(i 胜, j 负) 查表。kind: 'cert'（U(p0,1]）| 'kill'（U[0,p0)）| 'point'（点备择 q*）。"""

    def __init__(self, i_max, j_max, kind="cert", p0=P0, q_star=0.95):
        self.kind = kind
        self.p0 = p0
        ii = np.arange(i_max + 1)[:, None]
        jj = np.arange(j_max + 1)[None, :]
        log_den = ii * np.log(p0) + jj * np.log1p(-p0)
        if kind == "cert":
            log_num = _log_mix_table(i_max, j_max, p0, 1.0)
        elif kind == "kill":
            log_num = _log_mix_table(i_max, j_max, 0.0, p0)
        elif kind == "point":
            log_num = ii * np.log(q_star) + jj * np.log1p(-q_star)
        else:
            raise ValueError(kind)
        self.log_e = log_num - log_den
        self.log_thresh = np.log(E_STAR)

    def loge_path(self, wins_cum, t_idx):
        """wins_cum: 逐对累计胜数数组（任意形状最后一维=时间）；t_idx: 1..n 的对序号。"""
        i = wins_cum
        j = t_idx - wins_cum
        return self.log_e[i, j]

    def crossed(self, wins_cum, t_idx):
        return self.loge_path(wins_cum, t_idx) >= self.log_thresh


def first_crossing(loge_paths, log_thresh=np.log(E_STAR)):
    """
    loge_paths: (R, T) 逐对 log e。返回 (stopped_bool(R,), stop_time(R,) 1-based; 未越界记 T)。
    """
    hit = loge_paths >= log_thresh
    any_hit = hit.any(axis=1)
    stop = np.where(any_hit, hit.argmax(axis=1) + 1, loge_paths.shape[1])
    return any_hit, stop


def av_lower_bound(outcomes, grid=None):
    """
    任意时刻有效 95% 单侧下界：对 p0 网格反转认证 e-过程族（各自 U(p0,1] 先验）。
    outcomes: 0/1 序列。返回被拒的最大 p0（无 ⇒ 0.0）。
    """
    if grid is None:
        grid = np.arange(0.500, 0.9995, 0.001)
    outcomes = np.asarray(outcomes, dtype=int)
    n = len(outcomes)
    wins = np.cumsum(outcomes)
    t = np.arange(1, n + 1)
    lb = 0.0
    x, w = np.polynomial.legendre.leggauss(GL_NODES)
    for p0 in grid:
        q = 0.5 * (1 - p0) * x + 0.5 * (1 + p0)
        lw = np.log(w * 0.5 * (1 - p0)) - np.log(1 - p0)
        lq, l1q = np.log(q), np.log1p(-q)
        m = lw[None, :] + wins[:, None] * lq[None, :] + (t - wins)[:, None] * l1q[None, :]
        mx = m.max(axis=1)
        log_num = mx + np.log(np.exp(m - mx[:, None]).sum(axis=1))
        log_den = wins * np.log(p0) + (t - wins) * np.log1p(-p0)
        if np.any(log_num - log_den >= np.log(E_STAR)):
            lb = p0
        else:
            break  # e 关于 p0 单调递减方向，一旦不拒即停（网格自小而大）
    return float(lb)


def n_star_all_wins(kind="cert", q_star=0.95, n_max=500):
    """全胜流下首次 e>=E* 的连对数；kind='cert' 用混合先验，'point' 用点备择。"""
    tab = ETable(n_max, 0, kind=("cert" if kind == "cert" else "point"), q_star=q_star)
    for n in range(1, n_max + 1):
        if tab.log_e[n, 0] >= np.log(E_STAR):
            return n
    return None


def sha256_of(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()
