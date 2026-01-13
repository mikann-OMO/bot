import traceback
from typing import Optional, Callable, Any, Coroutine
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, MessageEvent


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        """初始化错误处理器"""
        # 错误处理函数注册
        self.error_handlers: dict[str, Callable[[Exception, Bot, MessageEvent], Coroutine[Any, Any, None]]] = {}
        
        # 注册默认错误处理器
        self.register_default_handlers()
    
    def register_default_handlers(self):
        """注册默认错误处理器"""
        logger.info("注册默认错误处理器...")
        
        # 网络错误处理器
        async def network_error_handler(e: Exception, bot: Bot, event: MessageEvent):
            """网络错误处理器"""
            error_msg = "网络连接失败，请检查网络设置后重试"
            await bot.send(event, error_msg)
            logger.error(f"网络错误: {e}")
        
        # API错误处理器
        async def api_error_handler(e: Exception, bot: Bot, event: MessageEvent):
            """API错误处理器"""
            error_msg = "API调用失败，请稍后重试"
            await bot.send(event, error_msg)
            logger.error(f"API错误: {e}")
        
        # 通用错误处理器
        async def general_error_handler(e: Exception, bot: Bot, event: MessageEvent):
            """通用错误处理器"""
            error_msg = "系统错误，请联系管理员"
            await bot.send(event, error_msg)
            logger.error(f"通用错误: {e}")
            logger.error(traceback.format_exc())
        
        # 注册处理器
        self.error_handlers["network"] = network_error_handler
        self.error_handlers["api"] = api_error_handler
        self.error_handlers["general"] = general_error_handler
        
        logger.info("默认错误处理器注册完成")
    
    def register_handler(self, error_type: str, handler: Callable[[Exception, Bot, MessageEvent], Coroutine[Any, Any, None]]):
        """
        注册错误处理器
        
        Args:
            error_type: 错误类型
            handler: 错误处理函数
        """
        self.error_handlers[error_type] = handler
        logger.info(f"注册错误处理器: {error_type}")
    
    async def handle_error(self, e: Exception, bot: Bot, event: MessageEvent, error_type: str = "general"):
        """
        处理错误
        
        Args:
            e: 异常对象
            bot: 机器人实例
            event: 消息事件
            error_type: 错误类型
        """
        try:
            # 获取错误处理器
            handler = self.error_handlers.get(error_type, self.error_handlers["general"])
            
            # 处理错误
            await handler(e, bot, event)
        except Exception as handler_error:
            logger.error(f"错误处理器执行失败: {handler_error}")
            logger.error(traceback.format_exc())
    
    def get_error_type(self, e: Exception) -> str:
        """
        根据异常类型获取错误类型
        
        Args:
            e: 异常对象
            
        Returns:
            错误类型
        """
        import aiohttp
        
        # 判断异常类型
        if isinstance(e, (aiohttp.ClientConnectionError, aiohttp.ClientTimeout)):
            return "network"
        elif isinstance(e, aiohttp.ClientResponseError):
            return "api"
        else:
            return "general"


# 创建错误处理器实例
error_handler = ErrorHandler()


def error_handler_decorator(func):
    """
    错误处理装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    async def wrapper(bot: Bot, event: MessageEvent, *args, **kwargs):
        try:
            return await func(bot, event, *args, **kwargs)
        except Exception as e:
            error_type = error_handler.get_error_type(e)
            await error_handler.handle_error(e, bot, event, error_type)
            return False
    
    return wrapper