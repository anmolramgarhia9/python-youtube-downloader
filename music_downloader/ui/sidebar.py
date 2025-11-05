"""
Modern sidebar navigation with icon-based navigation
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QFrame, QSizePolicy, QHBoxLayout
)


class NavButton(QPushButton):
    """Custom navigation button with icon and label"""
    
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.label_text = text
        self.is_selected = False
        
        # Fixed size for consistency
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)
        
        # Icon
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.icon_label)
        
        # Text
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("font-size: 11px; font-weight: 600;")
        layout.addWidget(self.text_label)
        
        self._update_style()
    
    def set_selected(self, selected: bool):
        """Mark button as selected"""
        self.is_selected = selected
        self._update_style()
    
    def _update_style(self):
        """Update button styling based on selection state"""
        if self.is_selected:
            self.setStyleSheet("""
                NavButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                               stop:0 rgba(29, 185, 84, 0.3),
                                               stop:1 rgba(30, 231, 96, 0.3));
                    border: none;
                    border-left: 4px solid #1db954;
                    border-radius: 0px;
                }
                QLabel {
                    color: #1ed760;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                NavButton {
                    background: transparent;
                    border: none;
                    border-left: 4px solid transparent;
                    border-radius: 0px;
                }
                NavButton:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-left: 4px solid rgba(29, 185, 84, 0.5);
                }
                QLabel {
                    color: #888;
                    background: transparent;
                }
                NavButton:hover QLabel {
                    color: #e8e8e8;
                }
            """)


class Sidebar(QWidget):
    """Modern sidebar with icon navigation"""
    
    # Signals for navigation
    navigate_to = pyqtSignal(int)  # page index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.current_index = 0
        
        self.setFixedWidth(100)
        self.setStyleSheet("""
            Sidebar {
                background: rgba(10, 10, 10, 0.8);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(0)
        
        # App logo/title
        logo = QLabel("🎵")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            font-size: 32px;
            padding: 10px;
            color: #1db954;
        """)
        layout.addWidget(logo)
        
        app_name = QLabel("Music\nDL")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            color: #888;
            padding-bottom: 20px;
            line-height: 1.3;
        """)
        layout.addWidget(app_name)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.1); max-height: 1px;")
        layout.addWidget(separator)
        
        layout.addSpacing(10)
        
        # Navigation buttons
        nav_items = [
            ("🔍", "Search"),
            ("📥", "Downloads"),
            ("⚙️", "Settings"),
        ]
        
        for i, (icon, text) in enumerate(nav_items):
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_clicked(idx))
            self.buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch(1)
        
        # Footer info
        footer = QLabel("v1.0")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("""
            font-size: 9px;
            color: #555;
            padding: 10px;
        """)
        layout.addWidget(footer)
        
        # Set first button as selected
        self.buttons[0].set_selected(True)
    
    def _on_nav_clicked(self, index: int):
        """Handle navigation button click"""
        if index != self.current_index:
            # Deselect old button
            self.buttons[self.current_index].set_selected(False)
            # Select new button
            self.buttons[index].set_selected(True)
            self.current_index = index
            # Emit navigation signal
            self.navigate_to.emit(index)
    
    def set_current_page(self, index: int):
        """Programmatically set current page"""
        if 0 <= index < len(self.buttons) and index != self.current_index:
            self.buttons[self.current_index].set_selected(False)
            self.buttons[index].set_selected(True)
            self.current_index = index
