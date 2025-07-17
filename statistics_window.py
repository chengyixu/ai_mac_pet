# statistics_window.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from activity_tracker import activity_tracker
import config

class StatisticsWindow(QDialog):
    """Window to display activity statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("喵喵的活动统计 ?")
        self.setModal(False)  # Non-modal so it doesn't block the pet
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Set size
        self.setFixedSize(400, 500)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("? 喵喵的活动统计")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Statistics display
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setFont(QFont("Courier", 12))
        self.stats_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                color: #212529;
            }
        """)
        layout.addWidget(self.stats_display)
        
        # Refresh button
        self.refresh_button = QPushButton("? 刷新统计")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #ff3838;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_statistics)
        layout.addWidget(self.refresh_button)
        
        # Close button
        self.close_button = QPushButton("关闭")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #868e96;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #6c757d;
            }
        """)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        
        # Initial load
        self.refresh_statistics()
        
        # Auto-refresh timer (every 30 seconds while window is open)
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_statistics)
        self.auto_refresh_timer.start(30000)  # 30 seconds
    
    def refresh_statistics(self):
        """Refresh the statistics display."""
        stats_text = activity_tracker.get_formatted_statistics()
        self.stats_display.setPlainText(stats_text)
        
        # Also show recent activities if available
        stats = activity_tracker.get_statistics()
        if stats["recent_activities"]:
            self.stats_display.append("\n\n? 最近的活动记录:")
            self.stats_display.append("-" * 30)
            
            for i, activity in enumerate(reversed(stats["recent_activities"][:5]), 1):
                time_str = activity_tracker._format_time(activity["timestamp"])
                top_categories = sorted(
                    activity["breakdown"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:2]  # Top 2 categories
                
                if top_categories:
                    cat_str = ", ".join([f"{cat}: {pct:.0f}%" for cat, pct in top_categories if pct > 0])
                    self.stats_display.append(f"\n{i}. {time_str}")
                    self.stats_display.append(f"   主要活动: {cat_str}")
    
    def closeEvent(self, event):
        """Stop the auto-refresh timer when window is closed."""
        self.auto_refresh_timer.stop()
        event.accept() 