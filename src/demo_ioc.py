"""
IoC 和消息队列演示
通过 main.py 启动自动加载
"""


# IoC 容器演示
class DemoService:
    """示例服务"""
    async def get_data(self):
        return {"message": "Hello from IoC!"}


# 注册到 IoC 容器
container.register(DemoService, DemoService, Scope.SINGLETON)


# 消息队列演示
@event_node(name="demo_event", event="demo.completed")
async def demo_event_handler(data: str = "default"):
    """事件节点演示"""
    result = {"input": data, "processed": True}
    return result


# 事件监听
@on_event("demo.completed")
async def on_demo_complete(message):
    """监听 demo.completed 事件"""
    print(f"收到事件: {message}")
