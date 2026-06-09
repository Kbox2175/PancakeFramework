"""Bean 方法装饰器 — @maker, @maker_name, @no_maker"""

from pancake.registry import export


@export
def maker(func_or_name=None):
    """@maker / @maker("name") — 标记方法返回值为 Bean，配合 @inject 使用"""
    if isinstance(func_or_name, str):
        name = func_or_name
        def decorator(func):
            func._is_maker = True
            func._maker_name = name
            return func
        return decorator
    func = func_or_name
    func._is_maker = True
    return func


@export
def maker_name(func_or_name=None):
    """@maker_name / @maker_name("name") — 标记方法返回值为 Bean，配合 @inject_name 使用"""
    if isinstance(func_or_name, str):
        name = func_or_name
        def decorator(func):
            func._is_maker = True
            func._maker_name = name
            func._inject_by_name = True
            return func
        return decorator
    func = func_or_name
    func._is_maker = True
    func._inject_by_name = True
    return func


@export
def no_maker(func):
    """@no_maker — 排除方法，不自动注册"""
    func._no_maker = True
    return func
