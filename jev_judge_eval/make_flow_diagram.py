"""Render the JEV-vs-GPT judge flow diagram as a PNG for the Word report."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = r"d:\Github\ADI\jev_judge_eval\results\flow_jev_vs_gpt.png"

fig, ax = plt.subplots(figsize=(11.2, 7.4), dpi=200)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

GREY = dict(fc="#E8EEF7", ec="#4A6FA5", lw=1.4)
GREEN = dict(fc="#E8F5E9", ec="#2E7D32", lw=1.4)
PURPLE = dict(fc="#F3E8FB", ec="#6A3FB5", lw=1.4)
ORANGE = dict(fc="#FFF3E0", ec="#E65100", lw=1.4)
DARK = dict(fc="#ECEFF1", ec="#37474F", lw=1.4)
ARROW = dict(arrowstyle="-|>", color="#546E7A", lw=1.4, mutation_scale=14)


def box(x, y, w, h, text, style, fontsize=8.6, bold_first=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.012",
                                **style))
    lines = text.split("\n")
    if bold_first and len(lines) > 1:
        ax.text(x, y + (len(lines) - 1) * 0.006, lines[0], ha="center", va="center",
                fontsize=fontsize + 0.6, fontweight="bold")
        rest = "\n".join(lines[1:])
        if rest:
            ax.text(x, y - 0.006, rest, ha="center", va="center", fontsize=fontsize)
    else:
        ax.text(x, y, text, ha="center", va="center", fontsize=fontsize)


def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=ARROW)


# Shared input / preparation
box(0.5, 0.915, 0.40, 0.085, "SME sheet row\nUser Query · ADI Response · Retrieved Context\nSME Yes/No + corrected answer", GREY)
box(0.5, 0.785, 0.46, 0.115, "prepare_rows\nidentical state for every judge:\nquery, response, full context, ordered chunks,\nprior conversation, reference answer", GREY)
arrow(0.5, 0.870, 0.5, 0.846)

# GPT path (left column)
box(0.27, 0.640, 0.36, 0.070, "GPT-4o judge\nRAGAS-style arm (adi_gt_evaluator.py)", GREEN, bold_first=True)
box(0.27, 0.525, 0.38, 0.095, "Prompt: extract factual claims and statements,\nthen judge each one against\ncontext, query and reference answer", GREEN)
box(0.27, 0.410, 0.36, 0.075, "GPT-4o writes a JSON answer\n(temperature 0, via OpenRouter)", GREEN)
box(0.27, 0.292, 0.40, 0.100, "Code maths\nfaithfulness = supported claims ÷ total claims\ncorrectness = 0.75 × factual F1 + 0.25 × semantic similarity", GREEN)
arrow(0.5, 0.724, 0.37, 0.678)  # prep -> GPT head
arrow(0.27, 0.605, 0.27, 0.573)
arrow(0.27, 0.477, 0.27, 0.448)
arrow(0.27, 0.372, 0.27, 0.343)

# JEV path (right column)
box(0.73, 0.640, 0.38, 0.070, "JEV judge\njev-1.13.0 via TypeSafe", PURPLE, bold_first=True)
box(0.73, 0.525, 0.40, 0.095, "One request per row:\nstate + typed Score questions,\neach with fixed ordered answer levels", PURPLE)
box(0.73, 0.410, 0.40, 0.075, "JEV returns a probability for every level\nplus a confidence — no free text", PURPLE)
box(0.73, 0.292, 0.40, 0.100, "Code maths\nraw = Σ level × probability\n0-1 score = raw ÷ highest level\ncorrectness = same 75/25 formula", PURPLE)
arrow(0.5, 0.724, 0.63, 0.678)  # prep -> JEV head
arrow(0.73, 0.605, 0.73, 0.573)
arrow(0.73, 0.477, 0.73, 0.448)
arrow(0.73, 0.372, 0.73, 0.343)

# Shared decision + reporting
box(0.5, 0.150, 0.62, 0.100, "framework_status(value)\nmetric-specific pass / review / fail bands\n(tone and toxicity use a binary 0.5 cut-off)", ORANGE)
box(0.5, 0.030, 0.62, 0.075, "Reports\nquery-level rows · session · sub-product · product · platform aggregates", DARK)
arrow(0.27, 0.241, 0.44, 0.202)
arrow(0.73, 0.241, 0.56, 0.202)
arrow(0.5, 0.100, 0.5, 0.068)

ax.text(0.5, 0.985, "One row, two judges - same 0-1 metrics out", ha="center",
        fontsize=12, fontweight="bold", color="#263238")

plt.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)
