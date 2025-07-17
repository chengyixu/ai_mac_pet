# pet_window.py
import sys
import threading
import platform
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QMouseEvent, QCursor, QPainter, QColor, QBrush
from PyQt6.QtCore import (Qt, QPoint, pyqtSignal, QTimer, QRect,
                         QMetaObject, Q_ARG, pyqtSlot)

import config # Use settings from config.py

# Platform-specific imports for macOS 
if platform.system() == 'Darwin':
    try:
        import objc
        from ctypes import c_void_p  # Add this import
        from Foundation import NSObject
        from AppKit import NSApplication, NSApp, NSWindow, NSNormalWindowLevel, NSUtilityWindowLevel
        MACOS_OBJC_AVAILABLE = True
        print("DEBUG: PyObjC available - macOS-specific window handling enabled")
    except ImportError:
        print("WARNING: PyObjC not available. macOS-specific window handling disabled.")
        MACOS_OBJC_AVAILABLE = False
else:
    MACOS_OBJC_AVAILABLE = False
    print("DEBUG: Not on macOS, skipping macOS-specific window handling")


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
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0) # No margins for the layout itself

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
            # Set window size based on the *scaled* pixmap
            self.setFixedSize(self.pixmap.size())
            print(f"DEBUG: Pet size set to {self.size()}")

        self.layout.addWidget(self.cat_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

        # Speech Bubble (created as a top-level window)
        self.speech_bubble = SpeechBubble(None)  # Top-level window

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
        else:
             event.ignore() # Ignore right-clicks etc.

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