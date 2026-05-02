{
  "creators": [
    {
      "name": "博主名称",
      "url": "https://www.douyin.com/user/你的博主链接",
      "videos": 1,
      "category": "finance"
    }
  ],
  "default_videos_per_creator": 5,
  "max_video_seconds": 60,

  "_comment_live_schedule": "weekdays: 周日=0, 周一=1, ..., 周六=6",
  "_comment_category": "category: finance=金融分析提示词, career=求职分析提示词",
  "live_creators": [
    {
      "name": "主播名称",
      "url": "https://live.douyin.com/你的直播间ID",
      "schedule": {
        "weekdays": [1, 2, 3, 4, 5],
        "time": "11:30"
      },
      "category": "career"
    }
  ],
  "live_record_minutes": 60,
  "live_check_early_minutes": 5,

  "paths": {
    "video_dir": "recordings",
    "transcript_dir": "transcripts",
    "word_dir": "word",
    "analysis_dir": "analysis"
  },
  "whisper": {
    "model_size": "medium",
    "device": "cpu",
    "language": "zh"
  },
  "obs": {
    "host": "localhost",
    "port": 4455,
    "password": "你的OBS密码"
  },
  "auto_cleanup": true,
  "deepseek": {
    "api_key": "在这里填入你的DeepSeek API Key",
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com"
  }
}
