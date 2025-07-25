import datetime
import os
import re
from typing import Dict, List, Optional
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, ListStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    ListFlowable,
    ListItem,
    Image,
    HRFlowable, # 用于添加水平线
)
from reportlab.lib.units import inch

# 字体路径映射表（统一字体名称）
FONT_PATHS = [
    # Windows系统
    ("C:/Windows/Fonts/simhei.ttf", "SimHei"),
    ("C:/Windows/Fonts/simsun.ttc", "SimSun"),
    ("C:/Windows/Fonts/msyh.ttc", "MicrosoftYaHei"),
    ("C:/Windows/Fonts/msyhbd.ttc", "MicrosoftYaHei-Bold"),
    ("C:/Windows/Fonts/simkai.ttf", "SimKai"),
    # macOS系统
    ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
    ("/System/Library/Fonts/STHeiti Light.ttc", "STHeitiLight"),
    # Linux系统
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYiZenHei"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf", "NotoSansCJK"),
]

class PDFGenerator:
    """PDF报告生成器，支持中文字体、自定义样式和结构化内容解析"""

    def __init__(self):
        self.font_name = self._register_fonts()
        self.default_styles = self._init_default_styles()

    def _register_fonts(self) -> str:
        """注册系统中的中文字体，优先选择常用字体"""
        preferred_fonts = ["MicrosoftYaHei", "SimSun", "STSong"]
        available_fonts = []
        print("🔍 开始注册字体...")
        for path, font_name in FONT_PATHS:
            if not os.path.exists(path):
                print(f"⚠️ 路径不存在: {path}")
                continue
            if not os.access(path, os.R_OK):
                print(f"⚠️ 没有读取权限: {path}")
                continue
            try:
                print(f"🔄 正在尝试注册字体: {font_name} (路径: {path})")
                pdfmetrics.registerFont(TTFont(font_name, path))
                available_fonts.append(font_name)
                print(f"✅ 成功注册字体: {font_name}")
            except Exception as e:
                print(f"❌ 注册失败: {font_name}, 错误信息: {str(e)}")
        # 返回首选字体或第一个可用字体
        for font in preferred_fonts:
            if font in available_fonts:
                print(f"✔️ 使用首选字体: {font}")
                return font
        if available_fonts:
            print(f"ℹ️ 使用非首选字体: {available_fonts[0]}")
            return available_fonts[0]
        print("❌ 错误：未检测到可用中文字体，将使用默认字体 Helvetica（不支持中文）")
        return "Helvetica"

    def _init_default_styles(self) -> Dict[str, ParagraphStyle]:
        """初始化默认样式配置，并确保字体有效"""
        base_styles = getSampleStyleSheet()
        # 验证当前字体是否已注册
        if self.font_name not in pdfmetrics.getRegisteredFontNames():
            print(f"⚠️ 当前字体 {self.font_name} 未注册，使用默认字体 Helvetica")
            self.font_name = "Helvetica"
        print(f"🖌️ 使用字体: {self.font_name}")

        # 基础字体设置
        base_font_name = self.font_name
        base_font_size = 12

        styles = {
            "title": ParagraphStyle(
                name="TitleStyle",
                parent=base_styles["Title"],
                fontName=base_font_name,
                fontSize=24,
                textColor=HexColor("#2E4A66"), # 深蓝色标题
                alignment=TA_CENTER,
                spaceAfter=30,
                leading=30
            ),
            "main_heading": ParagraphStyle( # 例如 "AI 面试评估报告"
                name="MainHeadingStyle",
                fontName=base_font_name,
                fontSize=18,
                textColor=HexColor("#1A365D"),
                alignment=TA_CENTER,
                spaceBefore=20,
                spaceAfter=20,
                leading=22
            ),
            "section_heading": ParagraphStyle( # 例如 "一、各项分析结果"
                name="SectionHeadingStyle",
                fontName=base_font_name + "-Bold" if base_font_name != "Helvetica" else "Helvetica-Bold", # 尝试加粗
                fontSize=16,
                textColor=HexColor("#333333"),
                alignment=TA_LEFT,
                spaceBefore=25,
                spaceAfter=15,
                leading=20
            ),
            "subsection_heading": ParagraphStyle( # 例如 "1. 各项分析结果" 或 "图像分析结果："
                name="SubsectionHeadingStyle",
                fontName=base_font_name + "-Bold" if base_font_name != "Helvetica" else "Helvetica-Bold",
                fontSize=14,
                textColor=HexColor("#444444"),
                alignment=TA_LEFT,
                spaceBefore=15,
                spaceAfter=10,
                leading=18
            ),
            "body": ParagraphStyle(
                name="BodyStyle",
                parent=base_styles["BodyText"],
                fontName=base_font_name,
                fontSize=base_font_size,
                textColor=Color(0, 0, 0),
                alignment=TA_JUSTIFY,
                leading=18,
                spaceAfter=12,
                firstLineIndent=base_font_size * 2
            ),
            "list_item_text": ParagraphStyle( # 列表项的文本样式
                name="ListItemText",
                parent=base_styles["BodyText"],
                fontName=base_font_name,
                fontSize=base_font_size,
                firstLineIndent=0,
                leftIndent=0,
                leading=18,
                spaceAfter=6
            ),
            # 用于键值对列表项的样式
            "key_value_text": ParagraphStyle(
                name="KeyValueText",
                parent=base_styles["BodyText"],
                fontName=base_font_name,
                fontSize=base_font_size,
                firstLineIndent=0,
                leftIndent=20, # 稍微缩进
                leading=18,
                spaceAfter=4
            ),
            # 用于对话历史的样式
            "conversation_text": ParagraphStyle(
                name="ConversationText",
                parent=base_styles["BodyText"],
                fontName=base_font_name,
                fontSize=base_font_size - 1, # 稍小一点
                firstLineIndent=0,
                leftIndent=20,
                leading=16,
                spaceAfter=4
            ),
            # 分隔线样式
            "divider": HRFlowable
        }
        return styles

    def _parse_text_to_elements(self, text: str) -> List:
        elements = []
        lines = [line.rstrip() for line in text.strip().split("\n")]
        current_paragraph = []

        def flush_paragraph():
            nonlocal current_paragraph
            if current_paragraph:
                para_text = "<br/>".join(current_paragraph).strip()
                # 简单的加粗处理
                para_text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", para_text)
                elements.append(Paragraph(para_text, self.default_styles["body"]))
                current_paragraph = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            next_line = lines[i+1].strip() if i + 1 < len(lines) else ""

            # 处理主标题 ("AI 面试评估报告")
            if line == "AI 面试评估报告":
                elements.append(Paragraph(line, self.default_styles["main_heading"]))
                i += 1
                continue

            # 处理章节标题 (例如 "一、各项分析结果")
            if re.match(r"^[一二三四五六七八九十]+、", line):
                flush_paragraph()
                elements.append(Paragraph(line, self.default_styles["section_heading"]))
                # 如果下一行是分隔线，则跳过分隔线
                if next_line.startswith("=" * 20):
                    i += 2
                else:
                    i += 1
                continue

            # 处理小节标题 (例如 "1. 各项分析结果" 或 "图像分析结果：")
            if re.match(r"^\d+\. ", line) or line.endswith("："):
                flush_paragraph()
                elements.append(Paragraph(line, self.default_styles["subsection_heading"]))
                # 如果下一行是分隔线，则跳过分隔线
                if next_line.startswith("-" * 10):
                    i += 2
                else:
                    i += 1
                continue

            # 处理分隔线
            if line.startswith("=" * 20):
                flush_paragraph()
                elements.append(self.default_styles["divider"](
                    width="80%", thickness=1, color=HexColor("#CCCCCC"), spaceBefore=10, spaceAfter=10
                ))
                i += 1
                continue
            if line.startswith("-" * 10):
                 # 较细的分隔线，用于小节内
                flush_paragraph()
                elements.append(self.default_styles["divider"](
                    width="60%", thickness=0.5, color=HexColor("#DDDDDD"), spaceBefore=6, spaceAfter=6
                ))
                i += 1
                continue

            # 处理空行
            if not line:
                flush_paragraph()
                elements.append(Spacer(1, 12)) # 稍大的间距
                i += 1
                continue

            # 处理键值对列表 (例如 "视觉表现：85.00%" 或 "面试者：你好...")
            if "：" in line and not line.startswith(("- ", "* ")):
                 # 判断是键值对还是对话
                 parts = line.split("：", 1)
                 if len(parts) == 2 and parts[1]: # 确保有值
                     # 尝试判断是否为数字或百分比结尾，更可能是键值对
                     value_part = parts[1].strip()
                     if value_part.replace('.', '', 1).isdigit() or value_part.endswith('%') or value_part.replace('.', '', 1).replace('%', '').isdigit():
                         flush_paragraph()
                         elements.append(Paragraph(line, self.default_styles["key_value_text"]))
                         i += 1
                         continue

            # 处理普通列表项
            if line.startswith(("- ", "* ")):
                flush_paragraph()
                list_text = line[2:].strip()
                elements.append(Paragraph(list_text, self.default_styles["list_item_text"]))
                elements.append(Spacer(1, 4)) # 列表项之间的小间距
                i += 1
                continue

            # 处理对话历史 (假设是 "面试者：..." 或 "AI助手：..." 格式)
            if line.startswith(("面试者：", "AI助手：", "用户：")):
                 flush_paragraph()
                 elements.append(Paragraph(line, self.default_styles["conversation_text"]))
                 i += 1
                 continue

            # 其他普通文本行，添加到当前段落
            current_paragraph.append(line)
            i += 1

        # 处理最后可能剩余的段落
        flush_paragraph()

        return elements

    def generate(self, text: str, title: str = "报告",
                 output_dir: str = "output_reports",
                 filename: Optional[str] = None,
                 image_path: Optional[str] = None) -> str:
        try:
            os.makedirs(output_dir, exist_ok=True)
            # 仅在filename为None时生成默认文件名
            if filename is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_prefix = title.replace(" ", "_")
                filename = f"{file_prefix}_{timestamp}.pdf"
            file_path = os.path.join(output_dir, filename)
            doc = SimpleDocTemplate(file_path, pagesize=A4,
                                    leftMargin=50, rightMargin=50, # 调整边距
                                    topMargin=50, bottomMargin=50)
            story = self._build_document_content(text, title, image_path, doc)
            doc.build(story)
            print(f"✅ PDF报告已生成: {file_path}")
            return file_path
        except Exception as e:
            error_msg = f"❌ PDF生成失败：{str(e)}"
            print(error_msg)
            raise

    def _build_document_content(self, text: str, title: str, image_path: Optional[str], doc: SimpleDocTemplate) -> List:
        story = [
            Paragraph(title, self.default_styles["title"]),
            Spacer(1, 0.3 * inch)
        ]
        story.extend(self._parse_text_to_elements(text))
        if image_path and os.path.exists(image_path):
            try:
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("能力雷达图:", self.default_styles["section_heading"]))
                img = Image(image_path)
                page_width = A4[0] - doc.leftMargin - doc.rightMargin
                aspect_ratio = img.drawHeight / img.drawWidth
                img.drawWidth = page_width * 0.8
                img.drawHeight = img.drawWidth * aspect_ratio
                story.append(img)
                story.append(Spacer(1, 0.3 * inch))
            except IOError as e:
                print(f"⚠️ 图片文件读取失败: {e}")
            except Exception as e:
                print(f"⚠️ 添加图片失败: {e}")
        return story

# --- 示例用法 ---
if __name__ == "__main__":
    # 这里使用你优化后的文本内容示例
    sample_text = """AI 面试评估报告

面试类型：软件工程师

========================================
一、各项分析结果
------------------------------
1. 各项分析结果
图像分析结果：
面部表情评估：整体表现自然，微笑频率适中（约30%的帧出现微笑），眼神交流良好，未出现明显负面情绪（如皱眉、不耐烦）。

语音分析结果：
语速评估：平均语速为2.5字/秒，处于正常范围（1.5-3字/秒），未出现过快或过慢情况。
停顿分析：每段回答平均停顿2-3次，停顿时长合理（0.5-1秒），无过长停顿（>3秒）。

文本内容评估结果：
内容相关性：回答与问题高度相关。
逻辑性：回答结构清晰，论点明确。

========================================
二、辅助多模态模型量化分数
------------------------------
视觉表现：85.00%
音频表现：90.50%
文本内容：88.75%
综合得分：87.25%

========================================
三、能力雷达图数据
------------------------------
雷达图已嵌入报告中，以下是其原始数据：

沟通能力：85
专业技能：90
逻辑思维：88
应变能力：82
学习能力：91

========================================
四、综合评估对话历史
------------------------------
面试者：你好，我叫张三。
AI助手：你好张三，请简单介绍一下你自己。
面试者：我是一名有三年工作经验的软件工程师...
AI助手：很好，能谈谈你最近参与的一个项目吗？
"""

    generator = PDFGenerator()
    output_path = generator.generate(
        text=sample_text,
        title="AI面试评估报告",
        output_dir="output_reports",
        image_path=r"output_chart/radar_chart_20240520_120000.png" # 请替换为实际存在的图片路径
    )
    print(f"PDF 已保存到: {output_path}")
