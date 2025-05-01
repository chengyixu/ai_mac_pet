# screenshot_analyzer.py
import base64
import subprocess
import os
import time
import glob
import datetime
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from PIL import Image # Requires Pillow library: pip install Pillow
import io
import config # Import settings from config.py

# Configure the OpenAI client for DashScope
# Ensure API_KEY and API_BASE_URL are correctly set in config.py / .env
client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.API_BASE_URL,
)

def ensure_screenshot_directory():
    """Ensures the screenshot directory exists."""
    if not os.path.exists(config.SCREENSHOT_DIRECTORY):
        try:
            os.makedirs(config.SCREENSHOT_DIRECTORY)
            print(f"DEBUG: Created screenshot directory: {config.SCREENSHOT_DIRECTORY}")
        except OSError as e:
            print(f"ERROR: Could not create screenshot directory: {e}")
            return False
    return True

def clean_old_screenshots():
    """Keeps only the most recent MAX_SAVED_SCREENSHOTS screenshots."""
    if not ensure_screenshot_directory():
        return
        
    try:
        # Get all screenshot files in the directory
        screenshot_pattern = os.path.join(config.SCREENSHOT_DIRECTORY, "cat_screenshot_*.png")
        screenshot_files = glob.glob(screenshot_pattern)
        
        # Sort by modification time (newest last)
        screenshot_files.sort(key=os.path.getmtime)
        
        # If we have more than our limit, delete the oldest ones
        if len(screenshot_files) > config.MAX_SAVED_SCREENSHOTS:
            files_to_delete = screenshot_files[:-config.MAX_SAVED_SCREENSHOTS]
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    print(f"DEBUG: Deleted old screenshot: {file_path}")
                except OSError as e:
                    print(f"WARNING: Failed to delete old screenshot {file_path}: {e}")
                    
            print(f"DEBUG: Kept {config.MAX_SAVED_SCREENSHOTS} most recent screenshots")
        else:
            print(f"DEBUG: Only {len(screenshot_files)} screenshots stored, below limit of {config.MAX_SAVED_SCREENSHOTS}")
    except Exception as e:
        print(f"ERROR: Failed to clean old screenshots: {e}")

def get_timestamp_filename():
    """Generates a timestamped filename for the screenshot."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return config.SCREENSHOT_FILENAME_FORMAT.format(timestamp=timestamp)

def capture_screenshot() -> str | None:
    """
    Captures the main screen and saves it to a timestamped file path.
    Returns the path to the saved screenshot or None if failed.
    """
    print("DEBUG: Attempting screenshot capture...")
    
    # For the analysis process, we still use the temp screenshot path
    screenshot_path = config.SCREENSHOT_PATH
    
    try:
        # Ensure the screenshot directory exists
        if not ensure_screenshot_directory():
            return None
            
        # Using /tmp/, usually writable without special permissions
        command = ['screencapture', '-x', screenshot_path]
        print(f"DEBUG: Running command: {' '.join(command)}")
        # Run the command. check=True raises CalledProcessError on non-zero exit.
        subprocess.run(command, check=True, timeout=10) # 10 second timeout
        print(f"DEBUG: Screenshot saved to {screenshot_path}")
        
        # Verify file exists immediately after command returns
        if os.path.exists(screenshot_path):
            print("DEBUG: Screenshot file verified.")
            
            # For permanent storage, save a copy with timestamp to the storage directory
            timestamp_filename = get_timestamp_filename()
            permanent_path = os.path.join(config.SCREENSHOT_DIRECTORY, timestamp_filename)
            
            try:
                # Copy the file to permanent storage
                Image.open(screenshot_path).save(permanent_path)
                print(f"DEBUG: Saved permanent copy to {permanent_path}")
                
                # Clean up old screenshots if we have too many
                clean_old_screenshots()
            except Exception as e:
                print(f"WARNING: Failed to save permanent copy: {e}")
            
            return screenshot_path
        else:
            # This case is unlikely if check=True didn't raise error, but good sanity check
            print("ERROR: Screenshot command ran but file not found immediately after!")
            return None
    except FileNotFoundError:
        # Handle case where screencapture command itself isn't found
        print(f"ERROR: 'screencapture' command not found. Is this macOS and is it in the PATH?")
        return None
    except subprocess.CalledProcessError as e:
        # screencapture command returned a non-zero exit code
        print(f"ERROR: Screenshot command failed with exit code {e.returncode} - {e}")
        return None
    except subprocess.TimeoutExpired:
        # Command took longer than the timeout
        print("ERROR: Screenshot command timed out")
        return None
    except Exception as e:
        # Catch any other unexpected exceptions
        print(f"ERROR: Unexpected error during screenshot capture: {e}")
        return None

def encode_image_to_base64(image_path: str) -> str | None:
    """Reads an image file and encodes it to base64 data URL."""
    print(f"DEBUG: Attempting to encode image: {image_path}")
    try:
        # Assume png format from screencapture. Could add logic to detect format if needed.
        image_format = "png"
        with open(image_path, "rb") as image_file:
            # Read the binary data
            binary_data = image_file.read()
            # Encode to base64 bytes, then decode to utf-8 string
            base64_encoded_string = base64.b64encode(binary_data).decode('utf-8')
            print(f"DEBUG: Image encoded successfully. Base64 string length: {len(base64_encoded_string)}")
            # Construct the data URI
            return f"data:image/{image_format};base64,{base64_encoded_string}"
    except FileNotFoundError:
        print(f"ERROR: Encoding failed - File not found at {image_path}")
        return None
    except Exception as e:
        print(f"ERROR: Encoding failed - {e}")
        return None

def compress_image(image_path: str, max_size=(1920, 1920)): # Default max dimensions
    """
    Resizes image proportionally to fit within max_size using Pillow
    and saves it back as an optimized PNG, overwriting the original file.
    """
    try:
        print(f"DEBUG: Resizing image to fit within {max_size}: {image_path}")
        # Open the image using Pillow
        img = Image.open(image_path)
        original_size = img.size
        print(f"DEBUG: Original image size: {original_size}")

        # thumbnail modifies the image object in-place, maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS) # LANCZOS is high quality filter

        # Save the resized image back to the *same path* as an optimized PNG
        img.save(image_path, "PNG", optimize=True)
        # Verify size after saving (optional)
        final_size_bytes = os.path.getsize(image_path)
        print(f"DEBUG: Image resized from {original_size} to {img.size}. Final file size: {final_size_bytes / 1024:.1f} KB.")
    except FileNotFoundError:
         print(f"ERROR: Cannot compress/resize - File not found: {image_path}")
         # Indicate failure? For now, just log error. Subsequent steps might fail.
    except Exception as e:
        # Log a warning if compression/resize fails, but allow the process to continue.
        # The original (potentially large) image will be used if this fails.
        print(f"WARNING: Could not compress/resize image {image_path}: {e}")


def analyze_screenshot_with_qwen(image_path: str) -> str:
    """
    Encodes the image, sends it to Qwen-VL model for analysis via DashScope API.
    Always returns a string (either the analysis result or an error message).
    """
    print("DEBUG: analyze_screenshot_with_qwen called.")
    analysis_result_text = "喵？（内部处理时有点问题...）" # Default fallback message

    # --- Pre-API Checks ---
    if not config.API_KEY:
         print("ERROR: API Key is missing in analyze_screenshot_with_qwen.")
         return "喵？（主人没给我钥匙欸... API Key missing!）" # Return error string

    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found before encoding: {image_path}")
        return "喵？（图片在处理前就消失了欸...）" # Return error string

    # --- Encode Image ---
    print("DEBUG: Encoding image for API...")
    base64_image_url = encode_image_to_base64(image_path)
    if not base64_image_url:
        print("ERROR: Failed to encode image for API.")
        # Try to delete the file even if encoding failed, as analysis won't proceed
        if os.path.exists(image_path):
             try: os.remove(image_path); print("DEBUG: Cleaned up file after encoding failure.")
             except OSError as e: print(f"WARNING: Failed to cleanup file after encoding failure: {e}")
        return "喵？图片好像编码失败了..." # Return error string

    # --- Check Encoded Size BEFORE API Call (Approximate) ---
    # Calculate approximate size in bytes (Base64 string length * 3/4)
    approx_bytes = len(base64_image_url) * 0.75
    # Limit from API error was 10 * 1024 * 1024 bytes
    api_limit_bytes = 10 * 1024 * 1024
    print(f"DEBUG: Approximate Base64 data size: {approx_bytes / (1024*1024):.2f} MB")
    if approx_bytes > api_limit_bytes:
         print(f"ERROR: Estimated Base64 size ({approx_bytes / (1024*1024):.2f} MB) exceeds API limit ({api_limit_bytes / (1024*1024)} MB) even after resize attempt!")
         # Delete the file as analysis won't proceed
         if os.path.exists(image_path):
              try: os.remove(image_path); print("DEBUG: Cleaned up oversized file.")
              except OSError as e: print(f"WARNING: Failed to cleanup oversized file: {e}")
         return "喵~ （图片还是太大了，API不喜欢...）" # Return specific error string

    # --- Call API ---
    print("DEBUG: Sending request to Qwen API...")
    start_time = time.time()
    try:
        completion = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": config.PROMPT_TEMPLATE},
                        {"type": "image_url", "image_url": {"url": base64_image_url}}
                    ]
                }
            ],
            timeout=config.ANALYSIS_TIMEOUT_SECONDS # Pass timeout if supported by library version
        )
        end_time = time.time()
        print(f"DEBUG: Qwen response received in {end_time - start_time:.2f} seconds.")

        # --- Process Response ---
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
             analysis_result_text = completion.choices[0].message.content.strip()
             print(f"DEBUG: Analysis result extracted: '{analysis_result_text}'")
             # Ensure result is not empty string
             if not analysis_result_text:
                  print("WARNING: API returned an empty content string.")
                  analysis_result_text = "喵~ （API 好像没说话... 内容是空的。）"
        else:
             # Handle cases where response structure is wrong or content is missing
             print("ERROR: Qwen response structure unexpected or content missing/empty.")
             print(f"DEBUG: Full API Response object for inspection: {completion}")
             analysis_result_text = "喵~ （API 的回应有点奇怪...）"

    # --- Handle Specific API/Network Errors ---
    except APITimeoutError:
         print(f"ERROR: Qwen API request timed out after {config.ANALYSIS_TIMEOUT_SECONDS} seconds.")
         analysis_result_text = f"喵... （反应太慢了... Timeout! {config.ANALYSIS_TIMEOUT_SECONDS}s）"
    except RateLimitError as e:
         print(f"ERROR: Qwen API rate limit exceeded. {e}")
         analysis_result_text = "喵~ 让我歇会儿！（Rate Limit）"
    except APIError as e: # Catch other DashScope/OpenAI specific API errors
         print(f"ERROR: Qwen API returned an error. Status Code: {e.status_code}, Response: {e.response}, Body: {e.body}, Message: {e}")
         # Try to extract a meaningful message from the error body for the user
         error_body_msg = "Unknown API Error"
         if isinstance(e.body, dict):
              # Look for common error message fields
              error_body_msg = e.body.get('message', e.body.get('msg', str(e.body)))
         elif e.body: # If body is not a dict but exists
              error_body_msg = str(e.body)
         else: # Fallback to the string representation of the error
             error_body_msg = str(e)
         # Prepend our cat prefix
         analysis_result_text = f"喵呜！API 出错了：{error_body_msg}"
         # Specific check for the size error we encountered before
         if "max bytes per data-uri item" in error_body_msg:
             print("ERROR: Received data-uri size limit error from API again.")
             analysis_result_text = "喵~ （图片还是太大了，API 不收...）" # More specific message

    except Exception as e: # Catch any other unexpected exceptions (network, library bugs, etc.)
         print(f"ERROR: Unexpected error during API call: {e}")
         analysis_result_text = "喵？！发生了一些奇怪的事情..."

    # --- File Cleanup (runs regardless of API success/failure) ---
    if os.path.exists(image_path) and image_path == config.SCREENSHOT_PATH:
        try:
            os.remove(image_path)
            print(f"DEBUG: Temporary screenshot {image_path} deleted after analysis attempt.")
        except OSError as e:
            print(f"WARNING: Error deleting temp screenshot {image_path} after analysis attempt: {e}")
    else:
         # This shouldn't happen if capture worked, but check anyway
         print(f"WARNING: Temp screenshot {image_path} not found for deletion after analysis attempt.")


    # --- Return Result ---
    # Ensure we always return a non-empty string
    if not isinstance(analysis_result_text, str) or not analysis_result_text:
        print(f"WARNING: Final analysis result was invalid ('{analysis_result_text}'). Using fallback.")
        analysis_result_text = "喵？（嗯... 最后有点小混乱。）"

    return analysis_result_text


def run_analysis_cycle() -> str: # Ensure it always returns a string
    """
    Performs one cycle of capture, resize/compress, and analysis.
    Returns the analysis result or an error message as a string.
    """
    print("DEBUG: --- Starting Analysis Cycle (Triggered) ---")
    screenshot_file = capture_screenshot()
    analysis_result = "喵？（开始就出错了...）" # Default error if capture fails

    if screenshot_file:
        # ---- RESIZE/COMPRESS THE IMAGE before analysis ----
        # Use a reasonable size limit; adjust if needed
        compress_image(screenshot_file, max_size=(1920, 1920))
        # --------------------------------------------------

        # Proceed with analysis using the (potentially resized) image file
        # analyze_screenshot_with_qwen handles its own errors and returns a string
        analysis_result = analyze_screenshot_with_qwen(screenshot_file)

        # Final check if analysis returned None/empty (shouldn't happen with current logic)
        if not isinstance(analysis_result, str) or not analysis_result:
             print("ERROR: Analysis function returned invalid result even after checks. Using fallback.")
             analysis_result = "喵？（分析步骤出错了...）"
    else:
        # capture_screenshot failed, set specific error message
        print("ERROR: Screenshot capture failed in cycle.")
        analysis_result = "喵？（截图失败了欸...）"


    print(f"DEBUG: Analysis cycle finished. Result to be returned: '{analysis_result}'")
    return analysis_result # Always return a string (result or error message)