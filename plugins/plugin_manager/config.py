from pydantic import BaseModel


class Config(BaseModel):
    """插件管理器配置"""
    # 插件自动加载开关
    plugin_auto_load: bool = True
    
    # 插件目录
    plugins_dir: str = "plugins"
    
    # 禁用的插件列表
    disabled_plugins: list[str] = []