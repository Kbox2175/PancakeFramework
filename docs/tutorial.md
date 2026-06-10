# Pancake 框架教程

> 从零开始学习 Pancake 框架，涵盖核心概念、IoC 容器、ORM、Web 开发、AI 集成和全部插件。

---

## 目录

1. [快速开始](#1-快速开始)
2. [核心概念](#2-核心概念)
3. [IoC 容器](#3-ioc-容器)
4. [配置系统](#4-配置系统)
5. [插件系统](#5-插件系统)
6. [Embed 插件 — 零 import](#6-embed-插件--零-import)
7. [MyBatis 插件 — ORM](#7-mybatis-插件--orm)
8. [Web 插件 — Web 服务器](#8-web-插件--web-服务器)
9. [Web Template 插件 — 模板渲染](#9-web-template-插件--模板渲染)
10. [Web Security 插件 — 安全](#10-web-security-插件--安全)
11. [AI 插件 — 人工智能](#11-ai-插件--人工智能)
12. [Redis 插件 — 缓存](#12-redis-插件--缓存)
13. [消息队列](#13-消息队列)
14. [LangGraph 插件 — 工作流](#14-langgraph-插件--工作流)
15. [Remote 插件 — 远程调用](#15-remote-插件--远程调用)
16. [CUI 插件 — 命令行界面](#16-cui-插件--命令行界面)
17. [GUI 插件 — 桌面界面](#17-gui-插件--桌面界面)
18. [CLI 命令参考](#18-cli-命令参考)

---

## 1. 快速开始

### 1.1 安装

```bash
pip install pancake_framework
```

### 1.2 创建项目

```bash
pancake create myapp
cd myapp
```

生成的项目结构：

```
myapp/
├── main.py                  # 入口文件
├── pancake.xml              # 插件配置
├── pyproject.toml           # 项目元数据
└── src/
    ├── resource/
    │   ├── yaml/            # YAML 配置
    │   │   └── service.yaml
    │   └── json/            # JSON 配置
    ├── templates/           # HTML 模板
    └── mapper/              # Mapper 层
```

### 1.3 入口文件

```python
import pancake

if __name__ == "__main__":
    pancake.run()
```

### 1.4 运行

```bash
python main.py
```

### 1.5 启动流程

```
main.py → pancake.run()
  ├── init()                    # 环境检查、结构检查、加载 dotenv/logging
  └── run()
      ├── load_xml()            # 加载 pancake.xml → 插件列表 + 全局配置
      ├── load_config()         # 加载 YAML/JSON → settings
      ├── load_ovenware()       # 加载插件 (按 init_order 排序)
      ├── load_dish()           # 加载用户代码 src/
      ├── build()               # 创建 Bean → 拓扑排序 → on_init → on_start
      └── run_loop_methods()    # 运行 loop_method (如 Web 服务器)
```

---

## 2. 核心概念

### 2.1 Dough — Bean 基类

`Dough` 是所有框架类型的基类，类似于 Spring 的 `Object`。所有自定义 Bean 都应继承 `Dough` 或其子类。

```python
class MyBean(Dough):
    async def on_init(self):
        # 初始化后调用（@PostConstruct）
        pass

    async def on_start(self):
        # 就绪后调用
        pass

    async def on_stop(self):
        # 停止时调用
        pass

    async def on_destroy(self):
        # 销毁前调用（@PreDestroy）
        pass
```

### 2.2 生命周期

```
__init__()  →  on_init()  →  on_start()  →  [运行中]  →  on_stop()  →  on_destroy()
   构造        @PostConstruct    就绪                        停止         @PreDestroy
```

所有生命周期方法支持同步和异步实现，`DoughFactory` 会自动检测并正确调用。

### 2.3 作用域

```python
# 单例（默认）
@singleton
class MyService(Service):
    pass

# 多例 — 每次获取创建新实例
@prototype
class MyPrototype(Service):
    pass

# 懒加载 — 首次访问时创建
@lazy
class MyLazy(Service):
    pass
```

### 2.4 基类体系

| 基类 | 用途 | 示例 |
|------|------|------|
| `Service` | 服务类，方法集合 | `UserService`、`OrderService` |
| `Configuration` | 配置类，方法返回值自动注册为 Bean | `AppConfig`、`DatabaseConfig` |
| `Struct` | 数据结构（dataclass） | `User`、`OrderForm` |
| `Function` | 函数包装 | `FormatDate`、`ValidateEmail` |

---

## 3. IoC 容器

### 3.1 注册 Bean

Bean 通过以下方式注册到 IoC 容器：

1. **继承 Dough 子类** — `DoughMeta` 元类自动注册
2. **@service / @configuration** — 类型转换装饰器
3. **Configuration 方法返回值** — 自动注册
4. **手动注册** — `DoughFactory.get().register(cls)`

### 3.2 依赖注入

#### @inject — 按类型注入

```python
@singleton
class OrderService(Service):
    async def on_init(self):
        # 手动解析
        self.user_service = DoughFactory.get().resolve("UserService")

    @inject
    async def create_order(self, user: UserService):
        # 参数自动按类型注入
        return await user.get_user(1)
```

#### @inject 用于类 — 自动注入属性

```python
@singleton
@inject
class OrderService(Service):
    user_service: UserService  # 自动注入
    db: Database               # 自动注入

    async def on_init(self):
        # user_service 和 db 已经注入完成
        pass
```

#### @inject_name — 按名称注入

```python
@inject
async def my_func(primary_db = inject_name("primary_db")):
    # 按指定名称注入
    pass
```

### 3.3 @depends_on — 声明依赖

```python
@singleton
@depends_on("DatabaseService", "CacheService")
class UserService(Service):
    async def on_init(self):
        # DatabaseService 和 CacheService 已在此前创建
        self.db = DoughFactory.get().resolve("DatabaseService")
        self.cache = DoughFactory.get().resolve("CacheService")
```

`DoughFactory` 使用 Kahn 算法进行拓扑排序，确保依赖先于被依赖者创建。检测到循环依赖时会抛出 `ValueError`。

### 3.4 @import_class — 导入外部类

```python
@configuration
@import_class(ExternalServiceA, ExternalServiceB)
class AppConfig(Configuration):
    pass
# ExternalServiceA 和 ExternalServiceB 会被自动注册到工厂
```

### 3.5 Configuration — Bean 工厂

`Configuration` 类的非私有方法返回值自动注册为 Bean：

```python
@configuration
class AppConfig(Configuration):
    def cache_manager(self):
        """返回值自动注册为 Bean，名称为 'cache_manager'"""
        return CacheManager()

    def database(self):
        return Database("sqlite:///app.db")

    @maker("my_cache")  # 自定义 Bean 名称
    def create_cache(self):
        return RedisCache()

    @no_maker  # 排除，不注册为 Bean
    def helper(self):
        return "not a bean"
```

### 3.6 解析 Bean

```python
# 按名称解析
service = DoughFactory.get().resolve("UserService")

# 所有实例
instances = DoughFactory.get().get_all_instances()

# 所有注册的类
classes = DoughFactory.get().get_all_classes()
```

---

## 4. 配置系统

### 4.1 配置来源和优先级

```
pancake.xml <config>  →  YAML 文件  →  JSON 文件  →  默认值
         高优先级                                                    低优先级
```

### 4.2 pancake.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pancake>
    <config>
        <service.title>myapp</service.title>
        <service.port>8080</service.port>
        <mybatis.database.url>sqlite:///resource/db/app.db</mybatis.database.url>
    </config>
    <dependencies>
        <dependency>
            <groupId>io.pancake</groupId>
            <artifactId>embed</artifactId>
        </dependency>
    </dependencies>
</pancake>
```

支持 `${env:VAR_NAME}` 引用环境变量。

### 4.3 YAML 配置

在 `src/resource/yaml/` 下创建 `.yaml` 文件：

```yaml
# src/resource/yaml/service.yaml
service:
  title: myapp
  port: 8080

mybatis:
  database:
    url: sqlite:///resource/db/app.db
```

YAML 支持 `${key.path}` 占位符引用其他配置值。

### 4.4 JSON 配置

在 `src/resource/json/` 下创建 `.json` 文件，格式与 YAML 相同。

### 4.5 读取配置

```python
from pancake import settings

# 获取配置
title = settings.get("service.title")
port = settings.get("service.port", 8080)  # 带默认值

# 获取所有配置
all_config = settings.get_all()
service_config = settings.get_all("service.")  # 按前缀过滤

# 手动设置
settings.set("custom.key", "value")
```

### 4.6 @config — 从配置注入 Struct 字段

```python
@config
@struct
class DatabaseConfig:
    url: str = None
    min_size: int = None
    max_size: int = None
# 自动从 settings 读取 databaseconfig.url、databaseconfig.min_size 等
```

---

## 5. 插件系统

### 5.1 插件架构

Pancake 采用插件化架构。所有扩展功能（ORM、Web、AI 等）都通过插件提供。

插件的加载顺序由 `init_order` 控制（值小先加载）：

| 插件 | init_order | 说明 |
|------|-----------|------|
| mybatis | 1 | 数据库 ORM |
| ai | 4 | AI 模型 |
| redis | 2 | Redis 缓存 |
| web | 50 | Web 服务器 |
| web-template | 51 | 模板渲染 |
| web-security | 52 | 安全模块 |
| langgraph | 90 | 工作流 |
| remote | 80 | 远程调用 |
| cui | 50 | CLI 框架 |
| gui | 70 | GUI 框架 |
| embed | 999 | 零 import（最后加载） |

### 5.2 pancake.xml 声明插件

```xml
<dependencies>
    <dependency>
        <groupId>io.pancake</groupId>
        <artifactId>embed</artifactId>
    </dependency>
    <dependency>
        <groupId>io.pancake</groupId>
        <artifactId>mybatis</artifactId>
    </dependency>
    <dependency>
        <groupId>io.pancake</groupId>
        <artifactId>web</artifactId>
    </dependency>
    <!-- 第三方包 -->
    <dependency>
        <groupId>pypi</groupId>
        <artifactId>requests</artifactId>
    </dependency>
</dependencies>
```

### 5.3 自动安装

插件未安装时，框架会自动 `pip install`：

```
io.pancake + mybatis → pip install pancake_mybatis
io.pancake + web → pip install pancake_web
pypi + requests → pip install requests
```

### 5.4 禁用插件

```xml
<config>
    <framework.disable_dlc>["mybatis", "redis"]</framework.disable_dlc>
</config>
```

### 5.5 CLI 管理

```bash
pancake plugin list              # 列出已配置的插件
pancake plugin add mybatis       # 添加插件
pancake plugin remove mybatis    # 移除插件
pancake plugin clear             # 清空所有插件
```

---

## 6. Embed 插件 — 零 import

`pancake-embed` 是 Pancake 最重要的插件之一，它实现了"零 import"机制。

### 6.1 原理

Embed 插件在 `init_order=999`（最后）加载，将所有已注册的装饰器、类和服务注入 Python 的 `builtins` 模块。后续定义的 Dough 子类和注册的装饰器也会自动注入。

### 6.2 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>embed</artifactId>
</dependency>
```

### 6.3 效果

启用后，用户代码无需任何 import：

```python
# src/user_service.py — 无需 import

@singleton
class UserService(Service):
    async def find_user(self, user_id: int):
        return {"id": user_id, "name": "Alice"}

@configuration
class AppConfig(Configuration):
    def cache(self):
        return {}
```

### 6.4 注入的内容

Embed 会注入以下内容到 builtins：

- **flour** — 所有装饰器：`@singleton`、`@inject`、`@Mapper`、`@get`、`@post` 等
- **water** — 所有类：`DoughFactory`、`Scope`、`Configuration`、`Service` 等
- **egg** — 方法/构建器
- **sugar** — 其他 API
- **已注册的 Dough 子类** — 用户定义的 Bean 类

---

## 7. MyBatis 插件 — ORM

`pancake-mybatis` 提供 MyBatis Plus 风格的异步 ORM。

### 7.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>mybatis</artifactId>
</dependency>
```

### 7.2 配置

```yaml
# src/resource/yaml/mybatis.yaml
mybatis:
  database:
    url: sqlite:///resource/db/app.db
    min_size: 1
    max_size: 5
```

支持的数据库：
- SQLite: `sqlite:///resource/db/app.db`
- PostgreSQL: `postgresql://user:pass@host/db`
- MySQL: `mysql://user:pass@host/db`

### 7.3 定义 Mapper

```python
@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        email: str = None
        age: int = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users")
    async def find_all(self) -> list[User]: ...

    @Select("SELECT * FROM users WHERE id = #{id}")
    async def find_by_id(self, id: int) -> User: ...

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...

    @Insert("INSERT INTO users (name, email, age) VALUES (#{name}, #{email}, #{age})")
    async def insert_user(self, name: str, email: str, age: int) -> int: ...

    @Update("UPDATE users SET name = #{name} WHERE id = #{id}")
    async def update_name(self, id: int, name: str) -> int: ...

    @Delete("DELETE FROM users WHERE id = #{id}")
    async def delete_by_id(self, id: int) -> int: ...
```

### 7.4 内置 CRUD 方法

`BaseMapper` 提供内置方法，无需手写 SQL：

```python
@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None

    _entity_class = User
    _table_name = "users"

# 内置方法：
# insert(entity)        — 插入记录
# insert_batch(entities) — 批量插入
# update_by_id(entity)  — 按 ID 更新
# delete_by_id(id)      — 按 ID 删除
# select_by_id(id)      — 按 ID 查询
# select_list(wrapper)  — 条件查询
# select_one(wrapper)   — 查询单条
# select_count(wrapper) — 计数
# select_page(page, wrapper) — 分页查询
```

### 7.5 链式查询

```python
# QueryWrapper — 查询条件
users = await mapper.select_list(
    qw().eq("name", "Alice")
        .ge("age", 18)
        .order_by_desc("age")
        .limit(50)
)

# UpdateWrapper — 更新条件
await mapper.update(
    uw().set("name", "Bob")
        .eq("id", 1)
)

# 便捷函数
users = await mapper.select_list(qw().like("name", "A"))
count = await mapper.select_count(qw().gt("age", 20))
```

### 7.6 事务

```python
# @Transactional 装饰器
@Transactional
async def transfer_money(from_id: int, to_id: int, amount: int):
    await mapper.update(uw().set("balance", "balance - #{amount}").eq("id", from_id))
    await mapper.update(uw().set("balance", "balance + #{amount}").eq("id", to_id))

# 手动事务
async with begin_transaction() as tx:
    await mapper.insert_user("Alice", "alice@example.com", 25)
    await mapper.insert_user("Bob", "bob@example.com", 30)
    # 自动提交或回滚
```

### 7.7 分页

```python
from pancake_mybatis import Page

page = Page(page_num=1, page_size=10)
result = await mapper.select_page(page, qw().eq("status", "active"))
# result.records — 数据列表
# result.total   — 总记录数
# result.pages   — 总页数
```

### 7.8 自动建表

```python
@Table("users")
class User:
    @Column(primary_key=True, auto_increment=True)
    id: int = None

    @Column(nullable=False, length=50)
    name: str = None

    @Column(unique=True, length=100)
    email: str = None
```

---

## 8. Web 插件 — Web 服务器

`pancake-web` 提供 aiohttp 驱动的 Spring MVC 风格 Web 服务器。

### 8.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web</artifactId>
</dependency>
```

### 8.2 配置

```yaml
# src/resource/yaml/service.yaml
pancake:
  web:
    host: 127.0.0.1
    port: 8080
    debug: false
    static: src/static
    templates: src/templates
    cors:
      allow_origins: "*"
      allow_methods: "GET,POST,PUT,DELETE,OPTIONS"
    session:
      secret_key: your-secret-key
    request:
      timeout: 30
      max_body_size: 1048576  # 1MB
```

### 8.3 控制器

```python
@controller("/api/users")
class UserController:
    @get("/")
    async def list_users(self, request):
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    @get("/{id}")
    async def get_user(self, id: int = path_variable()):
        return {"id": id, "name": "Alice"}

    @post("/")
    async def create_user(self, body: dict = request_body()):
        return {"id": 3, **body}, 201

    @put("/{id}")
    async def update_user(self, id: int = path_variable(), body: dict = request_body()):
        return {"id": id, **body}

    @delete("/{id}")
    async def delete_user(self, id: int = path_variable()):
        return None  # 204 No Content
```

### 8.4 参数绑定

```python
# 路径变量
@get("/users/{id}")
async def get_user(self, id: int = path_variable()):
    return {"id": id}

# 查询参数
@get("/search")
async def search(self, keyword: str = request_param(), page: int = request_param(default=1)):
    return {"keyword": keyword, "page": page}

# 请求体
@post("/users")
async def create_user(self, body: UserForm = request_body()):
    return body

# request 对象
@get("/info")
async def info(self, request):
    return {"method": request.method, "path": request.path}
```

### 8.5 返回值自动转换

| 返回值类型 | 转换结果 |
|-----------|---------|
| `None` | 204 No Content |
| `web.Response` | 原样返回 |
| `(data, status)` | JsonResponse(data, status) |
| `dataclass/Struct` | JsonResponse(asdict(data)) |
| `dict/list` | JsonResponse |
| `str` | HtmlResponse |
| `int/float/bool` | JsonResponse |

### 8.6 中间件

```python
@middleware(order=0)
class LoggingMiddleware:
    async def process(self, request, handler):
        logger.info(f"{request.method} {request.path}")
        response = await handler(request)
        logger.info(f"Status: {response.status}")
        return response

@middleware(order=1)
async def timing_middleware(request, handler):
    import time
    start = time.time()
    response = await handler(request)
    duration = time.time() - start
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response
```

### 8.7 异常处理

```python
@exception_handler(ValueError)
async def handle_value_error(request, exc):
    return JsonResponse({"error": str(exc)}, status=400)

@exception_handler(PermissionError)
async def handle_permission_error(request, exc):
    return JsonResponse({"error": "Forbidden"}, status=403)
```

### 8.8 Controller 依赖注入

Controller 由 IoC 容器管理，支持 `@inject`：

```python
@controller("/api/orders")
@inject
class OrderController:
    order_service: OrderService  # 自动注入
    user_service: UserService    # 自动注入

    @get("/")
    async def list_orders(self, request):
        return await self.order_service.find_all()
```

---

## 9. Web Template 插件 — 模板渲染

`pancake-web-template` 提供 Jinja2 模板引擎集成。

### 9.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-template</artifactId>
</dependency>
```

### 9.2 使用 @template 装饰器

```python
@controller("/")
class HomeController:
    @get("/")
    @template("home.html")
    async def home(self, request):
        return {"title": "首页", "items": ["Python", "Pancake", "IoC"]}
```

模板文件 `src/templates/home.html`：

```html
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</body>
</html>
```

### 9.3 手动渲染

```python
@controller("/pages")
class PageController:
    @get("/about")
    async def about(self, request):
        return render("about.html", title="关于我们")
```

### 9.4 自定义过滤器

```python
register_filter("reverse", lambda s: s[::-1])
register_filter("upper", lambda s: s.upper())
```

模板中使用：

```html
{{ name | reverse }}
{{ name | upper }}
```

---

## 10. Web Security 插件 — 安全

`pancake-web-security` 提供 Spring Security 风格的认证和授权。

### 10.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>web-security</artifactId>
</dependency>
```

### 10.2 配置

```yaml
# src/resource/yaml/security.yaml
security:
  enabled: true
  auth_type: both          # form | jwt | both
  password_encoder: bcrypt # bcrypt | argon2 | plain
  bcrypt_rounds: 12
  memory_users:
    - username: admin
      password: admin123
      roles: [ADMIN]
    - username: user
      password: user123
      roles: [USER]
  jwt:
    secret: your-jwt-secret
    expire: 3600
    header: Authorization
    prefix: Bearer
```

### 10.3 认证

```python
# Form 登录
@controller("/auth")
class AuthController:
    @post("/login")
    async def login(self, body: dict = request_body()):
        auth = await auth_manager.authenticate(
            username=body["username"],
            password=body["password"]
        )
        return {"token": auth.token, "user": auth.principal.username}

    @get("/me")
    @has_role("USER")
    async def me(self, user: User = authenticated_user()):
        return {"username": user.username, "roles": user.roles}
```

### 10.4 授权装饰器

```python
@get("/admin/dashboard")
@has_role("ADMIN")
async def admin_dashboard(self, request):
    return {"message": "Admin Dashboard"}

@get("/users/delete")
@has_permission("user:delete")
async def delete_user(self, request):
    return {"message": "User deleted"}

@get("/protected")
@secured(roles=["ADMIN", "MODERATOR"], permissions=["access:protected"])
async def protected_resource(self, request):
    return {"message": "Protected"}
```

### 10.5 密码加密

```python
# 自动注入
password_encoder: PasswordEncoder

# 使用
hashed = password_encoder.encode("my_password")
is_valid = password_encoder.matches("my_password", hashed)
```

---

## 11. AI 插件 — 人工智能

`pancake-ai` 提供统一的 LLM 客户端、记忆管理和 RAG。

### 11.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>ai</artifactId>
</dependency>
```

### 11.2 配置

```yaml
# src/resource/yaml/ai.yaml
ai:
  default_model: deepseek
  providers:
    deepseek:
      type: openai
      base_url: https://api.deepseek.com
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      max_tokens: 4096
      temperature: 0.7
    openai:
      type: openai
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model: gpt-4o
    gemini:
      type: google
      api_key: ${GEMINI_API_KEY}
      model: gemini-2.0-flash
    ollama:
      type: ollama
      base_url: http://localhost:11434
      model: llama3
  memory:
    short_term:
      backend: memory      # memory | redis | mybatis
      max_messages: 20
      ttl: 86400
    long_term:
      backend: memory
      ttl: 0               # 0 = 永不过期
  rag:
    backend: pgvector       # pgvector | redis | mongodb
    chunk_size: 500
    chunk_overlap: 50
    top_k: 5
```

### 11.3 对话

```python
# 基本对话
response = await chat_model.chat([{"role": "user", "content": "你好"}])

# 指定模型
response = await chat_model.chat(
    [{"role": "user", "content": "解释量子力学"}],
    model="gemini"
)

# 流式输出
async for chunk in chat_model.chat_stream([{"role": "user", "content": "写一首诗"}]):
    print(chunk, end="")
```

### 11.4 短期记忆

```python
# 添加消息
short_term_memory.add("user", "我叫小明")
short_term_memory.add("assistant", "你好小明！")
short_term_memory.add("user", "我今年 25 岁")

# 获取消息列表（自动管理上下文窗口）
messages = short_term_memory.get_messages()
# [
#   {"role": "user", "content": "我叫小明"},
#   {"role": "assistant", "content": "你好小明！"},
#   {"role": "user", "content": "我今年 25 岁"},
# ]

# 清空记忆
short_term_memory.clear()
```

### 11.5 长期记忆

```python
# 存储
await long_term_memory.remember("user_name", "小明")
await long_term_memory.remember("user_age", 25)

# 读取
name = await long_term_memory.recall("user_name")  # "小明"

# 删除
await long_term_memory.forget("user_age")
```

### 11.6 RAG（检索增强生成）

```python
# 添加文档
await rag.add_document("Pancake 是一个装饰器驱动的 Python 框架")
await rag.add_document("Pancake 的核心是 Dough IoC 容器")
await rag.add_document("Pancake 支持 MyBatis Plus ORM")

# 问答
answer = await rag.ask("什么是 Pancake？")
# 自动检索相关文档，结合 LLM 生成回答
```

### 11.7 自定义 Provider

```python
from pancake_ai import BaseProvider, register_provider

class MyProvider(BaseProvider):
    async def chat(self, messages, **kwargs):
        # 自定义实现
        return "Hello from MyProvider"

    async def chat_stream(self, messages, **kwargs):
        yield "Hello "
        yield "from "
        yield "MyProvider"

register_provider("my_provider", MyProvider)
```

---

## 12. Redis 插件 — 缓存

`pancake-redis` 提供 Redis 缓存集成。

### 12.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>redis</artifactId>
</dependency>
```

### 12.2 配置

```yaml
redis:
  url: redis://localhost:6379
  db: 0
  password: null
  key_prefix: "pancake:"
  default_ttl: 3600
```

### 12.3 基本操作

```python
# 获取 Redis 客户端
client = redis_client

# 基础缓存
await client.set("user:1", {"name": "Alice", "age": 25}, ttl=3600)
user = await client.get("user:1")
await client.delete("user:1")

# Hash
await client.hset("user:1", "name", "Alice")
name = await client.hget("user:1", "name")
all_fields = await client.hgetall("user:1")

# List
await client.lpush("queue", "task1", "task2")
task = await client.rpop("queue")

# Set
await client.sadd("tags", "python", "pancake")
members = await client.smembers("tags")
```

### 12.4 @cached 装饰器

```python
@cached(ttl=300, key_prefix="user")
async def get_user(user_id: int):
    # 结果自动缓存 300 秒
    return await user_mapper.select_by_id(user_id)
```

### 12.5 CacheGuard — 防穿透/雪崩/击穿

```python
guard = CacheGuard(
    redis_client=redis_client,
    ttl=3600,
    null_ttl=60,           # 空值缓存时间（防穿透）
    lock_ttl=10,            # 分布式锁时间（防击穿）
    jitter_range=(0, 300),  # TTL 随机抖动范围（防雪崩）
)

# 使用
user = await guard.get_or_load(
    key="user:1",
    loader=lambda: user_mapper.select_by_id(1)
)
```

---

## 13. 消息队列

Pancake 内置消息队列模块，支持事件驱动架构。

### 13.1 @event_node — 事件节点

```python
@event_node(name="process_order", event="order_created")
async def process_order(order_id: int):
    # 处理订单
    result = {"order_id": order_id, "status": "processed"}
    return result
# 执行后自动发布 "order_created" 事件
```

### 13.2 @on_event — 事件监听

```python
@on_event("order_created")
async def send_notification(message: dict):
    # message 包含: source, result, data
    print(f"订单已创建: {message['result']}")
```

### 13.3 SimpleBroker — 内存消息队列

默认使用 `SimpleBroker`，基于内存的消息队列：

```python
broker = get_broker()
await broker.publish("user_registered", {"user_id": 1, "name": "Alice"})
await broker.subscribe("user_registered", lambda msg: print(msg))
```

### 13.4 RedisBroker — Redis 消息队列

分布式场景使用 `RedisBroker`：

```python
from pancake.ovenware.broker import RedisBroker, set_broker

set_broker(RedisBroker(url="redis://localhost:6379"))
```

---

## 14. LangGraph 插件 — 工作流

`pancake-langgraph` 提供 LangGraph 状态图工作流集成。

### 14.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>langgraph</artifactId>
</dependency>
```

### 14.2 定义节点

```python
@langgraph_node(name="analyze")
async def analyze_node(state):
    # 分析节点
    messages = state.get("messages", [])
    # ... 处理逻辑
    return {"messages": messages + ["分析完成"]}

@langgraph_node(name="decide")
async def decide_node(state):
    # 决策节点
    return {"next": "action_a"}  # 决定下一个节点
```

### 14.3 定义边

```python
@langgraph_edge(from_node="analyze", to_node="decide")
def analyze_to_decide(state):
    return True  # 条件函数

@langgraph_edge(from_node="decide", to_node="action_a", condition=lambda s: s.get("next") == "action_a")
def decide_to_action_a(state):
    return True
```

### 14.4 配置

```yaml
langgraph:
  enable_graph: true
  state_fields:
    messages: list
    context: dict
```

---

## 15. Remote 插件 — 远程调用

`pancake-remote` 提供 HTTP 和 gRPC 远程调用客户端。

### 15.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>remote</artifactId>
</dependency>
```

### 15.2 HTTP 远程调用

```python
# 创建客户端
api = HttpRemote(base_url="https://api.example.com", timeout=30)

# GET 请求
users = await api.call("/users", method="GET")

# POST 请求
result = await api.call("/users", method="POST", data={"name": "Alice"})

# 关闭连接
await api.close()
```

### 15.3 gRPC 远程调用

```python
grpc_client = GrpcRemote(host="localhost", port=50051)
result = await grpc_client.call("UserService", "GetUser", {"user_id": 1})
```

### 15.4 @remote_node 装饰器

```python
@remote_node(base_url="https://api.example.com")
async def fetch_user(user_id: int, remote: HttpRemote):
    return await remote.call(f"/users/{user_id}", method="GET")
```

---

## 16. CUI 插件 — 命令行界面

`pancake-cui` 提供 Click 驱动的 CLI 框架。

### 16.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>cui</artifactId>
</dependency>
```

### 16.2 配置

```yaml
client:
  type: cui
  cui:
    app_name: mycli
    version: 1.0.0
```

### 16.3 定义命令

```python
@cui_command()
@cui_option("--name", prompt="Your name", help="Your name")
def greet(name: str):
    """Greet someone"""
    cui_success(f"Hello, {name}!")

@cui_group()
class DatabaseCommands:
    """Database management commands"""

@cui_command(group="database")
@cui_option("--force", is_flag=True, help="Force reset")
def migrate(force: bool):
    """Run database migration"""
    if force:
        cui_warning("Force reset!")
    cui_info("Migration complete")
```

### 16.4 输出工具

```python
cui_info("Processing...")       # 蓝色 [INFO]
cui_success("Done!")            # 绿色 [OK]
cui_warning("Careful!")         # 黄色 [WARN]
cui_error("Failed!")            # 红色 [ERROR]
cui_print("Custom", fg="cyan")  # 自定义颜色

name = cui_prompt("Enter name")         # 交互输入
confirm = cui_confirm("Are you sure?")  # 确认输入

with cui_progress(100, "Downloading") as p:
    for i in range(100):
        p.update(1)
```

---

## 17. GUI 插件 — 桌面界面

`pancake-gui` 提供 Flet 驱动的桌面 GUI 框架。

### 17.1 启用

```xml
<dependency>
    <groupId>io.pancake</groupId>
    <artifactId>gui</artifactId>
</dependency>
```

### 17.2 定义页面

```python
@gui_page("/")
def home_page(page):
    """首页"""
    page.add(
        ft.Text("Welcome to Pancake GUI!", size=30),
        ft.ElevatedButton("Click Me", on_click=lambda _: gui_action("greet")),
    )

@gui_action
def greet():
    print("Hello from Pancake!")
```

---

## 18. CLI 命令参考

### 项目管理

| 命令 | 说明 |
|------|------|
| `pancake version` | 显示框架版本 |
| `pancake cover` | 显示 Pancake 封面 |
| `pancake init` | 在当前目录初始化项目 |
| `pancake create <name>` | 创建新项目 |
| `pancake run` | 运行项目 |
| `pancake check` | 检查项目结构和环境 |
| `pancake build` | 打包项目为 wheel |

### 插件管理

| 命令 | 说明 |
|------|------|
| `pancake plugin list` | 列出已配置的插件 |
| `pancake plugin add <name>` | 添加插件到 pancake.xml |
| `pancake plugin remove <name>` | 移除插件 |
| `pancake plugin clear` | 清空所有插件 |

### 配置管理

| 命令 | 说明 |
|------|------|
| `pancake config show` | 显示当前配置 |

### 其他

| 命令 | 说明 |
|------|------|
| `pancake audit` | 审核代码质量 |
| `pancake update` | 更新框架 |
| `pancake install` | 安装缺失依赖 |
