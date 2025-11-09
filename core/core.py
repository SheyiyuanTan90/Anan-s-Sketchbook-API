import os
from utils.conf import Config
from utils.log import Logos

# 默认配置 - 只包含相对路径配置
DEFAULT_CONFIG = {
    "project_name": "Anan's Sketchbook API",
    "api_route": "/api",
    "api_port": 14541,
    "api_host": "0.0.0.0",
    "api_token": "",  # 留空表示不启用认证
    "domain": "localhost",
    # 使用相对路径配置资源路径
    "resource_path": {
        "images": "BaseImages",
        "font_file": "fonts/font.ttf"  # 字体资源配置具体到文件
    },
    # 添加差分表情映射配置
    "emotion_mapping": {
        "#普通#": "base.png",
        "#开心#": "开心.png",
        "#生气#": "生气.png",
        "#无语#": "无语.png",
        "#脸红#": "脸红.png",
        "#病娇#": "病娇.png"
    },
    # 文本渲染配置
    "text_config": {
        "max_font_size": 96,  # 最大字体大小，上限96
        "min_font_size": 12   # 最小字体大小，下限12
    },
    # 图片渲染配置
    "image_config": {
        "enable_sleeve_overlay": True  # 启用衣袖遮挡
    },
    # 文件配置
    "file_config": {
        "temp_file_retention_seconds": 300  # 临时文件保留时间，单位为秒，为0时禁用
    }
}

# 初始化配置和日志 - 配置文件移到data目录下
# 获取工作目录（项目根目录）
work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_file = os.path.join(work_dir, "data", "config.toml")

# 检查配置文件是否存在，如果不存在则创建带注释的配置文件
has_config_file = os.path.exists(config_file)
config = Config(config_file)

# 设置工作目录和日志路径（这些不会写入配置文件）
log_path = os.path.join(work_dir, "data", "log")

# 确保资源路径是绝对路径用于内部使用
resource_paths = {
    "images": os.path.join(work_dir, DEFAULT_CONFIG["resource_path"]["images"]),
    "font_file": os.path.join(work_dir, DEFAULT_CONFIG["resource_path"]["font_file"])
}

log = Logos(
    name="AnanSketchbook",
    log_file=os.path.join(log_path, "app.log")
)

# 确保必要的目录存在
os.makedirs(os.path.join(work_dir, "data"), exist_ok=True)
os.makedirs(log_path, exist_ok=True)
os.makedirs(resource_paths["images"], exist_ok=True)
os.makedirs(os.path.dirname(resource_paths["font_file"]), exist_ok=True)

# 如果是第一次创建配置文件，使用带注释的配置模板
if not has_config_file:
    config_template = """# Anan's Sketchbook API 配置文件
# 项目基本信息
project_name = "Anan's Sketchbook API"

# API配置
api_route = "/api"  # API路由前缀
api_port = 14541  # API监听端口
api_host = "0.0.0.0"  # API监听地址
api_token = ""  # API认证令牌，留空表示不启用认证
domain = "localhost"  # 域名，用于生成回调URL

# 资源路径配置（相对路径）
[resource_path]
images = "BaseImages"  # 图片资源目录
font_file = "fonts/font.ttf"  # 字体文件路径

# 表情差分映射配置
[emotion_mapping]
"#普通#" = "base.png"  # 普通表情
"#开心#" = "开心.png"  # 开心表情
"#生气#" = "生气.png"  # 生气表情
"#无语#" = "无语.png"  # 无语表情
"#脸红#" = "脸红.png"  # 脸红表情
"#病娇#" = "病娇.png"  # 病娇表情

# 文本渲染配置
[text_config]
max_font_size = 96  # 最大字体大小，上限96
min_font_size = 12  # 最小字体大小，下限12

# 图片渲染配置
[image_config]
enable_sleeve_overlay = true  # 启用衣袖遮挡

# 文件配置
[file_config]
temp_file_retention_seconds = 300  # 临时文件保留时间，单位为秒，为0时禁用
"""
    # 直接写入带注释的配置文件
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_template)
        # 重新加载配置
        config.load()
    except Exception as e:
        print(f"创建带注释的配置文件失败: {e}")
        # 回退到默认的配置合并逻辑
        for key, value in DEFAULT_CONFIG.items():
            if config.get(key) is None:
                config.set(key, value)
else:
    # 合并默认配置和用户配置 - 只写入相对路径配置
    for key, value in DEFAULT_CONFIG.items():
        if config.get(key) is None:
            config.set(key, value)

# 为了保持向后兼容性，创建一个包含绝对路径的内部配置对象
class InternalConfig:
    def __init__(self):
        self.work_dir = work_dir
        self.log_path = log_path
        self.resource_path = resource_paths

# 创建内部配置对象，供代码内部使用
internal_config = InternalConfig()