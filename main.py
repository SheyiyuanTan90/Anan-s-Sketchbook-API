# hotkey_demo.py
import keyboard
import time
import pyperclip
import io
from PIL import Image
import win32clipboard

from config import DELAY, FONT_FILE, BASEIMAGE_FILE, AUTO_SEND_IMAGE, AUTO_PASTE_IMAGE, BLOCK_HOTKEY, HOTKEY, SEND_HOTKEY,PASTE_HOTKEY,CUT_HOTKEY,SELECT_ALL_HOTKEY,TEXT_BOX_TOPLEFT,IMAGE_BOX_BOTTOMRIGHT

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

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


def cut_all_and_get_text() -> str:
    """
    模拟 Ctrl+A / Ctrl+X 剪切全部文本，并返回剪切得到的内容。
    delay: 每步之间的延时（秒），默认0.1秒。
    """
    # 备份原剪贴板
    old_clip = pyperclip.paste()

    # 清空剪贴板，防止读到旧数据
    pyperclip.copy("")

    # 发送 Ctrl+A 和 Ctrl+X
    keyboard.send(SELECT_ALL_HOTKEY)
    keyboard.send(CUT_HOTKEY)
    time.sleep(DELAY)

    # 获取剪切后的内容
    new_clip = pyperclip.paste()

    return new_clip

def try_get_image() -> Image.Image | None:
    """
    尝试从剪贴板获取图像，如果没有图像则返回 None。
    仅支持 Windows。
    """
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
                return image
    except Exception as e:
        print("无法从剪贴板获取图像：", e)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
    return None

def Start():
    print("Start generate...")

    text=cut_all_and_get_text()
    image=try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return
    
    png_bytes=None

    if image is not None:
        print("Get image")

        png_bytes = paste_image_auto(
                    image_source=BASEIMAGE_FILE,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    content_image=image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True, 
                    keep_alpha=True,      # 使用内容图 alpha 作为蒙版
                    )
    
    elif text != "":
        print("Get text: "+text)

        png_bytes = draw_text_auto(
                    image_source=BASEIMAGE_FILE,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    text=text,
                    color=(0, 0, 0),
                    max_font_height=64,        # 例如限制最大字号高度为 64 像素
                    font_path=FONT_FILE,
                    )
        
    if png_bytes is None:
        print("Generate image failed!")
        return
    
    copy_png_bytes_to_clipboard(png_bytes)
    
    if AUTO_PASTE_IMAGE:
        keyboard.send(PASTE_HOTKEY)

        time.sleep(DELAY)

        if AUTO_SEND_IMAGE:
            keyboard.send(SEND_HOTKEY)


    

# 绑定 Ctrl+Alt+H 作为全局热键
ok=keyboard.add_hotkey(HOTKEY, Start, suppress=BLOCK_HOTKEY or HOTKEY==SEND_HOTKEY)

print("Starting...")
print("Hot key bind: "+str(bool(ok)))

# 保持程序运行
keyboard.wait()
