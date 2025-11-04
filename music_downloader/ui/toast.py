from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QLabel


class Toast(QWidget):
    def __init__(self, parent: QWidget, text: str, duration_ms: int = 3000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.label = QLabel(text, self)
        self.label.setStyleSheet(
            "color: white; padding: 10px 14px; font-size: 11pt; font-family: 'Segoe UI', 'Inter';"
        )
        self._duration = duration_ms
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self.resize(self.label.sizeHint().width() + 28, self.label.sizeHint().height() + 18)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setBrush(QColor(20, 22, 28, 230))
        p.setPen(QColor(60, 65, 75, 255))
        p.drawRoundedRect(r, 10, 10)

    def set_text(self, text: str):
        self.label.setText(text)
        self.resize(self.label.sizeHint().width() + 28, self.label.sizeHint().height() + 18)

    def show_animated(self, start: QPoint, end: QPoint):
        self.move(start)
        self.setWindowOpacity(0.0)
        self.show()
        # slide
        self._anim.stop(); self._fade.stop()
        self._anim.setDuration(220)
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.setDuration(220)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._anim.start(); self._fade.start()
        QTimer.singleShot(self._duration, self.hide_animated)

    def hide_animated(self):
        if not self.isVisible():
            return
        end = self.pos() + QPoint(0, 12)
        self._anim.stop(); self._fade.stop()
        self._anim.setDuration(200)
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(end)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade.setDuration(200)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)
        self._anim.start(); self._fade.start()


class ToastManager:
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.margin = 16
        self.gap = 8
        self.toasts: List[Toast] = []

    def show_toast(self, text: str, duration_ms: int = 3000):
        t = Toast(self.parent, text, duration_ms)
        self.toasts.append(t)
        self._reposition()

    def _reposition(self):
        # stack bottom-right inside parent window
        if not self.parent.isVisible():
            return
        g: QRect = self.parent.geometry()
        x_right = g.x() + g.width() - self.margin
        y_bottom = g.y() + g.height() - self.margin
        y = y_bottom
        # remove invisible
        self.toasts = [t for t in self.toasts if t.isVisible() or not t.isHidden()]
        for t in list(self.toasts):
            tsize = t.size()
            end = QPoint(x_right - tsize.width(), y - tsize.height())
            start = end + QPoint(0, 12)
            t.show_animated(start, end)
            y = end.y() - self.gap
            # auto-remove after hide
            QTimer.singleShot(t._duration + 400, lambda tt=t: self._cleanup(tt))

    def _cleanup(self, t: Toast):
        try:
            if t in self.toasts:
                self.toasts.remove(t)
            t.deleteLater()
        except Exception:
            pass
