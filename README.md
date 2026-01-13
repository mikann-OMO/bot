# NoneBot QQ 机器人 - 基于 NapCat 的实现

## 🌟 简介

这是一个基于 [NoneBot2](https://github.com/nonebot/nonebot2) 和 [OneBot V11](https://github.com/howmanybots/onebot) 协议的 QQ 机器人项目，使用 [NapCatQQ](https://github.com/NapNeko/NapCatQQ) 作为协议端。

该机器人采用插件化架构，支持命令系统、关键词回复等功能，可以轻松扩展以满足各种需求。

### 特性

- 🧩 **插件化架构**: 模块化的插件系统，易于扩展和维护
- ⚡ **高性能**: 基于 Python 异步编程模型
- 📦 **内置插件**: 包含命令系统、关键词回复等实用功能
- 🛠️ **易配置**: 使用环境变量和配置文件进行灵活配置
- 🎯 **命令系统**: 支持多种命令前缀（/, !, #）
- 🔑 **权限管理**: 完善的超级用户权限控制

## 🚀 快速开始

### 环境要求

- Python >= 3.10
- NapCatQQ 服务端（用于连接 QQ）
- [NapCatQQ 部署文档](https://www.napcat.wiki/)

### 安装步骤

1. 克隆项目：
```bash
git clone <仓库地址>
cd Bmikan-bot/bot
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
编辑 `.env` 文件，设置必要的配置项：
```dotenv
# NoneBot 配置
DRIVER=~fastapi
ADAPTERS=~onebot.v11
SUPERUSERS=["3352604554"]
COMMAND_START=["/", "!", "#"]
COMMAND_SEP=[" "]

# OneBot V11 适配器配置
ONEBOT_V11_WS_URLS=["ws://127.0.0.1:3001"]
ONEBOT_V11_ACCESS_TOKEN=""
```

4. 启动机器人：
```bash
python bot.py
```

## 🧩 插件系统

机器人支持多种内置插件，以下是主要插件：

| 插件名称 | 功能描述 |
|---------|----------|
| cmds | 核心命令系统（帮助、状态、插件管理等） |
| keyword | 关键词回复插件 |
| 更多插件 | 可自行扩展 |

### 核心命令

- `#帮助`: 查看帮助信息
- `#状态`: 查看机器人运行状态
- `#插件`: 查看已加载的插件
- `#设置`: 超级用户设置（仅超级用户可用）

## ⚙️ 配置说明

### 环境变量配置 (.env)

主要配置项说明：

- `SUPERUSERS`: 超级用户 QQ 号列表
- `COMMAND_START`: 命令前缀列表
- `COMMAND_SEP`: 命令分隔符列表
- `ONEBOT_V11_WS_URLS`: OneBot WebSocket 连接地址
- `ONEBOT_V11_ACCESS_TOKEN`: 访问令牌（可选）

### 插件配置

各插件的配置可以在对应插件目录下找到，例如：
- `plugins/keyword/`: 关键词插件配置

## 📁 项目结构

```
bot/
├── plugins/              # 插件目录
│   ├── cmds.py          # 核心命令插件
│   ├── keyword/         # 关键词回复插件
│   └── ...              # 其他插件
├── bot.py               # 机器人入口文件
├── .env                 # 环境变量配置
├── pyproject.toml       # Python 项目配置
├── requirements.txt     # 依赖列表
└── README.md            # 项目文档
```

## 🛠️ 开发指南

### 编写新插件

NoneBot2 提供了简单的插件开发接口，示例：

```python
from nonebot import on_command, CommandSession
from nonebot.permission import SUPERUSER

@on_command('example', permission=SUPERUSER)
async def _(session: CommandSession):
    await session.send('这是一个示例命令')
```

### 运行开发环境

```bash
python bot.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目！

## 📄 许可证

本项目采用 MIT 许可证，详情请见 LICENSE 文件。

## 🙏 致谢

- 感谢 [NoneBot2](https://github.com/nonebot/nonebot2) 提供的机器人框架
- 感谢 [NapCatQQ](https://github.com/NapNeko/NapCatQQ) 提供的 QQ 协议支持
- 感谢 [OneBot V11](https://github.com/howmanybots/onebot) 提供的统一协议标准

---

Made with ❤️