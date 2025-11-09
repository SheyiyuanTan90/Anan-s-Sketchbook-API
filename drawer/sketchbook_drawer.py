import os
import io
from typing import Union, Tuple, Optional, Literal
from PIL import Image, ImageDraw, ImageFont
from core.core import config, log

Align = Literal["left", "center", "right"]
VAlign = Literal["top", "middle", "bottom"]

class SketchbookGenerator:
    def __init__(self):
        # 从配置中获取基础设置
        self.base_images_dir = config.get("resource_path").get("images")
        self.font_file = os.path.join(config.get("work_dir"), config.get("resource_path").get("fonts"), "font.ttf")
        
        # 从原始config.py中导入的配置
        self.TEXT_BOX_TOPLEFT = (119, 450)
        self.IMAGE_BOX_BOTTOMRIGHT = (119+279, 450+175)
        self.BASE_OVERLAY_FILE = os.path.join(self.base_images_dir, "base_overlay.png")
        self.USE_BASE_OVERLAY = True
        
        # 差分表情映射
        self.BASEIMAGE_MAPPING = {
            "#普通#": os.path.join(self.base_images_dir, "base.png"),
            "#开心#": os.path.join(self.base_images_dir, "开心.png"),
            "#生气#": os.path.join(self.base_images_dir, "生气.png"),
            "#无语#": os.path.join(self.base_images_dir, "无语.png"),
            "#脸红#": os.path.join(self.base_images_dir, "脸红.png"),
            "#病娇#": os.path.join(self.base_images_dir, "病娇.png")
        }
        
        # 默认底图
        self.current_image_file = os.path.join(self.base_images_dir, "base.png")
    
    def draw_text_auto(self, 
                      image_source: Union[str, Image.Image],
                      text: str,
                      color: Tuple[int, int, int] = (0, 0, 0),
                      max_font_height: Optional[int] = None,
                      align: Align = "center",
                      valign: VAlign = "middle",
                      line_spacing: float = 0.15,
                      bracket_color: Tuple[int, int, int] = (128, 0, 128),
                      image_overlay: Union[str, Image.Image, None] = None
                     ) -> bytes:
        """在指定矩形内自适应字号绘制文本"""
        # 打开图像
        if isinstance(image_source, Image.Image):
            img = image_source.copy()
        else:
            img = Image.open(image_source).convert("RGBA")
        draw = ImageDraw.Draw(img)
    
        if image_overlay is not None:
            if isinstance(image_overlay, Image.Image):
                img_overlay = image_overlay.copy()
            else:
                img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None
    
        x1, y1 = self.TEXT_BOX_TOPLEFT
        x2, y2 = self.IMAGE_BOX_BOTTOMRIGHT
        if not (x2 > x1 and y2 > y1):
            raise ValueError("无效的文字区域。")
        region_w, region_h = x2 - x1, y2 - y1
    
        # 字体加载
        def _load_font(size: int) -> ImageFont.FreeTypeFont:
            if os.path.exists(self.font_file):
                return ImageFont.truetype(self.font_file, size=size)
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size=size)
            except Exception:
                return ImageFont.load_default()
    
        # 文本包行
        def wrap_lines(txt: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
            lines = []
            for para in txt.splitlines() or [""]:
                has_space = (" " in para)
                units = para.split(" ") if has_space else list(para)
                buf = ""
    
                def unit_join(a: str, b: str) -> str:
                    if not a:
                        return b
                    return (a + " " + b) if has_space else (a + b)
    
                for u in units:
                    trial = unit_join(buf, u)
                    w = draw.textlength(trial, font=font)
                    if w <= max_w:
                        buf = trial
                    else:
                        if buf:
                            lines.append(buf)
                        if has_space and len(u) > 1:
                            tmp = ""
                            for ch in u:
                                if draw.textlength(tmp + ch, font=font) <= max_w:
                                    tmp += ch
                                else:
                                    if tmp:
                                        lines.append(tmp)
                                    tmp = ch
                            buf = tmp
                        else:
                            if draw.textlength(u, font=font) <= max_w:
                                buf = u
                            else:
                                lines.append(u)
                                buf = ""
                if buf != "":
                    lines.append(buf)
                if para == "" and (not lines or lines[-1] != ""):
                    lines.append("")
            return lines
    
        # 寻找最佳字体大小
        min_size, max_size = 1, max_font_height or 128
        best_size = 1
        best_lines = []
        best_block_h = 0
        best_line_h = 0
    
        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            font = _load_font(mid_size)
            lines = wrap_lines(text, font, region_w)
            
            # 计算行高和总高度
            line_h = font.size * (1 + line_spacing)
            block_h = len(lines) * line_h
            
            if block_h <= region_h:
                best_size = mid_size
                best_lines = lines
                best_block_h = block_h
                best_line_h = line_h
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1
    
        if best_size == 0:
            font = _load_font(1)
            best_lines = wrap_lines(text, font, region_w)
            _, best_block_h, best_line_h = 0, 1, 1
            best_size = 1
        else:
            font = _load_font(best_size)
    
        # 解析着色片段
        def parse_color_segments(s: str, in_bracket: bool) -> Tuple[list, bool]:
            segs = []
            buf = ""
            for ch in s:
                if ch == "[" or ch == "【":
                    if buf:
                        segs.append((buf, bracket_color if in_bracket else color))
                        buf = ""
                    segs.append((ch, bracket_color))
                    in_bracket = True
                elif ch == "]" or ch == "】":
                    if buf:
                        segs.append((buf, bracket_color))
                        buf = ""
                    segs.append((ch, bracket_color))
                    in_bracket = False
                else:
                    buf += ch
            if buf:
                segs.append((buf, bracket_color if in_bracket else color))
            return segs, in_bracket
    
        # 垂直对齐
        if valign == "top":
            y_start = y1
        elif valign == "middle":
            y_start = y1 + (region_h - best_block_h) // 2
        else:
            y_start = y2 - best_block_h
    
        # 绘制
        y = y_start
        in_bracket = False
    
        for line in best_lines:
            if not line:  # 处理空行
                y += best_line_h
                continue
    
            # 解析行的着色片段
            color_segments, in_bracket = parse_color_segments(line, in_bracket)
    
            # 计算行的总宽度和起始X坐标
            total_width = sum(draw.textlength(seg[0], font=font) for seg in color_segments)
            if align == "left":
                x = x1
            elif align == "center":
                x = x1 + (region_w - total_width) // 2
            else:  # right
                x = x2 - total_width
    
            # 绘制每个着色片段
            for text_seg, text_color in color_segments:
                draw.text((x, y), text_seg, font=font, fill=text_color)
                x += draw.textlength(text_seg, font=font)
    
            y += best_line_h
    
        # 应用覆盖层
        if image_overlay is not None:
            if img_overlay:
                img.paste(img_overlay, (0, 0), img_overlay if img_overlay.mode == 'RGBA' else None)
    
        # 保存为PNG字节流
        with io.BytesIO() as output:
            img.save(output, format="PNG")
            png_bytes = output.getvalue()
    
        return png_bytes
    
    def paste_image_auto(self, 
                        image_source: Union[str, Image.Image],
                        content_image: Image.Image,
                        align: Align = "center",
                        valign: VAlign = "middle",
                        padding: int = 12,
                        allow_upscale: bool = True,
                        keep_alpha: bool = True,
                        image_overlay: Union[str, Image.Image, None] = None
                       ) -> bytes:
        """自动调整图片大小并粘贴到指定区域"""
        # 打开源图像
        if isinstance(image_source, Image.Image):
            img = image_source.copy()
        else:
            img = Image.open(image_source).convert("RGBA")
    
        # 打开覆盖层图像
        if image_overlay is not None:
            if isinstance(image_overlay, Image.Image):
                img_overlay = image_overlay.copy()
            else:
                img_overlay = Image.open(image_overlay).convert("RGBA") if os.path.isfile(image_overlay) else None
    
        # 获取粘贴区域
        x1, y1 = self.TEXT_BOX_TOPLEFT
        x2, y2 = self.IMAGE_BOX_BOTTOMRIGHT
        if not (x2 > x1 and y2 > y1):
            raise ValueError("无效的粘贴区域。")
    
        # 计算有效粘贴区域（考虑内边距）
        effective_x1 = x1 + padding
        effective_y1 = y1 + padding
        effective_x2 = x2 - padding
        effective_y2 = y2 - padding
        effective_width = effective_x2 - effective_x1
        effective_height = effective_y2 - effective_y1
    
        if effective_width <= 0 or effective_height <= 0:
            raise ValueError("内边距过大，有效粘贴区域为空。")
    
        # 打开内容图像
        content_img = content_image.copy()
    
        # 计算缩放比例
        img_width, img_height = content_img.size
        scale = min(effective_width / img_width, effective_height / img_height)
    
        # 如果不允许放大，且原图已经小于目标区域，则不缩放
        if not allow_upscale and scale > 1:
            scale = 1
    
        # 计算新尺寸
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
    
        # 调整图像大小
        content_img = content_img.resize((new_width, new_height), Image.LANCZOS)
    
        # 计算粘贴位置（根据对齐方式）
        if align == "left":
            paste_x = effective_x1
        elif align == "center":
            paste_x = effective_x1 + (effective_width - new_width) // 2
        else:  # right
            paste_x = effective_x2 - new_width
    
        if valign == "top":
            paste_y = effective_y1
        elif valign == "middle":
            paste_y = effective_y1 + (effective_height - new_height) // 2
        else:  # bottom
            paste_y = effective_y2 - new_height
    
        # 处理透明度
        if keep_alpha and content_img.mode == 'RGBA':
            img.paste(content_img, (paste_x, paste_y), content_img)
        else:
            if content_img.mode == 'RGBA':
                content_img = content_img.convert('RGB')
            img.paste(content_img, (paste_x, paste_y))
    
        # 应用覆盖层
        if image_overlay is not None:
            if img_overlay:
                img.paste(img_overlay, (0, 0), img_overlay if img_overlay.mode == 'RGBA' else None)
    
        # 保存为PNG字节流
        with io.BytesIO() as output:
            img.save(output, format="PNG")
            png_bytes = output.getvalue()
    
        return png_bytes
    
    def generate_sketchbook(self, text: str = "", image: Optional[Image.Image] = None, emotion: str = "") -> bytes:
        """生成素描本图片"""
        # 检查是否指定了表情差分
        if emotion in self.BASEIMAGE_MAPPING:
            self.current_image_file = self.BASEIMAGE_MAPPING[emotion]
        elif text:
            # 从文本中查找表情差分指令
            for keyword, img_file in self.BASEIMAGE_MAPPING.items():
                if keyword in text:
                    self.current_image_file = img_file
                    text = text.replace(keyword, "").strip()
                    break
    
        png_bytes = None
    
        # 如果有图像，生成带图像的素描本
        if image is not None:
            try:
                overlay_file = self.BASE_OVERLAY_FILE if self.USE_BASE_OVERLAY else None
                png_bytes = self.paste_image_auto(
                    image_source=self.current_image_file,
                    content_image=image,
                    image_overlay=overlay_file,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True,
                    keep_alpha=True
                )
            except Exception as e:
                log.error(f"生成图像失败: {e}")
                raise
    
        # 如果有文本，生成带文本的素描本
        elif text != "":
            try:
                overlay_file = self.BASE_OVERLAY_FILE if self.USE_BASE_OVERLAY else None
                png_bytes = self.draw_text_auto(
                    image_source=self.current_image_file,
                    text=text,
                    image_overlay=overlay_file,
                    color=(0, 0, 0),
                    max_font_height=64
                )
            except Exception as e:
                log.error(f"生成文本图像失败: {e}")
                raise
    
        if png_bytes is None:
            raise ValueError("没有提供文本或图像，无法生成素描本。")
    
        return png_bytes