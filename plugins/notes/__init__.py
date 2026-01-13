from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import Message
from nonebot.adapters.onebot.v11 import Bot
import os
import json
import time
import datetime
import webbrowser
import re
from nonebot.log import logger


class NotesManager:
    """便签管理类"""
    
    def __init__(self):
        """初始化便签管理器"""
        # 博客目录配置
        self.BLOG_DIR = r"D:\Blog\orange"
        self.NOTES_DIR = os.path.join(self.BLOG_DIR, "src", "content", "notes")
        self.LAST_NOTE_FILE = os.path.join(self.NOTES_DIR, ".last_note.json")
        
        # 确保目录存在
        os.makedirs(self.NOTES_DIR, exist_ok=True)
    
    async def create_new_note(self, event: MessageEvent, args: Message) -> str:
        """创建新便签"""
        # 提取文本内容
        note_content = args.extract_plain_text().strip()
        
        # 提取图片
        images = []
        for segment in args:
            if segment.type == "image":
                images.append(segment.data["url"])
        
        if not note_content and not images:
            return "请输入便签内容或添加图片！"
        
        try:
            # 生成唯一的便签文件名
            timestamp = int(time.time())
            note_file = os.path.join(self.NOTES_DIR, f"note_{timestamp}.md")
            
            # 处理图片 - 直接使用原始URL
            image_markdown = ""
            if images:
                for i, image_url in enumerate(images):
                    # 直接使用原始图片URL
                    image_markdown += f"![图片{i+1}]({image_url})\n\n"
                    logger.info(f"Added image URL to note: {image_url}")
            
            # 组合内容
            full_content = note_content
            if image_markdown:
                if full_content:
                    full_content += "\n\n" + image_markdown
                else:
                    full_content = image_markdown
            
            # 获取当前时间
            now = datetime.datetime.now()
            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
            # 生成带微秒的ISO格式时间，并添加Z时区标识
            iso_time = now.isoformat()[:23] + "Z"

            # 写入便签内容，包含YAML Front Matter
            with open(note_file, "w", encoding="utf-8") as f:
                f.write("---\n")
                f.write(f"title: 便签 {formatted_time}\n")
                f.write(f"published: {iso_time}\n")
                f.write("draft: false\n")
                f.write("---\n\n")
                f.write(f"# 便签 {formatted_time}\n\n")
                f.write(full_content)
            
            # 记录最后一条便签
            self._save_last_note_info(note_file, timestamp, full_content)
            
            logger.info(f"Created new note: {note_file}")
            return f"便签已创建：{note_file}"
        except Exception as e:
            logger.error(f"Failed to create note: {str(e)}")
            return f"创建便签失败：{str(e)}"
    
    async def recall_last_note(self) -> str:
        """撤回上一条便签"""
        try:
            if not os.path.exists(self.LAST_NOTE_FILE):
                return "没有可撤回的便签！"
            
            # 读取最后一条便签信息
            last_note_info = self._read_last_note_info()
            
            # 删除便签文件
            if os.path.exists(last_note_info["file"]):
                os.remove(last_note_info["file"])
                logger.info(f"Recalled note: {last_note_info['file']}")
            
            # 删除记录文件
            os.remove(self.LAST_NOTE_FILE)
            
            return "已撤回上一条便签及相关图片！"
        except Exception as e:
            logger.error(f"Failed to recall note: {str(e)}")
            return f"撤回便签失败：{str(e)}"
    
    async def preview_notes(self) -> str:
        """预览便签"""
        try:
            # 简单的HTML预览生成
            preview_html = os.path.join(self.NOTES_DIR, "preview.html")
            
            # 获取所有便签文件
            note_files = self._get_note_files()
            
            # 生成预览HTML
            html_content = self._generate_preview_html(note_files)
            
            # 写入预览HTML文件
            with open(preview_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # 打开浏览器预览
            webbrowser.open(f"file://{preview_html}")
            
            logger.info(f"Generated note preview: {preview_html}")
            return f"已生成预览，浏览器已打开：{preview_html}"
        except Exception as e:
            logger.error(f"Failed to preview notes: {str(e)}")
            return f"预览失败：{str(e)}"
    
    def _save_last_note_info(self, note_file: str, timestamp: int, content: str):
        """保存最后一条便签信息"""
        last_note_info = {
            "file": note_file,
            "timestamp": timestamp,
            "content": content
        }
        with open(self.LAST_NOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(last_note_info, f, ensure_ascii=False, indent=2)
    
    def _read_last_note_info(self) -> dict:
        """读取最后一条便签信息"""
        with open(self.LAST_NOTE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _get_note_files(self) -> list:
        """获取所有便签文件"""
        return sorted(
            [f for f in os.listdir(self.NOTES_DIR) if f.startswith("note_") and f.endswith(".md")],
            key=lambda x: int(x.split("_")[1].split(".")[0]),
            reverse=True
        )
    
    def _generate_preview_html(self, note_files: list) -> str:
        """生成预览HTML"""
        html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>便签预览</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .note {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .note h1 {
            font-size: 18px;
            color: #333;
            margin-bottom: 10px;
        }
        .note-content {
            font-size: 16px;
            line-height: 1.6;
            color: #666;
        }
        .no-notes {
            text-align: center;
            color: #999;
            padding: 40px;
        }
    </style>
</head>
<body>
    <h1>博客便签预览</h1>
"""
        
        if not note_files:
            html_content += "<div class='no-notes'>暂无便签</div>"
        else:
            for note_file in note_files[:10]:  # 只显示最近10条
                note_path = os.path.join(self.NOTES_DIR, note_file)
                with open(note_path, "r", encoding="utf-8") as f:
                    note_content = f.read()
                
                # 解析便签内容，跳过YAML Front Matter
                title, content = self._parse_note_content(note_content)
                
                # 处理Markdown图片 - 直接使用原始URL
                content_html = content
                # 替换Markdown图片为HTML图片标签
                content_html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1" style="max-width: 100%; height: auto; margin: 10px 0; border-radius: 4px;" />', content_html)
                # 处理换行
                content_html = content_html.replace("\n", "<br>")
                
                html_content += f"""
        <div class='note'>
            <h1>{title}</h1>
            <div class='note-content'>{content_html}</div>
        </div>
"""
        
        html_content += """
</body>
</html>"""
        
        return html_content
    
    def _parse_note_content(self, note_content: str) -> tuple[str, str]:
        """解析便签内容，提取标题和正文"""
        # 解析便签内容，跳过YAML Front Matter
        lines = note_content.split("\n")
        content_start_idx = 0
        
        # 跳过YAML Front Matter
        if lines and lines[0] == "---":
            for i, line in enumerate(lines[1:], 1):
                if line == "---":
                    content_start_idx = i + 1
                    break
        
        # 从内容部分查找标题
        title = "未命名便签"
        content_lines = []
        
        for line in lines[content_start_idx:]:
            if line.startswith("# ") and title == "未命名便签":
                title = line[2:]
            else:
                content_lines.append(line)
        
        content = "\n".join(content_lines)
        return title, content


# 创建便签管理器实例
notes_manager = NotesManager()

# 创建命令处理器
new_note_cmd = on_command('新建便签', permission=SUPERUSER)
recall_note_cmd = on_command('便签 撤回', permission=SUPERUSER)
preview_note_cmd = on_command('便签 预览', permission=SUPERUSER)


@new_note_cmd.handle()
async def handle_new_note(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """处理新建便签命令"""
    result = await notes_manager.create_new_note(event, args)
    await new_note_cmd.send(result)


@recall_note_cmd.handle()
async def handle_recall_note(event: MessageEvent):
    """处理撤回便签命令"""
    result = await notes_manager.recall_last_note()
    await recall_note_cmd.send(result)


@preview_note_cmd.handle()
async def handle_preview_note(event: MessageEvent):
    """处理预览便签命令"""
    result = await notes_manager.preview_notes()
    await preview_note_cmd.send(result)