"""
Pancake AI Plugin — AI 模型集成
提供 ChatModel、ShortTermMemory、LongTermMemory、RAG 等功能。
"""

import logging

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

from .ai_model import ChatModel, ShortTermMemory, LongTermMemory, RAG

logger = logging.getLogger(__name__)


class Main(InitAction):
    """AI 插件主类"""

    name = "ai_model"
    version = "0.1.0"
    description = "AI 对话模型、短期/长期记忆、RAG 检索增强生成"
    init_order = 4
    build_order = 4
    _dependencies = ["openai"]
    _extras = "ai"

    def __init__(self):
        pass

    def check(self) -> bool:
        return check_dependencies(["openai"], "ai")

    def build(self):
        """注册 AI 相关装饰器和类"""
        oven.muffin_flour["ChatModel"] = ChatModel
        oven.muffin_flour["ShortTermMemory"] = ShortTermMemory
        oven.muffin_flour["LongTermMemory"] = LongTermMemory
        oven.muffin_flour["RAG"] = RAG
        logger.info("AI 模块构建完成")

    async def startup(self):
        pass

    async def shutdown(self):
        pass


__all__ = [
    "ChatModel", "ShortTermMemory", "LongTermMemory", "RAG",
]
