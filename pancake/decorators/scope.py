"""作用域装饰器 — @dough, @singleton, @prototype, @lazy"""

from pancake.dough import Scope
from pancake.registry import export


@export
def dough(cls):
    """@dough — 标记类为 Bean"""
    cls._scope = Scope.SINGLETON
    return cls


@export
def singleton(cls):
    """@singleton — 单例作用域"""
    cls._scope = Scope.SINGLETON
    return cls


@export
def prototype(cls):
    """@prototype — 每次获取创建新实例"""
    cls._scope = Scope.PROTOTYPE
    return cls


@export
def lazy(cls):
    """@lazy — 延迟初始化"""
    cls._scope = Scope.LAZY
    cls._lazy = True
    return cls
