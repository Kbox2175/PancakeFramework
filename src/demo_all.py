"""
所有组件融合测试
MyBatis + Web + 消息队列 + 生命周期 + auto_inject
"""


# ============================================================
# 1. 定义数据模型和 Mapper
# ============================================================

@Mapper
class ProductMapper(BaseMapper):
    @dataclass
    class Product:
        id: int = None
        name: str = None
        price: float = None
        stock: int = None

    _entity_class = Product
    _table_name = "products"

    @Select("SELECT * FROM products WHERE price >= #{min_price}")
    async def find_by_price(self, min_price: float) -> list[Product]: ...


# ============================================================
# 2. 生命周期管理的服务
# ============================================================

class InventoryService(Lifecycle):
    """库存服务 - 带生命周期管理"""

    async def on_init(self):
        self.cache = {}

    async def check_stock(self, product_id: int):
        if product_id in self.cache:
            return self.cache[product_id]
        result = {"product_id": product_id, "available": True}
        self.cache[product_id] = result
        return result

    async def process(self, state=None):
        return {"cache_size": len(self.cache)}


# ============================================================
# 3. 消息队列事件处理
# ============================================================

@event_node(name="product_created", event="product.created")
async def on_product_created(name: str = "", price: float = 0):
    """商品创建事件节点"""
    return {"name": name, "price": price, "status": "created"}


@on_event("product.created")
async def notify_stock_service(message):
    """监听商品创建事件，更新库存"""
    print(f"[事件] 商品已创建: {message}")


# ============================================================
# 4. Web 控制器（融合所有组件）
# ============================================================

@get_controller("/products")
async def get_products():
    """获取所有商品 - MyBatis"""
    mapper = ProductMapper()
    products = await mapper.select_list()
    return [{"id": p.id, "name": p.name, "price": p.price, "stock": p.stock} for p in products]


@post_controller("/products")
async def create_product(name: str, price: float, stock: int):
    """创建商品 - MyBatis + 事件驱动"""
    mapper = ProductMapper()
    product_id = await mapper.insert(name=name, price=price, stock=stock)
    await on_product_created(name=name, price=price)
    return {"id": product_id, "message": "商品已创建"}


@get_controller("/products/price")
async def get_by_price(min_price: float = 0):
    """按价格筛选 - MyBatis"""
    mapper = ProductMapper()
    products = await mapper.find_by_price(min_price)
    return [{"id": p.id, "name": p.name, "price": p.price} for p in products]


@get_controller("/inventory/{product_id}")
async def check_inventory(product_id: int):
    """检查库存 - 生命周期服务"""
    svc = InventoryService()
    await svc.on_init()
    result = await svc.check_stock(product_id)
    return result


@get_controller("/system/info")
async def system_info():
    """系统信息 - auto_inject + 生命周期"""
    mapper = ProductMapper()
    products = await mapper.select_list()

    inventory_svc = InventoryService()
    await inventory_svc.on_init()
    inv_result = await inventory_svc.process()

    return {
        "service_title": service_title,
        "service_version": service_version,
        "product_count": len(products),
        "inventory_cache": inv_result["cache_size"],
    }
