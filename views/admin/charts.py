"""Matplotlib chart helpers for admin dashboard / reports — Modern & Premium styling."""
from __future__ import annotations

import math
from datetime import datetime

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as path_effects

from resources import theme as T


# ---------------------------------------------------------------------------
# Tooltip & Palette Constants
# ---------------------------------------------------------------------------
_TT_BG = "#2F2A24"
_TT_FG = "#FFFFFF"
_TT_FONT = 9
_TT_PAD = 6

# Curated palette matching NGOKAF TRANS design system
CHART_COLORS = [
    "#8C6A00",  # Theme Primary Gold
    "#2563EB",  # Royal Blue
    "#10B981",  # Emerald Green
    "#F59E0B",  # Warm Amber
    "#7C3AED",  # Vibrant Purple
    "#EC4899",  # Modern Pink
    "#14B8A6",  # Teal
    "#F97316",  # Orange
]


def _fmt_amount(v: float) -> str:
    """Format a monetary value with space-separated thousands and FC suffix."""
    return f"{int(v):,} FC".replace(",", " ")


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
class ChartCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=3, dpi=110, parent=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=T.BG_CARD)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=1.2)
        self._hover_cids: list[int] = []

    def clear_plot(self) -> None:
        for cid in self._hover_cids:
            self.mpl_disconnect(cid)
        self._hover_cids.clear()

        self.ax.clear()
        self.ax.set_facecolor(T.BG_CARD)
        for spine in self.ax.spines.values():
            spine.set_color(T.BORDER)


# ---------------------------------------------------------------------------
# Shared axes styling
# ---------------------------------------------------------------------------
def style_axes(ax) -> None:
    ax.set_facecolor(T.BG_CARD)
    ax.tick_params(colors=T.TEXT_SECONDARY, labelsize=8.5, length=3)
    ax.xaxis.label.set_color(T.TEXT_SECONDARY)
    ax.yaxis.label.set_color(T.TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(T.BORDER)
        spine.set_linewidth(0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", alpha=0.3, color=T.BORDER, linestyle="--", linewidth=0.7)


# ---------------------------------------------------------------------------
# 1) LINE CHART — Revenus avec courbe douce & surface ombragée
# ---------------------------------------------------------------------------
def plot_line_revenue(canvas: ChartCanvas, dates, values, title: str = "Revenus") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)
    xs = [d.strftime("%d/%m") if hasattr(d, "strftime") else str(d) for d in dates]
    ys = [float(v) for v in values]

    if not xs:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                color=T.TEXT_SECONDARY, transform=ax.transAxes, fontsize=10)
        canvas.draw_idle()
        return

    # Line plot with smooth styling
    line, = ax.plot(
        range(len(xs)), ys, color=T.PRIMARY, linewidth=2.5,
        marker="o", markersize=5, markerfacecolor="#FFFFFF", markeredgecolor=T.PRIMARY,
        markeredgewidth=1.8, zorder=5
    )
    ax.fill_between(range(len(xs)), ys, color=T.PRIMARY, alpha=0.15, zorder=3)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    if len(xs) > 10:
        step = max(1, len(xs) // 8)
        ax.set_xticks(range(0, len(xs), step))
        ax.set_xticklabels([xs[i] for i in range(0, len(xs), step)], rotation=25, ha="right")
    else:
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, rotation=25, ha="right")

    # Hover elements
    vline = ax.axvline(x=0, color=T.PRIMARY, linestyle="--", linewidth=1, alpha=0.6, visible=False)
    dot, = ax.plot([], [], "o", color=T.PRIMARY, markersize=8, markerfacecolor="#FFFFFF",
                   markeredgewidth=2.5, zorder=10, visible=False)
    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    def _on_move(event):
        if event.inaxes != ax:
            _hide()
            return
        xi = round(event.xdata) if event.xdata is not None else None
        if xi is None or xi < 0 or xi >= len(ys):
            _hide()
            return
        vline.set_xdata([xi, xi])
        vline.set_visible(True)
        dot.set_data([xi], [ys[xi]])
        dot.set_visible(True)
        tooltip.xy = (xi, ys[xi])
        tooltip.set_text(f" {xs[xi]}\n {_fmt_amount(ys[xi])} ")
        tooltip.set_visible(True)
        canvas.draw_idle()

    def _hide():
        vline.set_visible(False)
        dot.set_visible(False)
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _hide())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 2) DONUT CHART — Design moderne avec anneau & résumé au centre
# ---------------------------------------------------------------------------
def plot_donut(canvas: ChartCanvas, labels, values, title: str = "Répartition") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    vals = [float(v) for v in values]
    total = sum(vals)

    if total <= 0:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                color=T.TEXT_SECONDARY, fontsize=10)
        ax.set_axis_off()
        canvas.draw_idle()
        return

    colors = CHART_COLORS[:len(vals)]
    wedges, texts, autotexts = ax.pie(
        vals,
        labels=None,
        autopct="%1.0f%%",
        colors=colors,
        wedgeprops=dict(width=0.35, edgecolor=T.BG_CARD, linewidth=2.5),
        startangle=90,
        pctdistance=0.78,
    )
    for t in autotexts:
        t.set_fontsize(8.5)
        t.set_color("#FFFFFF")
        t.set_fontweight("bold")

    # Center text showing total
    ax.text(0, 0, f"TOTAL\n{_fmt_amount(total)}", ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=T.PRIMARY_ALT)

    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15),
              ncol=min(len(labels), 3), fontsize=8.5, frameon=False)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(14, 14), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    orig_fc = [w.get_facecolor() for w in wedges]

    def _on_move(event):
        if event.inaxes != ax:
            _reset()
            return
        hit_any = False
        for i, w in enumerate(wedges):
            contains, _ = w.contains(event)
            if contains:
                hit_any = True
                for j, ww in enumerate(wedges):
                    fc = list(orig_fc[j])
                    fc[3] = 1.0 if j == i else 0.35
                    ww.set_facecolor(fc)
                pct = vals[i] / total * 100
                tooltip.xy = (event.xdata, event.ydata)
                tooltip.set_text(f" {labels[i]}\n {_fmt_amount(vals[i])} ({pct:.1f}%) ")
                tooltip.set_visible(True)
                break
        if not hit_any:
            _reset()
        canvas.draw_idle()

    def _reset():
        for j, ww in enumerate(wedges):
            ww.set_facecolor(orig_fc[j])
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _reset())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 3) BAR CHART — Barres élégantes avec valeurs au-dessus
# ---------------------------------------------------------------------------
def plot_bars(canvas: ChartCanvas, labels, values, title: str = "Ventes") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)
    vals = [float(v) for v in values]

    if not vals or sum(vals) <= 0:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                transform=ax.transAxes, color=T.TEXT_SECONDARY, fontsize=10)
        canvas.draw_idle()
        return

    bars = ax.bar(range(len(vals)), vals, color=T.PRIMARY, width=0.55, edgecolor="none", zorder=4)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8.5)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")
    max_val = max(vals)
    ax.set_ylim(0, max_val * 1.18 if max_val > 0 else 10)

    for b, v in zip(bars, vals):
        if v:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + (max_val * 0.02),
                    f"{int(v):,}".replace(",", " "),
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=T.PRIMARY_ALT)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(0, 14), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, ha="center", fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    full_labels = list(labels)

    def _on_move(event):
        if event.inaxes != ax:
            _reset()
            return
        hit_any = False
        for i, b in enumerate(bars):
            contains, _ = b.contains(event)
            if contains:
                hit_any = True
                for j, bb in enumerate(bars):
                    bb.set_alpha(1.0 if j == i else 0.35)
                tooltip.xy = (b.get_x() + b.get_width() / 2, b.get_height())
                tooltip.set_text(f" {full_labels[i]}\n {_fmt_amount(vals[i])} ")
                tooltip.set_visible(True)
                break
        if not hit_any:
            _reset()
        canvas.draw_idle()

    def _reset():
        for b in bars:
            b.set_alpha(1.0)
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _reset())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 4) HEATMAP CHART — Affluence par heure et par jour
# ---------------------------------------------------------------------------
def plot_heatmap(canvas: ChartCanvas, heatmap_data: list[tuple[int, int, int]], title: str = "Affluence par Heure / Jour") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)

    grid = [[0.0] * 24 for _ in range(7)]
    for db_day, hour, count in heatmap_data:
        day_idx = (db_day - 2) % 7
        if 0 <= day_idx < 7 and 0 <= hour < 24:
            grid[day_idx][hour] += count

    im = ax.imshow(grid, cmap="YlOrBr", aspect="auto", interpolation="nearest")
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    days_labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    ax.set_yticks(range(7))
    ax.set_yticklabels(days_labels, fontsize=8.5)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}h" for h in range(0, 24, 2)], fontsize=8.5)
    ax.grid(False)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    def _on_move(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            tooltip.set_visible(False)
            canvas.draw_idle()
            return
        col = int(math.floor(event.xdata + 0.5))
        row = int(math.floor(event.ydata + 0.5))
        if 0 <= row < 7 and 0 <= col < 24:
            val = grid[row][col]
            tooltip.xy = (col, row)
            tooltip.set_text(f" {days_labels[row]} à {col:02d}h\n {int(val)} billet(s) ")
            tooltip.set_visible(True)
        else:
            tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: tooltip.set_visible(False))
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 5) COMPARATIVE LINE CHART
# ---------------------------------------------------------------------------
def plot_comparative_line(canvas: ChartCanvas, current_values: list[float], prev_values: list[float], title: str = "Comparatif de Revenus") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)

    n = len(current_values)
    if n == 0:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                transform=ax.transAxes, color=T.TEXT_SECONDARY, fontsize=10)
        canvas.draw_idle()
        return

    xs = list(range(n))
    ax.plot(xs, current_values, color=T.PRIMARY, linewidth=2.5, label="Période actuelle", zorder=5)
    ax.plot(xs, prev_values, color="#9CA3AF", linewidth=1.8, linestyle="--", label="Période précédente", zorder=4)

    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    if n > 1:
        step = max(1, n // 6)
        ax.set_xticks(range(0, n, step))
        ax.set_xticklabels([f"J-{n - i}" for i in range(0, n, step)], fontsize=8.5)
    else:
        ax.set_xticks([0])
        ax.set_xticklabels(["Aujourd'hui"], fontsize=8.5)

    vline = ax.axvline(x=0, color=T.PRIMARY, linestyle="--", linewidth=1, alpha=0.5, visible=False)
    dot_curr, = ax.plot([], [], "o", color=T.PRIMARY, markersize=7, visible=False, zorder=10)
    dot_prev, = ax.plot([], [], "o", color="#9CA3AF", markersize=6, visible=False, zorder=9)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    def _on_move(event):
        if event.inaxes != ax or event.xdata is None:
            _hide()
            return
        xi = int(round(event.xdata))
        if 0 <= xi < n:
            vline.set_xdata([xi, xi])
            vline.set_visible(True)

            dot_curr.set_data([xi], [current_values[xi]])
            dot_curr.set_visible(True)
            dot_prev.set_data([xi], [prev_values[xi]])
            dot_prev.set_visible(True)

            tooltip.xy = (xi, current_values[xi])
            txt = f" Jour {xi + 1}\n Actuel: {_fmt_amount(current_values[xi])}\n Précédent: {_fmt_amount(prev_values[xi])} "
            tooltip.set_text(txt)
            tooltip.set_visible(True)
        else:
            _hide()
        canvas.draw_idle()

    def _hide():
        vline.set_visible(False)
        dot_curr.set_visible(False)
        dot_prev.set_visible(False)
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _hide())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 6) FILLING RATE CHART — Taux de remplissage horizontal
# ---------------------------------------------------------------------------
def plot_filling_rate(canvas: ChartCanvas, routes: list[str], rates: list[float], title: str = "Taux de Remplissage Moyen") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)

    if not routes:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                transform=ax.transAxes, color=T.TEXT_SECONDARY, fontsize=10)
        canvas.draw_idle()
        return

    ys = list(range(len(routes)))
    colors = []
    for r in rates:
        if r >= 75:
            colors.append("#10B981")  # Emerald Green
        elif r >= 40:
            colors.append(T.PRIMARY)  # Gold
        else:
            colors.append("#EF4444")  # Alert Red

    bars = ax.barh(ys, rates, color=colors, height=0.52, zorder=4)
    ax.set_yticks(ys)
    ax.set_yticklabels(routes, fontsize=8.5)
    ax.set_xlim(0, 115)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    ax.axvline(x=100, color="#EF4444", linestyle=":", linewidth=1.2, alpha=0.7)

    for b, r in zip(bars, rates):
        ax.text(b.get_width() + 1.5, b.get_y() + b.get_height() / 2, f"{r:.1f}%",
                va="center", ha="left", fontsize=8, fontweight="bold", color=T.TEXT_PRIMARY)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    def _on_move(event):
        if event.inaxes != ax:
            _reset()
            return
        hit_any = False
        for i, b in enumerate(bars):
            contains, _ = b.contains(event)
            if contains:
                hit_any = True
                for j, bb in enumerate(bars):
                    bb.set_alpha(1.0 if j == i else 0.35)
                tooltip.xy = (event.xdata, b.get_y() + b.get_height() / 2)
                tooltip.set_text(f" {routes[i]}\n Remplissage: {rates[i]:.1f}% ")
                tooltip.set_visible(True)
                break
        if not hit_any:
            _reset()
        canvas.draw_idle()

    def _reset():
        for b in bars:
            b.set_alpha(1.0)
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _reset())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()


# ---------------------------------------------------------------------------
# 7) HORIZONTAL BAR CHART — Top Caissiers / Performance
# ---------------------------------------------------------------------------
def plot_horizontal_bars(canvas: ChartCanvas, labels: list[str], values: list[float], title: str = "Ventes par Caissier") -> None:
    canvas.clear_plot()
    ax = canvas.ax
    style_axes(ax)

    if not values:
        ax.text(0.5, 0.5, "Aucune donnée disponible", ha="center", va="center",
                transform=ax.transAxes, color=T.TEXT_SECONDARY, fontsize=10)
        canvas.draw_idle()
        return

    ys = list(range(len(labels)))
    bars = ax.barh(ys, values, color=T.PRIMARY, height=0.52, zorder=4)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8.5)

    max_val = max(values)
    ax.set_xlim(0, max_val * 1.18 if max_val > 0 else 1000)
    ax.set_title(title, color=T.PRIMARY_ALT, fontsize=11.5, fontweight="bold", pad=12, loc="left")

    for b, v in zip(bars, values):
        ax.text(b.get_width() + (max_val * 0.01), b.get_y() + b.get_height() / 2, f"{_fmt_amount(v)}",
                va="center", ha="left", fontsize=8, fontweight="bold", color=T.PRIMARY_ALT)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        fontsize=_TT_FONT, color=_TT_FG, fontweight="bold",
        bbox=dict(boxstyle=f"round,pad={_TT_PAD / 10}", fc=_TT_BG, ec="none", alpha=0.94),
        zorder=20, visible=False,
    )

    def _on_move(event):
        if event.inaxes != ax:
            _reset()
            return
        hit_any = False
        for i, b in enumerate(bars):
            contains, _ = b.contains(event)
            if contains:
                hit_any = True
                for j, bb in enumerate(bars):
                    bb.set_alpha(1.0 if j == i else 0.35)
                tooltip.xy = (event.xdata, b.get_y() + b.get_height() / 2)
                tooltip.set_text(f" {labels[i]}\n {_fmt_amount(values[i])} ")
                tooltip.set_visible(True)
                break
        if not hit_any:
            _reset()
        canvas.draw_idle()

    def _reset():
        for b in bars:
            b.set_alpha(1.0)
        tooltip.set_visible(False)
        canvas.draw_idle()

    cid1 = canvas.mpl_connect("motion_notify_event", _on_move)
    cid2 = canvas.mpl_connect("axes_leave_event", lambda e: _reset())
    canvas._hover_cids.extend([cid1, cid2])

    canvas.fig.tight_layout(pad=1.2)
    canvas.draw_idle()
