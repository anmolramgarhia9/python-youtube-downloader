"""
Theme system for Music Downloader
Provides Light, Dark, and AMOLED themes with dynamic switching
"""

from enum import Enum


class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"
    AMOLED = "amoled"


class Theme:
    """Base theme configuration"""
    
    # Common styles
    COMMON_BASE = """
        /* Global Styles */
        QMainWindow, QWidget {
            font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
        }
        
        /* ScrollBars */
        QScrollBar:vertical {{
            background: {scrollbar_bg};
            width: 10px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: {scrollbar_handle};
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {scrollbar_handle_hover};
        }}
        
        QScrollBar:horizontal {{
            background: {scrollbar_bg};
            height: 10px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {scrollbar_handle};
            border-radius: 5px;
            min-width: 30px;
        }}
        
        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
        
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}
        
        /* ComboBox */
        QComboBox {{
            background: {combo_bg};
            border: 2px solid {combo_border};
            border-radius: 10px;
            padding: 10px 15px;
            color: {text_primary};
            font-size: 13px;
        }}
        
        QComboBox:hover {{
            border: 2px solid {combo_border_hover};
            background: {combo_bg_hover};
        }}
        
        QComboBox:focus {{
            border: 2px solid {accent_primary};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
            padding-right: 10px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {text_secondary};
        }}
        
        QComboBox QAbstractItemView {{
            background: {dropdown_bg};
            color: {text_primary};
            selection-background-color: {accent_primary};
            selection-color: #fff;
            border: 1px solid {dropdown_border};
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 15px;
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background: {dropdown_item_hover};
        }}
    """
    
    @staticmethod
    def get_theme(theme_type: ThemeType) -> str:
        """Get complete stylesheet for theme"""
        if theme_type == ThemeType.LIGHT:
            return Theme._get_light_theme()
        elif theme_type == ThemeType.AMOLED:
            return Theme._get_amoled_theme()
        else:
            return Theme._get_dark_theme()
    
    @staticmethod
    def _get_dark_theme() -> str:
        """Modern dark theme with gradient backgrounds"""
        return """
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f0f0f, stop:1 #1a1a1a);
                color: #e8e8e8;
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
            }
        """
    
    @staticmethod
    def _get_light_theme() -> str:
        """Clean light theme"""
        return """
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f5f5f5, stop:1 #e8e8e8);
                color: #1a1a1a;
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
            }
        """
    
    @staticmethod
    def _get_amoled_theme() -> str:
        """Pure black AMOLED theme for battery saving"""
        return """
            QMainWindow, QWidget {
                background: #000000;
                color: #ffffff;
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
            }
        """


def apply_theme(app, theme_type: ThemeType):
    """Apply theme to QApplication"""
    stylesheet = Theme.get_theme(theme_type)
    app.setStyleSheet(stylesheet)
