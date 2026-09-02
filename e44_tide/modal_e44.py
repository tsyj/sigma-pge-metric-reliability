#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""modal_paper_20260828/modal_paper.py -- 逐垂向模态分解搬到论文正文那座海山 (零机时, 只读)。

判据: PREREG_MODAL_PAPER.md (先盖章)。设计输入: DESIGN_PAPER.json。
通量与环带口径逐字沿用 paperseamount_bigdom_20260828/harvest_ps.py 的 flux_COH / annulus_metrics / P_of_r;
投影函数 project()/zw_from_Hz() 从 modal_decomp_20260828/modal_decomp.py 按源码文本原样抽出执行。
用法: modal_paper.py [--arms dj,v4,combo] [--wins W_MID,...]
"""
import sys, os, json, time, hashlib
import numpy as np
import netCDF4 as nc

PGE = "/data/xinyuan/zpg_roms_dev/pge_test/"
PS = PGE + "paperseamount_bigdom_20260828/"
MD = PGE + "modal_decomp_20260828/"
MP = PGE + "modal_paper_20260828/"
BT = PGE + "bandtoll_20260830/"
sys.path.insert(0, MD)
sys.path.insert(0, PS)
import modes_lib as ML
import harvest_ps as HP
G0 = HP.G0

RHO0, ALPHA, GG, T0, T_M2, DA, DX = HP.RHO0, HP.ALPHA, HP.GG, HP.T0, HP.T_M2, HP.DA, HP.DX
OMEGA, F0 = HP.OMEGA, HP.F0
XC, YC = HP.XC, HP.YC
WINDOWS = HP.WINDOWS
BANDS = HP.BANDS
ARMS = ["e44g16", "e44v4x"]
NLEV = 13
NKEEP = NLEV - 1                    # 全谱 = 12
N_PROP = 7                          # DESIGN_PAPER.json subspace_split.N_PROP_FIXED
ZDEEP = -450.0
RFAR = (60000.0, 120000.0)
CHUNK = 20000
RB = G0.RB
ARCH = dict(dj=97.1956844225798, v4=91.93708213403171, combo=91.55159255748983)   # COH/W_MID/FAR_60_100
NREC_EXPECT = 433

# ---------------------------------------------------------------- 抽出上一轮的投影实现
_src = open(MD + "modal_decomp.py", encoding="utf-8").read()
_i0 = _src.index("def project(")
_i1 = _src.index("class Ring:")
PROJ_SRC = _src[_i0:_i1].rstrip() + "\n"
PROJ_SHA = hashlib.sha256(PROJ_SRC.encode("utf-8")).hexdigest()
_ns = dict(np=np, ML=ML, NKEEP=NKEEP, NREC=N_PROP, ZDEEP=ZDEEP, CHUNK=CHUNK)
exec(compile(PROJ_SRC, MD + "modal_decomp.py::project", "exec"), _ns)
project = _ns["project"]
zw_from_Hz = _ns["zw_from_Hz"]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def dct2_matrix(n):
    """DCT-II 矩阵 (正交归一), 层序号空间 -- 与层结、与模态基都无关。"""
    k = np.arange(n)
    D = np.cos(np.pi * k[:, None] * (2 * k[None, :] + 1) / (2.0 * n))
    D = D * np.sqrt(2.0 / n)
    D[0] = D[0] / np.sqrt(2.0)
    return D


class Arm:
    """按窗口惰性读盘 (只读需要的帧), z_w 逐字 = harvest_ps.Case。"""
    def __init__(self, path, geom):
        ds = nc.Dataset(path)
        self.ds = ds
        self.ot = np.array(ds.variables["ocean_time"][:], np.float64)
        self.h = np.array(ds.variables["h"][:], np.float64)
        s_w = np.array(ds.variables["s_w"][:], np.float64)
        Cs_w = np.array(ds.variables["Cs_w"][:], np.float64)
        hc = float(np.array(ds.variables["hc"][:]))
        assert int(np.array(ds.variables["Vtransform"][:])) == 2
        self.Zo_w = (hc * s_w[:, None, None] + Cs_w[:, None, None] * self.h) / (hc + self.h)
        self.nrec = len(self.ot)
        self.geom = geom
        assert np.array_equal(self.h[:, 1:-1], geom.h[:, 1:-1]), "his h != grid h"

    def sel(self, ta, tb):
        ot = self.ot
        i0 = max(int(np.searchsorted(ot, ta, side="right")) - 1, 0)
        i1 = min(int(np.searchsorted(ot, tb, side="left")), len(ot) - 1)
        assert ot[i0] <= ta + 1e-6 and ot[i1] >= tb - 1e-6, "窗口超出 his 范围"
        s = np.arange(i0, i1 + 1)
        assert len(s) >= 6
        return s

    def has(self, ta, tb):
        return self.ot[0] <= ta + 1e-6 and self.ot[-1] >= tb - 1e-6

    def read(self, s):
        v = self.ds.variables
        za = np.array(v["zeta"][s[0]:s[-1] + 1], np.float32)
        te = np.array(v["temp"][s[0]:s[-1] + 1], np.float32)
        uu = np.array(v["u"][s[0]:s[-1] + 1], np.float32)
        vv = np.array(v["v"][s[0]:s[-1] + 1], np.float32)
        return za, te, uu, vv

    def close(self):
        self.ds.close()


class Rings:
    def __init__(self, geom):
        self.geom = geom
        ii = np.zeros(geom.h.shape, bool); ii[1:-1, 1:-1] = True
        self.ii = ii
        self.rmax = float(geom.rr[ii].max())
        self.edges = []
        self.centers = []
        for r0, r1 in zip(RB[:-1], RB[1:]):
            if r0 > self.rmax:
                break
            self.edges.append((r0, r1))
            self.centers.append(0.5 * (r0 + r1) / 1e3)
        self.centers = np.array(self.centers)
        self.base = [(geom.rr >= r0) & (geom.rr < r1) & ii for r0, r1 in self.edges]

    def P_of_r(self, Fr, fin):
        out = np.full(len(self.centers), np.nan)
        for i, b in enumerate(self.base):
            m = b & fin
            if m.sum():
                out[i] = float(np.mean(2 * np.pi * self.geom.rr[m] * Fr[m]) / 1e6)
        return out


def main():
    t_start = time.time()
    only_a, only_w = None, None
    for a in sys.argv[1:]:
        if a.startswith("--arms"):
            only_a = a.split("=", 1)[1].split(",")
        if a.startswith("--wins"):
            only_w = a.split("=", 1)[1].split(",")
    geom = HP.Geom(PS + "inputs/dom500km/grid.nc", XC, YC)
    R = Rings(geom)
    ny, nx = geom.h.shape
    des = json.load(open(MP + "DESIGN_PAPER.json"))
    C_THR = {w: des["subspace_split"]["per_window"][w]["c_threshold_m_s"] for w in WINDOWS}
    Dm = dct2_matrix(NLEV)
    zan = np.linspace(-3000.0, 0.0, 3001)
    Tan = ML.T_thermo(zan)
    ii = R.ii

    res = dict(prereg="PREREG_BANDTOLL.md (管线逐字沿用 PREREG_MODAL_PAPER.md)", design="DESIGN_PAPER.json",
               windows=WINDOWS, bands={k: [v[0] / 1e3, v[1] / 1e3] for k, v in BANDS.items()},
               nkeep=NKEEP, n_prop_fixed=N_PROP, z_deep_m=ZDEEP, rfar_m=list(RFAR),
               T_M2_s=T_M2, arch_COH_W_MID_FAR_60_100=ARCH,
               ring_centers_km=[float(x) for x in R.centers],
               pipeline=dict(modal_paper_md5=md5(os.path.abspath(__file__)),
                             modes_lib_md5=md5(MD + "modes_lib.py"),
                             modal_decomp_md5=md5(MD + "modal_decomp.py"),
                             project_src_sha256=PROJ_SHA,
                             harvest_ps_md5=md5(PS + "harvest_ps.py"),
                             design_paper_md5=md5(MP + "design_paper.py"),
                             prereg_sha256=hashlib.sha256(
                                 open(MP + "PREREG_MODAL_PAPER.md", "rb").read()).hexdigest()),
               gate_G1=des["spectrum"]["sigma13_h3000"]["health"],
               gate_G4=des["gate_G4_window_condition"],
               gate_G6=des["gate_G6_degeneracy"],
               per_arm={})
    g2 = {}; g3 = {}; g5 = {}
    ot_ref = None

    for arm in ARMS:
        if only_a and arm not in only_a:
            continue
        tag = arm
        hf = BT + tag + "/his_%s.nc" % tag
        print("\n=== %s   t=%.0fs" % (arm, time.time() - t_start), flush=True)
        A = Arm(hf, geom)
        g5[arm] = dict(nrec=A.nrec, nrec_ok=bool(A.nrec == NREC_EXPECT),
                       h_ghost_max_abs=float(np.abs(A.h - geom.h).max()))
        if ot_ref is None:
            ot_ref = A.ot
            g5[arm]["ot_same_as_first"] = True
        else:
            g5[arm]["ot_same_as_first"] = bool(np.array_equal(A.ot, ot_ref))
        rec = dict(arm=arm, tag=tag, nrec=A.nrec, windows={})
        for wn, (p0, p1) in WINDOWS.items():
            if only_w and wn not in only_w:
                continue
            ta, tb = T0 + p0 * T_M2, T0 + p1 * T_M2
            if not A.has(ta, tb):
                print("  %s 超出 his 范围, 跳过" % wn); continue
            tw = time.time()
            s = A.sel(ta, tb); t = A.ot[s]; tau = t - T0
            P = np.linalg.pinv(G0.fitmat(tau)); w = G0.trap_weights(t, ta, tb)
            za, te, uu, vv = A.read(s)
            zaf = np.array(za, np.float64)
            zw = zaf[:, None] + (zaf[:, None] + A.h) * A.Zo_w[None]
            Hz = np.diff(zw, axis=1)
            Hzb = np.tensordot(w, Hz, axes=(0, 0))
            zwm = np.tensordot(w, zw, axes=(0, 0)); zrm = 0.5 * (zwm[1:] + zwm[:-1])
            del zw, Hz

            def amp(Y):
                c = np.tensordot(P, np.array(Y, np.float64), axes=(1, 0))
                return c[1] - 1j * c[2]
            te64 = np.array(te, np.float64); del te
            That = amp(te64); Tbar = np.tensordot(w, te64, axes=(0, 0)); del te64
            uhat = amp(uu); del uu
            vhat = amp(vv); del vv, za
            rh = (-RHO0 * ALPHA * That) * Hzb
            csum = np.cumsum(rh[::-1], axis=0)[::-1] - rh
            phat = GG * (csum + 0.5 * rh)
            Hz_u = 0.5 * (Hzb[..., :-1] + Hzb[..., 1:]); Hz_v = 0.5 * (Hzb[:, :-1, :] + Hzb[:, 1:, :])
            ubh = (Hz_u * uhat).sum(0) / Hz_u.sum(0); vbh = (Hz_v * vhat).sum(0) / Hz_v.sum(0)
            uph = uhat - ubh[None]; vph = vhat - vbh[None]
            p_u = 0.5 * (phat[..., :-1] + phat[..., 1:]); p_v = 0.5 * (phat[:, :-1, :] + phat[:, 1:, :])
            fx_u = 0.5 * np.real(uph * np.conj(p_u) * Hz_u)
            fy_v = 0.5 * np.real(vph * np.conj(p_v) * Hz_v)
            Fxu_tot = fx_u.sum(0); Fyv_tot = fy_v.sum(0)
            Fx = np.full((ny, nx), np.nan); Fy = np.full((ny, nx), np.nan)
            Fx[:, 1:-1] = 0.5 * (Fxu_tot[:, :-1] + Fxu_tot[:, 1:])
            Fy[1:-1, :] = 0.5 * (Fyv_tot[:-1, :] + Fyv_tot[1:, :])
            fin = np.isfinite(Fx) & np.isfinite(Fy)
            Fr_tot = np.where(fin, Fx * geom.nx_ + Fy * geom.ny_, np.nan)

            def band_P(Fr, R1, R2):
                good = (geom.rr >= R1) & (geom.rr <= R2) & fin
                return float(np.where(good, Fr, 0.0).sum() * DA / (R2 - R1) / 1e6)
            tot_bands = {bn: band_P(Fr_tot, *BANDS[bn]) for bn in BANDS}
            P_tot_r = R.P_of_r(Fr_tot, fin)
            if wn == "W_MID" and arm in ARCH:
                a_ref = ARCH[arm]
                g3.setdefault(arm, {})["archive_FAR_60_100"] = dict(
                    mine=tot_bands["FAR_60_100"], archive=a_ref,
                    rel=abs(tot_bands["FAR_60_100"] - a_ref) / abs(a_ref))
            wrec = dict(window_P=[p0, p1], nrec=int(len(s)),
                        t_first_P=float(tau[0] / T_M2), t_last_P=float(tau[-1] / T_M2),
                        fit_cond=float(np.linalg.cond(G0.fitmat(tau))),
                        P_total_bands_MW=tot_bands,
                        P_total_of_r_MW=[None if not np.isfinite(x) else float(x) for x in P_tot_r])

            # ---- 参考层结
            far = ii & (geom.h > 2999.9) & (geom.rr >= RFAR[0]) & (geom.rr <= RFAR[1])
            Tfar = Tbar[:, far].mean(1); zfar = zrm[:, far].mean(1)
            o = np.argsort(zfar)
            wrec["n_far_cols"] = int(far.sum())
            wrec["Tref_self_z"] = [float(x) for x in zfar[o]]
            wrec["Tref_self_T"] = [float(x) for x in Tfar[o]]
            TREF = dict(self=(zfar[o], Tfar[o]), analytic=(zan, Tan))

            nk = NLEV
            zwu_top = 0.5 * (zwm[-1, :, :-1] + zwm[-1, :, 1:])
            zwu = np.moveaxis(zw_from_Hz(np.moveaxis(Hz_u, 0, -1), zwu_top), -1, 0)
            zwv_top = 0.5 * (zwm[-1, :-1, :] + zwm[-1, 1:, :])
            zwv = np.moveaxis(zw_from_Hz(np.moveaxis(Hz_v, 0, -1), zwv_top), -1, 0)
            shu = Hz_u.shape[1:]; shv = Hz_v.shape[1:]
            annm = ii & (geom.rr >= BANDS["FAR_60_100"][0]) & (geom.rr <= BANDS["FAR_60_100"][1])
            umask_far = far[:, 1:] | far[:, :-1]
            umask_ann = annm[:, 1:] | annm[:, :-1]

            for basis in ("self", "analytic"):
                tz, tt = TREF[basis]
                PU = project(np.moveaxis(Hz_u, 0, -1).reshape(-1, nk),
                             np.moveaxis(zwu, 0, -1).reshape(-1, nk + 1), tz, tt,
                             np.moveaxis(uph, 0, -1).reshape(-1, nk),
                             np.moveaxis(p_u, 0, -1).reshape(-1, nk))
                PV = project(np.moveaxis(Hz_v, 0, -1).reshape(-1, nk),
                             np.moveaxis(zwv, 0, -1).reshape(-1, nk + 1), tz, tt,
                             np.moveaxis(vph, 0, -1).reshape(-1, nk),
                             np.moveaxis(p_v, 0, -1).reshape(-1, nk))
                e2u = float(np.abs(PU["F_sum"].reshape(shu) - Fxu_tot).max()
                            / max(np.abs(Fxu_tot).max(), 1e-300))
                e2v = float(np.abs(PV["F_sum"].reshape(shv) - Fyv_tot).max()
                            / max(np.abs(Fyv_tot).max(), 1e-300))
                Fn_u = PU["F_n"].reshape(shu + (NKEEP,))
                Fn_v = PV["F_n"].reshape(shv + (NKEEP,))
                Pn_bands = {bn: [] for bn in BANDS}
                Pn_r = np.zeros((NKEEP, len(R.centers)))
                for n in range(NKEEP):
                    fxn = np.full((ny, nx), np.nan); fyn = np.full((ny, nx), np.nan)
                    fxn[:, 1:-1] = 0.5 * (Fn_u[:, :-1, n] + Fn_u[:, 1:, n])
                    fyn[1:-1, :] = 0.5 * (Fn_v[:-1, :, n] + Fn_v[1:, :, n])
                    Frn = np.where(fin, fxn * geom.nx_ + fyn * geom.ny_, np.nan)
                    for bn in BANDS:
                        Pn_bands[bn].append(band_P(Frn, *BANDS[bn]))
                    Pn_r[n] = R.P_of_r(Frn, fin)
                e3 = {bn: abs(sum(Pn_bands[bn]) - tot_bands[bn]) / max(abs(tot_bands[bn]), 1e-300)
                      for bn in BANDS}
                # 逐柱可变划分 (并列)
                cthr = C_THR[wn]
                mprop_u = (PU["c_n"] >= cthr)
                mprop_v = (PV["c_n"] >= cthr)
                fxv = np.full((ny, nx), np.nan); fyv_ = np.full((ny, nx), np.nan)
                a_ = np.where(mprop_u, PU["F_n"], 0.0).sum(1).reshape(shu)
                b_ = np.where(mprop_v, PV["F_n"], 0.0).sum(1).reshape(shv)
                fxv[:, 1:-1] = 0.5 * (a_[:, :-1] + a_[:, 1:]); fyv_[1:-1, :] = 0.5 * (b_[:-1, :] + b_[1:, :])
                Fr_pv = np.where(fin, fxv * geom.nx_ + fyv_ * geom.ny_, np.nan)
                ent = dict(gate_G2_u=e2u, gate_G2_v=e2v, gate_G3_sum_vs_total=e3,
                           P_n_bands_MW={bn: [float(x) for x in Pn_bands[bn]] for bn in BANDS},
                           P_n_of_r_MW=[[None if not np.isfinite(x) else float(x) for x in Pn_r[n]]
                                        for n in range(NKEEP)],
                           P_prop_fixed_bands_MW={bn: float(sum(Pn_bands[bn][:N_PROP])) for bn in BANDS},
                           P_tail_fixed_bands_MW={bn: float(sum(Pn_bands[bn][N_PROP:])) for bn in BANDS},
                           P_prop_varcol_bands_MW={bn: band_P(Fr_pv, *BANDS[bn]) for bn in BANDS},
                           c_thr_varcol=float(cthr),
                           n_prop_varcol_far_mean=float(mprop_u[umask_far.ravel()].sum(1).mean()),
                           n_prop_varcol_ann_mean=float(mprop_u[umask_ann.ravel()].sum(1).mean()),
                           c_n_far_mean=[float(x) for x in np.nanmean(
                               PU["c_n"].reshape(shu + (NKEEP,))[umask_far], 0)],
                           wdeep_n_far=[float(x) for x in
                                        PU["wdeep_n"].reshape(shu + (NKEEP,))[umask_far].mean(0)],
                           wdeep_n_ann=[float(x) for x in
                                        PU["wdeep_n"].reshape(shu + (NKEEP,))[umask_ann].mean(0)],
                           n_neg_N2=int(PU["n_neg_N2"] + PV["n_neg_N2"]),
                           n_col_skipped=int(PU["n_col_skipped"] + PV["n_col_skipped"]))
                # ---- 谱交叉验证 (只在主窗 + self 基上做)
                if wn == "W_MID" and basis == "self":
                    urec = np.moveaxis(PU["u_rec"].reshape(shu + (nk,)), -1, 0)
                    ures = uph - urec
                    Fx_lo = np.full((ny, nx), np.nan)
                    lo_u = Fn_u[:, :, :N_PROP].sum(-1)
                    Fx_lo[:, 1:-1] = 0.5 * (lo_u[:, :-1] + lo_u[:, 1:])
                    Fx_full = Fx.copy()
                    Fx_res = Fx_full - Fx_lo
                    spec = {}
                    jall = np.arange(1, ny - 1)
                    yy = geom.yr[:, 0]
                    jfar = jall[np.abs(yy[jall] - YC) > 60000.0]
                    for nmL, arrf in (("full", Fx_full), ("low_n_le_7", Fx_lo), ("residual", Fx_res)):
                        d = {}
                        for rl, js in (("all_rows", jall), ("far_rows", jfar)):
                            blk = arrf[js][:, 1:251]                # 250 点 = 恰好一个东西周期
                            Fk = np.fft.rfft(blk - blk.mean(1, keepdims=True), axis=1)
                            pw = (np.abs(Fk) ** 2).mean(0)
                            tot = pw[1:].sum()
                            kk = np.arange(len(pw))
                            d[rl] = dict(power=[float(x) for x in pw],
                                         hi_frac=float(pw[kk >= len(pw) // 2].sum() / max(tot, 1e-300)),
                                         nyq_frac=float(pw[-1] / max(tot, 1e-300)),
                                         lam_median_km=float(np.interp(
                                             0.5, np.cumsum(pw[1:]) / max(tot, 1e-300),
                                             2.0 * 250.0 / kk[1:])))
                        spec[nmL] = d
                    dctp = {}
                    sel_u = umask_ann.ravel()
                    for nmL, fld in (("full", uph), ("low_n_le_7", urec), ("residual", ures)):
                        col = np.moveaxis(fld, 0, -1).reshape(-1, nk)[sel_u]
                        Cm = np.abs(col @ Dm.T) ** 2
                        pm = Cm.mean(0)
                        tot = pm[1:].sum()
                        dctp[nmL] = dict(power=[float(x) for x in pm],
                                         vhi_frac=float(pm[6:].sum() / max(tot, 1e-300)),
                                         last_frac=float(pm[-1] / max(tot, 1e-300)))
                    ent["spectra"] = dict(horizontal_kx=spec, vertical_dct_sigma_index=dctp,
                                          n_far_rows=int(len(jfar)), n_ann_ucols=int(sel_u.sum()),
                                          note="水平: 深度积分 u 面通量密度沿东西 250 点周期 FFT; "
                                               "垂向: sigma 层序号空间 DCT-II, 主带环带柱平均")
                    del urec, ures
                wrec[basis] = ent
                if basis == "self":
                    g2.setdefault(arm, {})[wn] = dict(u=e2u, v=e2v)
                    g3.setdefault(arm, {})[wn] = e3
                del PU, PV, Fn_u, Fn_v
            print("  %-8s G2=%.1e/%.1e  G3=%.1e  Ptot(60-100)=%9.4f  tail=%.3f%%  (%.0fs)"
                  % (wn, wrec["self"]["gate_G2_u"], wrec["self"]["gate_G2_v"],
                     max(wrec["self"]["gate_G3_sum_vs_total"].values()), tot_bands["FAR_60_100"],
                     100 * wrec["self"]["P_tail_fixed_bands_MW"]["FAR_60_100"] / tot_bands["FAR_60_100"],
                     time.time() - tw), flush=True)
            rec["windows"][wn] = wrec
            del That, uhat, vhat, phat, uph, vph, p_u, p_v, fx_u, fy_v, Hzb, zwm, zrm, Tbar
        res["per_arm"][arm] = rec
        A.close(); del A
        json.dump(res, open("/data/xinyuan/GOAI_ai4s_env/e44/analysis/MODAL_E44_RAW.json", "w"), indent=1, ensure_ascii=False, default=str)

    res["gate_G2"] = dict(values=g2, PASS=bool(all(v["u"] < 1e-9 and v["v"] < 1e-9
                                                   for a in g2.values() for v in a.values())))
    okA = True
    for _a in g3.values():
        for _k, _v in _a.items():
            if _k == "archive_FAR_60_100":
                continue
            if max(_v.values()) >= 1e-9:
                okA = False
    okB = all(a["archive_FAR_60_100"]["rel"] < 1e-9 for a in g3.values() if "archive_FAR_60_100" in a)
    res["gate_G3"] = dict(values=g3, PASS=bool(okA and okB), part_i_sum=bool(okA), part_ii_archive=bool(okB))
    res["gate_G5"] = dict(values=g5, PASS=bool(all(v["nrec_ok"] and v["ot_same_as_first"]
                                                   and v["h_ghost_max_abs"] == 0.0 for v in g5.values())))
    res["elapsed_s"] = time.time() - t_start
    json.dump(res, open("/data/xinyuan/GOAI_ai4s_env/e44/analysis/MODAL_E44_RAW.json", "w"), indent=1, ensure_ascii=False, default=str)
    print("\nG2 %s  G3 %s (i=%s ii=%s)  G5 %s   (%.0f s)"
          % (res["gate_G2"]["PASS"], res["gate_G3"]["PASS"], okA, okB, res["gate_G5"]["PASS"],
             res["elapsed_s"]))
    print("WROTE " + "/data/xinyuan/GOAI_ai4s_env/e44/analysis/MODAL_E44_RAW.json")


if __name__ == "__main__":
    main()
