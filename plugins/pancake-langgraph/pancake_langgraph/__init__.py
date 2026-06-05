"""
Pancake LangGraph Plugin — LangGraph 工作流集成
提供 AI 工作流节点和边的注册功能。
"""

import logging

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

from .core import langgraph_node, langgraph_edge

logger = logging.getLogger(__name__)


class Main(InitAction):
    """LangGraph 插件主类"""

    name = "langgraph"
    version = "0.1.0"
    description = "LangGraph 工作流：节点、边、状态图"
    init_order = 90
    build_order = 90
    _dependencies = ["langgraph"]
    _extras = "langgraph"

    def __init__(self):
        pass

    def check(self) -> bool:
        return check_dependencies(["langgraph"], "langgraph")

    def build(self):
        """注册 LangGraph 装饰器到 muffin_flour"""
        oven.muffin_flour["langgraph_node"] = langgraph_node
        oven.muffin_flour["langgraph_edge"] = langgraph_edge
        logger.info("LangGraph 模块构建完成")

    async def startup(self):
        pass

    async def shutdown(self):
        pass


__all__ = [
    "langgraph_node", "langgraph_edge",
]
