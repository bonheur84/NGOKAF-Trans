"""Matplotlib chart helpers for admin dashboard / reports."""
from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from resources import theme as T


class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=3, dpi=100, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=T.BG_CARD)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=1.2)

    def clear_plot(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor(T.BG_CARD)
        for spine in self.ax.spines.values():
            spine.set_color(T.BORDER)


def style_axes(ax) -> None:
    ax.set_facecolor(T.BG_CARD)
    ax.tick_params(colors=T.TEXT_SECONDARY, labelsize=8)
    ax.xaxis.label.set_color(T.TEXT_SECONDARY)
    ax.yaxis.label.set_color(T.TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(T.BORDER)
    ax.grid(True, axis="y", alpha=0.25, color=T.BORDER)


def plot_line_revenue(canvas: ChartCanvas, dates, values, title: str = "Revenus") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)
    xs = [d.strftime("%d/%m") for d in dates]
    ys = [float(v) for v in values]
    ax.plot(xs, ys, color=T.PRIMARY, linewidth=2, marker="o", markersize=3)
    ax.fill_between(range(len(ys)), ys, color=T.PRIMARY, alpha=0.12)
    ax.set_title(title, color=T.TEXT_PRIMARY, fontsize=11, fontweight="bold")
    if len(xs) > 10:
        step = max(1, len(xs) // 8)
        ax.set_xticks(range(0, len(xs), step))
        ax.set_xticklabels([xs[i] for i in range(0, len(xs), step)], rotation=30, ha="right")
    else:
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, rotation=30, ha="right")
    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


def plot_donut(canvas: ChartCanvas, labels, values, title: str = "Répartition") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    vals = [float(v) for v in values]
    if sum(vals) <= 0:
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", color=T.TEXT_SECONDARY)
        ax.set_axis_off()
        canvas.draw_idle()
        return
    colors = [T.PRIMARY, T.SECONDARY, "#C4A35A", "#6B5B3E", "#D4C4A8"]
    wedges, _texts, autotexts = ax.pie(
        vals,
        labels=None,
        autopct="%1.0f%%",
        colors=colors[: len(vals)],
        wedgeprops=dict(width=0.45, edgecolor=T.BG_CARD),
        startangle=90,
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color(T.TEXT_PRIMARY)
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_title(title, color=T.TEXT_PRIMARY, fontsize=11, fontweight="bold")
    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


def plot_bars(canvas: ChartCanvas, labels, values, title: str = "Ventes") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)
    vals = [float(v) for v in values]
    if not vals:
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", transform=ax.transAxes,
                color=T.TEXT_SECONDARY)
        canvas.draw_idle()
        return
    bars = ax.bar(range(len(vals)), vals, color=T.PRIMARY, width=0.6)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_title(title, color=T.TEXT_PRIMARY, fontsize=11, fontweight="bold")
    for b, v in zip(bars, vals):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(v):,}".replace(",", " "),
                    ha="center", va="bottom", fontsize=7, color=T.TEXT_SECONDARY)
    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()
