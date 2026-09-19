#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71G · 封存后扫描 → MMS_OPERATOR.json（＋描述性图）。

门控（任一不过即拒跑）：
  ① PREREG_mms_operator.sha256 缺失或首行 sha 与 PREREG 不符（封存必须早于任何留出读数）；
  ② 五个脚本（replica/scan/verdict/1step_clone/run）当前 sha256 与封存 PREREG §7 表所填不符。
内容 = PREREG §3/§5 的逐字执行：S0 锚（判定项 A0/A1/A2/A3；报告项 A2c 及 A3 内 row3 列表；
可选 A2b 仅当克隆一步运行已完成）、S1 四档陡度、S2 同步加密（解析高斯族）、S3 旋钮判决数字。
外部数据只读；新文件只写本 final/。
运行（amax，经 e71g_run.sh）：
  systemd-run --user --scope -p MemoryMax=16G nice -n 19 \
    env OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 \
    /home/xinyuan/anaconda3/envs/numpy1/bin/python -B e71g_scan.py
"""
import hashlib, json, os, re, sys, time
import numpy as np

FIN = '/data/xinyuan/GOAI_ai4s_env/e71_innov/mms_operator/final'
PRE, SHA = f'{FIN}/PREREG_mms_operator.md', f'{FIN}/PREREG_mms_operator.sha256'
OUT = f'{FIN}/MMS_OPERATOR.json'
PGE = '/data/xinyuan/zpg_roms_dev/pge_test'           # 只读
E56RUNS = '/data/xinyuan/GOAI_ai4s_env/e56/runs'      # 只读
E56JSON = '/data/xinyuan/GOAI_ai4s_env/e56/E56_BH93.json'
V0 = f'{E56RUNS}/bh93_r26steep_v0'
CLONE = f'{FIN}/clone_1step'
DT = 10.0
TIERS = ['smooth', 'steep', 'rx069', 'harsh']         # PREREG §3 S1 档序，钉死
VISC = ['0', '50', '150', '400', '800', '1500', '2747']
SCRIPTS = ['e71g_replica.py', 'e71g_scan.py', 'e71g_verdict.py', 'e71g_1step_clone.sh', 'e71g_run.sh']


def sha256(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def gate():
    if not os.path.exists(SHA):
        sys.exit('拒绝扫描：预注册尚未封存（PREREG_mms_operator.sha256 缺失）。')
    want = open(SHA).readline().split()[0]
    got = sha256(PRE)
    if want != got:
        sys.exit('拒绝扫描：PREREG 与封存 sha256 不符。')
    table = dict(re.findall(r'^\|\s*(e71g_[A-Za-z0-9_.]+)\s*\|\s*`?([0-9a-f]{64})`?\s*\|',
                            open(PRE, encoding='utf-8').read(), flags=re.M))
    cur = {s: sha256(f'{FIN}/{s}') for s in SCRIPTS}
    bad = [s for s in SCRIPTS if table.get(s) != cur[s]]
    if bad:
        sys.exit('拒绝扫描：脚本 sha256 与封存 PREREG §7 表不符：' + ','.join(bad))
    return got, cur


PREREG_SHA, CODE_SHA = gate()

sys.path.insert(0, FIN)
import e71g_replica as RP
import netCDF4 as nc

IN2 = (slice(1, -1), slice(1, -1))
IN3 = (slice(None), slice(1, -1), slice(1, -1))


def ds(path):
    d = nc.Dataset(path)
    d.set_auto_mask(False)
    return d


def load_grid(path):
    """只读网格：h、x_rho（缺则由 1/pm 累加）、mask_rho（缺则全湿）、dx。"""
    d = ds(path)
    h = np.asarray(d['h'][:], dtype=np.float64)
    pm = np.asarray(d['pm'][:], dtype=np.float64)
    dx = float(1.0 / pm.mean())
    if 'x_rho' in d.variables:
        x = np.asarray(d['x_rho'][:], dtype=np.float64)[0]
    else:
        x = (np.arange(h.shape[1]) + 0.5) * dx
    mask = (np.asarray(d['mask_rho'][:], dtype=np.float64)
            if 'mask_rho' in d.variables else np.ones_like(h))
    d.close()
    return h, x, mask, dx


def field_norms(h, x, dx, rho_fn, mask=None):
    """给定地形与 rho(x3,z3) 生成函数，跑复刻算子并出 PREREG §2 口径的四个范数。"""
    z_r, z_w, Hz = RP.set_depth_v2(h)
    X3 = np.broadcast_to(x[None, None, :], z_r.shape)
    rho = rho_fn(X3, z_r)
    a_u, a_v = RP.prsgrd31_sdj(rho, z_r, z_w, Hz, dx=dx, dy=dx)
    x_u = 0.5 * (x[1:] + x[:-1])
    z_u = 0.5 * (z_r[:, :, 1:] + z_r[:, :, :-1])
    a_tru = RP.a_x_true(np.broadcast_to(x_u[None, None, :], z_u.shape), z_u)
    # 注：扣参考态场共用同一真值——参考态只依赖 z，解析 x 梯度为零（PREREG §3 S3）
    n_land = int((mask < 0.5).sum()) if mask is not None else 0
    if n_land > 0:
        # PREREG §2：陆点相邻的 u/v 点排除（本族网格封存前已核全湿，此支仅保险）
        mu = (mask[:, 1:] * mask[:, :-1])[None]
        mv = (mask[1:, :] * mask[:-1, :])[None]
        a_u = np.where(mu > 0.5, a_u, np.nan)
        a_v = np.where(mv > 0.5, a_v, np.nan)
        a_tru = np.where(mu > 0.5, a_tru, np.nan)
        err = (a_u - a_tru)[:, 1:-1, 1:-1]
        w = 0.5 * (Hz[:, :, 1:] + Hz[:, :, :-1])[:, 1:-1, 1:-1] * dx * dx
        ok = np.isfinite(err)
        L2u = float(np.sqrt(np.nansum(w * np.where(ok, err, 0.0) ** 2) / np.sum(w[ok])))
        Liu = float(np.nanmax(np.abs(err)))
        ev = a_v[:, 1:-1, 1:-1]
        wv = 0.5 * (Hz[:, 1:, :] + Hz[:, :-1, :])[:, 1:-1, 1:-1] * dx * dx
        okv = np.isfinite(ev)
        L2v = float(np.sqrt(np.nansum(wv * np.where(okv, ev, 0.0) ** 2) / np.sum(wv[okv])))
        Liv = float(np.nanmax(np.abs(ev)))
    else:
        L2u, Liu = RP.norms_u(a_u, a_tru, Hz, dx, dx)
        L2v, Liv = RP.norms_v(a_v, Hz, dx, dx)
    return dict(EL2_u=L2u, ELinf_u=Liu, EL2_v=L2v, ELinf_v=Liv, n_land=n_land,
                rx0=RP.rx0_of(h), amax_u=float(np.nanmax(np.abs(a_u))))


def diag_rows(path, n=3):
    """seamount_diag.dat 前 n 行，列序 tdays, ubarmax, vbarmax, umax, vmax（analytical.f90 ana_diag L379-408）。"""
    with open(path) as fp:
        return [[float(v) for v in fp.readline().split()] for _ in range(n)]


R = dict(meta=dict(date=time.strftime('%F %T %z'), code_sha=CODE_SHA, prereg_sha256=PREREG_SHA,
                   numpy=np.__version__, netCDF4=nc.__version__, notes=[]))

# ---------- S0 锚 ----------
anch = {}
# A0 纵坐标锚：复刻 Cs_r vs out_his Cs_r
d = ds(f'{V0}/out_his.nc')
cs_roms = np.asarray(d['Cs_r'][:], dtype=np.float64)
d.close()
s_r, _ = RP.s_levels(13)
anch['A0'] = dict(max_dcs=float(np.max(np.abs(RP.cs_v4(s_r) - cs_roms))))

# A1 平底零锚：flat48 + 仅 z 依赖的制造场（eps=0）→ 逐位零
h_f, x_f, m_f, dx_f = load_grid(f'{PGE}/pge_grid_flat48_noN.nc')
z_r, z_w, Hz = RP.set_depth_v2(h_f)
rho0 = RP.rho_manufactured(np.zeros_like(z_r), z_r, eps=0.0)
au0, av0 = RP.prsgrd31_sdj(rho0, z_r, z_w, Hz, dx_f, dx_f)
anch['A1'] = dict(max_abs_u=float(np.max(np.abs(au0))), max_abs_v=float(np.max(np.abs(av0))))

# A2 陡臂首步锚（深度平均口径）：ini_rest 的 T → 线性 EOS → 复刻算子 → 层厚加权柱平均
h_s, x_s, m_s, dx_s = load_grid(f'{V0}/pge_grid_r26steep.nc')
d = ds(f'{V0}/ini_rest_r26steep.nc')
T = np.asarray(d['temp'][0], dtype=np.float64)
d.close()
z_r, z_w, Hz = RP.set_depth_v2(h_s)
au, av = RP.prsgrd31_sdj(RP.rho_linear_eos(T), z_r, z_w, Hz, dx_s, dx_s)
Hzu, Hzv = RP.hz_u(Hz), RP.hz_v(Hz)
abu, abv = RP.colmean(au, Hzu), RP.colmean(av, Hzv)
devu, devv = au - abu[None], av - abv[None]
rows = diag_rows(f'{V0}/seamount_diag.dat', 3)
ubar1 = rows[1][1]
dt_abs_ubar = DT * float(np.max(np.abs(abu[IN2])))
anch['A2'] = dict(
    diag_columns='tdays, ubarmax, vbarmax, umax, vmax (ana_diag MAX = signed max)',
    diag_row2=rows[1], diag_row3=rows[2], ubarmax_step1=ubar1,
    dt_absmax_ubar_repl=dt_abs_ubar,                                   # 判定量
    dt_signedmax_ubar_repl=DT * float(np.max(abu[IN2])),               # 记录
    dt_absmax_vbar_repl=DT * float(np.max(np.abs(abv[IN2]))),          # 记录
    dt_signedmax_vbar_repl=DT * float(np.max(abv[IN2])),               # 记录
    dt_absmax_au_pointwise=DT * float(np.max(np.abs(au[IN3]))),        # 记录（逐点口径，备审）
    dt_absmax_av_pointwise=DT * float(np.max(np.abs(av[IN3]))),        # 记录
    dt_absmax_au_pointwise_fullarray=DT * float(np.max(np.abs(au))),   # 记录
    ratio=dt_abs_ubar / ubar1,                                         # 判定：∈[0.5,2.0]
    ratio_pointwise_record=DT * float(np.max(np.abs(au[IN3]))) / ubar1)

# A2c 报告项（Z10 式三维括号，不入 anchor_failed）
X = DT * float(np.max(devu[IN3]))
M3 = rows[2][3]
anch['A2c'] = dict(report_only=True, X_dt_signedmax_dev_u=X, U_ubarmax_step1=ubar1, umax3d_row3=M3,
                   lo=0.95 * X, hi=1.05 * (X + ubar1),
                   in_bracket=bool(0.95 * X <= M3 <= 1.05 * (X + ubar1)),
                   rel_dev_from_X_plus_U=((M3 - (X + ubar1)) / M3) if M3 != 0 else None)

# A3 黏性首步近不变（纯已知数据，机械复算入 JSON 以给指针）
s1, s3 = [], []
for v in VISC:
    rr = diag_rows(f'{E56RUNS}/bh93_r26steep_v{v}/seamount_diag.dat', 3)
    s1.append(rr[1][1])
    s3.append(rr[2][3])
ej = json.load(open(E56JSON))
um = {r['VISC2']: r['u_max'] for r in ej if r['bathy'] == 'r26steep'}
anch['A3'] = dict(visc=VISC, step1_ubarmax=s1, spread=max(s1) / min(s1) - 1.0,        # 判定：≤0.04
                  day1_umax3d_abs_cm_v0=um[0.0], day1_umax3d_abs_cm_v2747=um[2747.0],
                  day1_ratio=um[0.0] / um[2747.0],
                  report_step1_umax3d_row3_signed=s3,
                  report_row3_spread=(max(s3) / min(s3) - 1.0) if min(s3) > 0 else None,
                  pointers=dict(step1='e56/runs/bh93_r26steep_v*/seamount_diag.dat row2 col2',
                                row3='row3 col4', day1='e56/E56_BH93.json [bathy=r26steep].u_max'))

# A2b 可选：克隆一步运行 u_prsgrd/v_prsgrd 的柱偏差归一化形状对拍
dia, log = f'{CLONE}/out_dia.nc', f'{CLONE}/run_1step.log'
if os.path.exists(dia):
    try:
        done = os.path.exists(log) and ('ROMS/TOMS: DONE' in open(log, errors='replace').read())
        d = ds(dia)
        ot = [float(t) for t in np.asarray(d['ocean_time'][:])]
        up = np.asarray(d['u_prsgrd'][0], dtype=np.float64)
        vp = np.asarray(d['v_prsgrd'][0], dtype=np.float64)
        d.close()

        def npat(a, b):   # 内点归一化形状 L∞（PREREG §5 A2b）
            ai, bi = a[IN3], b[IN3]
            return float(np.max(np.abs(ai / np.max(np.abs(ai)) - bi / np.max(np.abs(bi)))))

        dup, dvp = up - RP.colmean(up, Hzu)[None], vp - RP.colmean(vp, Hzv)[None]
        anch['A2b'] = dict(
            present=True, done=bool(done), nrec=len(ot), ocean_time=ot,
            binary_sha256=(sha256(f'{CLONE}/coawstM_goai_rest')
                           if os.path.exists(f'{CLONE}/coawstM_goai_rest') else None),
            pat_dev_linf_u=npat(devu, dup), pat_dev_linf_v=npat(devv, dvp),       # 判定量
            pat_raw_linf_u=npat(au, up), pat_raw_linf_v=npat(av, vp),             # 记录（含耦合替换，预期不等）
            scale_dev_u=float(np.max(np.abs(dup[IN3])) / np.max(np.abs(devu[IN3]))),
            scale_dev_v=float(np.max(np.abs(dvp[IN3])) / np.max(np.abs(devv[IN3]))))
    except Exception as e:
        anch['A2b'] = dict(present=True, done=False, error=repr(e))
else:
    anch['A2b'] = dict(present=False)
R['anchors'] = anch

# ---------- S1 四档陡度 ----------
R['S1_tiers'] = {}
for t in TIERS:
    h, x, m, dxg = load_grid(f'{PGE}/pge_grid_{t}.nc')
    R['S1_tiers'][t] = field_norms(h, x, dxg, RP.rho_manufactured, m)

# ---------- S2 同步加密（解析高斯族） ----------
R['S2_refine'] = {}
for name, L in (('smooth', 20000.0), ('steep', 4000.0)):
    row = dict(E=[], rx0=[], grids=[])
    for Npt, Nz, dxg in ((48, 13, 2000.0), (96, 26, 1000.0), (192, 52, 500.0)):
        h, x = RP.gauss_seamount(Npt, dxg, L)
        z_r, z_w, Hz = RP.set_depth_v2(h, N=Nz)
        X3 = np.broadcast_to(x[None, None, :], z_r.shape)
        a_u, a_v = RP.prsgrd31_sdj(RP.rho_manufactured(X3, z_r), z_r, z_w, Hz, dxg, dxg)
        x_u = 0.5 * (x[1:] + x[:-1])
        z_u = 0.5 * (z_r[:, :, 1:] + z_r[:, :, :-1])
        a_tru = RP.a_x_true(np.broadcast_to(x_u[None, None, :], z_u.shape), z_u)
        L2u, _ = RP.norms_u(a_u, a_tru, Hz, dxg, dxg)
        row['E'].append(L2u)
        row['rx0'].append(RP.rx0_of(h))
        row['grids'].append([Npt, Nz, dxg])
    row['p12'] = float(np.log2(row['E'][0] / row['E'][1]))
    row['p23'] = float(np.log2(row['E'][1] / row['E'][2]))
    R['S2_refine'][name] = row

# ---------- S3 旋钮判决数字 ----------
orig = field_norms(h_s, x_s, dx_s, RP.rho_manufactured, m_s)
flat = field_norms(h_f, x_f, dx_f, RP.rho_manufactured, m_f)
refsub = field_norms(h_s, x_s, dx_s,
                     lambda X_, Z_: RP.rho_manufactured(X_, Z_) - RP.rho_reference_z(Z_), m_s)
# 管线自检：同输入两次调用逐位一致（黏性/缩短积分不是算子输入的机械佐证）
z_r, z_w, Hz = RP.set_depth_v2(h_s)
X3 = np.broadcast_to(x_s[None, None, :], z_r.shape)
a1, _ = RP.prsgrd31_sdj(RP.rho_manufactured(X3, z_r), z_r, z_w, Hz, dx_s, dx_s)
a2, _ = RP.prsgrd31_sdj(RP.rho_manufactured(X3, z_r), z_r, z_w, Hz, dx_s, dx_s)
R['S3_knobs'] = dict(
    E_orig=orig, E_flat=flat, E_refsub=refsub,
    ratio_flat=flat['EL2_u'] / orig['EL2_u'],
    ratio_refsub=refsub['EL2_u'] / orig['EL2_u'],
    selfcheck_bitwise=bool(np.array_equal(a1, a2)),
    visc_visible=dict(day1_umax3d_abs_cm=[um[0.0], um[2747.0]], ratio=um[0.0] / um[2747.0],
                      pointer='e56/E56_BH93.json [bathy=r26steep, VISC2=0/2747].u_max'),
    note='黏性/缩短积分不是算子输入：解析论证记 0（不计真预测）；口径见 PREREG §3 S3/§8.8')

json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('落盘', OUT)

# ---------- 描述性图（不参与判分） ----------
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    xs = [R['S1_tiers'][t]['rx0'] for t in TIERS]
    ax[0].plot(xs, [R['S1_tiers'][t]['EL2_u'] for t in TIERS], 'o-', label='E_L2 (u, nonzero truth)')
    ax[0].plot(xs, [R['S1_tiers'][t]['ELinf_v'] for t in TIERS], 's--', label='E_Linf (v, spurious)')
    ax[0].set_xlabel('rx0')
    ax[0].set_ylabel('operator error [m/s^2]')
    ax[0].set_yscale('log')
    ax[0].legend(fontsize=8)
    for name, mk in (('smooth', 'o-'), ('steep', 's--')):
        r = R['S2_refine'][name]
        ax[1].plot([g[2] for g in r['grids']], r['E'], mk,
                   label=f"{name} p12={r['p12']:.2f} p23={r['p23']:.2f}")
    ax[1].set_xlabel('dx [m] (N doubled with dx halved)')
    ax[1].set_ylabel('E_L2 (u) [m/s^2]')
    ax[1].set_xscale('log')
    ax[1].set_yscale('log')
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f'{FIN}/fig_mms_operator.png', dpi=150)
    print('落盘 fig_mms_operator.png')
except Exception as e:
    R['meta']['notes'].append(f'fig failed: {e}')
    json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False)
