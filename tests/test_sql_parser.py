import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from ovenware.mybatis.sql_parser import parse_sql


def test_basic_param_binding():
    sql = "SELECT * FROM users WHERE id = #{id}"
    result, params = parse_sql(sql, {"id": 1})
    assert result == "SELECT * FROM users WHERE id = :id"
    assert params == {"id": 1}


def test_if_tag_true():
    sql = "SELECT * FROM users <if test=\"name\">WHERE name = #{name}</if>"
    result, params = parse_sql(sql, {"name": "Alice"})
    assert "WHERE name = :name" in result
    assert params["name"] == "Alice"


def test_if_tag_false():
    sql = "SELECT * FROM users <if test=\"name\">WHERE name = #{name}</if>"
    result, params = parse_sql(sql, {})
    assert "WHERE" not in result


def test_where_tag():
    sql = "SELECT * FROM users <where>AND id = #{id}</where>"
    result, params = parse_sql(sql, {"id": 1})
    assert result == "SELECT * FROM users WHERE id = :id"


def test_set_tag():
    sql = "UPDATE users <set>name = #{name},</set> WHERE id = #{id}"
    result, params = parse_sql(sql, {"name": "Bob", "id": 1})
    assert "SET name = :name" in result
    assert "WHERE id = :id" in result


def test_foreach():
    sql = 'SELECT * FROM users WHERE id IN <foreach collection="ids" item="id" open="(" close=")" separator=",">#{id}</foreach>'
    result, params = parse_sql(sql, {"ids": [1, 2, 3]})
    assert "IN (" in result
    assert ":__foreach_ids_0" in result


def test_choose_when():
    sql = 'SELECT * FROM users <choose><when test="name">WHERE name = #{name}</when><otherwise>WHERE 1=1</otherwise></choose>'
    result, _ = parse_sql(sql, {"name": "Alice"})
    assert "WHERE name = :name" in result

    result2, _ = parse_sql(sql, {})
    assert "WHERE 1=1" in result2


def test_multiple_params():
    sql = "SELECT * FROM users WHERE name = #{name} AND age > #{age}"
    result, params = parse_sql(sql, {"name": "Alice", "age": 18})
    assert ":name" in result
    assert ":age" in result
    assert params == {"name": "Alice", "age": 18}


def test_if_null_check():
    sql = '<if test="name != null">WHERE name = #{name}</if>'
    result, params = parse_sql(sql, {"name": "Alice"})
    assert "WHERE name = :name" in result

    result2, _ = parse_sql(sql, {})
    assert "WHERE" not in result2
