import os
from utils.conf import Config
from utils.log import Logos

# 默认配置
DEFAULT_CONFIG = {
    "project_name": "Anan's Sketchbook API",
    "work_dir": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "log_path": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "log"),
    "output_path": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"),
    "api_route": "/api/v1",
    "api_port": 8000,
    "api_host": "0.0.0.0",
    "api_token": "",  # 留空表示不启用认证
    "domain": "http://localhost:8000",
    "resource_path": {
        "images": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BaseImages"),
        "fonts": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
    }
}

# 初始化配置和日志 - 配置文件移到data目录下
config_file = os.path.join(DEFAULT_CONFIG["work_dir"], "data", "config.toml")
config = Config(config_file)
log = Logos(
    name="AnanSketchbook",
    log_file=os.path.join(DEFAULT_CONFIG["log_path"], "app.log")
)

# 确保必要的目录存在 - 添加data目录
os.makedirs(os.path.join(DEFAULT_CONFIG["work_dir"], "data"), exist_ok=True)
for path_key in ["log_path", "output_path"]:
    os.makedirs(DEFAULT_CONFIG[path_key], exist_ok=True)

for _, path in DEFAULT_CONFIG["resource_path"].items():
    os.makedirs(path, exist_ok=True)

# 合并默认配置和用户配置
for key, value in DEFAULT_CONFIG.items():
    if config.get(key) is None:
        config.set(key, value)