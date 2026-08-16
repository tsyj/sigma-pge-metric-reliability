"""Nature 论文风格（20260816 v3）：
无衬线（Helvetica 系，中文 Noto Sans）、开放式 L 形轴、刻度朝外、npg 配色、无边框柱。
图上只留数据：结论、实验条件一律进 caption。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Nature npg 调色板
RED, BLUE, TEAL, GREEN = "#E64B35", "#3C5488", "#4DBBD5", "#00A087"
ORANGE, PURPLE, GRAY = "#F39B7F", "#8491B4", "#97A1A9"


def paper_style():
    for cand in ("Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK HK"):
        if any(f.name == cand for f in font_manager.fontManager.ttflist):
            plt.rcParams["font.sans-serif"] = [cand, "DejaVu Sans"]
            break
    plt.rcParams.update({
        "axes.unicode_minus": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": "#333333", "axes.linewidth": 0.9,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 3.5, "ytick.major.size": 3.5,
        "xtick.major.width": 0.9, "ytick.major.width": 0.9,
        "xtick.color": "#333333", "ytick.color": "#333333",
        "xtick.labelcolor": "#1a1a1a", "ytick.labelcolor": "#1a1a1a",
        "axes.labelcolor": "#1a1a1a", "text.color": "#1a1a1a",
        "font.size": 12.5, "axes.labelsize": 13.5,
        "xtick.labelsize": 12, "ytick.labelsize": 12,
        "legend.fontsize": 12, "legend.frameon": False,
        "axes.grid": False, "savefig.dpi": 300,
        "lines.solid_capstyle": "round",
    })


def panel(ax, s):
    """Nature 面板标记：小写粗体 a b c，置于面板左上角外侧。"""
    s = s.strip("()（）")
    ax.text(-0.16, 1.04, s, transform=ax.transAxes, fontsize=17,
            fontweight="bold", va="bottom", ha="left")
