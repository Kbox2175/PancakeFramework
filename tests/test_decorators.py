"""Decorators 测试"""

import pytest
from pancake.dough import Dough, Scope
from pancake.decorators import (
    depends_on, import_class, dough, singleton, prototype, lazy,
    maker, maker_name, no_maker, inject, inject_name, config,
)


class TestDependsOn:

    def test_depends_on_sets_attribute(self):
        @depends_on("ServiceA", "ServiceB")
        class MyService(Dough):
            def __init__(self):
                pass

        assert MyService._depends_on == ["ServiceA", "ServiceB"]

    def test_depends_on_empty(self):
        @depends_on()
        class EmptyDeps(Dough):
            def __init__(self):
                pass

        assert EmptyDeps._depends_on == []

    def test_depends_on_preserves_class(self):
        """装饰器不改变类本身"""
        @depends_on("X")
        class Original(Dough):
            def __init__(self):
                self.marker = 123

        assert Original().marker == 123
        assert Original.__name__ == "Original"


class TestImport:

    def test_import_sets_attribute(self):
        class External(Dough):
            def __init__(self):
                pass

        @import_class(External)
        class MyConfig(Dough):
            def __init__(self):
                pass

        assert MyConfig._imports == [External]

    def test_import_multiple_classes(self):
        class A(Dough):
            def __init__(self):
                pass

        class B(Dough):
            def __init__(self):
                pass

        @import_class(A, B)
        class MyConfig(Dough):
            def __init__(self):
                pass

        assert MyConfig._imports == [A, B]

    def test_import_preserves_class(self):
        """装饰器不改变类本身"""
        class External(Dough):
            def __init__(self):
                pass

        @import_class(External)
        class MyConfig(Dough):
            def __init__(self):
                self.val = 42

        assert MyConfig().val == 42
        assert MyConfig.__name__ == "MyConfig"


class TestClassDecorators:

    def test_dough_sets_scope(self):
        @dough
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.SINGLETON

    def test_singleton_decorator(self):
        @singleton
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.SINGLETON

    def test_prototype_decorator(self):
        @prototype
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.PROTOTYPE

    def test_lazy_decorator(self):
        @lazy
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._lazy is True
        assert MyBean._scope == Scope.LAZY

    def test_decorator_composition(self):
        @prototype
        @dough
        class MyBean(Dough):
            def __init__(self):
                pass
        assert MyBean._scope == Scope.PROTOTYPE


class TestMakerDecorator:

    def test_maker_marks_method(self):
        class MyConfig(Dough):
            def __init__(self):
                pass
            @maker
            def my_bean(self):
                return "bean"
        assert hasattr(MyConfig.my_bean, "_is_maker")
        assert MyConfig.my_bean._is_maker is True


class TestNoMakerDecorator:

    def test_no_maker_marks_method(self):
        class MyConfig(Dough):
            def __init__(self):
                pass
            @no_maker
            def helper(self):
                return "helper"
        assert hasattr(MyConfig.helper, "_no_maker")
        assert MyConfig.helper._no_maker is True


class TestInjectDecorator:

    def test_inject_sync_function(self):
        """@inject 正确包装同步函数"""
        @inject
        def hello(name: str = "world"):
            return f"hello {name}"
        result = hello()
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_inject_async_function(self):
        """@inject 正确包装异步函数"""
        @inject
        async def hello(name: str = "world"):
            return f"hello {name}"
        result = await hello()
        assert result == "hello world"

    def test_inject_preserves_async_flag(self):
        """@inject 保留 async 特性"""
        import inspect
        @inject
        async def async_func():
            pass
        assert inspect.iscoroutinefunction(async_func)

    def test_inject_preserves_sync_flag(self):
        """@inject 保留 sync 特性"""
        import inspect
        @inject
        def sync_func():
            pass
        assert not inspect.iscoroutinefunction(sync_func)


class TestMakerName:

    def test_maker_with_name(self):
        """@maker("name") 设置自定义 bean name"""
        @maker("custom")
        def my_bean():
            return "bean"
        assert my_bean._is_maker is True
        assert my_bean._maker_name == "custom"

    def test_maker_without_name(self):
        """@maker 不设置 _maker_name"""
        @maker
        def my_bean():
            return "bean"
        assert my_bean._is_maker is True
        assert not hasattr(my_bean, "_maker_name")

    def test_maker_name_decorator(self):
        """@maker_name 标记 _inject_by_name"""
        @maker_name("cache")
        def cache_bean():
            return "cache"
        assert cache_bean._is_maker is True
        assert cache_bean._maker_name == "cache"
        assert cache_bean._inject_by_name is True

    def test_maker_name_no_args(self):
        """@maker_name 无参使用"""
        @maker_name
        def cache_bean():
            return "cache"
        assert cache_bean._is_maker is True
        assert cache_bean._inject_by_name is True


class TestInjectName:

    def test_inject_name_as_default_value(self):
        """inject_name("name") 作为参数默认值"""
        from pancake.decorators import _InjectName
        result = inject_name("my_db")
        assert isinstance(result, _InjectName)
        assert result.name == "my_db"

    def test_inject_resolves_by_param_name(self):
        """@inject 无类型注解时按形参名解析"""
        from pancake.registry import register_instance

        class FakeService:
            pass

        register_instance("my_param", FakeService())

        @inject
        def use_service(my_param):
            return my_param

        result = use_service()
        assert isinstance(result, FakeService)

    def test_inject_resolves_by_inject_name(self):
        """@inject 参数默认值 inject_name("name") 按指定名解析"""
        from pancake.registry import register_instance

        class FakeDB:
            pass

        register_instance("primary_db", FakeDB())

        @inject
        def use_db(db=inject_name("primary_db")):
            return db

        result = use_db()
        assert isinstance(result, FakeDB)
