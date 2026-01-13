#!/usr/bin/env python3
"""NoneBot 主入口文件"""

# 导入必要的模块
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11_Adapter
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot import get_driver
import os


# 全局变量：是否已发送上线消息
# 用于防止重复发送上线通知
shangxian_message_sent = False


def chushihua_nonebot():
    """初始化 NoneBot"""
    # 自动加载.env文件中的配置
    # 注意：.env文件需要放在项目根目录
    nonebot.init()
    
    # 注册OneBot V11适配器
    # 用于支持与OneBot协议兼容的机器人框架，如NapCat
    driver = get_driver()
    driver.register_adapter(ONEBOT_V11_Adapter)
    
    return driver


def jiazai_plugins():
    """加载所有插件"""
    # 获取插件目录路径
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    
    # 确保插件目录存在
    if not os.path.exists(plugins_dir):
        logger.warning(f"插件目录 {plugins_dir} 不存在")
        return
    
    # 遍历插件目录
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


async def fa_song_shangxian_message(bot: Bot, superusers: list):
    """向超级用户发送上线消息"""
    global shangxian_message_sent
    
    # 检查是否已经发送过上线消息
    if shangxian_message_sent:
        logger.info("上线消息已发送，跳过重复发送")
        return
    
    # 遍历所有超级用户
    for user in superusers:
        try:
            # 发送私聊消息通知上线
            await bot.send_private_msg(user_id=int(user), message="Bot已上线")
            logger.info(f"Bot {bot.self_id} 已向超级用户 {user} 发送上线消息")
            # 标记为已发送
            shangxian_message_sent = True
        except Exception as e:
            logger.error(f"Bot {bot.self_id} 向超级用户 {user} 发送上线消息失败: {e}")


def huo_qu_superusers():
    """获取超级用户列表"""
    # 从NoneBot驱动中获取配置
    driver = get_driver()
    superusers = driver.config.superusers
    
    # 检查是否配置了超级用户
    if not superusers:
        logger.warning("未配置超级用户")
        return None
    
    return superusers


async def on_startup():
    """Bot 启动事件处理"""
    logger.info("Bot 已启动，准备发送上线消息...")
    
    # 获取所有已连接的Bot实例
    bots: dict[str, Bot] = nonebot.get_bots()
    if not bots:
        logger.warning("暂无可用的Bot实例")
        return
    
    # 获取超级用户列表
    superusers = huo_qu_superusers()
    if not superusers:
        return
    
    # 向所有超级用户发送上线消息
    for bot_id, bot in bots.items():
        await fa_song_shangxian_message(bot, superusers)


async def on_bot_connect(bot: Bot):
    """Bot 连接成功事件处理"""
    logger.info(f"Bot {bot.self_id} 已连接")
    
    # 获取超级用户列表
    superusers = huo_qu_superusers()
    if not superusers:
        return
    
    # 向所有超级用户发送上线消息
    await fa_song_shangxian_message(bot, superusers)


if __name__ == "__main__":
    """程序主入口"""
    logger.info("Starting NoneBot with NapCat...")
    
    # 1. 初始化NoneBot
    driver = chushihua_nonebot()
    
    # 2. 注册事件处理函数
    # 注册启动事件和Bot连接事件
    driver.on_startup(on_startup)
    driver.on_bot_connect(on_bot_connect)
    
    # 3. 加载插件
    jiazai_plugins()
    
    # 4. 运行NoneBot
    # 监听所有网络接口，端口8080
    nonebot.run(host="0.0.0.0", port=8080)
