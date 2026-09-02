#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""复赛报告 md -> docx (宋体正文/黑体标题, 图与图注按锚点插入)"""
import re, docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
F='/home/xinyuan/比赛/赛道三赛题二/复赛/'
FIG1='/home/xinyuan/比赛/赛道三赛题二/figs/'
FIG2='/data/xinyuan/GOAI_ai4s_env/e44/figs/'
import sys
SRC=sys.argv[1] if len(sys.argv)>1 else '报告_完整合成稿_v3.md'
OUT=sys.argv[2] if len(sys.argv)>2 else '科学发现与环境定义报告_v3.docx'
md=open(F+SRC).read()
d=docx.Document()
for s in d.sections:
    s.top_margin=s.bottom_margin=Cm(2.0); s.left_margin=s.right_margin=Cm(2.2)
st=d.styles['Normal']; st.font.name='Times New Roman'; st.font.size=Pt(10.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')
def para(t,size=10.5,bold=False,ea='宋体',space=4,align=None,color=None,italic=False):
    p=d.add_paragraph()
    parts=re.split(r'(\*\*[^*]+\*\*)',t)
    for part in parts:
        if not part: continue
        b=part.startswith('**') and part.endswith('**')
        r=p.add_run(part[2:-2] if b else part)
        r.font.size=Pt(size); r.font.bold=(bold or b); r.font.italic=italic
        r.font.name='Times New Roman'; r.element.rPr.rFonts.set(qn('w:eastAsia'),ea)
        if color: r.font.color.rgb=RGBColor(*color)
    p.paragraph_format.space_after=Pt(space)
    p.paragraph_format.line_spacing=1.28
    if align: p.alignment=align
    return p
def table(rows_):
    cells=[[c.strip() for c in r.strip().strip('|').split('|')] for r in rows_ if not re.match(r'^\s*\|?\s*-{2,}',r)]
    if not cells: return
    ncol=max(len(r) for r in cells)
    tb=d.add_table(rows=len(cells),cols=ncol); tb.style='Table Grid'
    for i,row in enumerate(cells):
        for j in range(ncol):
            cell=tb.cell(i,j); cell.text=''
            pr=cell.paragraphs[0]; run=pr.add_run(row[j] if j<len(row) else '')
            run.font.size=Pt(9); run.font.bold=(i==0); run.font.name='Times New Roman'; run.element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')
    d.add_paragraph().paragraph_format.space_after=Pt(2)
def fig(path,cap,width=15.5):
    p=d.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path,width=Cm(width))
    para(cap,9,ea='宋体',space=8,color=(70,70,70))
CAPFIG={'图 1':FIG1+'fig_truth_sigma_vs_z.png','图 2':FIG1+'fig_env.png',
        '图 3':FIG1+'fig_llm.png','图 4':FIG1+'fig_metric.png'}
E44CAP=('图 5　内潮环境三轴扫描（84 km，同相位口径，末帧版）。(a) 500 km 隐藏锚：B 样条节点距 2/4/6 档的'
 '逐垂向模态远场功率保留比——第一模全档≈1.00，第二模 0.94→0.68→0.47；(b) 同一轴上 84 km 的三个可见读数'
 '（相对最轻档）：u/v 比值单调爬升报警，深层残余流缓降"变好看"，环带波功率（仅作环境内游戏分数）坠落；'
 '(c) 双谐波黏性八档与 (d) B 样条强度七档：残余流一路变好看，功率在 (d) 自 ×2 档后穿零反向，u/v 比值两轴'
 '均单调报警（黏性轴最低两档一处约 3% 回落，如实呈现）。')
CAP_PAR='''图 2　排序力 A 与抗刷率 B 的双目标平面（风驱环境全部 15376 个候选）。(a) 灰点为全体候选，蓝点为两关同时通过者（204 个），橙线为 Pareto 前沿（5 点），紫星为乌托邦角 (1,1)——实测为空；虚线/点线为本文阈值 A≥0.7 / B≥0.9。knee 为前沿上到两端连线垂距最大的折中点，它在风驱环境两关全过，却不在跨内潮的 13 个交集里。(b) 阈值敏感性：A、B 阈值组合下的通过数，蓝框为本文口径。两关 Spearman = −0.674，两关同过 204 个而独立期望 2159 个（贫化 10.6 倍）。'''
CAP_KB='''图 1　kill board：四把代表尺子 + 隐藏真值对照行 × 九项审计 + R 对照列。A9 为 Beckmann & Haidvogel (1993) 静止态海山检验；R 列为领域现行的 LLM 评审判据（内部逻辑/量纲/物理范围/文献接地）——四把尺子全过 R，而 A1–A9 把它们全杀。† 残余流行：风驱侧为 deep_rms_800，内潮侧为 deep_dc_rms。行：环带波功率（我们论文头条）、深层残余流、深水温度（内潮穷举三轴满分冠军，实为 ≈4 °C 的深水温度本身）、u/v 比值（风驱穷举冠军）、隐藏真值（对照）。每格判定按 KILLBOARD.json 的 rules 字段判读，格内为关键数与出处；python scorecard.py 一键重生成。'''
CAP_E52='''图 2　转向经向风后的判据得分与交集计数。(a) u/v 与 v/u 在纬向风、经向风下的排序力（−ρ，对隐藏技巧评分，越高越好）与配对抗刷分率；虚线为判据阈值 A 0.7 / B 0.9。(b) 三个环境各自通过判据的候选数与两两、三重交集（对数轴，风驱空间 15376 / 内潮 19600）；竖线为独立随机判据的期望——三重交集 0 与期望 0.71 无差别，纬向∩内潮与经向∩内潮贫化、纬向∩经向富集 16 倍。'''
CAP_E44='''图 3　内潮三轴扫描（84 km，同相位口径，末帧版；(b) 的 m=5、(c) 的 5e7/2e8、(d) 的 ×½/×2/×8 为预注册后加密臂）。(a) 500 km 自参照模态锚：第一模全档≈1.00，第二模 0.94→0.68→0.47；(b–d) 三条旋钮轴上的可见读数（相对基准档）：u/v 单调报警、残余流变好看、环带功率坠落并在 (d) 穿零——但见图 1 后续审计。'''
lines=md.split('\n')
i=0
while i<len(lines):
    ln=lines[i].rstrip()
    if not ln: i+=1; continue
    if ln.startswith('> '):
        if ('v4' in SRC or 'v5' in SRC or 'v6' in SRC) and not ln.startswith('> 初赛定稿'):
            para(ln[2:],10.5,ea='楷体',space=6,color=(60,60,60),italic=True)
        i+=1; continue
    if ln.startswith('|'):
        blk=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            blk.append(lines[i]); i+=1
        table(blk); continue
    if ln=='---': i+=1; continue
    m=re.match(r'^(#{1,3}) (.+)$',ln)
    if m:
        lvl=len(m.group(1)); t=m.group(2)
        if lvl==1 and t.startswith('谁来给尺子打分'):
            para(t,16,True,'黑体',10,WD_ALIGN_PARAGRAPH.CENTER)
        elif lvl==2 and t.startswith('复赛'):
            para(t,11,True,'黑体',8,WD_ALIGN_PARAGRAPH.CENTER,color=(90,90,90))
        elif lvl==1:
            para(t,14,True,'黑体',8)
        else:
            para(t,12 if lvl==2 else 11,True,'黑体',6)
        if lvl==1 and t.startswith('第四问') and 'v5' not in SRC:
            if 'v4' in SRC:
                fig(FIG2+'fig_killboard_print.png','图 1　kill board：四把代表尺子 + 隐藏真值对照行 × 九项审计 + R 对照列。A9 为 Beckmann & Haidvogel (1993) 静止态海山检验；R 列为领域现行的 LLM 评审判据（内部逻辑/量纲/物理范围/文献接地）——四把尺子全过 R，而 A1–A9 把它们全杀。† 残余流行：风驱侧为 deep_rms_800，内潮侧为 deep_dc_rms。行：环带波功率（我们论文头条）、深层残余流、深水温度（内潮穷举三轴满分冠军，实为 ≈4 °C 的深水温度本身）、u/v 比值（风驱穷举冠军）、隐藏真值（对照）。每格判定按 KILLBOARD.json 的 rules 字段判读，格内为关键数与出处；python scorecard.py 一键重生成。',14.5)
                fig(FIG2+'fig_e52.png','图 2　转向经向风后的判据得分与交集计数。(a) u/v 与 v/u 在纬向风、经向风下的排序力（−ρ，对隐藏技巧评分，越高越好）与配对抗刷分率；虚线为判据阈值 A 0.7 / B 0.9。(b) 三个环境各自通过判据的候选数与两两、三重交集（对数轴，风驱空间 15376 / 内潮 19600）；竖线为独立随机判据的期望——三重交集 0 与期望 0.71 无差别，纬向∩内潮与经向∩内潮贫化、纬向∩经向富集 16 倍。',15.0)
                fig(FIG2+'fig_e44_main.png','图 3　内潮三轴扫描（84 km，同相位口径，末帧版；(b) 的 m=5、(c) 的 5e7/2e8、(d) 的 ×½/×2/×8 为预注册后加密臂）。(a) 500 km 自参照模态锚：第一模全档≈1.00，第二模 0.94→0.68→0.47；(b–d) 三条旋钮轴上的可见读数（相对基准档）：u/v 单调报警、残余流变好看、环带功率坠落并在 (d) 穿零——但见图 1 后续审计。',15.5)
            else:
                fig(FIG2+'fig_e44_main.png',E44CAP,15.5)
        i+=1; continue
    cm=re.match(r'^(图 \d)　',ln)
    if cm and cm.group(1) in CAPFIG:
        pth=CAPFIG.pop(cm.group(1))
        pp=d.add_paragraph(); pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pp.add_run().add_picture(pth,width=Cm(12.5))
        para(ln,9,ea='宋体',space=8,color=(70,70,70))
        i+=1; continue
    para(ln,10.5)
    if ('v5' in SRC or 'v6' in SRC) and ln.startswith('**参照系**'):
        fig(FIG2+'fig_killboard_print.png',CAP_KB,14.5)
        if 'v6' in SRC: fig(FIG2+'fig_pareto.png',CAP_PAR,15.5)
        fig(FIG2+'fig_e52.png',CAP_E52,15.0); fig(FIG2+'fig_e44_main.png',CAP_E44,15.5)
    i+=1
# ---- 附录合订 (v5) ----
if 'v5' in SRC:
    from docx.enum.text import WD_BREAK
    def page_break(): d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    def md_block(text):
        ls=text.split('\n'); k=0
        while k<len(ls):
            ln=ls[k].rstrip()
            if not ln or ln=='---': k+=1; continue
            mm=re.match(r'^(#{1,3}) (.+)$',ln)
            if mm: para(mm.group(2),13 if len(mm.group(1))==1 else 11.5,True,'黑体',6); k+=1; continue
            if ln.startswith('|'):
                blk=[]
                while k<len(ls) and ls[k].strip().startswith('|'): blk.append(ls[k]); k+=1
                table(blk); continue
            if ln.startswith('> '): para(ln[2:],10,ea='楷体',space=4,color=(80,80,80),italic=True); k+=1; continue
            para(ln,10.5); k+=1
    page_break(); para('附录 A · 初赛定稿正文（原文，2026-08-16 提交版）',14,True,'黑体',8)
    md_block(open(F+'初赛终稿_提取.txt').read())
    page_break(); md_block(open(F+'附录B_实验表.md').read())
    page_break(); md_block(open(F+'附录C_ARENA规格.md').read())
    # 页码
    from docx.oxml import OxmlElement
    for sec in d.sections:
        fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        run=fp.add_run(); 
        for tag,txt_ in (('begin',None),('instr','PAGE'),('end',None)):
            if tag=='instr':
                el=OxmlElement('w:instrText'); el.set(qn('xml:space'),'preserve'); el.text='PAGE'
            else:
                el=OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'),tag)
            run._r.append(el)
        run.font.size=Pt(9)
d.save(F+OUT)
print('docx saved')
