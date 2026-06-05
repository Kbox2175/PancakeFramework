"""
Pancake CUI Plugin — CLI 框架集成
提供命令分组、彩色输出、进度条、交互式输入等功能。
"""

import asyncio
import functools
import logging
from typing import Callable

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

logger = logging.getLogger(__name__)


# ============================================================
#  命令信息
# ============================================================

class _CommandInfo:
    """存储一个 CLI 命令的元信息"""

    def __init__(self, name: str, func: Callable, help: str = None, group: str = None):
        self.name = name
        self.func = func
        self.help = help or func.__doc__
        self.group = group
        self.params: list = []
        self.is_async = asyncio.iscoroutinefunction(func)


class _GroupInfo:
    """存储一个命令分组的元信息"""

    def __init__(self, name: str, cls: type, help: str = None):
        self.name = name
        self.cls = cls
        self.help = help or cls.__doc__


# ============================================================
#  装饰器
# ============================================================

def cui_command(name: str = None, help: str = None, group: str = None, **kwargs):
    """CLI 命令装饰器 — 注册一个子命令"""
    def decorator(func: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = func.__name__.replace("_", "-")

        info = _CommandInfo(name, func, help, group)

        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        info.params = func._cui_params

        registry = oven.pancake_dough.setdefault("CuiCommand", {})
        registry[name] = info
        logger.info(f"CUI 命令 {name} 已注册")

        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        wrapper._cui_info = info
        return wrapper
    return decorator


def cui_group(name: str = None, help: str = None):
    """CLI 命令分组装饰器 — 注册一个命令组"""
    def decorator(cls: type) -> type:
        nonlocal name
        if name is None:
            name = cls.__name__.replace("_", "-").lower()

        info = _GroupInfo(name, cls, help)
        oven.pancake_dough.setdefault("CuiGroup", {})[name] = info
        logger.info(f"CUI 分组 {name} 已注册")
        return cls
    return decorator


def cui_option(*param_decls, **kwargs):
    """CLI 选项装饰器 — 为命令添加 --option 参数"""
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Option(param_decls, **kwargs))
        return func
    return decorator


def cui_argument(*param_decls, **kwargs):
    """CLI 参数装饰器 — 为命令添加 positional argument"""
    import click

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_cui_params"):
            func._cui_params = []
        func._cui_params.append(click.Argument(param_decls, **kwargs))
        return func
    return decorator


# ============================================================
#  彩色输出工具
# ============================================================

def cui_print(text: str, fg: str = None, bold: bool = False, **kwargs):
    """彩色打印"""
    import click
    click.echo(click.style(text, fg=fg, bold=bold), **kwargs)


def cui_info(text: str):
    """信息输出（蓝色）"""
    import click
    click.echo(click.style(f"[INFO] {text}", fg="blue"))


def cui_success(text: str):
    """成功输出（绿色）"""
    import click
    click.echo(click.style(f"[OK] {text}", fg="green"))


def cui_warning(text: str):
    """警告输出（黄色）"""
    import click
    click.echo(click.style(f"[WARN] {text}", fg="yellow"))


def cui_error(text: str):
    """错误输出（红色）"""
    import click
    click.echo(click.style(f"[ERROR] {text}", fg="red"))


def cui_prompt(text: str, default=None, type=None, **kwargs):
    """交互式输入"""
    import click
    return click.prompt(text, default=default, type=type, **kwargs)


def cui_confirm(text: str, default: bool = False, **kwargs):
    """确认输入"""
    import click
    return click.confirm(text, default=default, **kwargs)


class cui_progress:
    """进度条上下文管理器"""

    def __init__(self, total: int, label: str = ""):
        import click
        self._bar = click.progressbar(length=total, label=label)

    def __enter__(self):
        self._bar.__enter__()
        return self

    def __exit__(self, *args):
        self._bar.__exit__(*args)

    def update(self, n: int = 1):
        self._bar.update(n)


# ============================================================
#  异步命令包装
# ============================================================

def _make_click_callback(info: _CommandInfo) -> Callable:
    """将注册的命令函数包装为 click 可调用的回调"""
    import click

    if info.is_async:
        @functools.wraps(info.func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(info.func(*args, **kwargs))
        return sync_wrapper
    else:
        return info.func


# ============================================================
#  插件 Main 类
# ============================================================

class Main(InitAction):
    """CUI 插件主类"""

    name = "cui"
    version = "0.1.0"
    description = "CLI 框架：命令分组、彩色输出、进度条、交互式输入"
    init_order = 50
    build_order = 50
    _dependencies = ["click"]
    _extras = "cui"

    def __init__(self):
        oven.pancake_dough.setdefault("CuiCommand", {})
        oven.pancake_dough.setdefault("CuiGroup", {})

        cui_config = oven.pancake_yaml.get("client.cui", {})
        if isinstance(cui_config, str):
            cui_config = {}
        self.app_name = cui_config.get("app_name",
                        oven.pancake_yaml.get("client.cui.app_name", "app"))
        self.version = cui_config.get("version",
                       oven.pancake_yaml.get("client.cui.version", "0.1.0"))

        self._active = self._is_active()

    def _is_active(self) -> bool:
        """检查 CUI 是否在 client.type 配置中启用"""
        client_type = oven.pancake_yaml.get("client.type", "web")
        if isinstance(client_type, list):
            return "cui" in client_type
        return client_type == "cui"

    def check(self) -> bool:
        return check_dependencies(["click"], "cui")

    def build(self):
        if not self._active:
            logger.info("CUI 客户端未启用，跳过构建")
            return

        import click

        self.cli = click.Group(
            name=self.app_name,
            help=f"{self.app_name} v{self.version}",
        )

        # 注册内置命令
        self._register_builtins()

        # 注册命令分组
        groups = oven.pancake_dough.get("CuiGroup", {})
        click_groups: dict[str, click.Group] = {}
        for group_name, group_info in groups.items():
            click_group = click.Group(name=group_name, help=group_info.help)
            click_groups[group_name] = click_group

        # 注册命令
        commands = oven.pancake_dough.get("CuiCommand", {})
        for cmd_name, info in commands.items():
            callback = _make_click_callback(info)
            cmd = click.Command(
                name=info.name,
                callback=callback,
                params=info.params,
                help=info.help,
            )

            # 添加到分组或主 CLI
            if info.group and info.group in click_groups:
                click_groups[info.group].add_command(cmd)
            else:
                self.cli.add_command(cmd)

        # 将分组添加到主 CLI
        for group_name, click_group in click_groups.items():
            self.cli.add_command(click_group)

        logger.info(f"CUI 插件构建完成 ({len(commands)} 个命令, {len(groups)} 个分组)")

    def _register_builtins(self):
        """注册内置命令"""
        import click

        @self.cli.command("version")
        def version_cmd():
            """显示应用版本"""
            click.echo(f"{self.app_name} v{self.version}")

        @self.cli.command("plugins")
        def plugins_cmd():
            """列出已加载插件"""
            factory = oven.pancake_other.get("plugin_factory")
            if factory:
                for info in factory.get_info():
                    status = "✅" if info else "❌"
                    click.echo(f"  {status} {info['name']} v{info.get('version', '?')} — {info.get('description', '')}")
            else:
                click.echo("  PluginFactory 未初始化")

    def loop_method(self):
        if not self._active:
            return

        import sys
        import click

        # 没有 CLI 子命令参数时不启动（web 模式下正常情况）
        if len(sys.argv) <= 1:
            logger.info("CUI 客户端已启用，无子命令参数，跳过")
            return

        logger.info(f"启动 CUI: {self.app_name}")
        try:
            self.cli(standalone_mode=False)
        except (click.exceptions.Exit, SystemExit, click.exceptions.NoArgsIsHelpError):
            pass

    async def startup(self):
        pass

    async def shutdown(self):
        pass


__all__ = [
    "cui_command", "cui_group", "cui_option", "cui_argument",
    "cui_print", "cui_info", "cui_success", "cui_warning", "cui_error",
    "cui_prompt", "cui_confirm", "cui_progress",
]
