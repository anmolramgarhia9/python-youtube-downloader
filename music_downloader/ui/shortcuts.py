"""
Keyboard shortcuts and page transition animations
"""

from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QPoint
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QGraphicsOpacityEffect


class ShortcutManager:
    """Manage application keyboard shortcuts"""
    
    def __init__(self, window: QMainWindow):
        self.window = window
        self.shortcuts = []
    
    def setup_shortcuts(self, search_widget, downloads_tab, settings_tab, sidebar, pages):
        """Setup all keyboard shortcuts"""
        
        # Navigation: Ctrl+1/2/3 for tab switching
        shortcut_search = QShortcut(QKeySequence("Ctrl+1"), self.window)
        shortcut_search.activated.connect(lambda: self._switch_page(sidebar, pages, 0))
        self.shortcuts.append(shortcut_search)
        
        shortcut_downloads = QShortcut(QKeySequence("Ctrl+2"), self.window)
        shortcut_downloads.activated.connect(lambda: self._switch_page(sidebar, pages, 1))
        self.shortcuts.append(shortcut_downloads)
        
        shortcut_settings = QShortcut(QKeySequence("Ctrl+3"), self.window)
        shortcut_settings.activated.connect(lambda: self._switch_page(sidebar, pages, 2))
        self.shortcuts.append(shortcut_settings)
        
        # Search focus: Ctrl+F
        shortcut_focus_search = QShortcut(QKeySequence("Ctrl+F"), self.window)
        shortcut_focus_search.activated.connect(lambda: self._focus_search(search_widget, sidebar, pages))
        self.shortcuts.append(shortcut_focus_search)
        
        # Escape to cancel/clear
        shortcut_escape = QShortcut(QKeySequence("Esc"), self.window)
        shortcut_escape.activated.connect(lambda: self._on_escape(search_widget))
        self.shortcuts.append(shortcut_escape)
        
        # Ctrl+R to refresh/retry
        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self.window)
        shortcut_refresh.activated.connect(lambda: self._on_refresh(search_widget))
        self.shortcuts.append(shortcut_refresh)
        
        # Ctrl+W to close window (standard)
        shortcut_close = QShortcut(QKeySequence("Ctrl+W"), self.window)
        shortcut_close.activated.connect(self.window.close)
        self.shortcuts.append(shortcut_close)
        
        # Ctrl+Q to quit
        shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self.window)
        shortcut_quit.activated.connect(self.window.close)
        self.shortcuts.append(shortcut_quit)
    
    def _switch_page(self, sidebar, pages, index):
        """Switch to a page with animation"""
        if pages.currentIndex() != index:
            sidebar.set_current_page(index)
            pages.setCurrentIndex(index)
    
    def _focus_search(self, search_widget, sidebar, pages):
        """Focus the search box"""
        # Switch to search tab if not already there
        if pages.currentIndex() != 0:
            self._switch_page(sidebar, pages, 0)
        # Focus and select all text in search box
        search_widget.query.setFocus()
        search_widget.query.selectAll()
    
    def _on_escape(self, search_widget):
        """Handle Escape key - clear search or deselect"""
        if search_widget.query.hasFocus():
            search_widget.query.clear()
            search_widget.query.clearFocus()
    
    def _on_refresh(self, search_widget):
        """Handle Ctrl+R - retry last search"""
        if search_widget.query.text().strip():
            search_widget._do_search()


class PageTransitions:
    """Handle smooth page transitions for QStackedWidget"""
    
    def __init__(self, stacked_widget: QStackedWidget):
        self.stacked_widget = stacked_widget
        self._animation = None
    
    def slide_to_page(self, index: int, duration: int = 300):
        """Slide to a page with animation"""
        if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
            self._animation.stop()
        
        current_index = self.stacked_widget.currentIndex()
        if current_index == index:
            return
        
        # Determine direction
        direction = 1 if index > current_index else -1
        
        # Get current and next widgets
        current_widget = self.stacked_widget.currentWidget()
        next_widget = self.stacked_widget.widget(index)
        
        if not current_widget or not next_widget:
            self.stacked_widget.setCurrentIndex(index)
            return
        
        # Calculate offset
        width = self.stacked_widget.width()
        offset = width * direction
        
        # Position next widget offscreen
        next_widget.setGeometry(offset, 0, width, self.stacked_widget.height())
        next_widget.show()
        next_widget.raise_()
        
        # Animate current widget out
        self._animation = QPropertyAnimation(current_widget, b"pos")
        self._animation.setDuration(duration)
        self._animation.setStartValue(QPoint(0, 0))
        self._animation.setEndValue(QPoint(-offset, 0))
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animate next widget in (parallel)
        next_animation = QPropertyAnimation(next_widget, b"pos")
        next_animation.setDuration(duration)
        next_animation.setStartValue(QPoint(offset, 0))
        next_animation.setEndValue(QPoint(0, 0))
        next_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Cleanup and switch on finish
        def on_finished():
            self.stacked_widget.setCurrentIndex(index)
            current_widget.setGeometry(0, 0, width, self.stacked_widget.height())
        
        next_animation.finished.connect(on_finished)
        
        self._animation.start()
        next_animation.start()
    
    def fade_to_page(self, index: int, duration: int = 250):
        """Fade to a page with cross-fade animation"""
        if self._animation and self._animation.state() == QPropertyAnimation.State.Running:
            return
        
        current_index = self.stacked_widget.currentIndex()
        if current_index == index:
            return
        
        current_widget = self.stacked_widget.currentWidget()
        next_widget = self.stacked_widget.widget(index)
        
        if not current_widget or not next_widget:
            self.stacked_widget.setCurrentIndex(index)
            return
        
        # Setup opacity effects
        current_effect = QGraphicsOpacityEffect()
        current_widget.setGraphicsEffect(current_effect)
        
        next_effect = QGraphicsOpacityEffect()
        next_widget.setGraphicsEffect(next_effect)
        next_effect.setOpacity(0.0)
        
        # Show next widget
        next_widget.show()
        next_widget.raise_()
        
        # Fade out current
        fade_out = QPropertyAnimation(current_effect, b"opacity")
        fade_out.setDuration(duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Fade in next
        fade_in = QPropertyAnimation(next_effect, b"opacity")
        fade_in.setDuration(duration)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        def on_finished():
            self.stacked_widget.setCurrentIndex(index)
            current_widget.setGraphicsEffect(None)
            next_widget.setGraphicsEffect(None)
        
        fade_in.finished.connect(on_finished)
        
        fade_out.start()
        fade_in.start()
        
        self._animation = fade_in
