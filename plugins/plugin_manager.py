import os
import importlib
import importlib.util
import pkgutil
from typing import Dict, List, Optional, Type
from nonebot import get_driver, logger
from nonebot.plugin import Plugin, PluginMetadata
from nonebot.config import Config
import asyncio


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.driver = get_driver()
        self.config = self.driver.config
        
        # 插件目录
        self.plugins_dir = os.path.join(os.getcwd(), "plugins")
        
        # 插件信息存储
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_status: Dict[str, bool] = {}  # True 为启用，False 为禁用
        
        # 初始化时加载插件
        self.driver.on_startup(self.load_all_plugins)
    
    async def load_all_plugins(self):
        """加载所有插件"""
        logger.info("开始加载插件...")
        
        # 遍历插件目录
        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            
            # 跳过 __pycache__ 和隐藏目录
            if item.startswith("__") or item.startswith("."):
                continue
            
            # 跳过文件（只处理目录）
            if not os.path.isdir(item_path):
                continue
            
            # 检查是否有 __init__.py 文件
            init_file = os.path.join(item_path, "__init__.py")
            if not os.path.exists(init_file):
                logger.warning(f"插件目录 {item} 缺少 __init__.py 文件，跳过加载")
                continue
            
            # 加载插件
            await self.load_plugin(item)
        
        logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """
        加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否加载成功
        """
        try:
            # 构建插件路径
            plugin_path = os.path.join(self.plugins_dir, plugin_name)
            
            # 检查插件目录是否存在
            if not os.path.exists(plugin_path):
                logger.error(f"插件目录 {plugin_name} 不存在")
                return False
            
            # 检查 __init__.py 文件是否存在
            init_file = os.path.join(plugin_path, "__init__.py")
            if not os.path.exists(init_file):
                logger.error(f"插件 {plugin_name} 缺少 __init__.py 文件")
                return False
            
            # 尝试导入插件
            module_name = f"plugins.{plugin_name}"
            try:
                # 先尝试直接导入
                module = importlib.import_module(module_name)
            except ImportError:
                # 如果导入失败，尝试通过文件路径导入
                spec = importlib.util.spec_from_file_location(module_name, init_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    logger.error(f"无法加载插件 {plugin_name}")
                    return False
            
            # 检查插件是否有 __plugin_meta__
            if hasattr(module, "__plugin_meta__"):
                metadata = module.__plugin_meta__
                self.plugin_metadata[plugin_name] = metadata
                logger.info(f"加载插件: {metadata.name} - {metadata.description}")
            else:
                logger.warning(f"插件 {plugin_name} 缺少 __plugin_meta__")
            
            # 标记插件为启用状态
            self.plugin_status[plugin_name] = True
            
            # 存储插件信息
            self.plugins[plugin_name] = module
            
            return True
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否卸载成功
        """
        try:
            if plugin_name in self.plugins:
                # 从模块缓存中删除
                if f"plugins.{plugin_name}" in sys.modules:
                    del sys.modules[f"plugins.{plugin_name}"]
                
                # 从存储中删除
                del self.plugins[plugin_name]
                if plugin_name in self.plugin_metadata:
                    del self.plugin_metadata[plugin_name]
                if plugin_name in self.plugin_status:
                    del self.plugin_status[plugin_name]
                
                logger.info(f"卸载插件: {plugin_name}")
                return True
            else:
                logger.error(f"插件 {plugin_name} 未加载")
                return False
        except Exception as e:
            logger.error(f"卸载插件 {plugin_name} 失败: {e}")
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否重新加载成功
        """
        try:
            # 先卸载
            await self.unload_plugin(plugin_name)
            # 再加载
            return await self.load_plugin(plugin_name)
        except Exception as e:
            logger.error(f"重新加载插件 {plugin_name} 失败: {e}")
            return False
    
    async def toggle_plugin(self, plugin_name: str, enable: bool) -> bool:
        """
        启用/禁用指定插件
        
        Args:
            plugin_name: 插件名称
            enable: 是否启用
            
        Returns:
            是否操作成功
        """
        action = "启用" if enable else "禁用"
        try:
            if plugin_name in self.plugin_status:
                self.plugin_status[plugin_name] = enable
                logger.info(f"{action} 插件: {plugin_name}")
                return True
            else:
                logger.error(f"插件 {plugin_name} 未加载")
                return False
        except Exception as e:
            logger.error(f"{action} 插件 {plugin_name} 失败: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        获取指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件对象，如果不存在返回 None
        """
        return self.plugins.get(plugin_name)
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """
        获取指定插件的元数据
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件元数据，如果不存在返回 None
        """
        return self.plugin_metadata.get(plugin_name)
    
    def get_plugin_status(self, plugin_name: str) -> bool:
        """
        获取指定插件的状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件状态，True 为启用，False 为禁用
        """
        return self.plugin_status.get(plugin_name, False)
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """
        获取所有插件
        
        Returns:
            所有插件的字典
        """
        return self.plugins
    
    def get_enabled_plugins(self) -> List[str]:
        """
        获取所有启用的插件
        
        Returns:
            启用插件的名称列表
        """
        return [name for name, status in self.plugin_status.items() if status]
    
    def get_disabled_plugins(self) -> List[str]:
        """
        获取所有禁用的插件
        
        Returns:
            禁用插件的名称列表
        """
        return [name for name, status in self.plugin_status.items() if not status]
    
    async def get_plugins_info(self) -> str:
        """
        获取所有插件的信息
        
        Returns:
            插件信息字符串
        """
        info = "〓 插件信息 〓\n\n"
        
        # 启用的插件
        enabled_plugins = self.get_enabled_plugins()
        if enabled_plugins:
            info += "启用的插件:\n"
            for plugin_name in enabled_plugins:
                metadata = self.get_plugin_metadata(plugin_name)
                if metadata:
                    info += f"├─ {metadata.name} - {metadata.description or '无描述'}\n"
                else:
                    info += f"├─ {plugin_name} - 无元数据\n"
            info += "\n"
        
        # 禁用的插件
        disabled_plugins = self.get_disabled_plugins()
        if disabled_plugins:
            info += "禁用的插件:\n"
            for plugin_name in disabled_plugins:
                metadata = self.get_plugin_metadata(plugin_name)
                if metadata:
                    info += f"├─ {metadata.name} - {metadata.description or '无描述'}\n"
                else:
                    info += f"├─ {plugin_name} - 无元数据\n"
            info += "\n"
        
        info += f"总计: {len(self.plugins)} 个插件\n"
        info += f"启用: {len(enabled_plugins)} 个\n"
        info += f"禁用: {len(disabled_plugins)} 个"
        
        return info


# 导入 sys 模块（在函数中使用）
import sys

# 创建插件管理器实例
plugin_manager = PluginManager()