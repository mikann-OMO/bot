#!/usr/bin/env python3
"""NoneBot 主入口文件"""

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11_Adapter
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot import get_driver
import os


def init_nonebot():
    """初始化 NoneBot"""
    # 自动加载.env文件
    nonebot.init()
    
    # 注册适配器
    driver = get_driver()
    driver.register_adapter(ONEBOT_V11_Adapter)
    
    return driver


def load_plugins():
    """加载所有插件"""
    # 加载本地插件
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    
    # 确保插件目录存在
    if not os.path.exists(plugins_dir):
        logger.warning(f"插件目录 {plugins_dir} 不存在")
        return
    
    for plugin_name in os.listdir(plugins_dir):
        plugin_path = os.path.join(plugins_dir, plugin_name)
        
        # 加载单个Python插件文件
        if os.path.isfile(plugin_path) and plugin_path.endswith(".py"):
            try:
                nonebot.load_plugin(f"plugins.{plugin_name[:-3]}")
                logger.info(f"已加载插件: {plugin_name[:-3]}")
            except Exception as e:
                logger.error(f"加载插件 {plugin_name[:-3]} 失败: {e}")
        
        # 加载插件目录
        elif os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "__init__.py")):
            try:
                nonebot.load_plugin(f"plugins.{plugin_name}")
                logger.info(f"已加载插件: {plugin_name}")
            except Exception as e:
                logger.error(f"加载插件 {plugin_name} 失败: {e}")
    
    # 加载外部插件
    try:
        nonebot.load_plugin("nonebot_plugin_help")
        logger.info("已加载外部插件: nonebot_plugin_help")
    except Exception as e:
        logger.error(f"加载外部插件 nonebot_plugin_help 失败: {e}")
    
    try:
        nonebot.load_plugin("nonebot_plugin_manager")
        logger.info("已加载外部插件: nonebot_plugin_manager")
    except Exception as e:
        logger.error(f"加载外部插件 nonebot_plugin_manager 失败: {e}")


# 标志：是否已发送上线消息
online_message_sent = False

async def send_online_message(bot: Bot, superusers: list):
    """向超级用户发送上线消息"""
    global online_message_sent
    if online_message_sent:
        logger.info(f"上线消息已发送，跳过重复发送")
        return
    
    for user in superusers:
        try:
            await bot.send_private_msg(user_id=int(user), message="orange已上线")
            logger.info(f"Bot {bot.self_id} 已向超级用户 {user} 发送上线消息")
            online_message_sent = True
        except Exception as e:
            logger.error(f"Bot {bot.self_id} 向超级用户 {user} 发送上线消息失败: {e}")


async def on_startup():
    """Bot 启动事件处理"""
    logger.info("Bot 已启动，准备发送上线消息...")
    
    # 获取所有已连接的Bot实例
    bots: dict[str, Bot] = nonebot.get_bots()
    if not bots:
        logger.warning("暂无可用的Bot实例")
        return
    
    # 从配置中获取超级用户
    driver = get_driver()
    superusers = driver.config.superusers
    if not superusers:
        logger.warning("未配置超级用户")
        return
    
    # 向所有超级用户发送上线消息
    for bot_id, bot in bots.items():
        await send_online_message(bot, superusers)


async def on_bot_connect(bot: Bot):
    """Bot 连接成功事件处理"""
    logger.info(f"Bot {bot.self_id} 已连接")
    
    # 获取超级用户
    driver = get_driver()
    superusers = driver.config.superusers
    if not superusers:
        return
    
    # 向所有超级用户发送上线消息
    await send_online_message(bot, superusers)


if __name__ == "__main__":
    logger.info("Starting NoneBot with NapCat...")
    
    # 初始化NoneBot
    driver = init_nonebot()
    
    # 注册事件处理函数
    driver.on_startup(on_startup)
    driver.on_bot_connect(on_bot_connect)
    
    # 加载插件
    load_plugins()
    
    # 运行NoneBot
    nonebot.run(host="0.0.0.0", port=8080)
