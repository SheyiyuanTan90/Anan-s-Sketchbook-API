# 导入必要的模块
from fastapi import FastAPI, HTTPException, File, UploadFile, Request, Depends, Security
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import io
from PIL import Image
import os
import base64
import uuid
from datetime import datetime
import threading
import time
from pydantic import BaseModel, Field

from core.core import config, internal_config, log  # 导入internal_config
from drawer.sketchbook_drawer import SketchbookGenerator

# 创建FastAPI应用
anan_sketchbook_app = FastAPI(
    title="Anan's Sketchbook API",
    description="安安的素描本聊天框API，用于生成带文本或图片的素描本图片。",
    version="1.0.0"
)

# 创建素描本生成器实例
sketchbook_gen = SketchbookGenerator()

# 设置图片目录和域名配置
IMAGE_FOLDER = os.path.join(internal_config.work_dir, "data", "sketchbooks")
DOMAIN = config.get("domain", "localhost")
PORT = config.get("api_port", 14541)

# 确保图片目录存在
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 创建认证工具
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)

# 创建认证类
class AuthManager:
    @staticmethod
    def get_api_token() -> Optional[str]:
        """从配置中获取API Token"""
        return config.get("api_token")
        
    @staticmethod
    async def verify_credentials(
        bearer_credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
        api_key: Optional[str] = Security(api_key_header)
    ) -> Dict[str, Any]:
        """
        验证认证凭证，支持Bearer Token和X-API-Token两种方式
        返回包含认证信息的字典，用于后续权限控制
        """
        # 获取配置的API Token
        configured_token = AuthManager.get_api_token()
        
        # 如果未配置API Token，则跳过验证
        if not configured_token:
            return {"authenticated": False, "client_type": "anonymous"}
        
        # 确定使用哪个token进行验证
        token_to_verify = None
        auth_method = None
        
        if bearer_credentials:
            token_to_verify = bearer_credentials.credentials
            auth_method = "bearer_token"
        elif api_key:
            token_to_verify = api_key
            auth_method = "api_key"
        
        # 验证token
        if token_to_verify == configured_token:
            log.info(f"Successful authentication using {auth_method}")
            return {
                "authenticated": True,
                "client_type": "api_client",
                "auth_method": auth_method
            }
        else:
            log.warning(f"Failed authentication attempt using {auth_method}")
            raise HTTPException(
                status_code=401,
                detail="未授权访问：无效的API令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )

# 创建不同级别的认证依赖项
def require_authentication():    
    """需要认证的依赖项"""
    async def dependency(
        auth_result: Dict[str, Any] = Depends(AuthManager.verify_credentials)
    ) -> Dict[str, Any]:
        if auth_result["authenticated"]:
            return auth_result
        # 如果配置了token但请求未提供有效token，则拒绝访问
        if AuthManager.get_api_token():
            raise HTTPException(status_code=401, detail="需要认证")
        return auth_result
    
    return dependency

# 定义请求体模型
class TextGenerateRequest(BaseModel):
    """文本生成图片的请求体模型"""
    text: str = Field(..., description="要绘制的文本，可以包含表情标记（如#开心#、#生气#等，多个标记时只使用最后一个）")

class Base64GenerateRequest(BaseModel):
    """Base64生成图片的请求体模型"""
    text: Optional[str] = Field(None, description="要绘制的文本，可以包含表情标记（如#开心#、#生气#等，多个标记时只使用最后一个）")
    image_base64: Optional[str] = Field(None, description="Base64编码的图片，与text二选一")

# 修改所有POST接口，使用JSON请求体
@anan_sketchbook_app.post(f"{config.get('api_route')}/generate/text", tags=["生成图片"])
async def generate_text_image(
    request: TextGenerateRequest,
    auth_result: Dict[str, Any] = Depends(require_authentication())
):
    """根据文本生成素描本图片"""
    try:
        # 检查文本是否为空
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 生成图片
        log.info(f"生成文本图片: {request.text[:50]}...")
        # 不再传入emotion参数，表情标记从text中提取
        png_bytes = sketchbook_gen.generate_sketchbook(text=request.text)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"text_{timestamp}_{random_id}.png"
        
        # 保存图片并启动删除线程
        create_image_and_start_deletion(png_bytes, filename)
        
        # 返回图片URL
        img_url = build_full_url(DOMAIN, PORT, f"images/{filename}")
        log.info(f"图片已生成，URL: {img_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "img_url": img_url,
                    "filename": filename
                }
            }
        )
        
    except HTTPException as e:
        log.error(f"HTTP错误: {e.detail}")
        raise e
    except Exception as e:
        log.error(f"生成图片时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成图片失败: {str(e)}")

# 注意：对于文件上传接口，我们仍然需要使用multipart/form-data
# 但可以将其他参数放在JSON中传递
@anan_sketchbook_app.post(f"{config.get('api_route')}/generate/image", tags=["生成图片"])
async def generate_image_image(
    image: UploadFile = File(..., description="要粘贴的图片文件"),
    auth_result: Dict[str, Any] = Depends(require_authentication())
):
    """根据上传的图片生成素描本图片"""
    try:
        # 读取图片
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # 生成图片
        log.info(f"生成图片: {image.filename}")
        # 不再传入emotion参数
        png_bytes = sketchbook_gen.generate_sketchbook(image=img)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"image_{timestamp}_{random_id}.png"
        
        # 保存图片并启动删除线程
        create_image_and_start_deletion(png_bytes, filename)
        
        # 返回图片URL
        img_url = build_full_url(DOMAIN, PORT, f"images/{filename}")
        log.info(f"图片已生成，URL: {img_url}")
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "img_url": img_url,
                    "filename": filename
                }
            }
        )
        
    except HTTPException as e:
        log.error(f"HTTP错误: {e.detail}")
        raise e
    except Exception as e:
        log.error(f"生成图片时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成图片失败: {str(e)}")

@anan_sketchbook_app.post(f"{config.get('api_route')}/generate/base64", tags=["生成图片"])
async def generate_base64_image(
    request: Base64GenerateRequest,
    auth_result: Dict[str, Any] = Depends(require_authentication())
):
    """生成素描本图片并返回Base64编码"""
    try:
        # 检查参数
        if not request.text and not request.image_base64:
            raise HTTPException(status_code=400, detail="必须提供text或image_base64参数")
        
        img = None
        if request.image_base64:
            # 处理Base64图片
            try:
                img_data = base64.b64decode(request.image_base64)
                img = Image.open(io.BytesIO(img_data))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"无效的Base64图片: {str(e)}")
        
        # 生成图片
        if img is not None:
            log.info("生成Base64图片")
            png_bytes = sketchbook_gen.generate_sketchbook(image=img)
        else:
            log.info(f"生成Base64文本图片: {request.text[:50]}...")
            png_bytes = sketchbook_gen.generate_sketchbook(text=request.text)
        
        # 转换为Base64
        base64_str = base64.b64encode(png_bytes).decode("utf-8")
        
        # 生成唯一的文件名（仅用于日志）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"base64_{timestamp}_{random_id}.png"
        
        log.info(f"Base64图片已生成: {filename}")
        
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "base64": base64_str,
                    "filename": filename
                }
            }
        )
        
    except HTTPException as e:
        log.error(f"HTTP错误: {e.detail}")
        raise e
    except Exception as e:
        log.error(f"生成Base64图片时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成Base64图片失败: {str(e)}")

# 定时删除图片的函数
def delete_file(path):
    # 从配置中获取临时文件保留时间，默认300秒
    retention_seconds = config.get("file_config.temp_file_retention_seconds", 300)
    
    # 如果保留时间为0，则禁用自动删除
    if retention_seconds <= 0:
        return
    
    time.sleep(retention_seconds)  # 等待指定秒数后删除
    try:
        if os.path.exists(path):
            os.remove(path)
            log.info(f"已删除临时图片: {path}")
    except Exception as e:
        log.error(f"删除临时图片失败: {e}")

# 创建图片并启动删除线程
def create_image_and_start_deletion(image_bytes, image_name):
    # 保存图片
    image_path = os.path.join(IMAGE_FOLDER, image_name)
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    
    # 启动删除线程
    threading.Thread(target=delete_file, args=(image_path,)).start()
    
    return image_path

# 构建完整URL的函数
def build_full_url(domain, port, path):
    """构建完整的URL，自动处理端口"""
    # 检查域名是否已经包含协议和端口
    if not domain.startswith(('http://', 'https://')):
        domain = f"http://{domain}"
    return f"{domain.rstrip('/')}/{path.lstrip('/')}"

# 改进get_emotions函数的认证
@anan_sketchbook_app.get(f"{config.get('api_route')}/emotions", tags=["系统信息"])
async def get_emotions(
    auth_result: Dict[str, Any] = Depends(require_authentication())
):
    """获取所有可用的表情差分"""
    try:
        # 返回表情差分列表
        emotions = list(sketchbook_gen.BASEIMAGE_MAPPING.keys())
        return {
            "success": True,
            "emotions": emotions
        }
        
    except HTTPException as e:
        log.error(f"HTTP错误: {e.detail}")
        raise e
    except Exception as e:
        log.error(f"获取表情列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取表情列表失败: {str(e)}")

@anan_sketchbook_app.get(f"{config.get('api_route')}/status", tags=["系统信息"])
async def get_status():
    """获取系统状态（无需认证）"""
    return {
        "success": True,
        "app": "Anan's Sketchbook API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

# 挂载静态目录提供图片访问
anan_sketchbook_app.mount("/images", StaticFiles(directory=IMAGE_FOLDER), name="images")

# 错误处理
@anan_sketchbook_app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "detail": "请求的资源不存在"}
    )

@anan_sketchbook_app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    return JSONResponse(
        status_code=405,
        content={"success": False, "detail": "不支持的请求方法"}
    )

@anan_sketchbook_app.exception_handler(401)
async def unauthorized_handler(request, exc):
    """专门处理认证错误"""
    log.warning(f"Unauthorized access to {request.url}")
    return JSONResponse(
        status_code=401,
        content={"success": False, "detail": "未授权访问：请提供有效的API令牌"},
        headers={"WWW-Authenticate": "Bearer"}
    )