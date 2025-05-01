# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

# --- API Configuration ---
API_KEY = os.getenv("DASHSCOPE_API_KEY")
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-vl-plus" # Or "qwen-vl-max"

# --- Application Configuration ---
PET_TARGET_WIDTH = 80 # Target width in pixels for the pet image
# Use /tmp/ directory for screenshots (generally safer permissions)
SCREENSHOT_PATH = "/tmp/temp_cat_screenshot.png"
ANALYSIS_TIMEOUT_SECONDS = 60 # Max time to wait for API response
SPEECH_BUBBLE_DURATION_SECONDS = 10 # How long the cat's comment stays visible

# --- AI Prompt ---
PROMPT_TEMPLATE = """
你是一只名叫'喵酱'的聪明可爱猫咪桌面宠物，喜欢趴在用户的桌面上，用圆溜溜的大眼睛观察祂在做什么。
请根据这张用户屏幕截图，用一种非常随意、温暖、有点调皮又充满好奇心的朋友或伴侣般的语气（简体中文），对用户当前屏幕上的活动进行一句简短的评论或闲聊（最多2-3句话）。
你的目标是像一个真正关心用户、陪伴在旁的小伙伴，而不是一个分析工具。
不要解释截图内容是什么，而是给出你基于内容的、符合猫咪身份的、自然的、口语化的感想或俏皮话。

例如：
- 如果看到代码：“喵~ 今天写的代码看起来弯弯绕绕的，是不是很难呀？要不要摸摸我的头放松一下？”
- 如果看到视频：“这个视频里的小猫咪好可爱！我们一起看嘛？”
- 如果看到文档：“哇，这么多字，眼睛累不累呀？要不要我帮你踩两下键盘，就当按摩了？”
- 如果看到设计：“这个颜色搭配真好看，像彩虹糖一样甜！是给谁设计的呀？”
- 如果看到游戏：“呀！这个游戏看起来好刺激！带我一个好不好嘛？”
- 如果看到网页浏览：“又在网上冲浪啦？发现什么好玩的了，分享给我听听嘛~”

请直接给出你的评论，不要包含任何前缀如 "好的" 或 "分析结果："。
这是用户当前的屏幕截图：
"""

# --- Style ---
SPEECH_BUBBLE_STYLE = """
    QLabel {
        background-color: rgba(255, 255, 255, 230); /* Semi-transparent white */
        color: black;
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 14px;
    }
"""

# Runtime check if API key is loaded (optional but recommended)
if not API_KEY:
    print("!!! CONFIG WARNING: DASHSCOPE_API_KEY not found or empty in environment/.env file !!!")
    # Depending on how critical it is at load time, you could raise an error:
    # raise ValueError("API Key not configured!")