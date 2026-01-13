from nonebot import on_message, get_driver
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, PrivateMessageEvent, Bot
from nonebot.permission import SUPERUSER
from nonebot.log import logger
import asyncio
import os
import sys

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入插件管理器
from plugins.plugin_manager import plugin_manager


class MessageRouter:
    """消息路由器"""
    
    def __init__(self):
        """初始化消息路由器"""
        self.driver = get_driver()
        self.message_handler = on_message(priority=10)
        
        # 消息处理器注册
        self.message_handlers = []
        
        # 初始化时注册默认处理器
        self.driver.on_startup(self.register_default_handlers)
    
    def register_handler(self, handler, priority=50):
        """
        注册消息处理器
        
        Args:
            handler: 消息处理器函数
            priority: 优先级，数字越小优先级越高
        """
        self.message_handlers.append((priority, handler))
        # 按优先级排序
        self.message_handlers.sort(key=lambda x: x[0])
        logger.info(f"注册消息处理器，优先级: {priority}")
    
    async def register_default_handlers(self):
        """注册默认消息处理器"""
        logger.info("注册默认消息处理器...")
        
        # 这里可以注册一些默认的消息处理器
        # 例如：命令处理器、关键词处理器、AI回复处理器等
    
    async def route_message(self, bot: Bot, event: MessageEvent):
        """
        路由消息到相应的处理器
        
        Args:
            bot: 机器人实例
            event: 消息事件
        """
        # 检查消息类型
        is_group = isinstance(event, GroupMessageEvent)
        is_private = isinstance(event, PrivateMessageEvent)
        
        # 检查插件状态
        if not self._check_plugin_status("keyword"):
            logger.debug("关键词插件已禁用，跳过处理")
            return
        
        # 处理消息
        for priority, handler in self.message_handlers:
            try:
                result = await handler(bot, event)
                if result:
                    # 处理器已处理消息，停止路由
                    logger.debug(f"消息已被处理器处理，优先级: {priority}")
                    return
            except Exception as e:
                logger.error(f"消息处理器执行失败: {e}")
                continue
        
        # 如果没有处理器处理消息，继续传递给其他插件
        logger.debug("消息未被任何处理器处理，继续传递")
    
    def _check_plugin_status(self, plugin_name: str) -> bool:
        """
        检查插件状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件是否启用
        """
        return plugin_manager.get_plugin_status(plugin_name)


# 创建消息路由器实例
message_router = MessageRouter()


# 消息处理函数
@message_router.message_handler.handle()
async def handle_message(bot: Bot, event: MessageEvent):
    """处理消息事件"""
    await message_router.route_message(bot, event)