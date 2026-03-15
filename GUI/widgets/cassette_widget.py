"""
cassette_widget.py  —  Spotify Desktop Control v3.0
"""
from __future__ import annotations
import math, random
from typing import Optional

from PySide6.QtCore    import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui     import (
    QColor, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath, QPixmap, QFont, QFontMetrics,
)
from PySide6.QtWidgets import QWidget, QSizePolicy


def _hsl(h: float, s: float, l: float, a: float = 1.0) -> QColor:
    c = QColor.fromHslF((h / 360) % 1, s / 100, l / 100)
    c.setAlphaF(max(0.0, min(1.0, a)))
    return c

def _ms(ms: int) -> str:
    if not ms or ms <= 0: return "--:--"
    s = int(ms / 1000)
    return f"{s // 60:02d}:{s % 60:02d}"

def _elide(p: QPainter, text: str, max_w: float) -> str:
    return p.fontMetrics().elidedText(text, Qt.ElideRight, int(max_w))


class _Eq:
    N = 20
    def __init__(self):
        self.v    = [random.uniform(0.06, 0.22) for _ in range(self.N)]
        self.peak = list(self.v)
        self.hold = [0] * self.N

    def step(self):
        for i in range(self.N):
            self.v[i] += random.uniform(-0.13, 0.20)
            self.v[i]  = max(0.03, min(1.0, self.v[i]))
            if self.v[i] >= self.peak[i]:
                self.peak[i] = self.v[i]; self.hold[i] = 18
            elif self.hold[i] > 0: self.hold[i] -= 1
            else: self.peak[i] = max(self.v[i], self.peak[i] - 0.022)

    def freeze(self):
        for i in range(self.N):
            self.v[i]   *= 0.84
            self.peak[i] = max(self.v[i], self.peak[i] * 0.90)


class CassetteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(480, 340)

        self._hue          : float             = 220.0
        self._title        : str               = ""
        self._artist       : str               = ""
        self._progress_ms  : int               = 0
        self._duration_ms  : int               = 0
        self._is_playing   : bool              = False
        self._album_pixmap : Optional[QPixmap] = None

        self._reel_angle   : float = 0.0
        self._tape_sag     : float = 0.0
        self._eq           = _Eq()

        # ── RGB hue self-cycles at ~30 fps — no external call needed ──────
        self._rgb_timer = QTimer(self)
        self._rgb_timer.setInterval(33)
        self._rgb_timer.timeout.connect(self._rgb_tick)
        self._rgb_timer.start()

        # ── animation timer (reels + EQ) ──────────────────────────────────
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start()

    # ── RGB self-cycle ──────────────────────────────────────────────────────

    def _rgb_tick(self):
        # 0.4 degrees per frame × 30 fps ≈ full cycle every ~30 seconds
        self._hue = (self._hue + 0.4) % 360
        self.update()

    # ── animation tick ──────────────────────────────────────────────────────

    def _anim_tick(self):
        if self._is_playing:
            self._reel_angle = (self._reel_angle + 5) % 360
            self._tape_sag  += 0.08
            self._eq.step()
        else:
            self._eq.freeze()

    # ── public API ──────────────────────────────────────────────────────────

    def set_hue(self, hue: float):
        """Optional external override — keeps external callers working."""
        self._hue = hue % 360.0

    def set_rgb_sync(self, accent: QColor, hue: float = 0.0):
        self.set_hue(hue)

    def update_track(self, title, artist, album, progress_ms, duration_ms, genre_hint=None):
        self._title        = title or ""
        self._artist       = artist or ""
        self._progress_ms  = progress_ms or 0
        self._duration_ms  = duration_ms or 0
        self.update()

    def set_playing_state(self, playing: bool):
        self._is_playing = playing
        self.update()

    def set_album_art(self, pixmap: Optional[QPixmap]):
        self._album_pixmap = pixmap
        self.update()

    def set_playing(self, playing: bool):
        self.set_playing_state(playing)

    def update_info(self, t, a, al, p, d, m="default"):
        self.update_track(t, a, al, p, d, m)

    # ── paint ───────────────────────────────────────────────────────────────

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        try:
            W, H = self.width(), self.height()
            if W < 20 or H < 20:
                return

            CW   = min(W - 32, 460)
            CH   = min(H - 100, 232)
            CX   = (W - CW) // 2
            CY   = 12
            h    = self._hue
            frac = self._progress_ms / max(1, self._duration_ms)

            self._body     (p, CX, CY, CW, CH, h)
            self._label    (p, CX, CY, CW, CH, h)
            self._album_art_square(p, CX, CY, CW, CH, h)
            self._tape_win (p, CX, CY, CW, CH, h, frac)
            self._screws   (p, CX, CY, CW, CH, h)
            self._bottom   (p, CX, CY, CW, CH, h)
            self._eq_bars  (p, CX, CY + CH + 14, CW, 32, h)
            self._progress (p, CX, CY + CH + 54, CW, h, frac)

        except Exception:
            import traceback; traceback.print_exc()
        finally:
            p.end()

    # ── shell ───────────────────────────────────────────────────────────────

    def _body(self, p, bx, by, bw, bh, h):
        r = 16
        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, bw, bh), r, r)

        # shadow
        p.save(); p.translate(3, 5)
        p.fillPath(path, QColor(0, 0, 0, 80))
        p.restore()

        # shell fill — keyed to _hue
        p.fillPath(path, _hsl(h, 62, 38))

        # top gloss
        gp = QPainterPath()
        gp.addRoundedRect(QRectF(bx, by, bw, 32), r, r)
        gg = QLinearGradient(bx, by, bx, by + 32)
        gg.setColorAt(0, QColor(255, 255, 255, 30))
        gg.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(gp, QBrush(gg))

        p.setPen(QPen(QColor(255, 255, 255, 15), 1.0))
        p.setBrush(Qt.NoBrush)
        ip = QPainterPath()
        ip.addRoundedRect(QRectF(bx+1, by+1, bw-2, bh-2), r-1, r-1)
        p.drawPath(ip)

    # ── label (stripes + text only — no album art here) ─────────────────────

    def _label(self, p, bx, by, bw, bh, h):
        LM       = 26
        LX       = bx + LM
        LY       = by + 14
        LW       = bw - LM * 2
        BOTTOM_H = 46
        LH       = bh - 14 - BOTTOM_H
        LR       = 8

        lp = QPainterPath()
        lp.addRoundedRect(QRectF(LX, LY, LW, LH), LR, LR)
        p.fillPath(lp, QColor("#f0ede8"))
        p.setPen(QPen(QColor(0, 0, 0, 28), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawPath(lp)

        # ── diagonal stripes (bottom-left fan) ────────────────────────────
        p.save()
        p.setClipPath(lp)
        ox, oy = LX, LY + LH
        stripes = [(h + 30, 85, 62, 44), (h + 15, 90, 52, 32), (h, 85, 40, 24)]
        offset  = 0
        for sh, ss, sl, sw in stripes:
            sp = QPainterPath()
            sp.moveTo(ox + offset,           oy)
            sp.lineTo(ox + offset + sw,      oy)
            sp.lineTo(ox + offset + sw + LH, oy - LH)
            sp.lineTo(ox + offset + LH,      oy - LH)
            sp.closeSubpath()
            p.fillPath(sp, _hsl(sh, ss, sl))
            offset += sw
        p.restore()

        # ── C-60 badge top-right ───────────────────────────────────────────
        p.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Bold))
        p.setPen(_hsl(h, 55, 22))
        fm         = p.fontMetrics()
        badge_text = "C-60"
        badge_x    = int(LX + LW - LM - fm.horizontalAdvance(badge_text))
        p.drawText(badge_x, int(LY + 26), badge_text)

        # ── track / artist text in white zone ─────────────────────────────
        tx = ox + offset + LH + 12
        tw = (LX + LW - LM) - tx
        if tw > 20:
            p.setFont(QFont("Helvetica Neue", 9, QFont.Weight.Bold))
            p.setPen(QColor(0, 0, 0, 165))
            p.drawText(int(tx), int(LY + LH // 2 - 4),
                       _elide(p, self._title or "No track", tw))
            p.setFont(QFont("Helvetica Neue", 8))
            p.setPen(QColor(0, 0, 0, 100))
            p.drawText(int(tx), int(LY + LH // 2 + 10),
                       _elide(p, self._artist, tw))

    # ── album art square — centred above the tape window ────────────────────

    def _album_art_square(self, p, bx, by, bw, bh, h):
        """
        Draw a small square album art thumbnail centred horizontally,
        sitting just above the tape window inside the label area.
        Falls back to a plain dark square with a music note if no art loaded.
        """
        LM       = 26
        LX       = bx + LM
        LY       = by + 14
        LW       = bw - LM * 2
        BOTTOM_H = 46
        LH       = bh - 14 - BOTTOM_H

        # tape window top-y (same formula as _tape_win)
        WY = LY + LH - 64

        # square: 54×54, centred, sitting 8 px above the tape window
        SZ  = 54
        sx  = int(LX + LW / 2 - SZ / 2)
        sy  = int(WY - SZ - 8)

        if sy < LY + 6:
            return   # not enough vertical space

        art_rect = QRectF(sx, sy, SZ, SZ)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(art_rect, 5, 5)

        p.save()
        p.setClipPath(clip_path)

        if self._album_pixmap and not self._album_pixmap.isNull():
            # scale to fill the square (crop edges)
            scaled = self._album_pixmap.scaled(
                SZ, SZ,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            # centre-crop
            ox2 = (scaled.width()  - SZ) // 2
            oy2 = (scaled.height() - SZ) // 2
            p.drawPixmap(int(sx), int(sy),
                         scaled, ox2, oy2, SZ, SZ)
            # subtle dark vignette overlay
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, 40)))
            p.drawRect(art_rect)
        else:
            # placeholder: dark square + music note glyph
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_hsl(h, 30, 20)))
            p.drawRect(art_rect)
            p.setFont(QFont("Helvetica Neue", 20))
            p.setPen(_hsl(h, 40, 55))
            p.drawText(art_rect.toRect(), Qt.AlignCenter, "♪")

        p.restore()

        # border ring around the square — matches the shell hue
        p.setPen(QPen(_hsl(h, 60, 55), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(clip_path)

    # ── tape window ──────────────────────────────────────────────────────────

    def _tape_win(self, p, bx, by, bw, bh, h, frac):
        LM       = 26
        LX, LY   = bx + LM, by + 14
        LW       = bw - LM * 2
        BOTTOM_H = 46
        LH       = bh - 14 - BOTTOM_H
        WX, WY   = LX + 16, LY + LH - 64
        WW, WH   = LW - 32, 54

        wp = QPainterPath()
        wp.addRoundedRect(QRectF(WX, WY, WW, WH), 5, 5)
        p.fillPath(wp, _hsl((h + 180) % 360, 50, 28))
        p.setPen(QPen(QColor(0, 0, 0, 60), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(wp)

        cx, cy = WX + WW / 2, WY + WH / 2

        # magnetic head
        THW, THH = 50, 36
        THX, THY = cx - THW / 2, cy - THH / 2
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#d8d8d8")))
        hp = QPainterPath()
        hp.addRoundedRect(QRectF(THX, THY, THW, THH), 3, 3)
        p.drawPath(hp)
        p.setPen(QPen(QColor(0, 0, 0, 55), 0.9))
        for i in range(1, 7):
            lx = THX + i * (THW / 7)
            p.drawLine(QPointF(lx, THY + 4), QPointF(lx, THY + THH - 4))

        # capstan pins
        for px2 in [THX - 10, THX + THW + 10]:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_hsl(h, 30, 60)))
            p.drawEllipse(QRectF(px2 - 5, cy - 5, 10, 10))
            p.setPen(QPen(QColor(0, 0, 0, 50), 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(px2 - 5, cy - 5, 10, 10))

        # reels
        RS  = 21
        lrx = cx - WW * 0.31
        rrx = cx + WW * 0.31
        rry = cy - 1
        self._reel(p, lrx, rry, RS, 1 - frac,  self._reel_angle * (1 + frac * 0.5), h)
        self._reel(p, rrx, rry, RS,     frac,  -self._reel_angle * (1 - frac * 0.4), h)

        # tape strand
        ty    = rry + RS - 5
        sag   = 4 * math.sin(self._tape_sag) if self._is_playing else 0
        strand = QPainterPath()
        strand.moveTo(lrx, ty)
        strand.quadTo(cx, ty + sag, rrx, ty)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(40, 22, 8, 180), 3.0))
        p.drawPath(strand)
        p.setPen(QPen(QColor(110, 70, 30, 120), 1.5))
        p.drawPath(strand)

    def _reel(self, p, cx, cy, rs, tape_frac, angle, h):
        to = rs - 2
        ti = max(6, to - int(4 + tape_frac * 10))
        p.save()
        p.translate(cx, cy)
        p.rotate(angle)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#b0b0b8")))
        p.drawEllipse(QRectF(-rs, -rs, rs*2, rs*2))
        p.setPen(QPen(QColor(0,0,0,50), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-rs, -rs, rs*2, rs*2))

        p.setBrush(Qt.NoBrush)
        for ri in range(ti, to, 2):
            t = (ri - ti) / max(1, to - ti)
            p.setPen(QPen(QColor(int(50+t*30), int(18+t*10), int(5+t*5), 200), 2.2))
            p.drawEllipse(QRectF(-ri, -ri, ri*2, ri*2))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#e4e4e4")))
        p.drawEllipse(QRectF(-ti, -ti, ti*2, ti*2))
        p.setPen(QPen(QColor(0,0,0,30), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-ti, -ti, ti*2, ti*2))

        hub = 7
        p.setPen(QPen(QColor(120, 120, 130, 220), 1.5))
        for i in range(3):
            a = math.radians(i * 120)
            p.drawLine(QPointF(math.cos(a)*(hub+1), math.sin(a)*(hub+1)),
                       QPointF(math.cos(a)*(ti-2),  math.sin(a)*(ti-2)))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#28282e")))
        p.drawEllipse(QRectF(-hub, -hub, hub*2, hub*2))
        p.setPen(QPen(_hsl(h, 60, 55, 0.6), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-hub, -hub, hub*2, hub*2))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor("#0e0e14")))
        p.drawEllipse(QRectF(-3, -3, 6, 6))
        p.restore()

    # ── screws ───────────────────────────────────────────────────────────────

    def _screws(self, p, bx, by, bw, bh, h):
        for sx, sy in [(bx+13, by+13), (bx+bw-13, by+13),
                       (bx+13, by+bh-13), (bx+bw-13, by+bh-13)]:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_hsl(h, 50, 28)))
            p.drawEllipse(QRectF(sx-6, sy-6, 12, 12))
            p.setPen(QPen(QColor(0,0,0,50), 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(sx-6, sy-6, 12, 12))
            p.setPen(QPen(QColor(0,0,0,80), 0.8))
            p.drawLine(QPointF(sx-3, sy), QPointF(sx+3, sy))
            p.drawLine(QPointF(sx, sy-3), QPointF(sx, sy+3))

    # ── bottom bar ───────────────────────────────────────────────────────────

    def _bottom(self, p, bx, by, bw, bh, h):
        bar_y = by + bh - 46
        cx    = bx + bw // 2
        LM    = 26
        p.setPen(QPen(_hsl(h, 45, 28), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(bx + LM, bar_y), QPointF(bx + bw - LM, bar_y))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(_hsl(h, 45, 28)))
        tri = QPainterPath()
        tri.moveTo(bx+22, bar_y+10)
        tri.lineTo(bx+22, bar_y+26)
        tri.lineTo(bx+12, bar_y+18)
        tri.closeSubpath()
        p.drawPath(tri)

        for sx2, sw2 in [(cx-52, 28), (cx-8, 18), (cx+20, 28)]:
            sp2 = QPainterPath()
            sp2.addRoundedRect(QRectF(sx2, bar_y+10, sw2, 18), 3, 3)
            p.fillPath(sp2, _hsl(h, 45, 24))
            p.setPen(QPen(QColor(0,0,0,60), 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawPath(sp2)

        for hx2 in [cx-86, cx+70]:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(_hsl(h, 45, 24)))
            p.drawEllipse(QRectF(hx2-7, bar_y+11, 14, 14))
            p.setPen(QPen(QColor(0,0,0,60), 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QRectF(hx2-7, bar_y+11, 14, 14))

    # ── EQ bars ──────────────────────────────────────────────────────────────

    def _eq_bars(self, p, ex, ey, ew, eh, h):
        N  = self._eq.N
        bw = ew / (N * 1.6)
        gp = bw * 0.6
        for i in range(N):
            bh2 = eh * self._eq.v[i]
            bx2 = ex + i * (bw + gp)
            bg  = QLinearGradient(bx2, ey+eh, bx2, ey+eh-bh2)
            bg.setColorAt(0, _hsl(h, 70, 35, 0.15))
            bg.setColorAt(1, _hsl(h, 80, 60, 0.85))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(bg))
            bp = QPainterPath()
            bp.addRoundedRect(QRectF(bx2, ey+eh-bh2, bw, bh2), 1.5, 1.5)
            p.drawPath(bp)
            pk_y = ey + eh - eh * self._eq.peak[i] - 2
            p.fillRect(int(bx2), int(pk_y), max(1, int(bw)), 2, _hsl(h, 80, 72))

    # ── progress bar + time ───────────────────────────────────────────────────

    def _progress(self, p, px, py, pw, h, frac):
        tp = QPainterPath()
        tp.addRoundedRect(QRectF(px, py, pw, 4), 2, 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 30)))
        p.drawPath(tp)

        if frac > 0:
            fw = max(0, pw * frac)
            fg = QLinearGradient(px, 0, px+fw, 0)
            fg.setColorAt(0, _hsl(h, 70, 35))
            fg.setColorAt(1, _hsl(h, 75, 60))
            fp = QPainterPath()
            fp.addRoundedRect(QRectF(px, py, fw, 4), 2, 2)
            p.setBrush(QBrush(fg))
            p.drawPath(fp)
            p.setBrush(QBrush(QColor(255, 255, 255, 220)))
            p.drawEllipse(QRectF(px+fw-5, py-3, 10, 10))

        f = QFont("Courier New", 9)
        p.setFont(f)
        p.setPen(_hsl(h, 70, 62))
        p.drawText(int(px), int(py+18), _ms(self._progress_ms))
        ts = _ms(self._duration_ms)
        tw = QFontMetrics(f).horizontalAdvance(ts)
        p.drawText(int(px + pw - tw), int(py+18), ts)
