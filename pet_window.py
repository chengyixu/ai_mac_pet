# pet_window.py
import sys
import threading
import platform
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QMouseEvent, QCursor, QPainter, QColor, QBrush
from PyQt6.QtCore import (Qt, QPoint, pyqtSignal, QTimer, QRect,
                         QMetaObject, Q_ARG, pyqtSlot)

import config # Use settings from config.py
from favorability_system import FavorabilitySystem  # Import favorability system
from statistics_window import StatisticsWindow  # Import statistics window

# --- Platform Detection for macOS-specific features ---
MACOS_OBJC_AVAILABLE = False
NSUtilityWindowLevel = 4  # Default value

try:
    if sys.platform == "darwin":
        import objc
        from ctypes import c_void_p
        MACOS_OBJC_AVAILABLE = True
        
        # Try to get the actual NSUtilityWindowLevel value
        try:
            AppKit = objc.cdll.LoadLibrary('/System/Library/Frameworks/AppKit.framework/AppKit')
            NSUtilityWindowLevel = objc.objc_getClass('NSWindow').NSUtilityWindowLevel
        except:
            NSUtilityWindowLevel = 4  # Fallback to known value
            
except ImportError:
    pass


class SpeechBubble(QLabel):
    """A custom QLabel for the speech bubble with adjusted positioning."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(config.SPEECH_BUBBLE_STYLE)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide() # Initially hidden
        
        # Basic always-on-top without activation
        if parent is None:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.ToolTip  # Use ToolTip instead of Tool - doesn't appear in taskbar
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
            
            # Apply minimal macOS settings
            if MACOS_OBJC_AVAILABLE:
                self._apply_macos_settings()

    def _apply_macos_settings(self):
        """Apply minimal non-intrusive macOS settings"""
        if not MACOS_OBJC_AVAILABLE:
            return
        
        try:
            # Get the NSWindow from the Qt window
            window_id = self.winId()
            ns_window = objc.objc_object(c_void_p=int(window_id))
            
            # Use NSUtilityWindowLevel (4) - above normal but doesn't interfere with focus
            ns_window.setLevel_(NSUtilityWindowLevel)
            
            # Set behavior to avoid activation
            ns_window.setCanBecomeKeyWindow_(False)
            ns_window.setHidesOnDeactivate_(False)
        except Exception as e:
            print(f"WARNING: Failed to apply macOS window settings to speech bubble: {e}")

    def show_message(self, text: str, duration_ms: int, pet_widget: QWidget):
        print(f"DEBUG: SpeechBubble show_message called with text: '{text}'")
        self.setText(text)
        self.adjustSize() # Adjust size based on text content

        # Position bubble above the pet
        pet_rect = pet_widget.geometry()
        bubble_x = pet_rect.x() + (pet_rect.width() // 2) - (self.width() // 2)
        bubble_y = pet_rect.y() - self.height() - 10 # 10px spacing above pet

        # Prevent bubble going off-screen (simple check for left/top edges)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        bubble_x = max(0, bubble_x) # Don't go off left edge
        bubble_y = max(0, bubble_y) # Don't go off top edge

        if bubble_x + self.width() > screen_geometry.width():
            bubble_x = screen_geometry.width() - self.width()

        self.move(bubble_x, bubble_y)
        print(f"DEBUG: Moving speech bubble to ({bubble_x}, {bubble_y})")
        self.show()
        print("DEBUG: Speech bubble shown.")

        # Hide after duration using a helper method for logging
        QTimer.singleShot(duration_ms, self.hide_bubble)

    def hide_bubble(self):
        print("DEBUG: Hiding speech bubble.")
        self.hide()


class PetWindow(QWidget):
    """The main window for the desktop pet."""
    # Signal to emit when analysis result is ready (str result)
    analysis_received = pyqtSignal(str)
    # Signal emitted when the cat is clicked (and not busy)
    cat_clicked_request_analysis = pyqtSignal()
    # New signal for automatic analysis
    auto_screenshot_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        print("DEBUG: PetWindow __init__ starting.")
        self.offset = QPoint()
        self.is_dragging = False
        self.analysis_in_progress = False # Flag to prevent rapid clicks
        self.click_press_pos = None # Store click position to differentiate click/drag

        # Initialize favorability system BEFORE initUI
        self.favorability = FavorabilitySystem()

        self.initUI()

        # Connect the signal to the slot (method)
        self.analysis_received.connect(self.display_analysis_result)
        
        # Connect auto screenshot signal to the same handler as click
        self.auto_screenshot_requested.connect(self.start_auto_analysis)
        
        # Setup timer for automatic screenshots if enabled
        if config.AUTO_SCREENSHOT_ENABLED:
            self.auto_screenshot_timer = QTimer(self)
            self.auto_screenshot_timer.timeout.connect(self.request_auto_screenshot)
            # Start the timer (convert seconds to milliseconds)
            self.auto_screenshot_timer.start(config.AUTO_SCREENSHOT_INTERVAL_SECONDS * 1000)
            print(f"DEBUG: Auto screenshot timer started with interval {config.AUTO_SCREENSHOT_INTERVAL_SECONDS} seconds")
        else:
            print("DEBUG: Auto screenshot feature is disabled in config")
        
        print("DEBUG: PetWindow __init__ finished.")

    def initUI(self):
        print("DEBUG: PetWindow initUI starting.")
        
        # --- Set simplified but effective window flags ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip  # Use ToolTip instead of Tool - doesn't appear in taskbar
        )
        
        # Critical: Ensure we never activate or steal focus
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Cat Image Label - Load, Scale, and Set
        self.cat_label = QLabel(self)
        original_pixmap = QPixmap("assets/cat_idle.png") # Make sure this path is correct

        if original_pixmap.isNull():
            print("ERROR: Could not load cat image 'assets/cat_idle.png'")
            self.cat_label.setText("X_X") # Small fallback text
            self.setFixedSize(config.PET_TARGET_WIDTH, config.PET_TARGET_WIDTH) # Use target size anyway
        else:
            # Scale the pixmap
            self.pixmap = original_pixmap.scaledToWidth(
                config.PET_TARGET_WIDTH, # Use width from config
                Qt.TransformationMode.SmoothTransformation
            )
            self.cat_label.setPixmap(self.pixmap)
            print(f"DEBUG: Cat pixmap size: {self.pixmap.size()}")

        # --- Favorability Indicator ---
        self.favorability_label = QLabel(self)
        self.favorability_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 182, 193, 200); /* Light pink */
                color: #d63384;
                border-radius: 12px;
                padding: 3px 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self.favorability_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.favorability_label.setMaximumHeight(25)
        # Let the label adjust width based on content
        self.favorability_label.setMinimumWidth(100)
        self.favorability_label.adjustSize()
        self._update_favorability_display()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Add small margins
        layout.setSpacing(5)
        
        # Add favorability indicator at top
        layout.addWidget(self.favorability_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add cat image
        layout.addWidget(self.cat_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Adjust window size to fit content
        # We need slightly more height for the favorability indicator
        # and ensure width is enough for the favorability text
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            # Use the wider of cat image or minimum needed for favorability text
            window_width = max(self.pixmap.width(), 150)  # At least 150px for Chinese text
            window_height = self.pixmap.height() + 30  # Extra space for favorability indicator
            self.setFixedSize(window_width, window_height)
        else:
            self.setFixedSize(max(config.PET_TARGET_WIDTH, 150), config.PET_TARGET_WIDTH + 30)
        
        print(f"DEBUG: Window size set to {self.size()}")
        
        # Speech Bubble (created as a top-level window, not added to layout)
        self.speech_bubble = SpeechBubble(None)  # Top-level window
        
        # Statistics Window (created on demand)
        self.statistics_window = None

        # Set initial position: Bottom Right Corner
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        margin = 20 # Small margin from the edge
        initial_x = screen_geometry.width() - self.width() - margin
        initial_y = screen_geometry.height() - self.height() - margin
        self.move(initial_x, initial_y)
        print(f"DEBUG: Pet moved to initial position ({initial_x}, {initial_y})")

        # Apply platform-specific window settings (macOS)
        if MACOS_OBJC_AVAILABLE:
            self._apply_macos_settings()
            
        self.show()
        print("DEBUG: PetWindow shown.")
    
    def request_auto_screenshot(self):
        """Called by the timer to request an automatic screenshot and analysis."""
        if not self.analysis_in_progress:
            print("DEBUG: Auto screenshot timer triggered")
            self.auto_screenshot_requested.emit()
        else:
            print("DEBUG: Auto screenshot timer triggered but analysis already in progress, skipping")
    
    def start_auto_analysis(self):
        """Handler for automatic screenshot requests."""
        if not self.analysis_in_progress:
            print("DEBUG: Starting automatic analysis...")
            self.analysis_in_progress = True
            self._update_cat_state("thinking")  # Show thinking state
            
            # Start the analysis in a separate thread (same as click-triggered analysis)
            self.cat_clicked_request_analysis.emit()  # Reuse the existing signal/slot
        else:
            print("DEBUG: Analysis already in progress, skipping auto request")

    def _apply_macos_settings(self):
        """Apply minimal non-intrusive macOS settings"""
        if not MACOS_OBJC_AVAILABLE:
            return
        
        try:
            # Get the NSWindow from the Qt window
            window_id = self.winId()
            ns_window = objc.objc_object(c_void_p=int(window_id))
            
            # Use NSUtilityWindowLevel (4) - above normal but doesn't interfere with focus
            ns_window.setLevel_(NSUtilityWindowLevel)
            
            # Set behavior to avoid activation
            ns_window.setCanBecomeKeyWindow_(False)
            ns_window.setHidesOnDeactivate_(False)
            
            # This combination of flags should make window stay on top without being intrusive
            window_behavior = (
                1 << 1 |  # NSWindowCollectionBehaviorMoveToActiveSpace
                1 << 7    # NSWindowCollectionBehaviorStationary (stays in place)
            )
            ns_window.setCollectionBehavior_(window_behavior)
        except Exception as e:
            print(f"WARNING: Failed to apply macOS window settings: {e}")

    # This method is connected to the analysis_received signal
    def display_analysis_result(self, text: str):
        """Slot to display the text and reset analysis flag."""
        print(f"DEBUG: PetWindow display_analysis_result received: '{text}'")
        if not isinstance(text, str) or not text:
             print("WARNING: display_analysis_result received invalid text. Using fallback.")
             text = "喵~ （好像没什么可说的...）"
        
        # Update favorability display when showing results
        self._update_favorability_display()

        # Show talking state briefly, then show speech bubble
        self._update_cat_state("talking")
        
        # Call the speech bubble's method to show the message
        self.speech_bubble.show_message(
             text,
             config.SPEECH_BUBBLE_DURATION_SECONDS * 1000,
             self # Pass self (PetWindow instance) for positioning
        )

        print("DEBUG: Resetting analysis_in_progress flag.")
        self.analysis_in_progress = False
        
        # Reset to idle state after a short delay to show talking animation
        QTimer.singleShot(1000, lambda: self._update_cat_state("idle"))

    # --- Dragging and Click Handling ---
    def mousePressEvent(self, event: QMouseEvent):
        print("DEBUG: mousePressEvent")
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.pos()
            self.is_dragging = False # Reset dragging flag on new press
            self.click_press_pos = event.pos() # Record local press position
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Handle right-click to show statistics
            print("DEBUG: Right-click detected, showing statistics window")
            self.show_statistics_window()
            event.accept()
        else:
             event.ignore() # Ignore other buttons

    def mouseMoveEvent(self, event: QMouseEvent):
        # Only process if left button is held down AND we recorded a press position
        if event.buttons() & Qt.MouseButton.LeftButton and self.click_press_pos is not None:
            # Check if movement exceeds threshold only once after press
            if not self.is_dragging and (event.pos() - self.click_press_pos).manhattanLength() > QApplication.startDragDistance():
                 print("DEBUG: Drag detected.")
                 self.is_dragging = True # Now it's officially a drag
                 self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor)) # Change cursor

            # If dragging is active, move the window
            if self.is_dragging:
                new_pos = event.globalPosition().toPoint() - self.offset
                self.move(new_pos)
                event.accept()
            else:
                # Moved, but not enough to be a drag yet
                event.ignore()
        else:
             event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent):
        print("DEBUG: mouseReleaseEvent")
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor)) # Restore cursor
            if not self.is_dragging:
                # It's a click (no significant drag occurred)
                print("DEBUG: Click detected (no drag).")
                if not self.analysis_in_progress:
                    print("DEBUG: Analysis not in progress. Emitting request signal...")
                    self.analysis_in_progress = True # Prevent new requests immediately
                    self._update_cat_state("thinking") # Show thinking state visually
                    self.cat_clicked_request_analysis.emit() # Signal main thread to start analysis
                else:
                    print("INFO: Analysis already in progress, click ignored.")
            else:
                 print("DEBUG: Drag finished.") # Drag completed
            # Reset dragging state regardless, ready for next press
            self.is_dragging = False
            self.click_press_pos = None # Clear recorded press position
            event.accept()
        else:
            event.ignore()
    
    def show_statistics_window(self):
        """Show the statistics window with activity data."""
        if self.statistics_window is None:
            self.statistics_window = StatisticsWindow(self)
        
        # Center the statistics window relative to pet
        pet_pos = self.pos()
        stats_x = pet_pos.x() - 200  # Show to the left of the pet
        stats_y = pet_pos.y() - 250  # Show above the pet
        
        # Ensure window stays on screen
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        stats_x = max(0, min(stats_x, screen_geometry.width() - 400))
        stats_y = max(0, min(stats_y, screen_geometry.height() - 500))
        
        self.statistics_window.move(stats_x, stats_y)
        self.statistics_window.show()
        self.statistics_window.raise_()  # Bring to front
        self.statistics_window.activateWindow()

    def closeEvent(self, event):
        """Ensure speech bubble is also closed/cleaned up."""
        print("DEBUG: PetWindow closeEvent.")
        # Stop the auto screenshot timer if it exists
        if hasattr(self, 'auto_screenshot_timer'):
            self.auto_screenshot_timer.stop()
            print("DEBUG: Auto screenshot timer stopped")
            
        self.speech_bubble.hide()
        self.speech_bubble.deleteLater() # Schedule bubble for deletion
        event.accept()

    # --- Method to change cat's appearance ---
    def set_cat_state(self, state: str):
        """Public method to request cat state change."""
        # Use invokeMethod to queue the actual update
        QMetaObject.invokeMethod(self, "_update_cat_state", Qt.ConnectionType.QueuedConnection, Q_ARG(str, state))

    @pyqtSlot(str) # Decorator REQUIRED for invokeMethod to find it
    def _update_cat_state(self, state: str): # Actual GUI update runs in GUI thread
        """Private slot to perform the actual state update."""
        print(f"DEBUG: Updating cat state to: {state}")
        
        # Load appropriate image based on state
        if state == "thinking":
            thinking_pixmap = QPixmap("assets/cat_surprise.png")
            if not thinking_pixmap.isNull():
                scaled_pixmap = thinking_pixmap.scaledToWidth(
                    config.PET_TARGET_WIDTH,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cat_label.setPixmap(scaled_pixmap)
            self.cat_label.setToolTip("Hmm...")
        elif state == "talking":
            talking_pixmap = QPixmap("assets/cat_talking.png")
            if not talking_pixmap.isNull():
                scaled_pixmap = talking_pixmap.scaledToWidth(
                    config.PET_TARGET_WIDTH,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.cat_label.setPixmap(scaled_pixmap)
            self.cat_label.setToolTip("Meow!")
        else: # idle
            self.cat_label.setPixmap(self.pixmap) # Reset to original scaled idle pixmap
            self.cat_label.setToolTip("")

    def _update_favorability_display(self):
        """Update the favorability indicator display."""
        current_level = self.favorability.get_current_level()
        level_desc = self.favorability.get_level_description()
        
        # Show hearts based on level
        if current_level >= 10:
            hearts = "♥♥♥♥♥"
        elif current_level >= 5:
            hearts = "♥♥♥♥"
        elif current_level >= 0:
            hearts = "♥♥♥"
        elif current_level >= -5:
            hearts = "♥♥"
        else:
            hearts = "♥"
            
        self.favorability_label.setText(f"{hearts} {level_desc}")
        self.favorability_label.adjustSize()  # Ensure label resizes to fit text
        
        # Update color based on level
        if current_level >= 10:
            bg_color = "rgba(255, 105, 180, 200)"  # Hot pink
            text_color = "#8b0051"
        elif current_level >= 5:
            bg_color = "rgba(255, 182, 193, 200)"  # Light pink
            text_color = "#d63384"
        elif current_level >= 0:
            bg_color = "rgba(255, 218, 185, 200)"  # Peach
            text_color = "#cc5500"
        else:
            bg_color = "rgba(200, 200, 200, 200)"  # Gray
            text_color = "#555555"
            
        self.favorability_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)