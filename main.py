import uvicorn
from api.api import anan_sketchbook_app as app
from core.core import config, internal_config, log  # 导入internal_config

if __name__ == "__main__":
    # 获取配置信息
    host = config.get("api_host", "0.0.0.0")
    port = config.get("api_port", 8000)
    reload = config.get("api.reload", False)
    
    # 记录启动日志
    log.info(f"Anan's Sketchbook API 启动中...")
    log.info(f"访问地址: http://{host}:{port}")
    log.info(f"API文档: http://{host}:{port}/docs")
    
    # 启动FastAPI服务器
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )