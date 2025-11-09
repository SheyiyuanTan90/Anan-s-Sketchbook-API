import os
import logging
from typing import Optional

class Logos:
    def __init__(self, name: str = "AnanSketchbook", log_file: Optional[str] = None):
        # 创建logger对象
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # 设置最低日志级别
        
        # 检查是否已经添加过处理器，避免重复添加
        if not self.logger.handlers:
            # 定义日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # 添加文件处理器（如果指定了日志文件）
            if log_file:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """记录严重错误日志"""
        self.logger.critical(message)