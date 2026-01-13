import os
import json
from typing import Dict, Any, Optional
from nonebot.log import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 配置文件存储路径
        self.config_dir = os.path.join(os.getcwd(), "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 配置存储
        self.configs: Dict[str, Dict[str, Any]] = {}
        
        # 加载默认配置
        self.load_default_configs()
    
    def load_default_configs(self):
        """加载默认配置"""
        logger.info("加载默认配置...")
        
        # 插件默认配置
        self.configs["plugin_manager"] = {
            "auto_load": True,
            "disabled_plugins": []
        }
        
        self.configs["keyword"] = {
            "enableGroups": [-1],
            "cooldownTime": 180000
        }
        
        self.configs["orange"] = {
            "api_key": "d7025fba-5cb2-4102-a724-6cf0e15bf9a9",
            "model": "doubao-seed-1-6-251015",
            "robot_name": "orange"
        }
        
        logger.info("默认配置加载完成")
    
    def get_config(self, plugin_name: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        获取插件配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键名，None 表示获取所有配置
            default: 默认值，当配置不存在时返回
        
        Returns:
            配置值
        """
        # 加载插件配置
        if plugin_name not in self.configs:
            self.load_plugin_config(plugin_name)
        
        # 获取配置
        plugin_config = self.configs.get(plugin_name, {})
        
        if key is None:
            return plugin_config
        
        return plugin_config.get(key, default)
    
    def set_config(self, plugin_name: str, key: str, value: Any) -> bool:
        """
        设置插件配置
        
        Args:
            plugin_name: 插件名称
            key: 配置键名
            value: 配置值
        
        Returns:
            是否设置成功
        """
        try:
            # 加载插件配置
            if plugin_name not in self.configs:
                self.load_plugin_config(plugin_name)
            
            # 设置配置
            if plugin_name not in self.configs:
                self.configs[plugin_name] = {}
            
            self.configs[plugin_name][key] = value
            
            # 保存配置
            self.save_plugin_config(plugin_name)
            
            logger.info(f"设置插件 {plugin_name} 配置: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"设置插件 {plugin_name} 配置失败: {e}")
            return False
    
    def load_plugin_config(self, plugin_name: str):
        """
        加载插件配置
        
        Args:
            plugin_name: 插件名称
        """
        try:
            # 构建配置文件路径
            config_file = os.path.join(self.config_dir, f"{plugin_name}.json")
            
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.configs[plugin_name] = config
                    logger.info(f"加载插件 {plugin_name} 配置成功")
            else:
                # 使用默认配置
                if plugin_name in self.configs:
                    logger.info(f"插件 {plugin_name} 配置文件不存在，使用默认配置")
                else:
                    self.configs[plugin_name] = {}
                    logger.info(f"插件 {plugin_name} 无默认配置，使用空配置")
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 配置失败: {e}")
            self.configs[plugin_name] = {}
    
    def save_plugin_config(self, plugin_name: str):
        """
        保存插件配置
        
        Args:
            plugin_name: 插件名称
        """
        try:
            # 构建配置文件路径
            config_file = os.path.join(self.config_dir, f"{plugin_name}.json")
            
            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.configs.get(plugin_name, {}), f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存插件 {plugin_name} 配置成功")
        except Exception as e:
            logger.error(f"保存插件 {plugin_name} 配置失败: {e}")
    
    def reload_config(self, plugin_name: str):
        """
        重新加载插件配置
        
        Args:
            plugin_name: 插件名称
        """
        self.load_plugin_config(plugin_name)
        logger.info(f"重新加载插件 {plugin_name} 配置成功")
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有配置
        
        Returns:
            所有配置
        """
        return self.configs


# 创建配置管理器实例
config_manager = ConfigManager()