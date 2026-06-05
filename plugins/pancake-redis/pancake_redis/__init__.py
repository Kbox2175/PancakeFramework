"""
Pancake Redis Plugin — Redis 缓存集成
提供缓存操作、Hash/List/Set 数据结构、JSON 存储、装饰器缓存。
"""

import logging

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

from .redis_cache import RedisClient, CacheGuard, cached

logger = logging.getLogger(__name__)


class Main(InitAction):
    """Redis 插件主类"""

    name = "redis"
    version = "0.1.0"
    description = "Redis 缓存、Session 后端、CacheGuard（防穿透/雪崩/击穿）"
    init_order = 2
    build_order = 2
    _dependencies = ["redis"]
    _extras = "redis"

    def __init__(self):
        from pancake import settings
        url = oven.pancake_yaml.get("redis.url", settings.get("redis.url"))
        db = int(oven.pancake_yaml.get("redis.db", settings.get("redis.db")))
        password = oven.pancake_yaml.get("redis.password")
        prefix = oven.pancake_yaml.get("redis.key_prefix", "pancake:")
        default_ttl = int(oven.pancake_yaml.get("redis.default_ttl", 3600))

        client = RedisClient(
            url=url, db=db, password=password,
            key_prefix=prefix, default_ttl=default_ttl
        )

        # 注册到 oven
        oven.muffin_sugar["redis_client"] = client
        oven.muffin_flour["cached"] = cached
        oven.muffin_flour["CacheGuard"] = CacheGuard

    def check(self) -> bool:
        return check_dependencies(["redis"], "redis")

    def build(self):
        logger.info("Redis 缓存模块构建完成")

    async def startup(self):
        client = oven.muffin_sugar.get("redis_client")
        if client:
            await client._get_conn()
            logger.info("Redis 连接已建立")

    async def shutdown(self):
        client = oven.muffin_sugar.get("redis_client")
        if client:
            await client.close()
            logger.info("Redis 连接已关闭")


__all__ = [
    "RedisClient", "CacheGuard", "cached",
]
