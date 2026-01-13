from nonebot import on_command, get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.message import Message
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
import sys
import os

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置和插件管理器
from .config import Config
from plugins.plugin_manager import plugin_manager

config = get_plugin_config(Config)


# 插件管理命令
plugin_cmd = on_command('插件管理', permission=SUPERUSER)


@plugin_cmd.handle()
async def handle_plugin_manage(event: MessageEvent, args: Message = CommandArg()):
    """处理插件管理命令"""
    args_text = args.extract_plain_text().strip()
    args_list = args_text.split()
    
    if not args_list:
        # 显示帮助信息
        help_msg = '''〓 插件管理 〓
#插件管理 列表 - 查看所有插件
#插件管理 启用 <插件名> - 启用指定插件
#插件管理 禁用 <插件名> - 禁用指定插件
#插件管理 重载 <插件名> - 重载指定插件
#插件管理 信息 <插件名> - 查看插件信息'''
        await plugin_cmd.send(help_msg)
        return
    
    sub_command = args_list[0]
    
    if sub_command == '列表':
        # 查看所有插件
        info = await plugin_manager.get_plugins_info()
        await plugin_cmd.send(info)
    
    elif sub_command == '启用':
        # 启用指定插件
        if len(args_list) < 2:
            await plugin_cmd.send("请指定要启用的插件名称")
            return
        
        plugin_name = args_list[1]
        success = await plugin_manager.toggle_plugin(plugin_name, True)
        if success:
            await plugin_cmd.send(f"已启用插件: {plugin_name}")
        else:
            await plugin_cmd.send(f"启用插件失败: {plugin_name}")
    
    elif sub_command == '禁用':
        # 禁用指定插件
        if len(args_list) < 2:
            await plugin_cmd.send("请指定要禁用的插件名称")
            return
        
        plugin_name = args_list[1]
        success = await plugin_manager.toggle_plugin(plugin_name, False)
        if success:
            await plugin_cmd.send(f"已禁用插件: {plugin_name}")
        else:
            await plugin_cmd.send(f"禁用插件失败: {plugin_name}")
    
    elif sub_command == '重载':
        # 重载指定插件
        if len(args_list) < 2:
            await plugin_cmd.send("请指定要重载的插件名称")
            return
        
        plugin_name = args_list[1]
        success = await plugin_manager.reload_plugin(plugin_name)
        if success:
            await plugin_cmd.send(f"已重载插件: {plugin_name}")
        else:
            await plugin_cmd.send(f"重载插件失败: {plugin_name}")
    
    elif sub_command == '信息':
        # 查看插件信息
        if len(args_list) < 2:
            await plugin_cmd.send("请指定要查看的插件名称")
            return
        
        plugin_name = args_list[1]
        metadata = plugin_manager.get_plugin_metadata(plugin_name)
        if metadata:
            info = f'''〓 插件信息 〓
名称: {metadata.name}
描述: {metadata.description or '无'}
使用: {metadata.usage or '无'}
版本: {metadata.version or '无'}
作者: {metadata.authors or '无'}
'''
            await plugin_cmd.send(info)
        else:
            await plugin_cmd.send(f"插件 {plugin_name} 不存在或无元数据")
    
    else:
        await plugin_cmd.send("未知命令，请使用 #插件管理 查看帮助")


# 插件元数据
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="plugin_manager",
    description="插件管理功能",
    usage="#插件管理 列表/启用/禁用/重载/信息",
    version="1.0.0",
    authors=["Bot Developer"]
)