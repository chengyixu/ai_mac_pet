# activity_tracker.py
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import threading

class ActivityTracker:
    """
    Tracks and categorizes user activities from screenshot analyses.
    Maintains cumulative statistics of different activity categories.
    """
    
    ACTIVITY_CATEGORIES = [
        "工作编程",      # Work/Programming
        "娱乐休闲",      # Entertainment/Leisure
        "社交聊天",      # Social/Chatting
        "学习研究",      # Learning/Research
        "创作设计",      # Creation/Design
        "系统管理",      # System Management
        "网页浏览",      # Web Browsing
        "视频媒体",      # Video/Media
        "游戏",         # Gaming
        "其他"          # Other
    ]
    
    def __init__(self, data_file: str = "/tmp/cat_activity_data.json"):
        self.data_file = data_file
        self.lock = threading.Lock()
        self.data = self._load_data()
        
        # Initialize categories if new file
        if "total_analyses" not in self.data:
            self.data = {
                "total_analyses": 0,
                "category_scores": {cat: 0.0 for cat in self.ACTIVITY_CATEGORIES},
                "activity_history": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_data()
    
    def _load_data(self) -> Dict:
        """Load activity data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"ERROR: Could not load activity data: {e}")
                return {}
        return {}
    
    def _save_data(self):
        """Save activity data to file."""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERROR: Could not save activity data: {e}")
    
    def record_activity(self, activity_breakdown: Dict[str, float], screenshot_analysis: str = ""):
        """
        Record a new activity analysis.
        
        Args:
            activity_breakdown: Dictionary of category -> percentage (0-100)
            screenshot_analysis: Optional text analysis for context
        """
        with self.lock:
            # Validate and normalize percentages
            total = sum(activity_breakdown.values())
            if total > 0:
                # Normalize to ensure sum is 100
                normalized = {k: (v / total) * 100 for k, v in activity_breakdown.items()}
            else:
                normalized = activity_breakdown
            
            # Update cumulative scores
            self.data["total_analyses"] += 1
            for category, percentage in normalized.items():
                if category in self.data["category_scores"]:
                    # Add weighted percentage to cumulative score
                    self.data["category_scores"][category] += percentage
            
            # Add to history (keep last 1000 records)
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "breakdown": normalized,
                "analysis_text": screenshot_analysis[:200] if screenshot_analysis else ""
            }
            self.data["activity_history"].append(history_entry)
            if len(self.data["activity_history"]) > 1000:
                self.data["activity_history"] = self.data["activity_history"][-1000:]
            
            self.data["last_updated"] = datetime.now().isoformat()
            self._save_data()
            
            print(f"DEBUG: Recorded activity - {normalized}")
    
    def get_statistics(self) -> Dict:
        """
        Get current activity statistics.
        
        Returns:
            Dictionary with total analyses and percentage breakdown by category
        """
        with self.lock:
            if self.data["total_analyses"] == 0:
                return {
                    "total_analyses": 0,
                    "percentages": {cat: 0.0 for cat in self.ACTIVITY_CATEGORIES},
                    "last_updated": "Never",
                    "recent_activities": []
                }
            
            # Calculate average percentages
            percentages = {}
            for category, total_score in self.data["category_scores"].items():
                percentages[category] = round(total_score / self.data["total_analyses"], 1)
            
            return {
                "total_analyses": self.data["total_analyses"],
                "percentages": percentages,
                "last_updated": self.data.get("last_updated", "Unknown"),
                "recent_activities": self.data["activity_history"][-10:]  # Last 10 activities
            }
    
    def get_formatted_statistics(self) -> str:
        """Get formatted statistics for display."""
        stats = self.get_statistics()
        
        if stats["total_analyses"] == 0:
            return "还没有活动数据记录哦~ 多使用一会儿吧！"
        
        # Sort categories by percentage
        sorted_categories = sorted(
            stats["percentages"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        result = f"? 活动统计 (共分析 {stats['total_analyses']} 次)\n"
        result += "=" * 30 + "\n\n"
        
        # Show top categories with visual bars
        for category, percentage in sorted_categories:
            if percentage > 0:
                # Create visual bar
                bar_length = int(percentage / 5)  # Max 20 chars for 100%
                bar = "█" * bar_length + "?" * (20 - bar_length)
                result += f"{category:<8} {bar} {percentage:.1f}%\n"
        
        result += "\n" + "=" * 30 + "\n"
        result += f"最后更新: {self._format_time(stats['last_updated'])}"
        
        return result
    
    def _format_time(self, iso_time: str) -> str:
        """Format ISO time to readable format."""
        try:
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_time
    
    def analyze_screenshot_for_activities(self, analysis_text: str) -> Dict[str, float]:
        """
        Analyze screenshot analysis text to determine activity categories.
        This is a simple keyword-based approach - could be enhanced with AI.
        """
        # Initialize scores
        scores = {cat: 0.0 for cat in self.ACTIVITY_CATEGORIES}
        text_lower = analysis_text.lower()
        
        # Keyword-based scoring (can be enhanced)
        activity_keywords = {
            "工作编程": ["代码", "编程", "code", "programming", "开发", "debug", "函数", "变量", "git", "terminal", "ide", "vscode"],
            "娱乐休闲": ["视频", "电影", "音乐", "娱乐", "休闲", "youtube", "netflix", "bilibili", "抖音"],
            "社交聊天": ["聊天", "消息", "微信", "qq", "telegram", "discord", "邮件", "email", "chat"],
            "学习研究": ["学习", "文档", "阅读", "研究", "paper", "文献", "教程", "course", "study"],
            "创作设计": ["设计", "创作", "画", "photoshop", "figma", "sketch", "创意", "艺术"],
            "系统管理": ["系统", "设置", "配置", "管理", "finder", "preferences", "系统偏好"],
            "网页浏览": ["浏览器", "网页", "搜索", "chrome", "safari", "firefox", "google", "百度"],
            "视频媒体": ["播放器", "视频", "movie", "media", "vlc", "quicktime"],
            "游戏": ["游戏", "game", "steam", "play", "玩"],
        }
        
        # Score based on keyword matches
        for category, keywords in activity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[category] += 10
        
        # If no specific matches, mark as "其他"
        if all(score == 0 for score in scores.values()):
            scores["其他"] = 100
        
        # Normalize scores to percentages
        total = sum(scores.values())
        if total > 0:
            for cat in scores:
                scores[cat] = (scores[cat] / total) * 100
        
        return scores

# Global instance
activity_tracker = ActivityTracker() 