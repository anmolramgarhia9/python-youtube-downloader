"""
Circular progress indicator with animated percentage display
"""

from PyQt6.QtCore import Qt, QRect, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QConicalGradient
from PyQt6.QtWidgets import QWidget


class CircularProgress(QWidget):
    """
    Circular progress indicator with gradient and percentage display
    """
    
    def __init__(self, parent=None, size: int = 80):
        super().__init__(parent)
        self._progress = 0
        self._animated_progress = 0
        self._size = size
        
        # Colors
        self._bg_color = QColor(40, 40, 40, 100)
        self._progress_color = QColor(29, 185, 84)
        self._text_color = QColor(232, 232, 232)
        
        # Line widths
        self._bg_width = 6
        self._progress_width = 6
        
        # Animation
        self._animation = QPropertyAnimation(self, b"animated_progress")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.setFixedSize(size, size)
    
    @pyqtProperty(float)
    def animated_progress(self):
        return self._animated_progress
    
    @animated_progress.setter
    def animated_progress(self, value):
        self._animated_progress = value
        self.update()
    
    def set_progress(self, value: int):
        """Set progress value (0-100) with animation"""
        value = max(0, min(100, value))
        if value != self._progress:
            self._progress = value
            # Animate to new value
            self._animation.stop()
            self._animation.setStartValue(self._animated_progress)
            self._animation.setEndValue(float(value))
            self._animation.start()
    
    def set_colors(self, bg_color: QColor = None, progress_color: QColor = None, text_color: QColor = None):
        """Customize colors"""
        if bg_color:
            self._bg_color = bg_color
        if progress_color:
            self._progress_color = progress_color
        if text_color:
            self._text_color = text_color
        self.update()
    
    def paintEvent(self, event):
        """Paint the circular progress"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate rectangle for circle
        rect = QRectF(
            self._progress_width / 2,
            self._progress_width / 2,
            self.width() - self._progress_width,
            self.height() - self._progress_width
        )
        
        # Draw background circle
        pen = QPen(self._bg_color)
        pen.setWidth(self._bg_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # Draw progress arc with gradient
        if self._animated_progress > 0:
            # Create gradient
            gradient = QConicalGradient(rect.center(), 90)
            gradient.setColorAt(0, self._progress_color.lighter(120))
            gradient.setColorAt(self._animated_progress / 100, self._progress_color)
            gradient.setColorAt(1, self._progress_color.darker(120))
            
            pen = QPen(QBrush(gradient), self._progress_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Draw arc (start at top, go clockwise)
            span_angle = int(self._animated_progress * 360 / 100 * 16)
            painter.drawArc(rect, 90 * 16, -span_angle)
        
        # Draw percentage text
        painter.setPen(self._text_color)
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignCenter,
            f"{int(self._animated_progress)}%"
        )


class MiniCircularProgress(QWidget):
    """
    Smaller circular progress for compact display
    """
    
    def __init__(self, parent=None, size: int = 40):
        super().__init__(parent)
        self._progress = 0
        self._size = size
        
        # Colors
        self._bg_color = QColor(60, 60, 60, 150)
        self._progress_color = QColor(29, 185, 84)
        
        # Line widths
        self._line_width = 4
        
        self.setFixedSize(size, size)
    
    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self._progress = max(0, min(100, value))
        self.update()
    
    def paintEvent(self, event):
        """Paint the mini circular progress"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate rectangle
        margin = self._line_width / 2
        rect = QRectF(margin, margin, self.width() - self._line_width, self.height() - self._line_width)
        
        # Background circle
        pen = QPen(self._bg_color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # Progress arc
        if self._progress > 0:
            pen = QPen(self._progress_color)
            pen.setWidth(self._line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            span_angle = int(self._progress * 360 / 100 * 16)
            painter.drawArc(rect, 90 * 16, -span_angle)
        
        # Small percentage text
        painter.setPen(QColor(232, 232, 232))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._progress}%")
