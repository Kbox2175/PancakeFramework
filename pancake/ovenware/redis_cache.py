"""
Redis 缓存插件
提供缓存操作、Hash/List/Set 数据结构、JSON 存储、装饰器缓存

配置项（YAML 或 XML）：
  redis.url: redis://localhost:6379
  redis.db: 0
  redis.password: null
  redis.key_prefix: "pancake:"
  redis.default_ttl: 3600

可选依赖：pip install pancake[redis]
"""

import asyncio
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional

from pancake import oven

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 客户端封装"""

    def __init__(self, url: str = "redis://localhost:6379", db: int = 0,
                 password: str = None, key_prefix: str = "pancake:",
                 default_ttl: int = 3600):
        self.url = url
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._redis = None

    async def _get_conn(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self.url, db=self.db, password=self.password,
                decode_responses=True
            )
        return self._redis

    def _key(self, key: str) -> str:
        """添加 key 前缀"""
        if key.startswith(self.key_prefix):
            return key
        return f"{self.key_prefix}{key}"

    async def close(self):
        if self._redis:
            await self._redis.close()
            self._redis = None

    # ============================================================
    #  基础缓存操作
    # ============================================================

    async def get(self, key: str) -> Optional[str]:
        """获取值"""
        conn = await self._get_conn()
        return await conn.get(self._key(key))

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置值，可选过期时间（秒）"""
        conn = await self._get_conn()
        k = self._key(key)
        if ttl is None:
            ttl = self.default_ttl
        if ttl and ttl > 0:
            await conn.set(k, value, ex=ttl)
        else:
            await conn.set(k, value)

    async def delete(self, *keys: str) -> int:
        """删除一个或多个 key"""
        conn = await self._get_conn()
        return await conn.delete(*[self._key(k) for k in keys])

    async def exists(self, key: str) -> bool:
        """检查 key 是否存在"""
        conn = await self._get_conn()
        return bool(await conn.exists(self._key(key)))

    async def ttl(self, key: str) -> int:
        """获取 key 剩余过期时间（秒），-1 永不过期，-2 不存在"""
        conn = await self._get_conn()
        return await conn.ttl(self._key(key))

    async def expire(self, key: str, seconds: int) -> bool:
        """设置 key 过期时间"""
        conn = await self._get_conn()
        return await conn.expire(self._key(key), seconds)

    async def incr(self, key: str, amount: int = 1) -> int:
        """自增"""
        conn = await self._get_conn()
        return await conn.incrby(self._key(key), amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """自减"""
        conn = await self._get_conn()
        return await conn.decrby(self._key(key), amount)

    async def keys(self, pattern: str = "*") -> list[str]:
        """按模式搜索 key"""
        conn = await self._get_conn()
        full_keys = await conn.keys(self._key(pattern))
        prefix_len = len(self.key_prefix)
        return [k[prefix_len:] for k in full_keys]

    async def clear_prefix(self, prefix: str) -> int:
        """删除指定前缀的所有 key"""
        keys = await self.keys(f"{prefix}*")
        if keys:
            return await self.delete(*keys)
        return 0

    # ============================================================
    #  JSON 存储
    # ============================================================

    async def get_json(self, key: str) -> Any:
        """获取 JSON 对象"""
        data = await self.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set_json(self, key: str, value: Any, ttl: int = None) -> None:
        """存储 JSON 对象"""
        await self.set(key, json.dumps(value, ensure_ascii=False), ttl)

    # ============================================================
    #  Hash 操作
    # ============================================================

    async def hget(self, key: str, field: str) -> Optional[str]:
        """获取 hash 字段值"""
        conn = await self._get_conn()
        return await conn.hget(self._key(key), field)

    async def hset(self, key: str, field: str = None, value: Any = None,
                   mapping: dict = None) -> int:
        """设置 hash 字段"""
        conn = await self._get_conn()
        if mapping:
            return await conn.hset(self._key(key), mapping=mapping)
        return await conn.hset(self._key(key), field, value)

    async def hdel(self, key: str, *fields: str) -> int:
        """删除 hash 字段"""
        conn = await self._get_conn()
        return await conn.hdel(self._key(key), *fields)

    async def hgetall(self, key: str) -> dict:
        """获取 hash 所有字段"""
        conn = await self._get_conn()
        return await conn.hgetall(self._key(key))

    async def hkeys(self, key: str) -> list[str]:
        """获取 hash 所有字段名"""
        conn = await self._get_conn()
        return await conn.hkeys(self._key(key))

    async def hvals(self, key: str) -> list[str]:
        """获取 hash 所有值"""
        conn = await self._get_conn()
        return await conn.hvals(self._key(key))

    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """hash 字段自增"""
        conn = await self._get_conn()
        return await conn.hincrby(self._key(key), field, amount)

    # ============================================================
    #  List 操作
    # ============================================================

    async def lpush(self, key: str, *values: Any) -> int:
        """左侧推入"""
        conn = await self._get_conn()
        return await conn.lpush(self._key(key), *values)

    async def rpush(self, key: str, *values: Any) -> int:
        """右侧推入"""
        conn = await self._get_conn()
        return await conn.rpush(self._key(key), *values)

    async def lpop(self, key: str) -> Optional[str]:
        """左侧弹出"""
        conn = await self._get_conn()
        return await conn.lpop(self._key(key))

    async def rpop(self, key: str) -> Optional[str]:
        """右侧弹出"""
        conn = await self._get_conn()
        return await conn.rpop(self._key(key))

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list[str]:
        """获取列表范围"""
        conn = await self._get_conn()
        return await conn.lrange(self._key(key), start, end)

    async def llen(self, key: str) -> int:
        """获取列表长度"""
        conn = await self._get_conn()
        return await conn.llen(self._key(key))

    # ============================================================
    #  Set 操作
    # ============================================================

    async def sadd(self, key: str, *values: Any) -> int:
        """添加集合成员"""
        conn = await self._get_conn()
        return await conn.sadd(self._key(key), *values)

    async def srem(self, key: str, *values: Any) -> int:
        """删除集合成员"""
        conn = await self._get_conn()
        return await conn.srem(self._key(key), *values)

    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        conn = await self._get_conn()
        return await conn.smembers(self._key(key))

    async def sismember(self, key: str, value: Any) -> bool:
        """检查是否是集合成员"""
        conn = await self._get_conn()
        return await conn.sismember(self._key(key), value)

    async def scard(self, key: str) -> int:
        """获取集合大小"""
        conn = await self._get_conn()
        return await conn.scard(self._key(key))

    # ============================================================
    #  分布式锁
    # ============================================================

    async def lock(self, name: str, timeout: int = 10, blocking: bool = True,
                   blocking_timeout: int = 10) -> Optional["RedisLock"]:
        """获取分布式锁"""
        conn = await self._get_conn()
        lock_key = self._key(f"lock:{name}")
        lock = RedisLock(conn, lock_key, timeout=timeout)

        if blocking:
            acquired = await lock.acquire(blocking_timeout=blocking_timeout)
            if acquired:
                return lock
            return None
        else:
            acquired = await lock.acquire(blocking_timeout=0)
            if acquired:
                return lock
            return None


class RedisLock:
    """分布式锁"""

    def __init__(self, conn, key: str, timeout: int = 10):
        self._conn = conn
        self._key = key
        self._timeout = timeout
        self._token = None

    async def acquire(self, blocking_timeout: int = 10) -> bool:
        import secrets
        self._token = secrets.token_hex(16)
        end_time = asyncio.get_event_loop().time() + blocking_timeout
        while True:
            if await self._conn.set(self._key, self._token, nx=True, ex=self._timeout):
                return True
            if asyncio.get_event_loop().time() >= end_time:
                return False
            await asyncio.sleep(0.05)

    async def release(self) -> None:
        if self._token:
            # Lua 脚本保证原子性
            lua = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self._conn.eval(lua, 1, self._key, self._token)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


# ============================================================
#  缓存装饰器
# ============================================================

def cached(key: str = None, ttl: int = None, prefix: str = "cache"):
    """
    缓存装饰器 — 自动缓存函数返回值

    使用方法：
        @cached(ttl=300)
        async def get_user(user_id: int):
            return await db.query(user_id)

        @cached(key="user:{user_id}", ttl=600)
        async def get_user_detail(user_id: int):
            return await db.query_detail(user_id)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            global _client
            if _client is None:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # 构建缓存 key
            if key:
                cache_key = key.format(**kwargs, **{str(i): v for i, v in enumerate(args)})
            else:
                func_name = func.__qualname__
                params = f"{args}:{kwargs}"
                param_hash = hashlib.md5(params.encode()).hexdigest()[:8]
                cache_key = f"{prefix}:{func_name}:{param_hash}"

            # 尝试从缓存获取
            cached_data = await _client.get_json(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_data

            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 写入缓存
            await _client.set_json(cache_key, result, ttl=ttl)
            logger.debug(f"缓存写入: {cache_key}")
            return result

        wrapper._cache_clear = lambda: _client.clear_prefix(prefix) if _client else None
        return wrapper
    return decorator


# ============================================================
#  全局客户端
# ============================================================

_client: Optional[RedisClient] = None


def get_client() -> Optional[RedisClient]:
    """获取全局 Redis 客户端"""
    return _client


def set_client(client: RedisClient) -> None:
    """设置全局 Redis 客户端"""
    global _client
    _client = client


# ============================================================
#  插件 Main 类
# ============================================================

class Main(InitAction):
    """Redis 插件主类"""

    init_order = 2  # 在 mybatis 之后，web 之前

    def __init__(self):
        global _client
        url = oven.pancake_yaml.get("redis.url", "redis://localhost:6379")
        db = oven.pancake_yaml.get("redis.db", 0)
        password = oven.pancake_yaml.get("redis.password")
        prefix = oven.pancake_yaml.get("redis.key_prefix", "pancake:")
        default_ttl = oven.pancake_yaml.get("redis.default_ttl", 3600)

        _client = RedisClient(
            url=url, db=db, password=password,
            key_prefix=prefix, default_ttl=default_ttl
        )

        oven.pancake_other["redis"] = _client

    @staticmethod
    def check():
        try:
            import redis  # noqa: F401
        except ImportError:
            logger.warning("redis 包未安装，请运行: pip install pancake[redis]")

    def build(self):
        logger.info(f"Redis 插件构建完成 (url={_client.url})")

    async def loop_method(self):
        """测试连接"""
        try:
            conn = await _client._get_conn()
            await conn.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}")


# 注册到 oven
oven.muffin_flour["cached"] = cached
oven.muffin_flour["RedisClient"] = RedisClient
oven.muffin_suger["redis_client"] = get_client
