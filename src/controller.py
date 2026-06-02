def _u(u):
    """User -> dict"""
    return {"id": u.id, "name": u.name, "age": u.age, "email": u.email}


@get_controller("/hello")
def hello():
    return {"message": "Hello from Pancake!"}


@get_controller("/health")
def health():
    return {"status": "ok"}


@get_controller("/users")
async def get_users():
    return [_u(u) for u in await UserMapper().select_list()]


@get_controller("/users/search")
async def search_users(name: str = None, age: int = None):
    return [_u(u) for u in await UserMapper().find_by_condition(name=name, age=age)]


@get_controller("/users/chain")
async def chain_query(name: str = None, min_age: int = None):
    w = qw()
    if name: w.like("name", f"%{name}%")
    if min_age: w.ge("age", min_age)
    return [_u(u) for u in await UserMapper().select(w.orderByDesc("age").limit(50))]


@get_controller("/users/chain_count")
async def chain_count(min_age: int = 0):
    return {"count": await UserMapper().select_count(qw().ge("age", min_age))}


@get_controller("/users/chain_in")
async def chain_in(ids: str = "1,2,3"):
    return [_u(u) for u in await UserMapper().select(qw().in_("id", [int(x) for x in ids.split(",")]))]


@get_controller("/users/chain_between")
async def chain_between(min_age: int = 20, max_age: int = 30):
    return [_u(u) for u in await UserMapper().select(qw().between("age", min_age, max_age))]


@post_controller("/users")
async def create_user(name: str, age: int, email: str):
    return {"id": await UserMapper().insert(name=name, age=age, email=email)}


@post_controller("/users/chain_update")
async def chain_update(user_id: int, name: str = None, age: int = None):
    w = uw()
    if name: w.set("name", name)
    if age: w.set("age", age)
    return {"updated": await UserMapper().update(w.eq("id", user_id))}


@post_controller("/users/chain_delete")
async def chain_delete(user_id: int):
    return {"deleted": await UserMapper().delete(qw().eq("id", user_id))}


@get_controller("/users/{user_id}")
async def get_user(user_id: int):
    u = await UserMapper().select_by_id(user_id)
    return _u(u) if u else {"error": "User not found"}
