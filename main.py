# main.py
import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
# QMetaObject and Q_ARG are no longer needed here if using emit()
from PyQt6.QtCore import Qt # Keep Qt if needed elsewhere

import config # Import settings first
from pet_window import PetWindow # Import the PetWindow class
from screenshot_analyzer import run_analysis_cycle # Import the analysis function

# Global reference to the PetWindow instance (simplifies access from worker thread)
pet_app_instance = None

def analysis_task_runner():
    """
    Worker function to run the analysis cycle in a separate thread.
    It gets the result and EMITS the analysis_received signal on the PetWindow instance.
    """
    global pet_app_instance
    # Check instance validity at the start of the thread execution
    if not pet_app_instance:
        print("ERROR: PetWindow instance lost/unavailable at start of analysis thread.")
        return

    print("DEBUG: Analysis worker thread started.")
    # Perform the analysis cycle; ensures a string is always returned
    result = run_analysis_cycle()
    print(f"DEBUG: Analysis thread finished. Raw result: '{result}'")

    # Check instance validity AGAIN before emitting signal (window might have closed)
    if not pet_app_instance:
         print("WARNING: PetWindow closed during analysis execution.")
         return

    # Ensure result is a non-empty string before emitting
    if not isinstance(result, str) or not result:
         print(f"WARNING: Analysis returned invalid/empty result '{result}'. Using fallback.")
         result = "喵？（分析好像失败了...）" # Fallback inside thread too

    print(f"DEBUG: Emitting analysis_received signal from worker thread with result: '{result}'")
    # --- Emit the signal directly ---
    # Qt's signal/slot mechanism automatically handles marshalling the call
    # to the receiver's thread (the GUI thread in this case) because the
    # connection is cross-thread by default (AutoConnection -> QueuedConnection).
    try:
        pet_app_instance.analysis_received.emit(result)
        print("DEBUG: analysis_received signal emitted successfully.")
    except Exception as e:
        print(f"ERROR: Failed to emit analysis_received signal: {e}")


def start_analysis_on_click():
    """
    Slot function connected to the cat_clicked_request_analysis signal.
    Starts the analysis process in a new background thread.
    This function runs in the GUI thread because it's connected to a signal from PetWindow.
    """
    global pet_app_instance
    print("DEBUG: start_analysis_on_click slot called.")
    if not pet_app_instance:
        print("ERROR: Pet instance missing in start_analysis_on_click.")
        return

    # The analysis_in_progress flag is already set to True in PetWindow's mouseReleaseEvent
    # before the signal is emitted, so we don't need to check it again here.
    # We just need to start the thread.

    # Create and start the analysis thread
    analysis_thread = threading.Thread(target=analysis_task_runner, daemon=True)
    print("DEBUG: Starting analysis worker thread...")
    analysis_thread.start()


def main():
    global pet_app_instance

    print("DEBUG: Application starting...")

    # --- CRITICAL: Check API Key Early ---
    # config.py already prints a warning, let's make it fatal here.
    if not config.API_KEY:
        print("--- FATAL ERROR ---")
        print("DASHSCOPE_API_KEY is missing or empty in the .env file.")
        print("Please create a .env file in the same directory as main.py")
        print("and add the line: DASHSCOPE_API_KEY='sk-yourkey'")
        print("-------------------")
        # Simple console pause before exit
        # input("Press Enter to exit...") # Disable input for quicker exit on error
        sys.exit(1) # Exit immediately if key is missing
    else:
         print("DEBUG: API Key found.")

    # Create the Qt Application
    app = QApplication(sys.argv)

    print("DEBUG: Creating PetWindow...")
    # Create the Pet Window instance (this also shows the window via its initUI)
    try:
        pet_app_instance = PetWindow()
    except Exception as e:
        print(f"FATAL ERROR: Failed to create PetWindow: {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed traceback on GUI creation failure
        sys.exit(1)

    # --- Connect Signal ---
    # Connect the signal emitted by the pet on click to the function that starts the analysis thread
    print("DEBUG: Connecting cat_clicked_request_analysis signal...")
    try:
        pet_app_instance.cat_clicked_request_analysis.connect(start_analysis_on_click)
        print("DEBUG: Signal connected successfully.")
    except Exception as e:
        print(f"ERROR: Failed to connect signal cat_clicked_request_analysis: {e}")
        # Decide if this is fatal or not; probably is.
        # sys.exit(1)


    print("-" * 30)
    print("Desktop Pet Ready!")
    print("- Click the cat to analyze screen.")
    print("- Drag to move.")
    print("- Window should stay on top (except maybe fullscreen apps).")
    print("- Close window or Ctrl+C to quit.")
    print("-" * 30)

    # Start the Qt event loop - this blocks until the application quits
    exit_code = app.exec()

    # --- Cleanup ---
    print("DEBUG: Application event loop finished.")
    # No background scheduler thread to join anymore
    # Qt handles widget cleanup when app exits
    print("Cleanup complete. Exiting.")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()