# 插件系统文档

## 1. 插件系统结构

### 1.1 目录结构
```
plugins/
├── cmds/                # 命令插件
│   └── __init__.py
├── demo_plugin/         # 示例插件
│   ├── __init__.py
│   └── config.py
├── keyword/             # 关键词插件
│   ├── __init__.py
│   ├── config.json
│   ├── bqbao/           # 表情包资源
│   ├── containsKeywords/ # 包含匹配关键词配置
│   └── exactKeywords/   # 精确匹配关键词配置
├── note/                # 便签插件
│   └── __init__.py
├── orange/              # AI回复插件
│   └── __init__.py
├── plugin_manager/      # 插件管理器
│   ├── __init__.py
│   └── config.py
├── config_manager.py    # 配置管理器
├── error_handler.py     # 错误处理器
├── message_router.py    # 消息路由器
└── plugin_manager.py    # 插件管理核心
```

### 1.2 核心组件

| 组件 | 功能 | 路径 |
|------|------|------|
| 插件管理器 | 统一管理插件的加载、启用、禁用和重载 | plugins/plugin_manager.py |
| 消息路由器 | 统一路由消息到相应的处理器，避免重复处理 | plugins/message_router.py |
| 配置管理器 | 统一管理所有插件的配置 | plugins/config_manager.py |
| 错误处理器 | 统一处理所有插件的错误 | plugins/error_handler.py |

## 2. 插件开发指南

### 2.1 创建新插件

1. **创建插件目录**：在 `plugins` 目录下创建一个新的目录，例如 `my_plugin`
2. **创建 `__init__.py` 文件**：在插件目录中创建 `__init__.py` 文件
3. **添加插件元数据**：在 `__init__.py` 文件中添加插件元数据
4. **实现插件功能**：编写插件的核心功能

### 2.2 插件元数据示例

```python
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="my_plugin",
    description="我的插件描述",
    usage="#命令 示例",
    version="1.0.0",
    authors=["作者名称"]
)
```

### 2.3 注册消息处理器

```python
# 导入消息路由器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.message_router import message_router

# 注册消息处理器
async def my_message_handler(bot: Bot, event: MessageEvent) -> bool:
    """消息处理器"""
    # 处理逻辑
    return True

# 注册处理器，设置优先级
message_router.register_handler(my_message_handler, priority=50)
```

### 2.4 使用配置管理器

```python
# 导入配置管理器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.config_manager import config_manager

# 获取配置
api_key = config_manager.get_config("my_plugin", "api_key", "default_value")

# 设置配置
config_manager.set_config("my_plugin", "api_key", "new_value")
```

### 2.5 使用错误处理器

```python
# 导入错误处理器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugins.error_handler import error_handler, error_handler_decorator

# 使用装饰器
@error_handler_decorator
async def my_handler(bot: Bot, event: MessageEvent):
    """带错误处理的处理器"""
    # 处理逻辑

# 手动处理错误
try:
    # 可能出错的代码
except Exception as e:
    await error_handler.handle_error(e, bot, event)
```

## 3. 插件管理命令

### 3.1 查看插件列表
```
#插件管理 列表
```

### 3.2 启用插件
```
#插件管理 启用 <插件名>
```

### 3.3 禁用插件
```
#插件管理 禁用 <插件名>
```

### 3.4 重载插件
```
#插件管理 重载 <插件名>
```

### 3.5 查看插件信息
```
#插件管理 信息 <插件名>
```

## 4. 现有插件功能

### 4.1 命令插件 (cmds)
- `#状态` - 查看机器人状态
- `#关于` - 查看机器人关于信息
- `#退出` - 退出机器人
- `#设置` - 查看机器人设置

### 4.2 关键词插件 (keyword)
- 关键词回复功能
- 支持精确匹配和包含匹配
- 支持正则表达式
- 支持冷却时间设置
- `#kw on/off` - 启用/禁用关键词回复
- `#kw rm <关键词>` - 删除关键词
- `#关键词添加包含（关键词），（回复内容）` - 添加包含匹配关键词
- `#关键词添加确切（关键词），（回复内容）` - 添加精确匹配关键词

### 4.3 AI回复插件 (orange)
- 基于火山引擎ARK API的AI回复功能
- 支持@机器人或使用`oi`前缀触发
- 支持图片理解
- `#gpt <内容>` - 调用AI回复
- `#chat <内容>` - 简化版聊天

### 4.4 便签插件 (note)
- 快速创建博客便签
- 支持文本和图片
- `#新建便签 <内容>` - 创建新便签
- `#便签 撤回` - 撤回上一条便签
- `#便签 预览` - 预览所有便签

## 5. 性能优化建议

### 5.1 插件开发建议
1. **使用消息路由器**：通过消息路由器注册处理器，避免重复处理消息
2. **合理设置优先级**：根据插件功能设置合理的优先级
3. **使用配置管理器**：统一使用配置管理器管理配置
4. **使用错误处理器**：统一使用错误处理器处理错误
5. **避免阻塞操作**：使用异步操作，避免阻塞事件循环

### 5.2 性能监控
- 使用 `#状态` 命令查看机器人的运行状态
- 查看日志文件，监控插件的执行情况
- 定期检查内存和CPU使用情况

## 6. 故障排查

### 6.1 插件加载失败
1. 检查插件目录是否存在
2. 检查 `__init__.py` 文件是否存在
3. 检查插件代码是否有语法错误
4. 查看日志文件，了解具体错误信息

### 6.2 消息不响应
1. 检查插件是否已启用
2. 检查消息触发条件是否满足
3. 检查插件代码是否有逻辑错误
4. 查看日志文件，了解具体错误信息

### 6.3 配置不生效
1. 检查配置文件是否存在
2. 检查配置格式是否正确
3. 尝试重载插件，使配置生效
4. 查看日志文件，了解具体错误信息

## 7. 版本历史

### v1.0.0 (2026-01-13)
- 重构插件系统结构
- 添加插件管理器
- 添加消息路由器
- 添加配置管理器
- 添加错误处理器
- 优化消息处理机制
- 完善插件文档