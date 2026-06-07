"""
Dough 系统 — Bean 基类、元类、作用域
零 import 设计：定义 Dough 子类时自动从 muffin_flour 注入已注册的装饰器
"""

import asyncio
import inspect
import sys
from abc import ABC, ABCMeta
from enum import Enum


class Scope(Enum):
    """Bean 作用域"""
    SINGLETON = "singleton"  # 全局唯一（默认）
    PROTOTYPE = "prototype"  # 每次创建新实例
    LAZY = "lazy"           # 首次使用时创建


# 已注入过的模块，避免重复
_injected_modules: set[int] = set()


def _inject_into_module(module):
    """从 muffin 注册表注入已注册的装饰器和类到模块命名空间"""
    module_id = id(module)
    if module_id in _injected_modules:
        return
    _injected_modules.add(module_id)

    from pancake.oven.muffin import muffin_flour, muffin_water
    for name, obj in muffin_flour.items():
        if name not in module.__dict__:
            module.__dict__[name] = obj
    for name, obj in muffin_water.items():
        if name not in module.__dict__:
            module.__dict__[name] = obj


class DoughMeta(ABCMeta):
    """元类：自动注册类到全局注册表，并从 muffin_flour 注入装饰器

    跳过名为 "Dough" 的类（基类自身）
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Dough":
            from pancake.registry import register_class
            register_class(name, cls)
            # 从 muffin_flour 注入已注册的装饰器到定义该类的模块
            module = sys.modules.get(namespace.get("__module__", ""))
            if module is not None:
                _inject_into_module(module)
        return cls


class Dough(ABC, metaclass=DoughMeta):
    """Bean 基类 — 所有框架类型的基础

    生命周期:
        1. __init__()     — 构造
        2. on_init()      — @PostConstruct, 属性注入后
        3. on_start()     — 就绪，开始服务
        4. [使用中]
        5. on_stop()      — 停止服务
        6. on_destroy()   — @PreDestroy, 销毁前

    生命周期方法支持同步和异步实现：
        - 子类可以覆盖为 async def 或普通 def
        - DoughFactory 会自动检测并正确调用
    """

    _scope: Scope = Scope.SINGLETON
    _lazy: bool = False
    _name: str = ""

    def __init__(self):
        pass

    async def on_init(self):
        """@PostConstruct — 属性注入后调用"""
        pass

    async def on_start(self):
        """就绪 — 开始服务"""
        pass

    async def on_stop(self):
        """停止服务"""
        pass

    async def on_destroy(self):
        """@PreDestroy — 销毁前调用"""
        pass


async def _call_lifecycle(instance: object, method_name: str):
    """调用生命周期方法，自动处理 sync/async

    如果子类覆盖为同步方法，自动包装为 awaitable。
    """
    method = getattr(instance, method_name, None)
    if method is None:
        return
    if inspect.iscoroutinefunction(method):
        await method()
    else:
        method()
