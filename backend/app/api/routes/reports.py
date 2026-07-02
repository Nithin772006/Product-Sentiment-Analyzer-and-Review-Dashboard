"""
app/api/routes/reports.py
─────────────────────────
Export endpoints to generate CSV, Excel, and PDF reports of product reviews
and sentiment analysis datasets.

PDF export generates a premium business-analytics-style report with:
  • Gradient header with product info, stars, and sentiment emoji
  • KPI summary cards
  • Donut-style pie chart for sentiment distribution
  • Horizontal progress bars
  • Colour-coded review table (green / yellow / red rows)
  • Keyword pill tags
  • Pros & Cons cards
  • Overall Recommendation card
  • Per-page header banner + footer with page numbers
"""

from __future__ import annotations

import io
import math
import textwrap
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import StreamingResponse

# ── ReportLab ─────────────────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.graphics.shapes import Drawing, Wedge, String, Circle, Rect
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.piecharts import Pie
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Spacer,
    Paragraph,
    KeepTogether,
    Flowable,
    HRFlowable,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.sentiment_repository import SentimentRepository

router = APIRouter(prefix="/reports", tags=["reports"])

# ── Colour palette ─────────────────────────────────────────────────────────────
C_PRIMARY   = colors.HexColor("#4F46E5")
C_SECONDARY = colors.HexColor("#6366F1")
C_GRAD_END  = colors.HexColor("#7C3AED")
C_POSITIVE  = colors.HexColor("#22C55E")
C_NEUTRAL   = colors.HexColor("#FACC15")
C_NEGATIVE  = colors.HexColor("#EF4444")
C_BG        = colors.HexColor("#F8FAFC")
C_CARD      = colors.white
C_TEXT      = colors.HexColor("#1E293B")
C_MUTED     = colors.HexColor("#64748B")
C_GOLD      = colors.HexColor("#F59E0B")
C_GREEN_BG  = colors.HexColor("#DCFCE7")
C_YELLOW_BG = colors.HexColor("#FEF9C3")
C_RED_BG    = colors.HexColor("#FEE2E2")
C_BORDER    = colors.HexColor("#E2E8F0")

PAGE_W, PAGE_H = A4          # 595.28 x 841.89 pt
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


# ══════════════════════════════════════════════════════════════════════════════
#  Helper utilities
# ══════════════════════════════════════════════════════════════════════════════

def _stars(rating: float, max_stars: int = 5) -> str:
    """Return a filled/empty star string like ★★★★☆."""
    full  = int(round(rating))
    empty = max_stars - full
    return "★" * full + "☆" * empty


def _sentiment_emoji(pos_pct: float) -> str:
    if pos_pct >= 60:
        return "😊"
    elif pos_pct >= 35:
        return "😐"
    return "😡"


def _rating_label(avg: float) -> tuple[str, object]:
    """Return (label, colour) based on average rating."""
    if avg >= 4.5:
        return "Excellent Product", C_POSITIVE
    elif avg >= 3.5:
        return "Good Product", colors.HexColor("#16A34A")
    elif avg >= 2.5:
        return "Average Product", C_NEUTRAL
    return "Needs Improvement", C_NEGATIVE


def _overall_score(avg_rating: float, pos_pct: float) -> int:
    """Compute an overall product score 0-100."""
    return min(100, int(avg_rating / 5.0 * 60 + pos_pct * 0.40))


def _recommendation_text(pos_pct: float, avg_rating: float, product_name: str) -> str:
    short = product_name[:40] + "..." if len(product_name) > 40 else product_name
    if pos_pct >= 70:
        return (
            f'"{short}" has received overwhelmingly positive customer feedback. '
            f"Users highly appreciate its quality, performance, and value. "
            f"With an average rating of {avg_rating:.1f}/5.0, this product comes Highly Recommended."
        )
    elif pos_pct >= 45:
        return (
            f'"{short}" shows a generally positive reception with some mixed opinions. '
            f"Most customers are satisfied with the product at {avg_rating:.1f}/5.0 stars."
        )
    return (
        f'"{short}" has received mixed-to-negative feedback. '
        f"Significant concerns have been raised by reviewers. "
        f"Consider improvements based on the negative feedback themes highlighted above."
    )


def _truncate(text: str, limit: int = 110) -> str:
    return text[:limit] + "..." if len(text) > limit else text


def _pill_colors(idx: int) -> tuple:
    """Cycle through a set of pill background/text colors."""
    palettes = [
        (colors.HexColor("#EDE9FE"), colors.HexColor("#5B21B6")),
        (colors.HexColor("#DBEAFE"), colors.HexColor("#1D4ED8")),
        (colors.HexColor("#DCFCE7"), colors.HexColor("#166534")),
        (colors.HexColor("#FEF9C3"), colors.HexColor("#854D0E")),
        (colors.HexColor("#FCE7F3"), colors.HexColor("#9D174D")),
        (colors.HexColor("#FFEDD5"), colors.HexColor("#9A3412")),
        (colors.HexColor("#F0FDF4"), colors.HexColor("#14532D")),
        (colors.HexColor("#EFF6FF"), colors.HexColor("#1E40AF")),
    ]
    return palettes[idx % len(palettes)]


# ══════════════════════════════════════════════════════════════════════════════
#  Custom Flowables
# ══════════════════════════════════════════════════════════════════════════════

class RoundedCard(Flowable):
    """A rounded-rectangle card with a title bar and body content lines."""

    def __init__(self, width, height, title, lines,
                 title_bg=C_PRIMARY, title_fg=colors.white,
                 body_bg=C_CARD, border_color=C_BORDER,
                 radius=6, padding=8):
        super().__init__()
        self.width  = width
        self.height = height
        self.title  = title
        self.lines  = lines          # list of (text, font, size, colour)
        self.title_bg     = title_bg
        self.title_fg     = title_fg
        self.body_bg      = body_bg
        self.border_color = border_color
        self.radius  = radius
        self.padding = padding

    def draw(self):
        c = self.canv
        r = self.radius
        w, h = self.width, self.height
        title_h = 22

        # Shadow
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.roundRect(2, -2, w, h, r, fill=1, stroke=0)

        # Card body
        c.setFillColor(self.body_bg)
        c.setStrokeColor(self.border_color)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, r, fill=1, stroke=1)

        # Title bar
        c.setFillColor(self.title_bg)
        c.roundRect(0, h - title_h, w, title_h, r, fill=1, stroke=0)
        # square off bottom corners of title bar
        c.rect(0, h - title_h, w, title_h / 2, fill=1, stroke=0)

        c.setFillColor(self.title_fg)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.padding, h - title_h + 7, self.title)

        # Body lines
        y = h - title_h - self.padding
        for text, font, size, colour in self.lines:
            y -= size + 3
            c.setFont(font, size)
            c.setFillColor(colour)
            c.drawString(self.padding, y, str(text))


class KPIGrid(Flowable):
    """6 KPI cards drawn in a 3-column grid."""

    CARD_W = CONTENT_W / 3 - 5
    CARD_H = 72

    def __init__(self, kpis, width=CONTENT_W):
        super().__init__()
        self.kpis  = kpis   # list of dicts: {label, value, icon, color}
        self.width = width
        cols = 3
        rows = math.ceil(len(kpis) / cols)
        self.height = rows * (self.CARD_H + 8)

    def draw(self):
        c   = self.canv
        cw  = self.CARD_W
        ch  = self.CARD_H
        gap = 8
        cols = 3

        for i, kpi in enumerate(self.kpis):
            col = i % cols
            row = i // cols
            x = col * (cw + gap)
            y = self.height - (row + 1) * (ch + gap) + gap

            accent = kpi.get("color", C_PRIMARY)

            # Shadow
            c.setFillColor(colors.HexColor("#CBD5E1"))
            c.roundRect(x + 2, y - 2, cw, ch, 6, fill=1, stroke=0)

            # Card bg
            c.setFillColor(C_CARD)
            c.setStrokeColor(C_BORDER)
            c.setLineWidth(0.5)
            c.roundRect(x, y, cw, ch, 6, fill=1, stroke=1)

            # Left accent stripe
            c.setFillColor(accent)
            c.roundRect(x, y, 5, ch, 3, fill=1, stroke=0)

            # Icon circle background
            icon_bg = colors.HexColor(
                "#" + "".join(f"{min(255,int(v*255)+40):02X}"
                              for v in accent.rgb())
            )
            c.setFillColor(icon_bg)
            c.circle(x + cw - 22, y + ch / 2, 14, fill=1, stroke=0)

            # Icon (emoji)
            c.setFillColor(accent)
            c.setFont("Helvetica-Bold", 12)
            icon = kpi.get("icon", "●")
            c.drawCentredString(x + cw - 22, y + ch / 2 - 5, icon)

            # Value (big number)
            c.setFillColor(C_TEXT)
            c.setFont("Helvetica-Bold", 18)
            c.drawString(x + 10, y + ch / 2 + 2, str(kpi["value"]))

            # Label
            c.setFillColor(C_MUTED)
            c.setFont("Helvetica", 7)
            c.drawString(x + 10, y + ch / 2 - 12, kpi["label"])

            # Bottom subtle bg strip
            c.setFillColor(colors.HexColor("#F1F5F9"))
            c.rect(x + 5, y + 1, cw - 10, 14, fill=1, stroke=0)
            c.setFillColor(accent)
            c.setFont("Helvetica-Oblique", 6)
            c.drawString(x + 10, y + 5, kpi.get("sublabel", ""))


class StarRating(Flowable):
    """Big gold star rating display with label."""

    def __init__(self, avg_rating, width=CONTENT_W):
        super().__init__()
        self.avg    = avg_rating
        self.width  = width
        self.height = 90

    def draw(self):
        c = self.canv
        w = self.width

        # Card
        c.setFillColor(C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=1)

        # Shadow
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.roundRect(2, -2, w, self.height, 8, fill=1, stroke=0)
        c.setFillColor(C_CARD)
        c.roundRect(0, 0, w, self.height, 8, fill=1, stroke=0)

        # Stars
        star_str = _stars(self.avg)
        c.setFillColor(C_GOLD)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(w / 2, self.height - 42, star_str)

        # Numeric rating
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w / 2, self.height - 62, f"{self.avg:.1f} / 5.0")

        # Label
        label, colour = _rating_label(self.avg)
        c.setFillColor(colour)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, self.height - 78, label)


class SentimentPieChart(Flowable):
    """Pie chart using ReportLab graphics with legend."""

    def __init__(self, pos, neu, neg, width=CONTENT_W, height=160):
        super().__init__()
        self.pos    = pos
        self.neu    = neu
        self.neg    = neg
        self.width  = width
        self.height = height

    def draw(self):
        c   = self.canv
        w   = self.width
        h   = self.height
        total = self.pos + self.neu + self.neg or 1

        # Card bg
        c.setFillColor(C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12, h - 18, "😊 Sentiment Distribution")

        pie_r  = 52
        pie_cx = w * 0.28
        pie_cy = h / 2 - 8

        # Build a Drawing with a Pie chart
        d = Drawing(w, h)
        pie = Pie()
        pie.x       = pie_cx - pie_r
        pie.y       = pie_cy - pie_r
        pie.width   = pie_r * 2
        pie.height  = pie_r * 2
        pie.data    = [self.pos, self.neu, self.neg]
        pie.labels  = [
            f"{self.pos/total*100:.0f}%",
            f"{self.neu/total*100:.0f}%",
            f"{self.neg/total*100:.0f}%",
        ]
        pie.slices[0].fillColor    = C_POSITIVE
        pie.slices[1].fillColor    = C_NEUTRAL
        pie.slices[2].fillColor    = C_NEGATIVE
        pie.slices.strokeColor     = colors.white
        pie.slices.strokeWidth     = 1.5
        pie.simpleLabels           = False
        pie.slices[0].labelRadius  = 1.35
        pie.slices[1].labelRadius  = 1.35
        pie.slices[2].labelRadius  = 1.35

        # Donut effect: white circle in centre
        hole = Circle(pie_cx, pie_cy, pie_r * 0.45)
        hole.fillColor   = C_CARD
        hole.strokeColor = C_CARD

        d.add(pie)
        d.add(hole)

        # Centre emoji
        centre_text = String(pie_cx - 7, pie_cy - 5, _sentiment_emoji(self.pos / total * 100))
        centre_text.fontName = "Helvetica-Bold"
        centre_text.fontSize = 16
        d.add(centre_text)

        renderPDF.draw(d, c, 0, 0)

        # Legend on the right
        legend_x = w * 0.58
        legend_items = [
            ("😊 Positive", self.pos, C_POSITIVE, C_GREEN_BG),
            ("😐 Neutral",  self.neu, C_NEUTRAL,  C_YELLOW_BG),
            ("😡 Negative", self.neg, C_NEGATIVE, C_RED_BG),
        ]
        ly = h - 48
        for label, count, accent, bg in legend_items:
            # Pill bg
            c.setFillColor(bg)
            c.roundRect(legend_x - 4, ly - 5, w - legend_x - 8, 18, 4, fill=1, stroke=0)
            c.setFillColor(accent)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(legend_x, ly + 2, label)
            pct = count / total * 100
            c.setFillColor(C_TEXT)
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(w - 14, ly + 2, f"{count}  ({pct:.1f}%)")
            ly -= 26


class ProgressBars(Flowable):
    """Horizontal progress bars for sentiment %."""

    def __init__(self, pos_pct, neu_pct, neg_pct, width=CONTENT_W, height=110):
        super().__init__()
        self.pos_pct = pos_pct
        self.neu_pct = neu_pct
        self.neg_pct = neg_pct
        self.width   = width
        self.height  = height

    def _draw_bar(self, c, x, y, w, h, label, pct, bar_color, bg_color):
        bar_w = w - 90  # reserve space for label and number

        # Label
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y + 4, label)

        bx = x + 75
        # Track bg
        c.setFillColor(colors.HexColor("#E2E8F0"))
        c.roundRect(bx, y, bar_w, h, h / 2, fill=1, stroke=0)

        # Fill
        filled = max(4, bar_w * pct / 100)
        c.setFillColor(bar_color)
        c.roundRect(bx, y, filled, h, h / 2, fill=1, stroke=0)

        # Pct text
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(x + w, y + 4, f"{pct:.1f}%")

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        # Card
        c.setFillColor(C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12, h - 18, "📊 Review Statistics")

        bar_h   = 12
        spacing = 26
        start_y = h - 42

        bars = [
            ("😊 Positive", self.pos_pct, C_POSITIVE, C_GREEN_BG),
            ("😐 Neutral",  self.neu_pct, C_NEUTRAL,  C_YELLOW_BG),
            ("😡 Negative", self.neg_pct, C_NEGATIVE, C_RED_BG),
        ]
        for label, pct, color, bg in bars:
            self._draw_bar(c, 12, start_y, w - 24, bar_h, label, pct, color, bg)
            start_y -= spacing


class KeywordPills(Flowable):
    """Colourful keyword tag cloud."""

    PILL_H  = 16
    PILL_PD = 7   # horizontal padding per side
    GAP     = 5
    LINE_H  = 24

    def __init__(self, keywords, width=CONTENT_W, title="🔑 Top Keywords"):
        super().__init__()
        self.keywords = keywords  # list of str
        self.width    = width
        self.title    = title
        # Pre-calculate layout rows
        self._rows = self._layout()
        self.height = 32 + len(self._rows) * self.LINE_H + 16

    def _pill_width(self, word: str) -> float:
        # Approximate: each char ≈ 5.5pt at font 8
        return len(word) * 5.5 + self.PILL_PD * 2 + 6

    def _layout(self):
        rows = []
        row  = []
        row_w = 0
        avail = self.width - 24  # inner padding
        for i, kw in enumerate(self.keywords):
            pw = self._pill_width(kw)
            if row_w + pw + self.GAP > avail and row:
                rows.append(row)
                row  = [(i, kw, pw)]
                row_w = pw
            else:
                row.append((i, kw, pw))
                row_w += pw + self.GAP
        if row:
            rows.append(row)
        return rows

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        # Card
        c.setFillColor(C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Title
        c.setFillColor(C_TEXT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(12, h - 18, self.title)

        y = h - 34
        for row in self._rows:
            x = 12
            for idx, kw, pw in row:
                bg, fg = _pill_colors(idx)
                c.setFillColor(bg)
                c.roundRect(x, y - self.PILL_H + 3, pw, self.PILL_H, self.PILL_H / 2, fill=1, stroke=0)
                c.setFillColor(fg)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(x + self.PILL_PD, y - 7, kw)
                x += pw + self.GAP
            y -= self.LINE_H


class ProsConsCard(Flowable):
    """Side-by-side Pros (green) and Cons (red) card."""

    def __init__(self, pros, cons, width=CONTENT_W, height=None):
        super().__init__()
        self.pros  = pros[:6]
        self.cons  = cons[:6]
        self.width = width
        rows = max(len(self.pros), len(self.cons))
        self.height = height or (rows * 16 + 58)

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height
        hw = w / 2 - 4

        # Outer card
        c.setFillColor(C_CARD)
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 8, fill=1, stroke=1)

        # Pros header
        c.setFillColor(C_POSITIVE)
        c.roundRect(4, h - 26, hw, 22, 5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(10, h - 18, "✅ Most Mentioned Positives")

        # Cons header
        c.setFillColor(C_NEGATIVE)
        c.roundRect(hw + 8, h - 26, hw, 22, 5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(hw + 14, h - 18, "❌ Most Mentioned Negatives")

        # Pros items
        py = h - 42
        for item in self.pros:
            c.setFillColor(C_POSITIVE)
            c.circle(12, py + 3, 3, fill=1, stroke=0)
            c.setFillColor(C_TEXT)
            c.setFont("Helvetica", 8)
            c.drawString(18, py, _truncate(item.capitalize(), 28))
            py -= 15

        # Cons items
        cy = h - 42
        for item in self.cons:
            c.setFillColor(C_NEGATIVE)
            c.circle(hw + 16, cy + 3, 3, fill=1, stroke=0)
            c.setFillColor(C_TEXT)
            c.setFont("Helvetica", 8)
            c.drawString(hw + 22, cy, _truncate(item.capitalize(), 28))
            cy -= 15

        # Divider
        c.setStrokeColor(C_BORDER)
        c.setLineWidth(0.5)
        c.line(hw + 6, 8, hw + 6, h - 30)


class RecommendationCard(Flowable):
    """Overall recommendation card with score and trophy."""

    def __init__(self, score, rec_text, pos_pct, width=CONTENT_W, height=110):
        super().__init__()
        self.score    = score
        self.rec_text = rec_text
        self.pos_pct  = pos_pct
        self.width    = width
        self.height   = height

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        # Gradient simulation (layered rects)
        steps = 20
        for i in range(steps):
            t  = i / steps
            r1, g1, b1 = 0x4F/255, 0x46/255, 0xE5/255
            r2, g2, b2 = 0x7C/255, 0x3A/255, 0xED/255
            r  = r1 + (r2 - r1) * t
            g  = g1 + (g2 - g1) * t
            b  = b1 + (b2 - b1) * t
            c.setFillColorRGB(r, g, b)
            bx = w * (i / steps)
            bw = w / steps + 1
            c.roundRect(bx, 0, bw, h, 8 if i == 0 else 0, fill=1, stroke=0)

        # Trophy icon area
        c.setFillColor(colors.HexColor("#FBBF24"))
        c.circle(38, h / 2, 24, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(38, h / 2 - 8, "🏆")

        # Score
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 28)
        c.drawString(76, h - 36, f"{self.score}/100")

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#C4B5FD"))
        c.drawString(76, h - 48, "🏆 Overall Product Score")

        # Sentiment label
        if self.pos_pct >= 60:
            badge_txt = "😊 Recommended"
            badge_color = C_POSITIVE
        elif self.pos_pct >= 35:
            badge_txt = "😐 Moderately Recommended"
            badge_color = C_NEUTRAL
        else:
            badge_txt = "😡 Not Recommended"
            badge_color = C_NEGATIVE

        c.setFillColor(badge_color)
        c.roundRect(76, h - 68, 120, 14, 5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(80, h - 60, badge_txt)

        # Recommendation text wrapped
        wrapped = textwrap.wrap(self.rec_text, width=68)
        ty = h - 84
        for line in wrapped[:3]:
            c.setFillColor(colors.HexColor("#E0E7FF"))
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(76, ty, line)
            ty -= 10


# ══════════════════════════════════════════════════════════════════════════════
#  Page header / footer drawn on every page via onPage callback
# ══════════════════════════════════════════════════════════════════════════════

class _PDFState:
    """Mutable state passed into the page callback closures."""
    def __init__(self):
        self.page_count = 0   # filled in after build via setPageCount


def _make_header_footer(product_name: str, brand: str, avg_rating: float,
                        pos_pct: float, export_date: str,
                        state: _PDFState, total_pages_ref: list):

    HEADER_H = 58 * mm

    def draw_header_footer(canv: pdf_canvas.Canvas, doc):
        canv.saveState()

        # ── Gradient header ───────────────────────────────────────────────────
        steps = 40
        for i in range(steps):
            t  = i / steps
            r1, g1, b1 = 0x4F/255, 0x46/255, 0xE5/255
            r2, g2, b2 = 0x7C/255, 0x3A/255, 0xED/255
            r  = r1 + (r2 - r1) * t
            g  = g1 + (g2 - g1) * t
            b  = b1 + (b2 - b1) * t
            canv.setFillColorRGB(r, g, b)
            bx = PAGE_W * (i / steps)
            bw = PAGE_W / steps + 1
            canv.rect(bx, PAGE_H - HEADER_H, bw, HEADER_H, fill=1, stroke=0)

        # White overlay strip at bottom of header
        canv.setFillColor(colors.white)
        canv.rect(0, PAGE_H - HEADER_H - 1, PAGE_W, 4, fill=1, stroke=0)

        # Product title
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 14)
        title_lines = textwrap.wrap(product_name, width=52)
        ty = PAGE_H - 20 * mm
        for line in title_lines[:2]:
            canv.drawString(MARGIN, ty, line)
            ty -= 14

        # Subtitle info
        canv.setFont("Helvetica", 7)
        canv.setFillColor(colors.HexColor("#C4B5FD"))
        canv.drawString(MARGIN, ty, f"Brand: {brand}   |   Generated: {export_date}   |   Product Sentiment Analyzer")

        # Report label (top right)
        canv.setFillColor(colors.HexColor("#FBBF24"))
        canv.setFont("Helvetica-Bold", 9)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 16 * mm,
                             "Product Sentiment Summary Report")

        # Star rating (top right)
        star_str = _stars(avg_rating)
        canv.setFillColor(C_GOLD)
        canv.setFont("Helvetica-Bold", 12)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 22 * mm,
                             f"{star_str}  {avg_rating:.1f}/5.0")

        # Sentiment emoji
        emoji = _sentiment_emoji(pos_pct)
        canv.setFont("Helvetica-Bold", 16)
        canv.setFillColor(colors.white)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 30 * mm, emoji)

        # ── Footer ────────────────────────────────────────────────────────────
        FOOTER_H = 14 * mm
        # Separator line
        canv.setStrokeColor(C_PRIMARY)
        canv.setLineWidth(1)
        canv.line(MARGIN, FOOTER_H, PAGE_W - MARGIN, FOOTER_H)

        # Footer gradient strip
        for i in range(steps // 2):
            t  = i / (steps // 2)
            r1, g1, b1 = 0x4F/255, 0x46/255, 0xE5/255
            r2, g2, b2 = 0x7C/255, 0x3A/255, 0xED/255
            r  = r1 + (r2 - r1) * t
            g  = g1 + (g2 - g1) * t
            b  = b1 + (b2 - b1) * t
            canv.setFillColorRGB(r, g, b)
            bx = PAGE_W * (i / (steps // 2))
            bw = PAGE_W / (steps // 2) + 1
            canv.rect(bx, 0, bw, FOOTER_H - 1, fill=1, stroke=0)

        canv.setFillColor(colors.white)
        canv.setFont("Helvetica", 7)
        now = datetime.now(tz=timezone.utc)
        canv.drawString(MARGIN, 6 * mm,
                        f"📅 Generated: {now.strftime('%B %d, %Y  %H:%M UTC')}")
        canv.setFont("Helvetica-Bold", 7)
        canv.drawCentredString(PAGE_W / 2, 6 * mm, "Product Sentiment Analyzer")

        # Page number — filled after build; use placeholder string
        page_num = doc.page
        total    = total_pages_ref[0] if total_pages_ref else "?"
        canv.setFont("Helvetica", 7)
        canv.drawRightString(PAGE_W - MARGIN, 6 * mm, f"Page {page_num}")

        canv.restoreState()

    return draw_header_footer


# ══════════════════════════════════════════════════════════════════════════════
#  Helper — compile export dataset (reviews + sentiments joined)
# ══════════════════════════════════════════════════════════════════════════════

async def compile_export_data(product_id: str) -> list[dict]:
    """Compile reviews and sentiments for a specific product into unified dicts."""
    review_repo   = ReviewRepository()
    sentiment_repo = SentimentRepository()

    reviews, _    = await review_repo.find(filter_query={"product_id": product_id}, limit=5000)
    if not reviews:
        return []

    sentiments, _ = await sentiment_repo.find(filter_query={"product_id": product_id}, limit=5000)
    sentiment_map = {s["review_id"]: s for s in sentiments}

    rows = []
    for r in reviews:
        s  = sentiment_map.get(r["id"], {})
        rd = r.get("review_date")
        if hasattr(rd, "isoformat"):
            rd_str = rd.isoformat()
        elif rd:
            rd_str = str(rd)
        else:
            rd_str = ""

        rows.append({
            "Reviewer":          r.get("reviewer") or "Anonymous",
            "Rating":            r.get("rating") or 5,
            "Review Date":       rd_str,
            "Verified Purchase": "Yes" if r.get("verified_purchase") else "No",
            "Source Platform":   r.get("source", "Unknown").capitalize(),
            "Review Text":       r.get("review_text", ""),
            "Sentiment Class":   s.get("sentiment", "neutral").capitalize(),
            "VADER Score":       s.get("vader_compound", 0.0),
            "TextBlob Polarity": s.get("polarity", 0.0),
            "Subjectivity":      s.get("subjectivity", 0.0),
            "Keywords":          s.get("keywords", []),
        })
    return rows


# ══════════════════════════════════════════════════════════════════════════════
#  Routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/export/csv/{product_id}")
async def export_csv(
    product_id: str = Path(..., description="Product ID to export")
) -> StreamingResponse:
    """Export reviews and sentiment scores to a CSV file."""
    product_repo = ProductRepository()
    product      = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)
    if not data:
        raise HTTPException(status_code=400, detail="No reviews available to export")

    df        = pd.DataFrame(data)
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    filename = f"Reviews_Report_{product_id}.csv"
    response = StreamingResponse(iter([csv_bytes]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"]      = str(len(csv_bytes))
    return response


@router.get("/export/excel/{product_id}")
async def export_excel(
    product_id: str = Path(...),
) -> StreamingResponse:
    """Export reviews and sentiment scores to an Excel file."""
    product_repo = ProductRepository()
    product      = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)
    if not data:
        raise HTTPException(status_code=400, detail="No reviews available to export")

    df     = pd.DataFrame(data)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Reviews Data", index=False)

    stream.seek(0)
    excel_bytes = stream.read()
    filename    = f"Reviews_Report_{product_id}.xlsx"
    response = StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"]      = str(len(excel_bytes))
    return response


@router.get("/export/pdf/{product_id}")
async def export_pdf(
    product_id: str = Path(...),
) -> StreamingResponse:
    """
    Export product sentiment analysis as a premium multi-section PDF report.
    Sections:
      0. Header banner (every page)
      1. Executive Summary KPI Cards
      2. Rating Visualization
      3. Sentiment Distribution (Pie Chart)
      4. Review Statistics (Progress Bars)
      5. Sample Reviews Table
      6. Top Keywords (Pill Tags)
      7. Pros & Cons
      8. Overall Recommendation
      9. Footer (every page)
    """
    product_repo   = ProductRepository()
    sentiment_repo = SentimentRepository()

    product = await product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = await compile_export_data(product_id)

    # ── Derived statistics ────────────────────────────────────────────────────
    total_revs = len(data)
    avg_rating = float(product.get("average_rating") or 0.0)
    brand      = product.get("brand") or "Generic"
    category   = product.get("category") or "—"
    prod_name  = product.get("product_name", "Unknown Product")

    pos_count  = sum(1 for r in data if r["Sentiment Class"] == "Positive")
    neu_count  = sum(1 for r in data if r["Sentiment Class"] == "Neutral")
    neg_count  = sum(1 for r in data if r["Sentiment Class"] == "Negative")
    safe_total = total_revs or 1
    pos_pct    = pos_count / safe_total * 100
    neu_pct    = neu_count / safe_total * 100
    neg_pct    = neg_count / safe_total * 100

    # Keyword aggregation per sentiment
    pos_kw: dict[str, int] = {}
    neg_kw: dict[str, int] = {}
    all_kw: dict[str, int] = {}
    for r in data:
        sent = r["Sentiment Class"]
        for kw in r.get("Keywords", []):
            all_kw[kw] = all_kw.get(kw, 0) + 1
            if sent == "Positive":
                pos_kw[kw] = pos_kw.get(kw, 0) + 1
            elif sent == "Negative":
                neg_kw[kw] = neg_kw.get(kw, 0) + 1

    top_keywords = [w for w, _ in sorted(all_kw.items(), key=lambda x: x[1], reverse=True)[:20]]
    top_pros     = [w for w, _ in sorted(pos_kw.items(), key=lambda x: x[1], reverse=True)[:6]]
    top_cons     = [w for w, _ in sorted(neg_kw.items(), key=lambda x: x[1], reverse=True)[:6]]

    score    = _overall_score(avg_rating, pos_pct)
    rec_text = _recommendation_text(pos_pct, avg_rating, prod_name)
    export_date = datetime.now(tz=timezone.utc).strftime("%B %d, %Y")

    # ── Build PDF ─────────────────────────────────────────────────────────────
    pdf_buffer  = io.BytesIO()
    HEADER_H    = 58 * mm
    FOOTER_H    = 14 * mm
    FRAME_TOP   = PAGE_H - HEADER_H - 8 * mm
    FRAME_BOT   = FOOTER_H + 4 * mm

    total_pages_ref = [1]   # will be updated after first pass

    state = _PDFState()
    on_page = _make_header_footer(
        prod_name, brand, avg_rating, pos_pct, export_date,
        state, total_pages_ref,
    )

    doc = BaseDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=HEADER_H + 8 * mm,
        bottomMargin=FOOTER_H + 4 * mm,
    )

    frame = Frame(
        MARGIN, FRAME_BOT,
        CONTENT_W, FRAME_TOP - FRAME_BOT,
        id="main",
    )
    doc.addPageTemplates([
        PageTemplate(id="Page", frames=[frame], onPage=on_page),
    ])

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        borderPadding=(4, 0, 4, 0),
    )
    body_style = ParagraphStyle(
        "BodyText2",
        parent=styles["BodyText"],
        fontSize=8,
        textColor=C_TEXT,
        leading=12,
    )

    elems = []

    # ── Section 1: Executive Summary ──────────────────────────────────────────
    elems.append(Paragraph("1. Executive Summary", section_style))

    kpis = [
        {
            "label":    "Total Reviews",
            "value":    total_revs,
            "icon":     "📦",
            "color":    C_PRIMARY,
            "sublabel": "All scraped reviews",
        },
        {
            "label":    "Average Rating",
            "value":    f"{avg_rating:.2f}",
            "icon":     "⭐",
            "color":    C_GOLD,
            "sublabel": "Out of 5.0 stars",
        },
        {
            "label":    "Positive Ratio",
            "value":    f"{pos_pct:.1f}%",
            "icon":     "😊",
            "color":    C_POSITIVE,
            "sublabel": "Of all reviews",
        },
        {
            "label":    "Neutral Ratio",
            "value":    f"{neu_pct:.1f}%",
            "icon":     "😐",
            "color":    C_NEUTRAL,
            "sublabel": "Of all reviews",
        },
        {
            "label":    "Negative Ratio",
            "value":    f"{neg_pct:.1f}%",
            "icon":     "😡",
            "color":    C_NEGATIVE,
            "sublabel": "Of all reviews",
        },
        {
            "label":    "Reviews Analysed",
            "value":    total_revs,
            "icon":     "💬",
            "color":    C_SECONDARY,
            "sublabel": "NLP classified",
        },
    ]
    elems.append(KPIGrid(kpis))
    elems.append(Spacer(1, 10))

    # ── Section 2: Rating Visualization ───────────────────────────────────────
    elems.append(Paragraph("2. Rating Visualization", section_style))
    elems.append(StarRating(avg_rating))
    elems.append(Spacer(1, 10))

    # ── Section 3: Sentiment Distribution ─────────────────────────────────────
    elems.append(Paragraph("3. Sentiment Distribution", section_style))
    elems.append(SentimentPieChart(pos_count, neu_count, neg_count))
    elems.append(Spacer(1, 10))

    # ── Section 4: Review Statistics ──────────────────────────────────────────
    elems.append(Paragraph("4. Review Statistics", section_style))
    elems.append(ProgressBars(pos_pct, neu_pct, neg_pct))
    elems.append(Spacer(1, 10))

    # ── Section 5: Sample Reviews Table ───────────────────────────────────────
    elems.append(Paragraph("5. Sample Reviews", section_style))

    sample_data = data[:10]

    def _row_bg(sent):
        if sent == "Positive": return C_GREEN_BG
        if sent == "Neutral":  return C_YELLOW_BG
        return C_RED_BG

    def _sent_emoji(sent):
        if sent == "Positive": return "😊 Positive"
        if sent == "Neutral":  return "😐 Neutral"
        return "😡 Negative"

    # Build table data
    tbl_header = ["Reviewer", "Rating", "Sentiment", "Review Summary"]
    tbl_rows   = [tbl_header]
    row_colors = [C_PRIMARY]   # header colour placeholder

    for r in sample_data:
        stars_str = _stars(float(r["Rating"]))
        tbl_rows.append([
            Paragraph(r["Reviewer"][:22], ParagraphStyle("rc", fontSize=7, textColor=C_TEXT, fontName="Helvetica-Bold")),
            Paragraph(stars_str, ParagraphStyle("rs", fontSize=8, textColor=C_GOLD, fontName="Helvetica-Bold")),
            Paragraph(_sent_emoji(r["Sentiment Class"]), ParagraphStyle("rset", fontSize=7, textColor=C_TEXT, fontName="Helvetica-Bold")),
            Paragraph(_truncate(r["Review Text"], 110),
                      ParagraphStyle("rtxt", fontSize=6.5, textColor=C_TEXT, leading=9)),
        ])
        row_colors.append(_row_bg(r["Sentiment Class"]))

    # Column widths
    col_w = [CONTENT_W * 0.17, CONTENT_W * 0.14, CONTENT_W * 0.16, CONTENT_W * 0.53]
    tbl   = Table(tbl_rows, colWidths=col_w, repeatRows=1)

    style_cmds = [
        # Header
        ("BACKGROUND",   (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 7.5),
        ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 6),
        ("TOPPADDING",   (0, 0), (-1, 0), 6),
        # Body
        ("FONTSIZE",     (0, 1), (-1, -1), 7),
        ("ALIGN",        (1, 1), (2, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("GRID",         (0, 0), (-1, -1), 0.3, C_BORDER),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1),
         [_row_bg(sample_data[i]["Sentiment Class"]) for i in range(len(sample_data))]),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)
    elems.append(Spacer(1, 10))

    # ── Section 6: Top Keywords ────────────────────────────────────────────────
    elems.append(Paragraph("6. Top Keywords", section_style))
    if top_keywords:
        elems.append(KeywordPills(top_keywords))
    else:
        elems.append(Paragraph("No keywords extracted.", body_style))
    elems.append(Spacer(1, 10))

    # ── Section 7: Pros & Cons ────────────────────────────────────────────────
    elems.append(Paragraph("7. Pros & Cons", section_style))
    pros_display = top_pros if top_pros else ["No positive keywords extracted"]
    cons_display = top_cons if top_cons else ["No negative keywords extracted"]
    rows_needed  = max(len(pros_display), len(cons_display))
    pc_h         = rows_needed * 16 + 58
    elems.append(ProsConsCard(pros_display, cons_display, height=pc_h))
    elems.append(Spacer(1, 10))

    # ── Section 8: Overall Recommendation ─────────────────────────────────────
    elems.append(Paragraph("8. Overall Recommendation", section_style))
    elems.append(RecommendationCard(score, rec_text, pos_pct))
    elems.append(Spacer(1, 6))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(elems)

    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()

    filename = f"Sentiment_Report_{product_id}.pdf"
    response = StreamingResponse(iter([pdf_bytes]), media_type="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Length"]      = str(len(pdf_bytes))
    return response
