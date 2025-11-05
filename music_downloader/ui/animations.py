"""
Animation utilities for smooth UI transitions
Provides fade, slide, and scale animations for widgets
"""

from PyQt6.QtCore import (
    QObject, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup,
    QPoint, QSize, pyqtProperty
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


class AnimationHelper:
    """Helper class for creating smooth animations"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """Fade in a widget"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        
        # Store reference to prevent garbage collection
        widget._fade_anim = anim
        return anim
    
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300, on_finished=None):
        """Fade out a widget"""
        effect = widget.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        
        if on_finished:
            anim.finished.connect(on_finished)
        
        anim.start()
        widget._fade_anim = anim
        return anim
    
    @staticmethod
    def slide_in_from_bottom(widget: QWidget, distance: int = 50, duration: int = 400):
        """Slide widget in from bottom"""
        start_pos = widget.pos() + QPoint(0, distance)
        end_pos = widget.pos()
        
        widget.move(start_pos)
        
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        
        widget._slide_anim = anim
        return anim
    
    @staticmethod
    def slide_in_from_right(widget: QWidget, distance: int = 50, duration: int = 400):
        """Slide widget in from right"""
        start_pos = widget.pos() + QPoint(distance, 0)
        end_pos = widget.pos()
        
        widget.move(start_pos)
        
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        
        widget._slide_anim = anim
        return anim
    
    @staticmethod
    def slide_and_fade_in(widget: QWidget, distance: int = 30, duration: int = 400):
        """Combine slide and fade animations"""
        # Fade animation
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Slide animation
        start_pos = widget.pos() + QPoint(0, distance)
        end_pos = widget.pos()
        widget.move(start_pos)
        
        slide_anim = QPropertyAnimation(widget, b"pos")
        slide_anim.setDuration(duration)
        slide_anim.setStartValue(start_pos)
        slide_anim.setEndValue(end_pos)
        slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Parallel group
        group = QParallelAnimationGroup()
        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)
        group.start()
        
        widget._combined_anim = group
        return group
    
    @staticmethod
    def scale_in(widget: QWidget, duration: int = 300):
        """Scale widget from small to normal size"""
        # Note: Qt doesn't have native scale property for QWidget
        # This is a simplified version using size
        original_size = widget.size()
        start_size = QSize(
            int(original_size.width() * 0.9),
            int(original_size.height() * 0.9)
        )
        
        anim = QPropertyAnimation(widget, b"size")
        anim.setDuration(duration)
        anim.setStartValue(start_size)
        anim.setEndValue(original_size)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        anim.start()
        
        widget._scale_anim = anim
        return anim
    
    @staticmethod
    def bounce_in(widget: QWidget, duration: int = 600):
        """Bounce animation for widget entrance"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        start_pos = widget.pos() + QPoint(0, -20)
        end_pos = widget.pos()
        widget.move(start_pos)
        
        slide_anim = QPropertyAnimation(widget, b"pos")
        slide_anim.setDuration(duration)
        slide_anim.setStartValue(start_pos)
        slide_anim.setEndValue(end_pos)
        slide_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        group = QParallelAnimationGroup()
        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)
        group.start()
        
        widget._bounce_anim = group
        return group
    
    @staticmethod
    def stagger_fade_in(widgets: list, delay: int = 50, duration: int = 300):
        """Stagger fade-in animations for multiple widgets"""
        group = QSequentialAnimationGroup()
        
        for i, widget in enumerate(widgets):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # Add delay between animations
            if i > 0:
                from PyQt6.QtCore import QTimer
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda a=anim: a.start())
                timer.start(i * delay)
            else:
                anim.start()
            
            widget._stagger_anim = anim
        
        return group


class AnimatedWidget(QWidget):
    """Base class for widgets with built-in animation support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animator = AnimationHelper()
    
    def fade_in(self, duration: int = 300):
        """Fade in this widget"""
        return self._animator.fade_in(self, duration)
    
    def fade_out(self, duration: int = 300, on_finished=None):
        """Fade out this widget"""
        return self._animator.fade_out(self, duration, on_finished)
    
    def slide_in(self, distance: int = 30, duration: int = 400):
        """Slide in this widget"""
        return self._animator.slide_and_fade_in(self, distance, duration)
    
    def bounce_in(self, duration: int = 600):
        """Bounce in this widget"""
        return self._animator.bounce_in(self, duration)
