"""
Pancake Remote Plugin — 远程调用集成
提供 HTTP 和 gRPC 远程调用功能。
"""

import logging

from pancake import oven
from pancake.ovenware import InitAction, check_dependencies

from .remote import remote_node, HttpRemote, GrpcRemote

logger = logging.getLogger(__name__)


class Main(InitAction):
    """Remote 插件主类"""

    name = "remote"
    version = "0.1.0"
    description = "远程调用：HTTP/gRPC 客户端、服务发现"
    init_order = 80
    build_order = 80
    _dependencies = ["aiohttp"]
    _extras = "remote"

    def __init__(self):
        pass

    def check(self) -> bool:
        return check_dependencies(["aiohttp"], "remote")

    def build(self):
        """注册远程调用装饰器到 muffin_flour"""
        oven.muffin_flour["remote_node"] = remote_node
        oven.muffin_flour["HttpRemote"] = HttpRemote
        oven.muffin_flour["GrpcRemote"] = GrpcRemote
        logger.info("远程调用模块构建完成")

    async def startup(self):
        pass

    async def shutdown(self):
        pass


__all__ = [
    "remote_node", "HttpRemote", "GrpcRemote",
]
