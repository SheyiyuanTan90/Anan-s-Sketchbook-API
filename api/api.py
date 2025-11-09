# 导入必要的模块
from fastapi import FastAPI, HTTPException, File, Form, UploadFile, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import io
from PIL import Image
import os
import base64
import uuid
from datetime import datetime
import threading
import time

from core.core import config, log
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
file = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(file, "../")
IMAGE_FOLDER = path + "data/sketchbooks"
DOMAIN = config.get("api_domain", "localhost")
PORT = config.get("api_port", 8000)

# 确保图片目录存在
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 检查API token的依赖项（如果配置了）
async def verify_token(token: Optional[str] = None):
    api_token = config.get("api_token")
    if api_token and token != api_token:
        raise HTTPException(status_code=401, detail="未授权访问")

@anan_sketchbook_app.get("/", tags=["根路径"])
async def root():
    return {
        "app": "Anan's Sketchbook API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 定时删除图片的函数
def delete_file(path):
    time.sleep(300)  # 等待300秒后删除
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

@anan_sketchbook_app.post(f"{config.get('api_route')}/generate/text", tags=["生成图片"])
async def generate_text_image(
    text: str = Form(..., description="要绘制的文本"),
    emotion: Optional[str] = Form("", description="表情差分，可选值：#普通#, #开心#, #生气#, #无语#, #脸红#, #病娇#"),
    token: Optional[str] = Form(None, description="API访问令牌")
):
    """根据文本生成素描本图片"""
    try:
        # 验证token
        await verify_token(token)
        
        # 检查文本是否为空
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 生成图片
        log.info(f"生成文本图片: {text[:50]}...")
        png_bytes = sketchbook_gen.generate_sketchbook(text=text, emotion=emotion)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"text_{timestamp}_{random_id}.png"
        
        # 保存图片并启动删除线程
        create_image_and_start_deletion(png_bytes, filename)
        
        # 返回图片URL
        img_url = f"http://{DOMAIN}:{PORT}/images/{filename}"
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

@anan_sketchbook_app.post(f"{config.get('api_route')}/generate/image", tags=["生成图片"])
async def generate_image_image(
    image: UploadFile = File(..., description="要粘贴的图片文件"),
    emotion: Optional[str] = Form("", description="表情差分，可选值：#普通#, #开心#, #生气#, #无语#, #脸红#, #病娇#"),
    token: Optional[str] = Form(None, description="API访问令牌")
):
    """根据上传的图片生成素描本图片"""
    try:
        # 验证token
        await verify_token(token)
        
        # 读取图片
        image_data = await image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # 生成图片
        log.info(f"生成图片: {image.filename}")
        png_bytes = sketchbook_gen.generate_sketchbook(image=img, emotion=emotion)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"image_{timestamp}_{random_id}.png"
        
        # 保存图片并启动删除线程
        create_image_and_start_deletion(png_bytes, filename)
        
        # 返回图片URL
        img_url = f"http://{DOMAIN}:{PORT}/images/{filename}"
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
    text: Optional[str] = Form(None, description="要绘制的文本，与image_base64二选一"),
    image_base64: Optional[str] = Form(None, description="Base64编码的图片，与text二选一"),
    emotion: Optional[str] = Form("", description="表情差分，可选值：#普通#, #开心#, #生气#, #无语#, #脸红#, #病娇#"),
    token: Optional[str] = Form(None, description="API访问令牌")
):
    """生成素描本图片并返回Base64编码"""
    try:
        # 验证token
        await verify_token(token)
        
        # 检查参数
        if not text and not image_base64:
            raise HTTPException(status_code=400, detail="必须提供text或image_base64参数")
        
        img = None
        if image_base64:
            # 解析Base64图片
            try:
                # 移除可能的前缀
                if "," in image_base64:
                    image_base64 = image_base64.split(",")[1]
                image_data = base64.b64decode(image_base64)
                img = Image.open(io.BytesIO(image_data))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"无效的Base64图片: {str(e)}")
        
        # 生成图片
        log.info(f"生成Base64图片: {'文本' if text else '图片'}")
        png_bytes = sketchbook_gen.generate_sketchbook(text=text, image=img, emotion=emotion)
        
        # 转换为Base64
        base64_image = base64.b64encode(png_bytes).decode("utf-8")
        
        # 返回结果
        return {
            "success": True,
            "image": f"data:image/png;base64,{base64_image}",
            "size": len(png_bytes)
        }
        
    except HTTPException as e:
        log.error(f"HTTP错误: {e.detail}")
        raise e
    except Exception as e:
        log.error(f"生成图片时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成图片失败: {str(e)}")

@anan_sketchbook_app.get(f"{config.get('api_route')}/emotions", tags=["系统信息"])
async def get_emotions(token: Optional[str] = None):
    """获取所有可用的表情差分"""
    try:
        # 验证token
        await verify_token(token)
        
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
    """获取系统状态"""
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