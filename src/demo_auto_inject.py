"""
auto_inject 测试
通过 main.py 启动自动加载
"""

# 测试 1: 直接使用 auto_inject 装饰器（非 web 场景）
@auto_inject()
def test_yaml_inject(service_title: str, service_port: int):
    """测试从 YAML 自动注入 str/int 类型"""
    return {"title": service_title, "port": service_port}


# 测试 2: 使用 Service 装饰器（内部使用 auto_inject）
@Service
class DemoAutoService:
    """自动注入测试服务"""

    def __init__(self, service_title: str, service_host: str):
        self.title = service_title
        self.host = service_host

    def get_info(self):
        return {"title": self.title, "host": self.host}


# 测试 3: 使用同名参数映射
@auto_inject("service_title", "service_host")
def test_same_name(service_title: str, service_host: str):
    """测试同名参数注入"""
    return {"title": service_title, "host": service_host}


# 测试 4: Controller 中使用自动注入（使用默认值避免 FastAPI 强制校验）
@get_controller("/auto/test")
@auto_inject()
async def auto_test_endpoint(service_title: str = "", service_version: str = ""):
    """测试自动注入到 controller"""
    return {"title": service_title, "version": service_version}


# 测试 5: 混合参数
@get_controller("/auto/mixed")
@auto_inject()
async def mixed_test(service_title: str = "", custom_param: str = "default"):
    """测试混合参数"""
    return {"title": service_title, "custom": custom_param}


# 测试 6: 直接调用测试（不通过 web）
@get_controller("/auto/demo")
async def auto_demo():
    """演示自动注入结果"""
    # 直接调用测试
    result1 = test_yaml_inject()
    result2 = test_same_name()
    service = DemoAutoService()
    result3 = service.get_info()

    return {
        "test_yaml_inject": result1,
        "test_same_name": result2,
        "service_info": result3,
    }
