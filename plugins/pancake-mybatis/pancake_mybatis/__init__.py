"""
Pancake MyBatis Plugin — MyBatis Plus ORM 集成
提供 BaseMapper CRUD、链式查询、分页、动态 SQL 等功能。
"""

import logging
from dataclasses import dataclass

from pancake import oven
from pancake.ovenware import InitAction

from .mapper import (
    Mapper, BaseMapper, Select, SelectOne, Insert, Update, Delete,
    get_registered_mappers, Page, PageResult,
)
from .wrapper import QueryWrapper, UpdateWrapper, ColumnRef, qw, uw, entity_columns
from .connection import init_database, close_database, get_database
from .config import load_config

logger = logging.getLogger(__name__)


class Main(InitAction):
    """MyBatis 插件主类"""

    name = "mybatis"
    version = "0.1.0"
    description = "MyBatis Plus ORM: BaseMapper CRUD、链式查询、分页、动态 SQL"
    init_order = 1
    build_order = 1
    _dependencies = ["databases", "aiosqlite"]
    _extras = "mybatis"

    def __init__(self):
        self.config = load_config()

    def check(self) -> bool:
        from pancake import oven
        url = oven.pancake_yaml.get("mybatis.database.url")
        if url is None:
            logger.warning("未配置 mybatis.database.url，使用默认 SQLite")
        return True

    def build(self):
        """注册装饰器到 muffin_flour"""
        # 装饰器定义在子模块中，需手动注册到 muffin_flour
        oven.muffin_flour["Mapper"] = Mapper
        oven.muffin_flour["BaseMapper"] = BaseMapper
        oven.muffin_flour["Select"] = Select
        oven.muffin_flour["SelectOne"] = SelectOne
        oven.muffin_flour["Insert"] = Insert
        oven.muffin_flour["Update"] = Update
        oven.muffin_flour["Delete"] = Delete
        oven.muffin_flour["dataclass"] = dataclass
        oven.muffin_flour["qw"] = qw
        oven.muffin_flour["uw"] = uw
        oven.muffin_flour["UpdateWrapper"] = UpdateWrapper
        oven.muffin_flour["QueryWrapper"] = QueryWrapper
        oven.muffin_flour["ColumnRef"] = ColumnRef
        oven.muffin_flour["entity_columns"] = entity_columns
        oven.muffin_flour["Page"] = Page
        oven.muffin_flour["PageResult"] = PageResult

        logger.info("MyBatis Plus 模块构建完成")

    async def startup(self):
        await init_database(
            url=self.config["url"],
            min_size=self.config.get("min_size", 1),
            max_size=self.config.get("max_size", 5),
        )

    async def shutdown(self):
        await close_database()


__all__ = [
    "Mapper", "BaseMapper", "Select", "SelectOne", "Insert", "Update", "Delete",
    "QueryWrapper", "UpdateWrapper", "ColumnRef", "qw", "uw", "entity_columns",
    "get_database", "init_database", "close_database",
    "Page", "PageResult",
]
