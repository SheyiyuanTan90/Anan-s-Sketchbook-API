# hotkey_demo.py
import keyboard
import time
import pyperclip
import io
from PIL import Image
import win32clipboard
import win32gui
import win32process
import psutil
from typing import Optional, Tuple
from config import DELAY, FONT_FILE, BASEIMAGE_MAPPING, BASEIMAGE_FILE, AUTO_SEND_IMAGE, AUTO_PASTE_IMAGE, BLOCK_HOTKEY, HOTKEY, SEND_HOTKEY, PASTE_HOTKEY, CUT_HOTKEY, SELECT_ALL_HOTKEY, TEXT_BOX_TOPLEFT, IMAGE_BOX_BOTTOMRIGHT, BASE_OVERLAY_FILE, USE_BASE_OVERLAY, ALLOWED_PROCESSES

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

current_image_file = BASEIMAGE_FILE

def get_foreground_window_process_name():
    """
    获取当前前台窗口的进程名称
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().lower()
    except Exception as e:
        print(f"无法获取当前进程名称: {e}")
        return None

def copy_png_bytes_to_clipboard(png_bytes: bytes):
    # 打开 PNG 字节为 Image
    image = Image.open(io.BytesIO(png_bytes))
    # 转换成 BMP 字节流（去掉 BMP 文件头的前 14 个字节）
    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        bmp_data = output.getvalue()[14:]

    # 打开剪贴板并写入 DIB 格式
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    win32clipboard.CloseClipboard()

def get_clipboard_text_and_image() -> Tuple[str, Optional[Image.Image], object]:
    """
    获取剪贴板中的文本和图像内容，并返回原始剪贴板内容
    """
    # 备份原剪贴板
    old_clip = pyperclip.paste()

    # 先尝试获取图像
    image = None
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            if data:
                # 将 DIB 数据转换为字节流，供 Pillow 打开
                bmp_data = data
                # DIB 格式缺少 BMP 文件头，需要手动加上
                # BMP 文件头是 14 字节，包含 "BM" 标识和文件大小信息
                header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                image = Image.open(io.BytesIO(header + bmp_data))
    except Exception as e:
        print("无法从剪贴板获取图像：", e)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass

    # 再获取文本内容
    # 清空剪贴板，防止读到旧数据
    pyperclip.copy("")

    # 发送 Ctrl+A 和 Ctrl+X
    keyboard.send(SELECT_ALL_HOTKEY)
    keyboard.send(CUT_HOTKEY)
    time.sleep(DELAY)

    # 获取剪切后的内容
    text = pyperclip.paste()

    return text, image, old_clip

def is_vertical_image(image: Image.Image) -> bool:
    """
    判断图像是否为竖图
    """
    return image.height > image.width

def process_text_and_image(text: str, image: Optional[Image.Image]) -> Optional[bytes]:
    """
    同时处理文本和图像内容，将其绘制到同一张图片上
    """
    if text == "" and image is None:
        return None

    # 获取配置的区域坐标
    x1, y1 = TEXT_BOX_TOPLEFT
    x2, y2 = IMAGE_BOX_BOTTOMRIGHT
    region_width = x2 - x1
    region_height = y2 - y1

    # 只有图像的情况
    if text == "" and image is not None:
        print("Get image only")
        try:
            return paste_image_auto(
                image_source=current_image_file,
                image_overlay=BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                top_left=(x1, y1),
                bottom_right=(x2, y2),
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True, 
                keep_alpha=True,
            )
        except Exception as e:
            print("Generate image failed:", e)
            return None

    # 只有文本的情况
    elif text != "" and image is None:
        print("Get text only: " + text)
        try:
            return draw_text_auto(
                image_source=current_image_file,
                image_overlay=BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                top_left=(x1, y1),
                bottom_right=(x2, y2),
                text=text,
                color=(0, 0, 0),
                max_font_height=64,
                font_path=FONT_FILE,
            )
        except Exception as e:
            print("Generate image failed:", e)
            return None

    # 同时有图像和文本的情况
    else:
        print("Get both text and image")
        print("Text: " + text)
        try:
            # 根据图像方向决定排布方式
            if is_vertical_image(image):
                print("使用左右排布（竖图）")
                # 左右排布：图像在左，文本在右
                # 计算左右区域宽度（各占一半，留出间距）
                spacing = 10  # 左右区域之间的间距
                left_width = region_width // 2 - spacing // 2
                right_width = region_width - left_width - spacing
                
                # 左区域（图像）
                left_region_right = x1 + left_width
                # 右区域（文本）
                right_region_left = left_region_right + spacing
                
                # 先绘制左半部分的图像
                intermediate_bytes = paste_image_auto(
                    image_source=current_image_file,
                    image_overlay=None,  # 暂时不应用overlay
                    top_left=(x1, y1),
                    bottom_right=(left_region_right, y2),
                    content_image=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True, 
                    keep_alpha=True,
                )
                
                # 在已有图像基础上添加右半部分的文本
                final_bytes = draw_text_auto(
                    image_source=io.BytesIO(intermediate_bytes),
                    image_overlay=BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                    top_left=(right_region_left, y1),
                    bottom_right=(x2, y2),
                    text=text,
                    color=(0, 0, 0),
                    max_font_height=64,
                    font_path=FONT_FILE,
                )
            else:
                print("使用上下排布（横图）")
                # 上下排布：图像在上，文本在下
                # 动态计算图像和文本的区域分配
                # 根据文本长度和图像尺寸计算合适的比例
                
                # 估算文本所需高度（使用最大字体高度的一半作为初始估算）
                estimated_text_height = min(region_height // 2, 100)
                
                # 图像区域（上半部分）
                image_region_bottom = y1 + (region_height - estimated_text_height)
                
                # 文本区域（下半部分）
                text_region_top = image_region_bottom
                text_region_bottom = y2
                
                # 先绘制图像
                intermediate_bytes = paste_image_auto(
                    image_source=current_image_file,
                    image_overlay=None,  # 暂时不应用overlay
                    top_left=(x1, y1),
                    bottom_right=(x2, image_region_bottom),
                    content_image=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True, 
                    keep_alpha=True,
                )
                
                # 在已有图像基础上添加文本
                final_bytes = draw_text_auto(
                    image_source=io.BytesIO(intermediate_bytes),
                    image_overlay=BASE_OVERLAY_FILE if USE_BASE_OVERLAY else None,
                    top_left=(x1, text_region_top),
                    bottom_right=(x2, text_region_bottom),
                    text=text,
                    color=(0, 0, 0),
                    max_font_height=64,
                    font_path=FONT_FILE,
                )
            
            return final_bytes
            
        except Exception as e:
            print("Generate image failed:", e)
            return None

def Start():
    global current_image_file
    
    # 检查是否设置了允许的进程列表，如果设置了，则检查当前进程是否在允许列表中
    if ALLOWED_PROCESSES:
        current_process = get_foreground_window_process_name()
        if current_process is None or current_process not in [p.lower() for p in ALLOWED_PROCESSES]:
            print(f"当前进程 {current_process} 不在允许列表中，跳过执行")
            # 如果不是在允许的进程中，直接发送原始热键
            if not BLOCK_HOTKEY:
                keyboard.send(HOTKEY)
            return

    print("Start generate...")

    text, image, old_clipboard_content = get_clipboard_text_and_image()

    if text == "" and image is None:
        print("no text or image")
        return
    
    # 查找发送内容是否包含更换差分指令#差分名#，如果有则更换差分并移除关键字
    for keyword, img_file in BASEIMAGE_MAPPING.items():
        if keyword in text:
            current_image_file = img_file
            text = text.replace(keyword, "").strip()
            print(f"检测到关键词 '{keyword}'，使用底图: {current_image_file}")
            break
    
    png_bytes = process_text_and_image(text, image)
    
    if png_bytes is None:
        print("Generate image failed!")
        return
    
    copy_png_bytes_to_clipboard(png_bytes)
    
    if AUTO_PASTE_IMAGE:
        keyboard.send(PASTE_HOTKEY)

        time.sleep(DELAY)

        if AUTO_SEND_IMAGE:
            keyboard.send(SEND_HOTKEY)

    # 恢复原始剪贴板内容
    pyperclip.copy(old_clipboard_content)
    
    print("Generate image successed!")

# 绑定 Ctrl+Alt+H 作为全局热键
ok = keyboard.add_hotkey(HOTKEY, Start, suppress=BLOCK_HOTKEY or HOTKEY==SEND_HOTKEY)

print("Starting...")
print("Hot key bind: " + str(bool(ok)))
print("Allowed processes: " + str(ALLOWED_PROCESSES))

# 保持程序运行
keyboard.wait()