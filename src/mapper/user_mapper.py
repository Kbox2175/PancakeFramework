@Mapper
class UserMapper(BaseMapper):
    @dataclass
    class User:
        id: int = None
        name: str = None
        age: int = None
        email: str = None

    _entity_class = User
    _table_name = "users"

    @Select("SELECT * FROM users WHERE name = #{name}")
    async def find_by_name(self, name: str) -> list[User]: ...

    @Select("SELECT * FROM users <where><if test=\"name\">AND name = #{name}</if><if test=\"age\">AND age = #{age}</if></where>")
    async def find_by_condition(self, name: str = None, age: int = None) -> list[User]: ...
