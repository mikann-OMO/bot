from nonebot import on_command, get_driver
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import Message
import os
import sys
import psutil
import time
import platform
from nonebot.log import logger


# 获取NoneBot配置
driver = get_driver()
config = driver.config


class BotStatusManager:
    """Bot状态管理类"""
    
    @staticmethod
    async def get_status() -> str:
        """获取Bot状态信息"""
        # 插件数量信息
        plugins_count = BotStatusManager._count_plugins()
        
        # 运行时间（使用进程的运行时间而不是系统启动时间）
        formatted_time = BotStatusManager._get_uptime()
        
        # 内存信息
        mem_used_gb, mem_total_gb, mem_percent = BotStatusManager._get_memory_info()
        
        # 硬盘信息
        disk_used_gb, disk_total_gb, disk_percent = BotStatusManager._get_disk_info()
        
        status_msg = f'''〓 Bot 状态 〓
NoneBot
插件{plugins_count}个已启用
{formatted_time}
{platform.platform()} - {platform.architecture()[0]} - Python {platform.python_version()}
{mem_used_gb:.2f} GB/{mem_total_gb:.2f} GB - {mem_percent}%
{disk_used_gb:.2f} GB/{disk_total_gb:.2f} GB - {disk_percent}%'''
        return status_msg
    
    @staticmethod
    def _count_plugins() -> int:
        """统计插件数量"""
        plugins_dir = os.path.join(os.getcwd(), 'plugins')
        plugins_count = 0
        
        # 确保插件目录存在
        if not os.path.exists(plugins_dir):
            logger.warning(f"插件目录 {plugins_dir} 不存在")
            return 0
        
        for item in os.listdir(plugins_dir):
            item_path = os.path.join(plugins_dir, item)
            # 统计Python插件文件
            if os.path.isfile(item_path) and item.endswith('.py'):
                plugins_count += 1
            # 统计插件目录（包含__init__.py的目录）
            elif os.path.isdir(item_path):
                init_file = os.path.join(item_path, '__init__.py')
                if os.path.isfile(init_file):
                    plugins_count += 1
        
        return plugins_count
    
    @staticmethod
    def _get_uptime() -> str:
        """获取Bot运行时间"""
        process = psutil.Process()
        uptime_seconds = time.time() - process.create_time()
        
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        return f'{days}d {hours}h {minutes}m {seconds}s'
    
    @staticmethod
    def _get_memory_info() -> tuple[float, float, int]:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        mem_used_gb = mem.used / (1024 ** 3)
        mem_total_gb = mem.total / (1024 ** 3)
        return mem_used_gb, mem_total_gb, mem.percent
    
    @staticmethod
    def _get_disk_info() -> tuple[float, float, int]:
        """获取硬盘信息"""
        disk = psutil.disk_usage('C:' if platform.system() == 'Windows' else '/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        return disk_used_gb, disk_total_gb, disk.percent


class BotAboutManager:
    """Bot关于信息管理类"""
    
    @staticmethod
    async def get_about() -> str:
        """获取Bot关于信息"""
        return "〓 NoneBot〓\n新一代QQ机器人框架\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n核心特性\n├─ 极简轻量：不依赖复杂环境，安装即用\n├─ 优雅架构：Python 开发，类型安全\n├─ 热插拔插件：模块化设计，功能扩展无忧\n├─ 高性能：基于 NoneBot 事件驱动模型\n├─ 跨平台支持：Windows/Linux/macOS 全兼容\n\n技术架构\n└─ 底层协议：NapCatQQ 核心驱动\n└─ 开发框架：NoneBot2\n└─ 生态支持：pip 海量模块即插即用\n\n开发者友好\n完善文档 + 示例项目 = 1分钟快速上手\n\n开源协议：MIT License，欢迎贡献代码！"


class BotSettingManager:
    """Bot设置管理类"""
    
    @staticmethod
    async def handle_setting(args: str) -> str:
        """处理设置命令"""
        args_list = args.split()
        if not args_list:
            return '''〓 Bot 设置 〓
#设置 详情'''
        
        sub_command = args_list[0]
        
        if sub_command == '详情':
            return await BotSettingManager._get_settings_detail()
        
        return "未知命令！"
    
    @staticmethod
    async def _get_settings_detail() -> str:
        """获取设置详情"""
        # 使用NoneBot的SUPERUSERS配置
        master_list = '，'.join(map(str, config.superusers))
        return f'''〓 Bot 设置 〓
超级用户: {master_list}
注：管理员功能已移除，使用NoneBot标准权限系统'''


class BotExitManager:
    """Bot退出管理类"""
    
    @staticmethod
    async def handle_exit() -> str:
        """处理退出命令"""
        logger.info('Bot exit command received, exiting process...')
        return '已退出框架进程！'


# 使用on_command装饰器创建命令处理函数
status_cmd = on_command('状态', permission=SUPERUSER)
about_cmd = on_command('关于', permission=SUPERUSER)
exit_cmd = on_command('退出', permission=SUPERUSER)
setting_cmd = on_command('设置', permission=SUPERUSER)


@status_cmd.handle()
async def handle_status(event: MessageEvent):
    """处理状态命令"""
    status_msg = await BotStatusManager.get_status()
    await status_cmd.send(status_msg)


@about_cmd.handle()
async def handle_about(event: MessageEvent):
    """处理关于命令"""
    about_msg = await BotAboutManager.get_about()
    await about_cmd.send(about_msg)


@exit_cmd.handle()
async def handle_exit(event: MessageEvent):
    """处理退出命令"""
    exit_msg = await BotExitManager.handle_exit()
    await exit_cmd.send(exit_msg)
    sys.exit(0)


@setting_cmd.handle()
async def handle_setting(event: MessageEvent, args: Message = CommandArg()):
    """处理设置命令"""
    args_text = args.extract_plain_text().strip()
    msg = await BotSettingManager.handle_setting(args_text)
    await setting_cmd.send(msg)