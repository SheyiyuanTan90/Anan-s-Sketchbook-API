import os
import toml
from typing import Dict, Any, Optional

class Config:
    def __init__(self, config_file: str = "config.toml"):
        # 自动获取工作目录 - 项目根目录
        self.work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 使用相对路径的配置文件
        self.config_file = os.path.join(self.work_dir, config_file)
        self.config_data: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = toml.load(f)
            except Exception as e:
                print(f"配置文件 {self.config_file} 格式错误或读取失败: {e}")
                self.config_data = {}
        else:
            print(f"配置文件 {self.config_file} 不存在，将使用默认配置。")
            self.config_data = {}
    
    def save(self) -> None:
        """保存配置到文件"""
        # 确保目录存在
        dir_path = os.path.dirname(self.config_file)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                toml.dump(self.config_data, f)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        # 支持嵌套键访问，如 'api.port'
        if '.' in key:
            keys = key.split('.')
            value = self.config_data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        # 支持嵌套键设置
        if '.' in key:
            keys = key.split('.')
            data = self.config_data
            for i, k in enumerate(keys[:-1]):
                if k not in data or not isinstance(data[k], dict):
                    data[k] = {}
                data = data[k]
            data[keys[-1]] = value
        else:
            self.config_data[key] = value
        self.save()
    
    def get_path(self, key: str, default: str = "") -> str:
        """获取路径配置，确保路径存在"""
        path = self.get(key, default)
        if path:
            # 如果是相对路径，则相对于work_dir解析
            if not os.path.isabs(path):
                path = os.path.join(self.work_dir, path)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
        return path