from nonebot import on_command, on_message, on_startswith, get_driver, get_bot
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent, Bot
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
import json
import re
import aiohttp
import asyncio
from nonebot.log import logger

# 配置火山引擎API参数
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
ARK_API_KEY = "d7025fba-5cb2-4102-a724-6cf0e15bf9a9"
ARK_MODEL = "doubao-seed-1-6-251015"

# 机器人名称
ROBOT_NAME = "orange"

# 提取图片URL的正则表达式
IMG_URL_PATTERN = re.compile(r'url=(\?)(["\'])?(https?://[^\\"\']+)\1?\2?')

# 导入消息路由器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.message_router import message_router

async def get_ark_response(messages):
    """
    调用火山引擎ARK API获取响应
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ARK_API_KEY}"
    }
    
    data = {
        "model": ARK_MODEL,
        "max_completion_tokens": 65535,
        "messages": messages,
        "reasoning_effort": "medium"
    }
    
    try:
        logger.info(f"调用ARK API，消息数量: {len(messages)}")
        async with aiohttp.ClientSession() as session:
            async with session.post(ARK_API_URL, headers=headers, json=data, timeout=60) as response:
                response.raise_for_status()
                
                result = await response.json()
                logger.info(f"ARK API调用成功，响应长度: {len(str(result))}")
                
                # 检查响应结构
                if "choices" in result and result["choices"] and "message" in result["choices"][0]:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"ARK API响应结构异常: {json.dumps(result, ensure_ascii=False)}")
                    return "API响应结构异常，请稍后重试"
            
    except aiohttp.ClientTimeout:
        logger.error("ARK API调用超时")
        return "请求超时，请稍后重试"
    except aiohttp.ClientConnectionError:
        logger.error("ARK API连接失败")
        return "网络连接失败，请检查网络设置"
    except aiohttp.ClientResponseError as e:
        logger.error(f"ARK API HTTP错误: {str(e)}")
        return f"API请求错误: {str(e)}"
    except json.JSONDecodeError as e:
        logger.error(f"ARK API响应解析失败: {str(e)}")
        return "API响应解析失败，请稍后重试"
    except Exception as e:
        logger.error(f"ARK API调用失败: {str(e)}", exc_info=True)
        return "系统错误，请联系管理员"

async def extract_image_urls(message: Message):
    """
    从消息中提取图片URL
    """
    image_urls = []
    for segment in message:
        if segment.type == "image":
            image_urls.append(segment.data.get("url", ""))
        elif segment.type == "text":
            # 从文本中提取图片URL
            urls = IMG_URL_PATTERN.findall(segment.data.get("text", ""))
            for url in urls:
                image_urls.append(url[2])
    return image_urls

# 系统提示词（统一管理）
SYSTEM_PROMPT = "你是一个名叫orange的QQ群聊天机器人，性格友善、乐于助人且带一点中二幽默感。请用自然、友好的语言回复用户的问题和请求，适当加入一些有趣的表情或语气词，让对话更加生动有趣。"

async def build_ark_messages(text: str, image_urls: list):
    """
    构建ARK API请求的消息结构（统一构建逻辑）
    """
    messages = [
        {
            "content": [
                {
                    "text": SYSTEM_PROMPT,
                    "type": "text"
                }
            ],
            "role": "system"
        }
    ]
    
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
    if text:
        content.append({
            "text": text,
            "type": "text"
        })
    
    if content:
        messages.append({
            "content": content,
            "role": "user"
        })
    
    return messages

async def process_message_content(message: Message, bot_qq: str, is_at: bool, is_oi_prefix: bool) -> tuple[str, list]:
    """
    处理消息内容，提取文本和图片
    返回：(处理后的文本内容, 图片URL列表)
    """
    message_text = message.extract_plain_text().strip()
    image_urls = await extract_image_urls(message)
    
    content = message_text
    
    # 如果被@提及，去除@部分
    if is_at:
        pattern = r'@' + re.escape(bot_qq) + r'\s*'
        content = re.sub(pattern, '', message_text).strip()
    # 如果是oi前缀，去除前缀
    elif is_oi_prefix:
        content = message_text[2:].strip()
    
    return content, image_urls

async def generate_and_send_response(bot: Bot, event: MessageEvent, text: str, image_urls: list):
    """
    生成响应并发送（统一回复流程）
    """
    await bot.send(event, "正在思考中...")
    
    # 构建消息结构
    messages = await build_ark_messages(text, image_urls)
    
    if len(messages) > 1:  # 确保有用户消息内容
        try:
            # 调用API
            response = await get_ark_response(messages)
            await bot.send(event, response)
        except Exception as e:
            logger.error(f"生成回复失败: {str(e)}")
            await bot.send(event, f"回复生成失败: {str(e)}")
    else:
        await bot.send(event, "你找我有什么事吗？")

# 保留原有的gpt命令功能，以便兼容旧的使用方式
gpt_cmd = on_command('gpt')
gpt_chat_cmd = on_command('chat')

@gpt_cmd.handle()
async def handle_gpt(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    处理#gpt命令
    """
    text = args.extract_plain_text().strip()
    image_urls = await extract_image_urls(args)
    
    if not text and not image_urls:
        await gpt_cmd.send("请输入要查询的内容或图片")
        return
    
    await generate_and_send_response(bot, event, text, image_urls)

@gpt_chat_cmd.handle()
async def handle_gpt_chat(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    """
    处理#chat命令，简化版聊天
    """
    text = args.extract_plain_text().strip()
    
    if not text:
        await gpt_chat_cmd.send("请输入聊天内容")
        return
    
    await generate_and_send_response(bot, event, text, [])

# 注册orange消息处理器
async def orange_message_handler(bot: Bot, event: MessageEvent) -> bool:
    """
    处理消息并根据触发条件回复
    """
    # 获取机器人自身的QQ号
    bot_qq = bot.self_id
    
    # 获取消息内容
    message = event.message
    message_text = message.extract_plain_text().strip()
    
    # 检查是否被@提及
    is_at = False
    for segment in message:
        if segment.type == "at" and segment.data.get("qq") == bot_qq:
            is_at = True
            break
    
    # 检查是否使用oi前缀
    is_oi_prefix = message_text.lower().startswith("oi")
    
    # 如果满足触发条件
    if is_at or is_oi_prefix:
        # 处理消息内容
        content, image_urls = await process_message_content(message, bot_qq, is_at, is_oi_prefix)
        await generate_and_send_response(bot, event, content, image_urls)
        return True
    
    return False


# 注册处理器
message_router.register_handler(orange_message_handler, priority=60)

# 监听bot启动事件，向超级用户发送上线消息
driver = get_driver()

# 添加启动日志，确认插件被正确加载
logger.info(f"{ROBOT_NAME}插件已加载，将在bot连接时向超级用户发送上线消息")

# 标志：是否已发送上线消息
online_msg_sent = False

# 定义发送上线消息的函数
async def send_online_msg(bot: Bot):
    """
    向超级用户发送上线消息
    """
    global online_msg_sent
    if online_msg_sent:
        logger.info(f"上线消息已发送，跳过重复发送")
        return
    
    super_user = "3352604554"
    message = f"{ROBOT_NAME}已上线"
    try:
        logger.info(f"开始向超级用户 {super_user} 发送上线消息")
        logger.info(f"当前bot信息: {bot}")
        logger.info(f"准备发送的消息: {message}")
        
        # 发送私聊消息
        await bot.send_private_msg(user_id=super_user, message=message)
        logger.info(f"已向超级用户 {super_user} 发送上线消息: {message}")
        online_msg_sent = True
    except Exception as e:
        logger.error(f"发送上线消息失败: {str(e)}", exc_info=True)
        logger.error(f"失败详情: bot={bot}, user_id={super_user}, message={message}")

# @driver.on_bot_connect
# async def on_bot_connect_handler(bot: Bot):
#     """
#     当bot成功连接到适配器时，向超级用户发送上线消息
#     """
#     logger.info(f"bot已连接到适配器，触发on_bot_connect事件")
#     await send_online_msg(bot)

@driver.on_startup
async def on_startup_handler():
    """
    当NoneBot启动时，记录插件准备就绪状态
    """
    logger.info(f"NoneBot启动，{ROBOT_NAME}插件准备就绪")
    logger.info("将等待on_bot_connect事件触发后发送上线消息")
