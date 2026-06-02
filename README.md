# Pancake Framework

> A decorator-driven Python web framework with IoC, MyBatis-style ORM, and AI workflow integration.

[中文文档](./README_CN.md)

## Features

- **Decorator-Driven** - Register services, controllers, and mappers with simple decorators
- **Auto Dependency Injection** - `@auto_inject()` automatically resolves parameters from YAML/JSON config
- **MyBatis Plus ORM** - Async ORM with `BaseMapper` CRUD, `@Select`/`@Insert` SQL annotations, dynamic SQL (`<if>`, `<foreach>`, `<where>`)
- **FastAPI Web Server** - Built-in `@get_controller`/`@post_controller` decorators
- **IoC Container** - Singleton, transient, and scoped dependency management
- **LangGraph Integration** - AI workflow nodes, edges, and state graphs
- **Message Queue** - In-memory `SimpleBroker` and `RedisBroker` for event-driven architecture
- **Lifecycle Management** - `on_init`, `on_start`, `on_stop` hooks for services
- **Plugin System** - Load external plugins from directories or environment-configured paths
- **YAML Config** - Nested YAML with `${placeholder}` resolution, flat key access

## Quick Start

### Prerequisites

- Python 3.13+
- Poetry (auto-installed if missing)

### Installation

```bash
# Clone the project
git clone <repo-url>
cd framework

# Install dependencies
poetry install

# Run
poetry run python main.py
```

The server starts at `http://127.0.0.1:8080` by default.

### Project Structure

```
framework/
├── main.py                  # Entry point
├── pyproject.toml           # Dependencies
├── framework/               # Framework core
│   ├── __init__.py          # Bootstrap & initialization
│   ├── run.py               # Startup pipeline
│   ├── oven/                # Global registries (pancake_*, muffin_*)
│   ├── ovenware/            # Built-in plugins
│   │   ├── base.py          # @Service decorator
│   │   ├── auto_inject.py   # @auto_inject decorator
│   │   ├── web.py           # FastAPI web server
│   │   ├── embed.py         # Builtins injection
│   │   ├── mybatis/         # ORM module
│   │   └── langgraph/       # AI workflow module
│   ├── build/               # Plugin loading & build pipeline
│   ├── initialize/          # Environment & structure checks
│   ├── resource/            # Config loaders (YAML, JSON, logging)
│   └── tool/                # Utilities (ProgressBar)
└── src/                     # User code
    ├── resource/
    │   ├── yaml/            # YAML config files
    │   ├── json/            # JSON config files
    │   └── db/              # SQLite database
    ├── mapper/              # Data access layer
    ├── controller.py        # Web controllers
    └── demo_*.py            # Feature demos
```

## Usage

### Web Controller

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

Built-in CRUD methods: `select_by_id`, `select_list`, `select_one`, `select_count`, `insert`, `insert_batch`, `update_by_id`, `delete_by_id`.

Chain queries:

```python
from ovenware.mybatis.wrapper import qw, uw

# Query
users = await mapper.select(qw().ge("age", 18).like("name", "%Ali%").orderByDesc("age").limit(50))

# Update
await mapper.update(uw().set("name", "Bob").eq("id", 1))

# Delete
await mapper.delete(qw().lt("age", 18))
```

### Auto Dependency Injection

```python
@auto_inject()
def get_config(service_title: str, service_port: int):
    return {"title": service_title, "port": service_port}

# Parameters auto-resolved from YAML config (service.title -> service_title)
get_config()  # {"title": "Pancake Web Service", "port": 8080}
```

### IoC Container

```python
container.register(UserService, UserService, Scope.SINGLETON)
service = container.resolve(UserService)
```

### Event-Driven Messaging

```python
@event_node(name="order_created", event="order.created")
async def create_order(item: str, qty: int):
    return {"item": item, "qty": qty, "status": "created"}

@on_event("order.created")
async def notify_inventory(message):
    print(f"Order received: {message}")
```

### Lifecycle Hooks

```python
class MyService(Lifecycle):
    async def on_init(self):
        self.cache = {}

    async def on_start(self):
        await self.load_data()

    async def on_stop(self):
        await self.cleanup()
```

### YAML Config

Create YAML files in `src/resource/yaml/`:

```yaml
service:
  title: "My App"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 3000

mybatis:
  database:
    url: "sqlite:///resource/db/app.db"
```

Access as flat keys: `service.title`, `mybatis.database.url`. Supports `${placeholder}` references.

### Disable Plugins

In any YAML file:

```yaml
framework:
  disable_dlc:
    - langgraph
    - external_plugin
```

## Configuration

| Config Key | Description | Default |
|-----------|-------------|---------|
| `service.title` | App name | - |
| `service.version` | App version | - |
| `service.host` | Bind host | `127.0.0.1` |
| `service.port` | Bind port | `8080` |
| `mybatis.database.url` | Database URL | `sqlite:///resource/db/app.db` |
| `mybatis.database.min_size` | Connection pool min | `1` |
| `mybatis.database.max_size` | Connection pool max | `5` |
| `framework.disable_dlc` | Disabled plugins | `[]` |
| `LOG_FILE` | Log file path (env var) | `framework.log` |
| `EXTERNAL_PLUGIN_DIRS` | External plugin paths (env var) | - |
| `PANCAKE_AUTO_INSTALL` | Auto-install deps (env var) | - |

## Running Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## License

MIT
