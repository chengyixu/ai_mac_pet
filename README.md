# 🐱 AI Mac Pet - Intelligent Desktop Cat Companion

A charming macOS desktop pet application featuring an adorable cat that sits on your desktop, periodically analyzes your screen activity, and provides cute, friendly commentary in Chinese using AI technology.

![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)

## ✨ Features

- 🐾 **Adorable Desktop Pet**: A cute cat that stays on top of your desktop
- 🖼️ **Smart Screen Analysis**: Automatically captures and analyzes screenshots every 2 minutes
- 🤖 **AI-Powered Commentary**: Uses Qwen-VL model to provide friendly, personalized comments
- 💬 **Speech Bubbles**: Displays cute responses in speech bubbles above the cat
- 🎯 **Click Interaction**: Click the cat for instant screen analysis
- 🎪 **Drag & Drop**: Easily move the cat around your desktop
- 📸 **Screenshot Management**: Automatically saves and manages screenshot history
- 🌟 **macOS Optimized**: Designed specifically for macOS with proper window handling

## 📋 Requirements

- **macOS 10.14+** (required for screencapture functionality)
- **Python 3.8+**
- **DashScope API Key** (for Qwen-VL model access)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/chengyixu/ai_mac_pet.git
cd ai_mac_pet
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API key
nano .env
```

Replace `sk-your-api-key-here` with your actual DashScope API key from [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)

### 4. Run the Application

```bash
python main.py
```

## 🎮 Usage

### Basic Interaction
- **Click the cat**: Triggers immediate screen analysis
- **Drag the cat**: Move it anywhere on your desktop
- **Close window**: Quit the application

### What the Cat Sees
Your AI pet will analyze your screen and provide commentary about:
- 💻 Code you're writing
- 📹 Videos you're watching  
- 📚 Documents you're reading
- 🎮 Games you're playing
- 🌐 Websites you're browsing
- 🎨 Design work you're doing

### Example Responses
- *"喵~ 今天写的代码看起来弯弯绕绕的，是不是很难呀？要不要摸摸我的头放松一下？"*
- *"这个视频里的小猫咪好可爱！我们一起看嘛？"*
- *"又在网上冲浪啦？发现什么好玩的了，分享给我听听嘛~"*

## ⚙️ Configuration

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

## 📁 Project Structure

```
ai_mac_pet/
├── main.py                 # Application entry point
├── pet_window.py           # Desktop pet GUI and interactions
├── screenshot_analyzer.py  # Screen capture and AI analysis
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── assets/
│   └── cat_idle.png       # Cat sprite image
├── .env.example           # Environment template
└── README.md             # This file
```

## 🔧 Dependencies

- **PyQt6**: GUI framework for the desktop pet
- **Pillow**: Image processing for screenshots
- **python-dotenv**: Environment variable management
- **openai**: API client for Qwen-VL model
- **pyobjc**: macOS-specific window management (macOS only)

## 🐛 Troubleshooting

### Common Issues

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

### Debug Mode

Add debug output by modifying `config.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎨 Customization

### Adding Custom Cat Images
Replace or add new images in the `assets/` folder:
- `cat_idle.png` - Default state
- `cat_thinking.png` - During analysis (optional)
- `cat_talking.png` - When displaying results (optional)

### Modifying AI Personality
Edit the `PROMPT_TEMPLATE` in `config.py` to change how your cat responds:

```python
PROMPT_TEMPLATE = """
你是一只名叫'喵酱'的聪明可爱猫咪桌面宠物...
[Customize personality here]
"""
```

## 📝 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI
- Powered by [Qwen-VL](https://github.com/QwenLM/Qwen-VL) for intelligent analysis
- Inspired by classic desktop pet applications

---

**Made with 💖 for macOS users who want a cute coding companion!**
