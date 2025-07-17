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
import json
from collections import deque
from typing import Dict
import re
import config # Import settings from config.py
from favorability_system import FavorabilitySystem  # Import favorability system
from prompt_templates import PromptTemplateManager  # Import prompt templates
from activity_tracker import ActivityTracker  # Import activity tracker

# Configure the OpenAI client for DashScope
# Ensure API_KEY and API_BASE_URL are correctly set in config.py / .env
client = OpenAI(
    api_key=config.API_KEY,
    base_url=config.API_BASE_URL,
)

# Initialize favorability system
favorability = FavorabilitySystem()
prompt_manager = PromptTemplateManager()
activity_tracker = ActivityTracker()

# Message history tracking
MESSAGE_HISTORY_FILE = "/tmp/cat_message_history.json"
MAX_HISTORY_SIZE = 20  # Keep track of last 20 messages

class MessageHistory:
    """Tracks recent messages to avoid repetition."""
    
    def __init__(self, history_file=MESSAGE_HISTORY_FILE, max_size=MAX_HISTORY_SIZE):
        self.history_file = history_file
        self.max_size = max_size
        self.messages = deque(maxlen=max_size)
        self._load_history()
    
    def _load_history(self):
        """Load message history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = deque(data.get('messages', []), maxlen=self.max_size)
            except Exception as e:
                print(f"DEBUG: Could not load message history: {e}")
                self.messages = deque(maxlen=self.max_size)
    
    def _save_history(self):
        """Save message history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'messages': list(self.messages)}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"WARNING: Could not save message history: {e}")
    
    def add_message(self, message: str):
        """Add a message to history."""
        self.messages.append({
            'text': message,
            'timestamp': datetime.datetime.now().isoformat()
        })
        self._save_history()
    
    def get_recent_messages(self, count: int = 5) -> list:
        """Get the most recent messages."""
        return [msg['text'] for msg in list(self.messages)[-count:]]
    
    def contains_similar(self, message: str, threshold: float = 0.7) -> bool:
        """Check if a similar message exists in recent history."""
        # Simple similarity check - you could make this more sophisticated
        message_lower = message.lower().strip()
        for msg in self.messages:
            msg_lower = msg['text'].lower().strip()
            # Check for exact matches or very similar content
            if msg_lower == message_lower:
                return True
            # Check if core content is the same (ignoring emojis/punctuation)
            if self._similarity_ratio(msg_lower, message_lower) > threshold:
                return True
        return False
    
    def _similarity_ratio(self, s1: str, s2: str) -> float:
        """Calculate simple similarity ratio between two strings."""
        # Remove emojis and special characters for comparison
        import re
        s1_clean = re.sub(r'[^\w\s]', '', s1)
        s2_clean = re.sub(r'[^\w\s]', '', s2)
        
        if not s1_clean or not s2_clean:
            return 0.0
        
        # Simple word overlap ratio
        words1 = set(s1_clean.split())
        words2 = set(s2_clean.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

# Initialize message history
message_history = MessageHistory()

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


def analyze_activities_with_qwen(base64_image_url: str) -> Dict[str, float]:
    """
    Analyze screenshot for activity categories using Qwen.
    Returns dictionary of category -> percentage.
    """
    activity_prompt = """
请分析这个屏幕截图，判断用户正在进行什么类型的活动。
将活动分类到以下类别中，给出每个类别的百分比（总和必须为100%）：

1. 工作编程 - 编写代码、使用IDE、终端命令等
2. 娱乐休闲 - 看视频、听音乐、浏览娱乐内容等
3. 社交聊天 - 使用聊天软件、发邮件、社交媒体等
4. 学习研究 - 阅读文档、查资料、在线课程等
5. 创作设计 - 使用设计软件、绘画、视频剪辑等
6. 系统管理 - 系统设置、文件管理、软件安装等
7. 网页浏览 - 一般性网页浏览
8. 视频媒体 - 专门的视频播放器、音乐播放器
9. 游戏 - 玩游戏
10. 其他 - 不属于以上类别的活动

请用以下JSON格式回复（只返回JSON，不要有其他内容）：
{
  "工作编程": 70,
  "学习研究": 30,
  "娱乐休闲": 0,
  "社交聊天": 0,
  "创作设计": 0,
  "系统管理": 0,
  "网页浏览": 0,
  "视频媒体": 0,
  "游戏": 0,
  "其他": 0
}
"""
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": activity_prompt},
                        {"type": "image_url", "image_url": {"url": base64_image_url}}
                    ]
                }
            ],
            timeout=10  # Shorter timeout for activity analysis
        )
        
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            response_text = completion.choices[0].message.content.strip()
            print(f"DEBUG: Activity analysis response: {response_text}")
            
            # Try to parse JSON response
            try:
                # Remove any non-JSON content
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                if json_match:
                    activity_data = json.loads(json_match.group())
                    # Validate and normalize
                    valid_categories = activity_tracker.ACTIVITY_CATEGORIES
                    result = {}
                    for cat in valid_categories:
                        result[cat] = float(activity_data.get(cat, 0))
                    return result
            except Exception as e:
                print(f"WARNING: Could not parse activity JSON: {e}")
    
    except Exception as e:
        print(f"WARNING: Activity analysis failed: {e}")
    
    # Fallback: use keyword-based analysis from the main response
    return {}

def analyze_screenshot_with_qwen(image_path: str) -> tuple:
    """
    Encodes the image, sends it to Qwen-VL model for analysis via DashScope API.
    Returns tuple of (analysis_text, favorability_change)
    """
    print("DEBUG: analyze_screenshot_with_qwen called.")
    analysis_result_text = "喵？（内部处理时有点问题...）" # Default fallback message
    favorability_change = 0

    # --- Pre-API Checks ---
    if not config.API_KEY:
         print("ERROR: API Key is missing in analyze_screenshot_with_qwen.")
         return "喵？（主人没给我钥匙欸... API Key missing!）", 0 # Return error tuple

    if not os.path.exists(image_path):
        print(f"ERROR: Image file not found before encoding: {image_path}")
        return "喵？（图片在处理前就消失了欸...）", 0 # Return error tuple

    # --- Encode Image ---
    print("DEBUG: Encoding image for API...")
    base64_image_url = encode_image_to_base64(image_path)
    if not base64_image_url:
        print("ERROR: Failed to encode image for API.")
        # Try to delete the file even if encoding failed, as analysis won't proceed
        if os.path.exists(image_path):
             try: os.remove(image_path); print("DEBUG: Cleaned up file after encoding failure.")
             except OSError as e: print(f"WARNING: Failed to cleanup file after encoding failure: {e}")
        return "喵？图片好像编码失败了...", 0 # Return error tuple

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
         return "喵~ （图片还是太大了，API不喜欢...）", 0 # Return specific error tuple

    # Get favorability modifier and generate dynamic prompt
    mood_modifier = favorability.get_mood_modifier()
    current_level = favorability.get_current_level()
    
    # Generate dynamic prompt using the template manager
    enhanced_prompt = prompt_manager.generate_prompt(
        mood_state=mood_modifier,
        favorability_level=current_level
    )
    
    # Add recent message history to prompt to avoid repetition
    recent_messages = message_history.get_recent_messages(count=5)
    if recent_messages:
        enhanced_prompt += "\n\n【最近说过的话】请避免重复以下内容，要说些不同的话：\n"
        for i, msg in enumerate(recent_messages, 1):
            enhanced_prompt += f"{i}. {msg}\n"
        enhanced_prompt += "\n请确保你的回复与上述内容明显不同，换个话题或用不同的方式表达关心。"

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
                        {"type": "text", "text": enhanced_prompt},
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
                  # Check if the response is too similar to recent messages
                  if message_history.contains_similar(analysis_result_text, threshold=0.6):
                      print("DEBUG: Response too similar to recent messages, requesting variety...")
                      # Add a note to regenerate with more variety
                      analysis_result_text = "喵喵想想...还能说什么呢？"  # Fallback while we implement retry logic
        else:
             # Handle cases where response structure is wrong or content is missing
             print("ERROR: Qwen response structure unexpected or content missing/empty.")
             print(f"DEBUG: Full API Response object for inspection: {completion}")
             analysis_result_text = "喵~ （API 的回应有点奇怪...）"

        # Add successful response to history (but not error messages)
        if not any(error_phrase in analysis_result_text for error_phrase in ["API", "错误", "失败", "内容是空的"]):
            message_history.add_message(analysis_result_text)
            print(f"DEBUG: Added message to history. Total messages tracked: {len(message_history.messages)}")

        # Analyze activities from the screenshot
        print("DEBUG: Analyzing activities from screenshot...")
        activity_breakdown = analyze_activities_with_qwen(base64_image_url)
        
        # If activity analysis failed, try keyword-based fallback
        if not activity_breakdown or all(v == 0 for v in activity_breakdown.values()):
            print("DEBUG: Using keyword-based activity analysis as fallback...")
            activity_breakdown = activity_tracker.analyze_screenshot_for_activities(analysis_result_text)
        
        # Record the activity
        if activity_breakdown:
            activity_tracker.record_activity(activity_breakdown, analysis_result_text)
            print(f"DEBUG: Recorded activity breakdown: {activity_breakdown}")

        # Calculate favorability change based on the analysis
        favorability_change = favorability.analyze_screen_content(analysis_result_text)
        
    # --- Handle Specific API/Network Errors ---
    except APITimeoutError:
         print(f"ERROR: Qwen API request timed out after {config.ANALYSIS_TIMEOUT_SECONDS} seconds.")
         analysis_result_text = f"喵... （反应太慢了... Timeout! {config.ANALYSIS_TIMEOUT_SECONDS}s）"
         favorability_change = -1  # Slight negative for timeout
    except RateLimitError as e:
         print(f"ERROR: Qwen API rate limit exceeded. {e}")
         analysis_result_text = "喵~ 让我歇会儿！（Rate Limit）"
         favorability_change = 0
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
         favorability_change = 0
         # Specific check for the size error we encountered before
         if "max bytes per data-uri item" in error_body_msg:
             print("ERROR: Received data-uri size limit error from API again.")
             analysis_result_text = "喵~ （图片还是太大了，API 不收...）" # More specific message

    except Exception as e: # Catch any other unexpected exceptions (network, library bugs, etc.)
         print(f"ERROR: Unexpected error during API call: {e}")
         analysis_result_text = "喵？！发生了一些奇怪的事情..."
         favorability_change = 0

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

    return analysis_result_text, favorability_change


def run_analysis_cycle() -> tuple: # Ensure it always returns a tuple
    """
    Performs one cycle of capture, resize/compress, and analysis.
    Returns tuple of (analysis_result, favorability_change)
    """
    print("DEBUG: --- Starting Analysis Cycle (Triggered) ---")
    screenshot_file = capture_screenshot()
    analysis_result = "喵？（开始就出错了...）" # Default error if capture fails
    favorability_change = 0

    if screenshot_file:
        # ---- RESIZE/COMPRESS THE IMAGE before analysis ----
        # Use a reasonable size limit; adjust if needed
        compress_image(screenshot_file, max_size=(1920, 1920))
        # --------------------------------------------------

        # Proceed with analysis using the (potentially resized) image file
        # analyze_screenshot_with_qwen handles its own errors and returns a tuple
        analysis_result, favorability_change = analyze_screenshot_with_qwen(screenshot_file)

        # Update favorability if there's a change
        if favorability_change != 0:
            new_level, level_changed = favorability.update_favorability(
                favorability_change, 
                "屏幕活动分析"
            )
            print(f"DEBUG: Favorability updated: {favorability_change:+d} -> Level {new_level}")
            
            # Add special responses at certain levels
            if level_changed:
                special_responses = favorability.get_special_responses()
                if special_responses:
                    # Append a special response to the analysis
                    analysis_result += f"\n{special_responses[0]}"

        # Final check if analysis returned None/empty (shouldn't happen with current logic)
        if not isinstance(analysis_result, str) or not analysis_result:
             print("ERROR: Analysis function returned invalid result even after checks. Using fallback.")
             analysis_result = "喵？（分析步骤出错了...）"
    else:
        # capture_screenshot failed, set specific error message
        print("ERROR: Screenshot capture failed in cycle.")
        analysis_result = "喵？（截图失败了欸...）"


    print(f"DEBUG: Analysis cycle finished. Result to be returned: '{analysis_result}'")
    return analysis_result, favorability_change # Always return a tuple