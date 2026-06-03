"""
控制器装饰器模块
提供 HTTP 方法控制器、页面控制器、参数校验
"""

import asyncio
import functools
import inspect
import logging
from pathlib import Path
from typing import Any, Callable

from fastapi import Body, Request
from fastapi.responses import HTMLResponse

from pancake import oven

logger = logging.getLogger(__name__)

# HTTP 方法注册表 key 映射
_METHOD_REGISTRY_KEYS = {
    "GET": "GetController",
    "POST": "PostController",
    "PUT": "PutController",
    "DELETE": "DeleteController",
    "PATCH": "PatchController",
}

# 基础类型：不需要 Body 标注，FastAPI 自动当 query/path 参数
_PRIMITIVE_TYPES = {str, int, float, bool, type(None)}

# 已知的 FastAPI 参数类型，跳过不处理
_SKIP_PARAMS = {"request", "self", "current_user", "websocket"}

# 使用 body 的 HTTP 方法
_BODY_METHODS = {"POST", "PUT", "PATCH"}


def _extract_path_params(path: str) -> set[str]:
    """从路径模板中提取路径参数名，如 /students/{student_id} -> {'student_id'}"""
    import re
    return set(re.findall(r'\{(\w+)\}', path))


def _auto_annotate_body(func: Callable, method: str = "GET", path: str = "") -> Callable:
    """自动为参数添加 Body() 标注

    对于 POST/PUT/PATCH 请求：所有非路径参数自动从 body 读取。
    对于 GET/DELETE 请求：仅复杂类型添加 Body()。
    request 参数自动注入 Request 类型（用户无需 import）。
    """
    import re
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    modified = False
    path_params = set(re.findall(r'\{(\w+)\}', path)) if path else set()

    for i, param in enumerate(params):
        # request 参数自动注入 Request 类型（用户无需 import）
        if param.name == "request" and param.annotation is inspect.Parameter.empty:
            params[i] = param.replace(annotation=Request)
            modified = True
            continue

        # 跳过特殊参数
        if param.name in _SKIP_PARAMS:
            continue
        # 跳过路径参数
        if param.name in path_params:
            continue
        # 跳过 *args, **kwargs
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        # 跳过已有默认值且默认值是 Depends/Body 等的参数
        if param.default is not inspect.Parameter.empty:
            if hasattr(param.default, '__class__') and param.default.__class__.__name__ == 'Body':
                continue

        annotation = param.annotation

        # POST/PUT/PATCH：所有非路径参数都从 body 读取
        if method.upper() in _BODY_METHODS:
            params[i] = param.replace(default=Body(), annotation=annotation if annotation is not inspect.Parameter.empty else str)
            modified = True
            continue

        # GET/DELETE：仅复杂类型添加 Body()
        if annotation is inspect.Parameter.empty:
            continue
        origin = getattr(annotation, '__origin__', None)
        is_complex = False
        if origin in (list, dict, tuple, set, frozenset):
            is_complex = True
        elif origin is not None:
            is_complex = True
        elif annotation not in _PRIMITIVE_TYPES and not isinstance(annotation, type):
            is_complex = False
        elif annotation not in _PRIMITIVE_TYPES:
            is_complex = True

        if is_complex:
            params[i] = param.replace(default=Body(), annotation=annotation)
            modified = True

    if modified:
        func.__signature__ = sig.replace(parameters=params)
    return func


def _register_controller(method: str, path: str, name: str | None = None, tags: list[str] | None = None):
    """通用控制器注册内部方法"""
    registry_key = _METHOD_REGISTRY_KEYS[method]

    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough[registry_key][name] = func
        if tags:
            oven.pancake_other.setdefault("tags", {})[name] = tags
        logger.info(f"{registry_key} {name} 已加入库")
        return func
    return decorator


def get_controller(path: str, name: str = None, tags: list[str] = None) -> Callable:
    """GET 控制器装饰器"""
    return _register_controller("GET", path, name, tags)


def post_controller(path: str, name: str = None, tags: list[str] = None) -> Callable:
    """POST 控制器装饰器"""
    return _register_controller("POST", path, name, tags)


def put_controller(path: str, name: str = None, tags: list[str] = None) -> Callable:
    """PUT 控制器装饰器"""
    return _register_controller("PUT", path, name, tags)


def delete_controller(path: str, name: str = None, tags: list[str] = None) -> Callable:
    """DELETE 控制器装饰器"""
    return _register_controller("DELETE", path, name, tags)


def patch_controller(path: str, name: str = None, tags: list[str] = None) -> Callable:
    """PATCH 控制器装饰器"""
    return _register_controller("PATCH", path, name, tags)


def page_controller(path: str, template: str, name: str = None, tags: list[str] = None) -> Callable:
    """页面控制器装饰器 — 渲染 Jinja2 模板返回 HTML

    装饰的函数返回 dict，作为模板的 context 变量。

    用法:
        @page_controller("/home", template="home.html")
        async def home():
            return {"title": "首页", "message": "Hello"}

        @page_controller("/users", template="users.html")
        async def users_page():
            users = await UserMapper().select_list()
            return {"users": users}
    """
    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__
        oven.pancake_other["path"][name] = path
        oven.pancake_dough.setdefault("PageController", {})[name] = {
            "func": func,
            "template": template,
        }
        if tags:
            oven.pancake_other.setdefault("tags", {})[name] = tags
        logger.info(f"PageController {name} 已加入库: {path} -> {template}")
        return func
    return decorator


# ---- 兼容旧接口 ----

def post_auto_controller(path: str, name: str = None) -> Callable:
    """POST 自动填充参数控制器（向后兼容）"""
    return _register_controller("POST", path, name)


def get_auto_controller(path: str, name: str = None) -> Callable:
    """GET 自动填充参数控制器（向后兼容）"""
    return _register_controller("GET", path, name)


def validate(**validators: Callable):
    """参数校验装饰器 — 对控制器参数进行校验

    用法:
        @post_controller("/users")
        @validate(age=lambda v: 0 < v < 200, name=lambda v: len(v) > 0)
        async def create_user(name: str, age: int):
            ...
    """
    from fastapi import HTTPException

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for param_name, checker in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not checker(value):
                            raise HTTPException(
                                status_code=422,
                                detail=f"参数校验失败: {param_name}={value}"
                            )
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(
                            status_code=422,
                            detail=f"参数校验异常: {param_name} — {e}"
                        )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
