import nonebot
from nonebot import on_command, on_message, get_bot, logger
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, GroupMessageEvent, PrivateMessageEvent, Bot
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import Message
from nonebot import get_driver
import json
import os
import re
import time
import asyncio

# 导入orange插件的AI回复功能（延迟导入）
get_ark_response = None
extract_image_urls = None


async def import_orange_functions():
    """延迟导入orange插件的AI回复功能"""
    global get_ark_response, extract_image_urls
    try:
        from plugins.orange import get_ark_response as g, extract_image_urls as e
        get_ark_response = g
        extract_image_urls = e
        logger.info("已成功导入orange插件的AI回复功能")
    except Exception as e:
        logger.error(f"导入orange插件的AI回复功能失败: {e}")
        # 添加更详细的错误信息
        import traceback
        logger.error(f"导入失败详情: {traceback.format_exc()}")


class KeywordManager:
    """关键词管理类"""
    
    def __init__(self):
        """初始化关键词管理器"""
        # 配置文件路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.plugin_dir, "config.json")
        self.exact_keywords_path = os.path.join(self.plugin_dir, "exactKeywords", "config.json")
        self.contains_keywords_path = os.path.join(self.plugin_dir, "containsKeywords", "config.json")
        
        # 确保配置目录存在
        os.makedirs(os.path.join(self.plugin_dir, "exactKeywords"), exist_ok=True)
        os.makedirs(os.path.join(self.plugin_dir, "containsKeywords"), exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "enableGroups": [-1],  # 默认在所有群组中启用
            "cooldownTime": 180000  # 冷却时间，单位毫秒，默认3分钟
        }
        
        # 记录上次回复时间，键为关键词，值为时间戳
        self.last_reply_time = {}
        
        # 配置和关键词数据
        self.config = self.default_config.copy()
        self.exact_keywords = []
        self.contains_keywords = []
    
    async def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                self.config = {**self.default_config, **config_data}
            logger.info("配置文件加载成功")
        except FileNotFoundError:
            self.config = self.default_config.copy()
            await self.save_config()
            logger.info("配置文件不存在，使用默认配置并创建配置文件")
        except Exception as e:
            self.config = self.default_config.copy()
            logger.error(f"加载配置文件失败: {e}")
    
    async def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    async def load_keywords(self):
        """加载关键词配置"""
        # 加载精确匹配关键词
        try:
            with open(self.exact_keywords_path, "r", encoding="utf-8") as f:
                self.exact_keywords = json.load(f)
            logger.info(f"精确匹配关键词加载成功，共 {len(self.exact_keywords)} 个")
        except FileNotFoundError:
            self.exact_keywords = []
            logger.info("精确匹配关键词文件不存在，使用空列表")
        except Exception as e:
            self.exact_keywords = []
            logger.error(f"加载精确匹配关键词失败: {e}")
        
        # 加载包含匹配关键词
        try:
            with open(self.contains_keywords_path, "r", encoding="utf-8") as f:
                self.contains_keywords = json.load(f)
            logger.info(f"包含匹配关键词加载成功，共 {len(self.contains_keywords)} 个")
        except FileNotFoundError:
            self.contains_keywords = []
            logger.info("包含匹配关键词文件不存在，使用空列表")
        except Exception as e:
            self.contains_keywords = []
            logger.error(f"加载包含匹配关键词失败: {e}")
    
    async def save_keywords(self):
        """保存关键词配置"""
        try:
            with open(self.exact_keywords_path, "w", encoding="utf-8") as f:
                json.dump(self.exact_keywords, f, ensure_ascii=False, indent=2)
            logger.info("精确匹配关键词保存成功")
        except Exception as e:
            logger.error(f"保存精确匹配关键词失败: {e}")
        
        try:
            with open(self.contains_keywords_path, "w", encoding="utf-8") as f:
                json.dump(self.contains_keywords, f, ensure_ascii=False, indent=2)
            logger.info("包含匹配关键词保存成功")
        except Exception as e:
            logger.error(f"保存包含匹配关键词失败: {e}")
    
    @staticmethod
    def is_regex_string(s: str, allowed_flags: str = "gimsuy") -> bool:
        """检查是否为正则表达式字符串"""
        if not isinstance(s, str):
            return False
            
        regex_pattern = r"^/(.+)/(gimsuy*)$"
        match = re.match(regex_pattern, s)
        if not match:
            return False
        
        pattern, flags = match.groups()
        # 检查标志是否有效
        for flag in flags:
            if flag not in allowed_flags:
                return False
        
        # 检查正则表达式是否有效
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    @staticmethod
    def is_image_url(url: str) -> bool:
        """检查是否为图片URL"""
        if not isinstance(url, str):
            return False
        
        domain_pattern = r"^https://multimedia\.nt\.qq\.com\.cn"
        file_pattern = r"\.(png|jpe?g|gif)$"
        return bool(re.match(domain_pattern, url) or re.search(file_pattern, url, re.IGNORECASE) or os.path.exists(url))
    
    def check_cooldown(self, keyword: str, is_at: bool = False) -> bool:
        """检查冷却时间"""
        # 如果被@，则跳过冷却时间检查
        if is_at:
            # 更新上次回复时间
            now = time.time() * 1000  # 转换为毫秒
            self.last_reply_time[keyword] = now
            return True
        
        now = time.time() * 1000  # 转换为毫秒
        last_time = self.last_reply_time.get(keyword, 0)
        
        if now - last_time < self.config["cooldownTime"]:
            return False
        
        # 更新上次回复时间
        self.last_reply_time[keyword] = now
        return True
    
    def get_contains_keywords_count(self) -> int:
        """获取包含匹配关键词数量"""
        return len(self.contains_keywords)
    
    def get_exact_keywords_count(self) -> int:
        """获取精确匹配关键词数量"""
        return len(self.exact_keywords)
    
    def is_group_enabled(self, group_id: int) -> bool:
        """检查群聊是否启用了关键词回复"""
        return group_id in self.config["enableGroups"] or -1 in self.config["enableGroups"]


# 创建关键词管理器实例
keyword_manager = KeywordManager()


# 初始化加载配置和关键词
@get_driver().on_startup
async def init_keyword_plugin():
    """初始化关键词插件"""
    await keyword_manager.load_config()
    await keyword_manager.load_keywords()


# 命令定义
menus = [
    "#kw on/off",
    "#kw rm <关键词>"
]



# 关键词删除命令
kw_rm_cmd = on_command("kw rm", permission=SUPERUSER)


@kw_rm_cmd.handle()
async def handle_kw_rm(arg: Message = CommandArg()):
    """处理#kw rm命令"""
    keyword_to_remove = arg.extract_plain_text().strip()
    
    if not keyword_to_remove:
        await kw_rm_cmd.finish("请指定要删除的关键词")
    
    # 处理引号包围的关键词
    if (keyword_to_remove.startswith('"') and keyword_to_remove.endswith('"')) or \
       (keyword_to_remove.startswith("'") and keyword_to_remove.endswith("'")) or \
       (keyword_to_remove.startswith('`') and keyword_to_remove.endswith('`')):
        keyword_to_remove = keyword_to_remove[1:-1]
    
    removed = False
    
    # 检查并删除exactKeywords中的关键词
    for i, kw in enumerate(keyword_manager.exact_keywords):
        if kw["keyword"] == keyword_to_remove:
            keyword_manager.exact_keywords.pop(i)
            removed = True
            break
    
    # 如果exactKeywords中没有找到，检查containsKeywords
    if not removed:
        for i, kw in enumerate(keyword_manager.contains_keywords):
            if kw["keyword"] == keyword_to_remove:
                keyword_manager.contains_keywords.pop(i)
                removed = True
                break
    
    if removed:
        # 保存关键词配置
        await keyword_manager.save_keywords()
        await kw_rm_cmd.finish("已删除关键词回复")
    else:
        await kw_rm_cmd.finish(f"关键词 '{keyword_to_remove}' 不存在")



# 关键词开关命令
kw_on_cmd = on_command("kw on", permission=SUPERUSER)


@kw_on_cmd.handle()
async def handle_kw_on(event: GroupMessageEvent):
    """处理#kw on命令"""
    group_id = event.group_id
    if group_id not in keyword_manager.config["enableGroups"]:
        keyword_manager.config["enableGroups"].append(group_id)
        await keyword_manager.save_config()
        await kw_on_cmd.finish("已开启关键词回复")
    else:
        await kw_on_cmd.finish("关键词回复已处于开启状态")


kw_off_cmd = on_command("kw off", permission=SUPERUSER)


@kw_off_cmd.handle()
async def handle_kw_off(event: GroupMessageEvent):
    """处理#kw off命令"""
    group_id = event.group_id
    if group_id in keyword_manager.config["enableGroups"]:
        keyword_manager.config["enableGroups"].remove(group_id)
        await keyword_manager.save_config()
        await kw_off_cmd.finish("已关闭关键词回复")
    else:
        await kw_off_cmd.finish("关键词回复已处于关闭状态")


# 默认命令（显示菜单）
kw_cmd = on_command("kw", permission=SUPERUSER)


@kw_cmd.handle()
async def handle_kw():
    """处理#kw命令"""
    await kw_cmd.finish("\n".join(menus))


# 解析主人命令格式的关键词添加命令
def parse_master_add_command(message: str):
    """解析#关键词添加命令的参数"""
    # 匹配 #关键词添加包含（内容） 格式
    contains_match = re.match(r"^#关键词添加包含\s*([^，]+?)\s*，\s*(.+)$", message)
    if contains_match:
        keyword, reply = contains_match.groups()
        return {"keyword": keyword, "reply": reply, "exact_match": False}
    
    # 匹配 #关键词添加确切（内容） 格式
    exact_match = re.match(r"^#关键词添加确切\s*([^，]+?)\s*，\s*(.+)$", message)
    if exact_match:
        keyword, reply = exact_match.groups()
        return {"keyword": keyword, "reply": reply, "exact_match": True}
    
    return {"keyword": None, "reply": None, "exact_match": False}


# 主人专用关键词添加命令
keyword_add_cmd = on_command("关键词添加", permission=SUPERUSER)


@keyword_add_cmd.handle()
async def handle_keyword_add(event: MessageEvent):
    """处理#关键词添加命令"""
    raw_message = str(event.raw_message)
    
    parsed = parse_master_add_command(raw_message)
    if not parsed["keyword"] or not parsed["reply"]:
        await keyword_add_cmd.finish("命令格式错误，请使用：#关键词添加包含（关键词），（回复内容） 或 #关键词添加确切（关键词），（回复内容）")
    
    keyword = parsed["keyword"]
    reply = parsed["reply"]
    exact_match = parsed["exact_match"]
    
    # 检查关键词是否已存在
    existing_keyword = None
    for kw in keyword_manager.exact_keywords:
        if kw["keyword"] == keyword:
            existing_keyword = kw
            break
    if not existing_keyword:
        for kw in keyword_manager.contains_keywords:
            if kw["keyword"] == keyword:
                existing_keyword = kw
                break
    
    if existing_keyword:
        await keyword_add_cmd.finish(f"关键词 '{keyword}' 已存在")
    
    # 检查是否有图片
    image_url = ""
    for msg_seg in event.message:
        if msg_seg.type == "image":
            image_url = msg_seg.data["url"]
            break
    
    new_keyword = {
        "keyword": keyword,
        "reply": image_url if image_url else reply
    }
    
    # 根据exact_match值将关键词添加到相应数组
    if exact_match:
        keyword_manager.exact_keywords.append(new_keyword)
    else:
        keyword_manager.contains_keywords.append(new_keyword)
    
    # 保存关键词配置
    await keyword_manager.save_keywords()
    
    await keyword_add_cmd.finish(f"已添加{'确切' if exact_match else '包含'}关键词回复")


async def handle_whoami_question(event: MessageEvent, is_at: bool, plain_message: str):
    """处理'我是谁'这类问题"""
    who_am_i_regex = r"我是谁|你知道我是谁吗|我是什么身份"
    if not re.search(who_am_i_regex, plain_message, re.IGNORECASE):
        return False
    
    # 检查冷却时间，使用固定关键词"whoami"
    if not keyword_manager.check_cooldown("whoami", is_at):
        return True
    
    try:
        bot = get_bot()
        # 判断是否为超级用户
        if event.user_id in bot.config.superusers:
            reply_content = "你是吾选定的契约之主(ᗜᴗᗜ)"
        else:
            reply_content = "杂鱼而已，不需要知道太多。"
        
        await keyword_message_handler.finish(reply_content)
        return True
    except Exception as e:
        logger.error(f"处理'我是谁'问题失败: {e}")
        return False


async def handle_exact_match_keywords(event: MessageEvent, is_at: bool, plain_message: str):
    """处理精确匹配关键词"""
    for keyword_item in keyword_manager.exact_keywords:
        try:
            keyword = keyword_item["keyword"]
            reply = keyword_item["reply"]
            
            is_matched = False
            
            # 检查是否为正则表达式
            if keyword_manager.is_regex_string(keyword):
                regex_match = re.match(r"^/(.+)/(gimsuy*)$", keyword)
                if regex_match:
                    pattern, flags = regex_match.groups()
                    # 转换Python支持的标志
                    python_flags = 0
                    if 'i' in flags:
                        python_flags |= re.IGNORECASE
                    if 'm' in flags:
                        python_flags |= re.MULTILINE
                    if 's' in flags:
                        python_flags |= re.DOTALL
                    if 'u' in flags:
                        python_flags |= re.UNICODE
                    
                    is_matched = bool(re.fullmatch(pattern, plain_message, python_flags))
            else:
                # 精确匹配
                is_matched = plain_message.strip() == keyword
            
            if is_matched:
                # 检查冷却时间
                if not keyword_manager.check_cooldown(keyword, is_at):
                    continue
                
                # 处理回复
                if keyword_manager.is_image_url(reply):
                    # 发送图片
                    if os.path.exists(reply):
                        # 本地图片，使用绝对路径
                        await keyword_message_handler.finish(MessageSegment.image(os.path.abspath(reply)))
                    else:
                        # 网络图片
                        await keyword_message_handler.finish(MessageSegment.image(reply))
                else:
                    # 发送文本
                    await keyword_message_handler.finish(reply)
                    
                return True
        except Exception as e:
            logger.error(f"精确匹配关键词处理错误: {keyword_item}, {e}")
            continue
    
    return False


async def handle_contains_match_keywords(event: MessageEvent, is_at: bool, plain_message: str):
    """处理包含匹配关键词"""
    for keyword_item in keyword_manager.contains_keywords:
        try:
            keyword = keyword_item["keyword"]
            reply = keyword_item["reply"]
            
            is_matched = False
            
            # 检查是否为正则表达式
            if keyword_manager.is_regex_string(keyword):
                regex_match = re.match(r"^/(.+)/(gimsuy*)$", keyword)
                if regex_match:
                    pattern, flags = regex_match.groups()
                    # 转换Python支持的标志
                    python_flags = 0
                    if 'i' in flags:
                        python_flags |= re.IGNORECASE
                    if 'm' in flags:
                        python_flags |= re.MULTILINE
                    if 's' in flags:
                        python_flags |= re.DOTALL
                    if 'u' in flags:
                        python_flags |= re.UNICODE
                    
                    is_matched = bool(re.search(pattern, plain_message, python_flags))
            else:
                # 包含匹配
                is_matched = keyword in plain_message
            
            if is_matched:
                # 检查冷却时间
                if not keyword_manager.check_cooldown(keyword, is_at):
                    continue
                
                # 处理回复
                if keyword_manager.is_image_url(reply):
                    # 发送图片
                    if os.path.exists(reply):
                        # 本地图片，使用绝对路径
                        await keyword_message_handler.finish(MessageSegment.image(os.path.abspath(reply)))
                    else:
                        # 网络图片
                        await keyword_message_handler.finish(MessageSegment.image(reply))
                else:
                    # 发送文本
                    await keyword_message_handler.finish(reply)
                    
                return True
        except Exception as e:
            logger.error(f"包含匹配关键词处理错误: {keyword_item}, {e}")
            continue
    
    return False


async def handle_ai_reply(event: MessageEvent, is_at: bool, plain_message: str):
    """处理AI回复"""
    if not is_at:
        return False
    
    logger.info("被@且没有匹配到关键词，调用AI回复功能")
    await keyword_message_handler.send("正在思考中...")
    
    # 确保已经导入orange插件的函数
    if get_ark_response is None or extract_image_urls is None:
        await import_orange_functions()
    
    # 检查导入是否成功
    if get_ark_response is None or extract_image_urls is None:
        logger.error("导入orange插件的AI回复功能失败，无法处理@消息")
        await keyword_message_handler.finish("抱歉，AI回复功能暂时不可用")
        return True
    
    # 提取图片URL
    image_urls = await extract_image_urls(event.message)
    
    # 提取文本内容（去除@部分）
    text_content = ""
    for msg_seg in event.message:
        if msg_seg.type == "text":
            text_content += msg_seg.data.get("text", "").strip()
    
    # 构建消息结构
    content = []
    
    # 添加图片内容
    for img_url in image_urls:
        content.append({
            "image_url": {
                "url": img_url
            },
            "type": "image_url"
        })
    
    # 添加文本内容
    if text_content:
        content.append({
            "text": text_content,
            "type": "text"
        })
    
    if content:
        messages = [{"content": content, "role": "user"}]
        
        # 调用API
        try:
            response = await get_ark_response(messages)
            await keyword_message_handler.finish(response)
        except Exception as e:
            logger.error(f"调用AI回复功能失败: {e}")
            await keyword_message_handler.finish("抱歉，AI回复功能暂时不可用")
    else:
        await keyword_message_handler.finish("你@我有什么事吗？")
    
    return True


# 导入消息路由器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.message_router import message_router


# 注册关键词消息处理器
async def keyword_message_handler(bot: Bot, event: MessageEvent) -> bool:
    """处理消息事件，进行关键词匹配和回复"""
    # 检测是否被@
    is_at = False
    try:
        # 直接从bot参数中获取QQ号
        bot_qq = bot.self_id
        
        # 检查消息中是否包含@机器人的部分
        for msg_seg in event.message:
            if msg_seg.type == "at":
                at_qq = msg_seg.data.get("qq")
                if at_qq == bot_qq:
                    is_at = True
                    break
    except Exception as e:
        logger.error(f"检测是否被@失败: {e}")
    
    # 跳过所有以#开头的命令消息（除了关键词插件自己的命令）
    plain_message = event.message.extract_plain_text().strip()
    if plain_message.startswith('#') and not plain_message.startswith(('#kw', '#关键词添加')):
        return False
    
    # 支持群聊和私聊消息
    is_group = isinstance(event, GroupMessageEvent)
    if is_group:
        group_id = event.group_id
        if not keyword_manager.is_group_enabled(group_id):
            return False

    # 使用extract_plain_text()获取纯文本消息内容，这样可以排除@和表情符号等干扰
    plain_message = event.message.extract_plain_text().strip()
    
    # 特殊处理"我是谁"这类问题
    if await handle_whoami_question(event, is_at, plain_message):
        return True
    
    # 处理精确匹配关键词
    if await handle_exact_match_keywords(event, is_at, plain_message):
        return True
    
    # 处理包含匹配关键词
    if await handle_contains_match_keywords(event, is_at, plain_message):
        return True
    
    # 如果被@且没有匹配到关键词，调用AI回复功能
    if is_at:
        await handle_ai_reply(event, is_at, plain_message)
        return True
    
    return False


# 注册处理器
message_router.register_handler(keyword_message_handler, priority=50)
