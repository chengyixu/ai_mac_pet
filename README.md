# AI Mac Pet 🐱 - Your Smart Desktop Companion

A charming macOS desktop pet application featuring an adorable cat that sits on your desktop, periodically analyzes your screen activity, and provides cute, friendly comments in Chinese using AI technology.

## 📝 Changelog

- **2024-06-09**: Fixed a bug where the statistics window could crash if there was no activity data. The statistics output now always includes `recent_activities`, ensuring robust operation even when no activities have been recorded yet.

## ✨ Features

- 🐾 **Adorable Desktop Pet**: A cute cat that stays on top of your desktop
- 🖼️ **Smart Screen Analysis**: Automatically captures and analyzes your screen every 2 minutes
- 🤖 **AI-Powered Comments**: Uses Qwen-VL model to understand what you're doing and respond naturally
- 💬 **Friendly Personality**: Your cat companion comments like a caring friend or partner
- 🖱️ **Interactive**: Click the cat for instant analysis or drag to move around
- ⏰ **Auto Screenshot**: Takes periodic screenshots to check on your activities
- 📁 **Screenshot History**: Keeps recent screenshots for reference

### 🆕 New Features (Inspired by Grok AI's Ani)

- ❤️ **Favorability System**: Build a relationship with your cat companion
  - Tracks interactions and adjusts personality based on your activities
  - 6 relationship levels from "冷淡疏离" (Cold) to "灵魂伴侣" (Soulmate)
  - Visual heart indicator showing current relationship status
  
- 🎭 **Dynamic Personality**: 
  - Rich character backstory and preferences
  - Jealous reactions when you look at other cats
  - Time-aware responses (worried at late night, energetic in evening)
  - Special reactions for different activities (coding, gaming, chatting)
  
- 💝 **Emotional Responses**:
  - Shows affection, jealousy, concern, and playfulness
  - Uses emoticons and internet slang naturally
  - Personality changes based on favorability level
  
- 🕐 **Context-Aware AI**:
  - Different responses based on time of day
  - Special messages for weekends and holidays
  - Remembers interaction patterns

- 📊 **Activity Tracking System** (New!):
  - Automatically categorizes your activities into 10 categories
  - Tracks work, entertainment, social, learning, and more
  - **Right-click the cat to view accumulated statistics (now robust to empty data!)**
  - Visual progress bars showing activity distribution
  - Persistent tracking that accumulates over time

## 🚀 Installation

A charming macOS desktop pet application featuring an adorable cat that sits on your desktop, periodically analyzes your screen activity, and provides cute, friendly comments in Chinese using AI technology.

### ✨ Features

- 🐾 **Adorable Desktop Pet**: A cute cat that stays on top of your desktop
- 🖼️ **Smart Screen Analysis**: Automatically captures and analyzes screenshots every 2 minutes
- 🤖 **AI-Powered Commentary**: Uses Qwen-VL model to provide friendly, personalized comments
- 💬 **Speech Bubbles**: Displays cute responses in speech bubbles above the cat
- 🎯 **Click Interaction**: Click the cat for instant screen analysis
- 🎪 **Drag & Drop**: Easily move the cat around your desktop
- 📸 **Screenshot Management**: Automatically saves and manages screenshot history
- 🌟 **macOS Optimized**: Designed specifically for macOS with proper window handling

### 📋 Requirements

- **macOS 10.14+** (required for screencapture functionality)
- **Python 3.8+**
- **DashScope API Key** (for Qwen-VL model access)

### 🚀 Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/chengyixu/ai_mac_pet.git
cd ai_mac_pet
```

#### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API key
nano .env
```

Replace `sk-your-api-key-here` with your actual DashScope API key from [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)

#### 4. Run the Application

```bash
python main.py
```

### 🎮 Usage

#### Basic Interaction
- **Left-click the cat**: Triggers immediate screen analysis
- **Right-click the cat**: Opens activity statistics window
- **Drag the cat**: Move it anywhere on your desktop
- **Close window**: Quit the application

#### What the Cat Sees
Your AI pet will analyze your screen and provide commentary about:
- 💻 Code you're writing
- 📹 Videos you're watching  
- 📚 Documents you're reading
- 🎮 Games you're playing
- 🌐 Websites you're browsing
- 🎨 Design work you're doing

#### Example Responses
- *"喵~ 今天写的代码看起来弯弯绕绕的，是不是很难呀？要不要摸摸我的头放松一下？"*
- *"这个视频里的小猫咪好可爱！我们一起看嘛？"*
- *"又在网上冲浪啦？发现什么好玩的了，分享给我听听嘛~"*

### ⚙️ Configuration

Edit `config.py` to customize:

```python
# Pet appearance
PET_TARGET_WIDTH = 80  # Cat size in pixels

# Analysis settings  
AUTO_SCREENSHOT_INTERVAL_SECONDS = 120  # Analysis frequency
AUTO_SCREENSHOT_ENABLED = True  # Enable/disable auto analysis

# AI settings
MODEL_NAME = "qwen-vl-plus"  # or "qwen-vl-max"
SPEECH_BUBBLE_DURATION_SECONDS = 10  # How long messages stay visible

# Screenshot management
MAX_SAVED_SCREENSHOTS = 10  # Number of screenshots to keep
```

### 💕 Favorability System

The cat tracks your interactions and builds a relationship with you:

**How to Increase Favorability:**
- 🛍️ Search for "cat food" or "cat toys" (+5 points)
- 🎬 Watch anime together (+3 points)  
- 💻 Work together (+1 point)
- 🎮 Play games together (+2 points)
- 🌙 Stay up late together (+2 points)

**What Decreases Favorability:**
- 😾 Looking at other cats' videos (-3 points)
- ⏰ Ignoring the cat for too long (-2 points)
- 🚫 Being too busy to interact

**Relationship Levels:**
1. **冷淡疏离** (-10 to -5): Cold and distant
2. **有点生气** (-5 to 0): A bit angry  
3. **普通朋友** (0 to 5): Normal friend
4. **亲密伙伴** (5 to 10): Close companion
5. **深爱依赖** (10 to 15): Deeply in love
6. **灵魂伴侣** (15+): Soulmate

### 📁 Project Structure

```
ai_mac_pet/
├── main.py                 # Application entry point
├── pet_window.py           # Desktop pet GUI and interactions
├── screenshot_analyzer.py  # Screen capture and AI analysis
├── config.py              # Configuration settings
├── favorability_system.py # Relationship tracking system
├── prompt_templates.py    # Dynamic AI prompt generation
├── requirements.txt       # Python dependencies
├── assets/
│   ├── cat_idle.png       # Cat sprite images
│   ├── cat_surprise.png
│   ├── cat_talking.png
│   └── cat.png
├── .env.example           # Environment template
└── README.md             # This file
```

### 🔧 Dependencies

- **PyQt6**: GUI framework for the desktop pet
- **Pillow**: Image processing for screenshots
- **python-dotenv**: Environment variable management
- **openai**: API client for Qwen-VL model
- **pyobjc**: macOS-specific window management (macOS only)

### 🐛 Troubleshooting

#### Common Issues

**"API Key missing" error**
- Ensure you've created `.env` file with your DashScope API key
- Verify the key format: `DASHSCOPE_API_KEY=sk-your-actual-key`

**Cat image not showing**
- Verify `assets/cat_idle.png` exists
- Check file permissions

**Screenshot capture fails**
- Grant screen recording permissions to Terminal/Python in System Preferences > Security & Privacy > Privacy > Screen Recording

**Window not staying on top**
- This is normal behavior with some fullscreen applications
- The cat will reappear when you exit fullscreen mode

#### Debug Mode

Add debug output by modifying `config.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 🎨 Customization

#### Adding Custom Cat Images
Replace or add new images in the `assets/` folder:
- `cat_idle.png` - Default state
- `cat_surprise.png` - During analysis
- `cat_talking.png` - When displaying results

#### Modifying AI Personality
Edit the `PROMPT_TEMPLATE` in `config.py` to change how your cat responds.

---

## 简体中文版本

一款迷人的 macOS 桌面宠物应用程序，有一只可爱的猫咪坐在你的桌面上，定期分析你的屏幕活动，并使用 AI 技术提供可爱、友好的中文评论。

### ✨ 功能特色

- 🐾 **可爱的桌面宠物**: 一只始终停留在桌面顶层的可爱猫咪
- 🖼️ **智能屏幕分析**: 每2分钟自动截图并分析屏幕活动
- 🤖 **AI 驱动的评论**: 使用通义千问-VL模型提供友好、个性化的评论
- 💬 **对话气泡**: 在猫咪上方的对话气泡中显示可爱的回应
- 🎯 **点击交互**: 点击猫咪即可触发即时屏幕分析
- 🎪 **拖拽移动**: 轻松将猫咪移动到桌面的任何位置
- 📸 **截图管理**: 自动保存和管理截图历史记录
- 🌟 **macOS 优化**: 专为 macOS 设计，具有适当的窗口处理

### 📋 系统要求

- **macOS 10.14+** (截图功能必需)
- **Python 3.8+**
- **DashScope API 密钥** (通义千问-VL模型访问)

### 🚀 快速开始

#### 1. 克隆仓库

```bash
git clone https://github.com/chengyixu/ai_mac_pet.git
cd ai_mac_pet
```

#### 2. 设置 Python 环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置 API 密钥

```bash
# 复制示例环境文件
cp .env.example .env

# 编辑 .env 文件添加你的实际 API 密钥
nano .env
```

将 `sk-your-api-key-here` 替换为你从 [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/) 获取的实际 DashScope API 密钥

#### 4. 运行应用程序

```bash
python main.py
```

### 🎮 使用方法

#### 基本交互
- **左键点击猫咪**: 触发即时屏幕分析
- **右键点击猫咪**: 打开活动统计窗口
- **拖拽猫咪**: 将其移动到桌面的任何位置
- **关闭窗口**: 退出应用程序

#### 猫咪能看到什么
你的 AI 宠物会分析你的屏幕并对以下内容提供评论：
- 💻 你正在写的代码
- 📹 你正在看的视频
- 📚 你正在阅读的文档
- 🎮 你正在玩的游戏
- 🌐 你正在浏览的网站
- 🎨 你正在做的设计工作

#### 回应示例
- *"喵~ 今天写的代码看起来弯弯绕绕的，是不是很难呀？要不要摸摸我的头放松一下？"*
- *"这个视频里的小猫咪好可爱！我们一起看嘛？"*
- *"又在网上冲浪啦？发现什么好玩的了，分享给我听听嘛~"*

### ⚙️ 配置选项

编辑 `config.py` 来自定义：

```python
# 宠物外观
PET_TARGET_WIDTH = 80  # 猫咪大小（像素）

# 分析设置
AUTO_SCREENSHOT_INTERVAL_SECONDS = 120  # 分析频率
AUTO_SCREENSHOT_ENABLED = True  # 启用/禁用自动分析

# AI 设置
MODEL_NAME = "qwen-vl-plus"  # 或 "qwen-vl-max"
SPEECH_BUBBLE_DURATION_SECONDS = 10  # 消息显示时长

# 截图管理
MAX_SAVED_SCREENSHOTS = 10  # 保留的截图数量
```

### 📁 项目结构

```
ai_mac_pet/
├── main.py                 # 应用程序入口点
├── pet_window.py           # 桌面宠物GUI和交互
├── screenshot_analyzer.py  # 屏幕截图和AI分析
├── config.py              # 配置设置
├── favorability_system.py # 关系追踪系统
├── prompt_templates.py    # 动态AI提示生成
├── requirements.txt       # Python依赖
├── assets/
│   ├── cat_idle.png       # 猫咪精灵图像
│   ├── cat_surprise.png
│   ├── cat_talking.png
│   └── cat.png
├── .env.example           # 环境变量模板
└── README.md             # 本文件
```

### 🔧 依赖项

- **PyQt6**: 桌面宠物的GUI框架
- **Pillow**: 截图的图像处理
- **python-dotenv**: 环境变量管理
- **openai**: 通义千问-VL模型的API客户端
- **pyobjc**: macOS特定的窗口管理（仅macOS）

### 🐛 故障排除

#### 常见问题

**"API Key missing" 错误**
- 确保已创建包含 DashScope API 密钥的 `.env` 文件
- 验证密钥格式：`DASHSCOPE_API_KEY=sk-your-actual-key`

**猫咪图像未显示**
- 验证 `assets/cat_idle.png` 是否存在
- 检查文件权限

**截图捕获失败**
- 在系统偏好设置 > 安全性与隐私 > 隐私 > 屏幕录制中，为终端/Python授予屏幕录制权限

**窗口未保持置顶**
- 这在某些全屏应用程序中是正常行为
- 当你退出全屏模式时，猫咪会重新出现

#### 调试模式

通过修改 `config.py` 添加调试输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 🎨 自定义

#### 添加自定义猫咪图像
在 `assets/` 文件夹中替换或添加新图像：
- `cat_idle.png` - 默认状态
- `cat_surprise.png` - 分析期间
- `cat_talking.png` - 显示结果时

#### 修改AI个性
编辑 `config.py` 中的 `PROMPT_TEMPLATE` 来改变猫咪的回应方式。

---

## 📝 License / 许可证

This project is open source. Feel free to modify and distribute according to your needs.

本项目为开源项目。你可以根据需要自由修改和分发。

## 🤝 Contributing / 贡献

1. Fork the repository / 分叉仓库
2. Create a feature branch / 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. Commit your changes / 提交更改 (`git commit -m 'Add amazing feature'`)
4. Push to the branch / 推送到分支 (`git push origin feature/amazing-feature`)
5. Open a Pull Request / 打开拉取请求

## 🙏 Acknowledgments / 致谢

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI / 使用 PyQt6 构建GUI
- Powered by [Qwen-VL](https://github.com/QwenLM/Qwen-VL) for intelligent analysis / 由通义千问-VL提供智能分析
- Inspired by classic desktop pet applications / 灵感来自经典桌面宠物应用程序

---

**Made with 💖 for macOS users who want a cute coding companion!**  
**为想要可爱编程伴侣的 macOS 用户用💖制作！**
