# Pancake Framework

> 一个装饰器驱动的 Python Web 框架，集成 IoC、MyBatis 风格 ORM 和 AI 工作流。

[English](./README.md)

## 特性

- **装饰器驱动** - 用简单装饰器注册服务、控制器和 Mapper
- **自动依赖注入** - `@auto_inject()` 自动从 YAML/JSON 配置解析参数
- **MyBatis Plus ORM** - 异步 ORM，内置 `BaseMapper` CRUD、`@Select`/`@Insert` SQL 注解、动态 SQL（`<if>`、`<foreach>`、`<where>`）
- **FastAPI Web 服务** - 内置 `@get_controller`/`@post_controller` 装饰器
- **IoC 容器** - 支持单例、瞬态和作用域的依赖管理
- **LangGraph 集成** - AI 工作流节点、边和状态图
- **消息队列** - 内存 `SimpleBroker` 和 `RedisBroker` 事件驱动架构
- **生命周期管理** - 服务的 `on_init`、`on_start`、`on_stop` 钩子
- **插件系统** - 从目录或环境变量配置的路径加载外部插件
- **YAML 配置** - 嵌套 YAML 支持 `${占位符}` 解析，扁平化 key 访问

## 快速开始

### 环境要求

- Python 3.13+
- Poetry（如未安装会自动安装）

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd framework

# 安装依赖
poetry install

# 运行
poetry run python main.py
```

服务默认启动在 `http://127.0.0.1:8080`。

### 项目结构

```
framework/
├── main.py                  # 入口文件
├── pyproject.toml           # 依赖配置
├── framework/               # 框架核心
│   ├── __init__.py          # 引导和初始化
│   ├── run.py               # 启动流水线
│   ├── oven/                # 全局注册表 (pancake_*, muffin_*)
│   ├── ovenware/            # 内置插件
│   │   ├── base.py          # @Service 装饰器
│   │   ├── auto_inject.py   # @auto_inject 装饰器
│   │   ├── web.py           # FastAPI Web 服务
│   │   ├── embed.py         # builtins 注入
│   │   ├── mybatis/         # ORM 模块
│   │   └── langgraph/       # AI 工作流模块
│   ├── build/               # 插件加载和构建流水线
│   ├── initialize/          # 环境和结构检查
│   ├── resource/            # 配置加载器（YAML、JSON、日志）
│   └── tool/                # 工具类（ProgressBar）
└── src/                     # 用户代码
    ├── resource/
    │   ├── yaml/            # YAML 配置文件
    │   ├── json/            # JSON 配置文件
    │   └── db/              # SQLite 数据库
    ├── mapper/              # 数据访问层
    ├── controller.py        # Web 控制器
    └── demo_*.py            # 功能演示
```

## 使用方法

### Web 控制器

```python
@get_controller("/hello")
def hello():
    return {"message": "Hello from Pancake!"}

@post_controller("/users")
async def create_user(name: str, age: int, email: str):
    return {"id": await UserMapper().insert(name=name, age=age, email=email)}
```

### MyBatis Plus ORM

```python
@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        age: int = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...
```

内置 CRUD 方法：`select_by_id`、`select_list`、`select_one`、`select_count`、`insert`、`insert_batch`、`update_by_id`、`delete_by_id`。

链式查询：

```python
from ovenware.mybatis.wrapper import qw, uw

# 查询
users = await mapper.select(qw().ge("age", 18).like("name", "%Ali%").orderByDesc("age").limit(50))

# 更新
await mapper.update(uw().set("name", "Bob").eq("id", 1))

# 删除
await mapper.delete(qw().lt("age", 18))
```

### 自动依赖注入

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

# 参数自动从 YAML 配置解析 (service.title -> service_title)
get_config()  # {"title": "Pancake Web Service", "port": 8080}
```

### IoC 容器

```python
container.register(UserService, UserService, Scope.SINGLETON)
service = container.resolve(UserService)
```

### 事件驱动消息

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}

@on_event("order.created")
async def notify_inventory(message):
    print(f"收到订单: {message}")
```

### 生命周期钩子

```python
class MyService(Lifecycle):
    async def on_init(self):
        self.cache = {}

    async def on_start(self):
        await self.load_data()

    async def on_stop(self):
        await self.cleanup()
```

### YAML 配置

在 `src/resource/yaml/` 目录下创建 YAML 文件：

```yaml
service:
  title: "我的应用"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 3000

mybatis:
  database:
    url: "sqlite:///resource/db/app.db"
```

使用扁平化 key 访问：`service.title`、`mybatis.database.url`。支持 `${占位符}` 引用。

### 禁用插件

在任意 YAML 文件中配置：

```yaml
framework:
  disable_dlc:
    - langgraph
    - external_plugin
```

## 配置项

| 配置键 | 说明 | 默认值 |
|--------|------|--------|
| `service.title` | 应用名称 | - |
| `service.version` | 应用版本 | - |
| `service.host` | 绑定地址 | `127.0.0.1` |
| `service.port` | 绑定端口 | `8080` |
| `mybatis.database.url` | 数据库连接 URL | `sqlite:///resource/db/app.db` |
| `mybatis.database.min_size` | 连接池最小值 | `1` |
| `mybatis.database.max_size` | 连接池最大值 | `5` |
| `framework.disable_dlc` | 禁用的插件列表 | `[]` |
| `LOG_FILE` | 日志文件路径（环境变量） | `framework.log` |
| `EXTERNAL_PLUGIN_DIRS` | 外部插件路径（环境变量） | - |
| `PANCAKE_AUTO_INSTALL` | 自动安装依赖（环境变量） | - |

## 运行测试

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 可选依赖

核心依赖已包含在默认安装中。如需额外功能，可通过 extras 安装：

```bash
pip install framework[langgraph]   # LangGraph AI 工作流
pip install framework[grpc]        # gRPC 远程调用
pip install framework[redis]       # Redis 消息队列
pip install framework[all]         # 全部可选依赖
```

## 开源协议

MIT
