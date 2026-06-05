"""
Pancake GUI Plugin — Flet GUI 框架集成
提供 GUI 页面注册和管理功能。
"""

import logging

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

from .gui import gui_page, gui_action

logger = logging.getLogger(__name__)


class Main(InitAction):
    """GUI 插件主类"""

    name = "gui"
    version = "0.1.0"
    description = "Flet GUI 框架：页面注册、动作处理"
    init_order = 70
    build_order = 70
    _dependencies = ["flet"]
    _extras = "gui"

    def __init__(self):
        pass

    def check(self) -> bool:
        return check_dependencies(["flet"], "gui")

    def build(self):
        """注册 GUI 装饰器到 muffin_flour"""
        oven.muffin_flour["gui_page"] = gui_page
        oven.muffin_flour["gui_action"] = gui_action
        logger.info("GUI 模块构建完成")

    def loop_method(self):
        """运行 GUI 应用"""
        import flet as ft
        from .gui import _run_gui
        _run_gui()

    async def startup(self):
        pass

    async def shutdown(self):
        pass


__all__ = [
    "gui_page", "gui_action",
]
