# Pancake Framework Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix security vulnerabilities, stability issues, and code quality problems in the Pancake Python framework.

**Architecture:** Targeted fixes across framework core modules - no structural rewrites. Each fix is isolated and independently testable.

**Tech Stack:** Python 3.13, pytest, pytest-asyncio

---

## File Map

| File | Changes |
|------|---------|
| `framework/ovenware/mybatis/mapper.py` | Add SQL identifier validation |
| `framework/ovenware/mybatis/wrapper.py` | Add column name validation |
| `framework/build/load_src.py` | Add builtins injection conflict detection |
| `framework/ovenware/embed.py` | Add builtins injection conflict detection |
| `framework/ovenware/auto_inject.py` | Use isinstance() instead of type() == |
| `framework/resource/yml.py` | Add circular reference detection |
| `framework/resource/yml.py` | Replace bare except with specific exceptions |
| `framework/build/load_dlc.py` | Fix __module__ prefix matching |
| `framework/build/load_dlc.py` | Improve error reporting |
| `framework/initialize/check_env.py` | Add non-interactive mode |
| `pyproject.toml` | Separate optional dependencies |
| `tests/conftest.py` | Test infrastructure |
| `tests/test_sql_parser.py` | SQL parser tests |
| `tests/test_yml.py` | YAML parser tests |
| `tests/test_mapper_security.py` | SQL injection prevention tests |

---

### Task 1: SQL Identifier Validation (P0 Security)

**Files:**
- Modify: `framework/ovenware/mybatis/mapper.py`
- Modify: `framework/ovenware/mybatis/wrapper.py`

- [ ] **Step 1: Add validation function to mapper.py**

Add at the top of `mapper.py`, after imports:

```python
import re

_IDENTIFIER_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def _validate_identifier(name: str, kind: str = "identifier") -> str:
    """Validate SQL identifier (table name, column name) to prevent injection."""
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL {kind}: {name!r}")
    return name
```

- [ ] **Step 2: Apply validation to table names in BaseMapper**

In every method of `BaseMapper` that uses `self._table_name` in f-strings, wrap it:
- `select_by_id`: `f"SELECT * FROM {_validate_identifier(self._table_name, 'table')} WHERE id = :id"`
- `select_list`: same pattern
- `select_one` (both versions): same pattern
- `select_count` (both versions): same pattern
- `insert`: same pattern
- `insert_batch`: same pattern
- `update_by_id`: same pattern
- `delete_by_id`: same pattern
- `delete_batch_by_ids`: same pattern
- `select`: same pattern (wrapper path and kwargs path)
- `update`: same pattern
- `delete`: same pattern (wrapper path and kwargs path)

- [ ] **Step 3: Apply validation to column names in _build_where_from_dict**

```python
def _build_where_from_dict(params: dict) -> tuple[str, dict]:
    conditions = []
    values = {}
    for key, val in params.items():
        if val is not None:
            _validate_identifier(key, "column")
            conditions.append(f"{key} = :{key}")
            values[key] = val
    where = " AND ".join(conditions)
    return (" WHERE " + where) if where else "", values
```

- [ ] **Step 4: Add validation to wrapper.py**

Add the same `_validate_identifier` function to `wrapper.py` (or import from mapper). Apply it in `_resolve_column`:

```python
def _resolve_column(column) -> str:
    if isinstance(column, str):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column):
            raise ValueError(f"Invalid column name: {column!r}")
        return column
    if hasattr(column, '_column_name'):
        return column._column_name
    raise TypeError(f"Expected str or ColumnRef, got {type(column)}")
```

Add `import re` at the top of wrapper.py.

- [ ] **Step 5: Commit**

```bash
git add framework/ovenware/mybatis/mapper.py framework/ovenware/mybatis/wrapper.py
git commit -m "fix(security): validate SQL identifiers to prevent injection"
```

---

### Task 2: Builtins Injection Conflict Detection (P0 Security)

**Files:**
- Modify: `framework/build/load_src.py`
- Modify: `framework/ovenware/embed.py`

- [ ] **Step 1: Add conflict detection to load_src.py**

In `safe_register()`, before the `builtins.__dict__[node.name] = ...` line:

```python
# In the loop that injects into builtins:
for node in definitions:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if node.name in _shared_globals:
            existing = builtins.__dict__.get(node.name)
            if existing is not None and existing is not _shared_globals.get(node.name):
                logger.warning(f"Builtins conflict: '{node.name}' already exists, overwriting")
            builtins.__dict__[node.name] = _shared_globals[node.name]
```

Add `import logging` and `logger = logging.getLogger(__name__)` at the top of load_src.py.

- [ ] **Step 2: Add conflict detection to embed.py**

In `embed.py`'s `build()` method, before each `__builtins__[key] = value` assignment, add a check:

```python
def _safe_set_builtin(key, value):
    """Set builtin with conflict warning."""
    if key in __builtins__ and __builtins__[key] is not value:
        logger.warning(f"Builtins conflict: '{key}' already exists, overwriting")
    __builtins__[key] = value
```

Replace all `__builtins__[key] = value` patterns with `_safe_set_builtin(key, value)`.

- [ ] **Step 3: Commit**

```bash
git add framework/build/load_src.py framework/ovenware/embed.py
git commit -m "fix(security): add builtins injection conflict detection"
```

---

### Task 3: auto_inject Type Checking (P1 Stability)

**Files:**
- Modify: `framework/ovenware/auto_inject.py`

- [ ] **Step 1: Replace type() != with isinstance()**

In `auto_inject.py`, change line 67:
```python
# Before:
if type(kwargs[param_item_]) != param_types[param_item_] and type(kwargs[param_item_]) is not None:
# After:
if not isinstance(kwargs[param_item_], param_types[param_item_]) and kwargs[param_item_] is not None:
```

Change line 79:
```python
# Before:
if type(arg) != param_type and type(arg) is not None:
# After:
if not isinstance(arg, param_type) and arg is not None:
```

- [ ] **Step 2: Commit**

```bash
git add framework/ovenware/auto_inject.py
git commit -m "fix: use isinstance() for type checking in auto_inject"
```

---

### Task 4: YAML Circular Reference Protection (P1 Stability)

**Files:**
- Modify: `framework/resource/yml.py`

- [ ] **Step 1: Add circular reference detection**

Replace the `resolve` function in `yaml_init()`:

```python
def resolve(obj, resolving=None):
    if resolving is None:
        resolving = set()
    if isinstance(obj, dict):
        return {k: resolve(v, resolving) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve(i, resolving) for i in obj]
    if isinstance(obj, str):
        for _ in range(10):  # max 10 iterations to prevent infinite loop
            match = pattern.search(obj)
            if not match:
                break
            key_path = match.group(1)
            if key_path in resolving:
                logger.warning(f"Circular reference detected: {key_path}")
                break
            resolving.add(key_path)
            keys = key_path.split('.')
            value = data
            try:
                for k in keys:
                    value = value[k]
            except (KeyError, TypeError):
                value = match.group(0)
            obj = obj.replace(match.group(0), str(value))
            resolving.discard(key_path)
        return obj
    return obj
```

Add `import logging` and `logger = logging.getLogger(__name__)` at the top if not already present.

- [ ] **Step 2: Replace bare except**

Change line 37:
```python
# Before:
except:
    value = match.group(0)
# After:
except (KeyError, TypeError):
    value = match.group(0)
```

- [ ] **Step 3: Commit**

```bash
git add framework/resource/yml.py
git commit -m "fix: add circular reference detection and fix bare except in yml.py"
```

---

### Task 5: Plugin Module Filtering (P2 Quality)

**Files:**
- Modify: `framework/build/load_dlc.py`

- [ ] **Step 1: Fix __module__ filtering**

In `load_dlc.py`, change line 33:
```python
# Before:
and member.__module__ == plugin.__name__
# After:
and (member.__module__ == plugin.__name__ or member.__module__.startswith(plugin.__name__ + "."))
```

- [ ] **Step 2: Improve error reporting in load_dlc.py**

In `run()`, around line 59:
```python
# Before:
except Exception as e:
    import sys
    sys.exit(1)
# After:
except Exception as e:
    logger.error(f"Plugin check failed for {plugin_name[0]}: {e}")
    import sys
    sys.exit(1)
```

- [ ] **Step 3: Commit**

```bash
git add framework/build/load_dlc.py
git commit -m "fix: improve plugin module filtering and error reporting"
```

---

### Task 6: Non-Interactive Environment Check (P2 Quality)

**Files:**
- Modify: `framework/initialize/check_env.py`

- [ ] **Step 1: Add non-interactive mode**

In `check_environment()`, replace the `input()` call:

```python
def check_environment():
    REQUIRED_LIBRARIES = ["python-dotenv", "pyyaml"]
    REQUIRED_MODULES = ["dotenv", "yaml"]
    if not find_module(REQUIRED_MODULES):
        # Check for non-interactive mode
        if os.getenv("PANCAKE_AUTO_INSTALL", "").lower() in ("1", "true", "yes"):
            auto_install = True
        elif not sys.stdin.isatty():
            logger.error("Missing required libraries and running in non-interactive mode. Set PANCAKE_AUTO_INSTALL=1 to auto-install.")
            sys.exit(1)
        else:
            auto_install = input("Missing required libraries. Auto-install? (y/n)").lower().startswith("y")

        if not auto_install:
            sys.exit(1)
        # ... rest of install logic
```

Add `import logging` and `logger = logging.getLogger(__name__)` at the top.

- [ ] **Step 2: Commit**

```bash
git add framework/initialize/check_env.py
git commit -m "fix: add non-interactive mode for environment check"
```

---

### Task 7: Optional Dependencies (P2 Quality)

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Separate optional dependencies**

```toml
[tool.poetry]
name = "framework"
version = "0.1.0"
description = "Pancake - Decorator-driven Python web framework"
authors = ["drayee <1473443474@qq.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.13"
requests = "^2.33.1"
fastapi = "^0.136.1"
uvicorn = "^0.46.0"
python-dotenv = "^1.2.2"
pyyaml = "^6.0.3"
peewee = "^4.0.5"
databases = "^0.9.0"
aiosqlite = "^0.22.1"

# Optional dependencies
langgraph = {version = "^1.1.10", optional = true}
websocket-client = {version = "^1.9.0", optional = true}
aiohttp = {version = "^3.9.0", optional = true}
grpcio = {version = "^1.60.0", optional = true}
redis = {version = "^5.0.0", optional = true}

[tool.poetry.extras]
langgraph = ["langgraph"]
websocket = ["websocket-client"]
http = ["aiohttp"]
grpc = ["grpcio"]
redis = ["redis"]
all = ["langgraph", "websocket-client", "aiohttp", "grpcio", "redis"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat: separate optional dependencies with extras"
```

---

### Task 8: Test Infrastructure + Core Tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_sql_parser.py`
- Create: `tests/test_yml.py`
- Create: `tests/test_mapper_security.py`

- [ ] **Step 1: Create test infrastructure**

`tests/__init__.py`: empty file

`tests/conftest.py`:
```python
import sys
import os

# Add framework to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))
```

- [ ] **Step 2: Write SQL parser tests**

`tests/test_sql_parser.py`:
```python
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
    assert result.endswith("WHERE id = :id")


def test_foreach():
    sql = "SELECT * FROM users WHERE id IN <foreach collection=\"ids\" item=\"id\" open=\"(\" close=\")\" separator=\",\">#{id}</foreach>"
    result, params = parse_sql(sql, {"ids": [1, 2, 3]})
    assert "IN (" in result
    assert ":__foreach_ids_0" in result


def test_choose_when():
    sql = "SELECT * FROM users <choose><when test=\"name\">WHERE name = #{name}</when><otherwise>WHERE 1=1</otherwise></choose>"
    result, _ = parse_sql(sql, {"name": "Alice"})
    assert "WHERE name = :name" in result

    result2, _ = parse_sql(sql, {})
    assert "WHERE 1=1" in result2
```

- [ ] **Step 3: Write YAML parser tests**

`tests/test_yml.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

import tempfile
import os


def test_yaml_basic_load():
    from resource.yml import yaml_init
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = os.path.join(tmpdir, "resource", "yaml")
        os.makedirs(yaml_dir)
        with open(os.path.join(yaml_dir, "test.yaml"), "w") as f:
            f.write("app:\n  name: test\n  version: 1.0\n")
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            data = yaml_init()
            assert data["app.name"] == "test"
            assert data["app.version"] == "1.0"
        finally:
            os.chdir(original_dir)


def test_yaml_placeholder_resolution():
    from resource.yml import yaml_init
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = os.path.join(tmpdir, "resource", "yaml")
        os.makedirs(yaml_dir)
        with open(os.path.join(yaml_dir, "test.yaml"), "w") as f:
            f.write("base:\n  name: app\nfull:\n  title: ${base.name} v1\n")
        original_dir = os.getcwd()
        os.chdir(tmpdir)
        try:
            data = yaml_init()
            assert data["full.title"] == "app v1"
        finally:
            os.chdir(original_dir)
```

- [ ] **Step 4: Write mapper security tests**

`tests/test_mapper_security.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

import pytest
from ovenware.mybatis.mapper import _validate_identifier


def test_valid_identifiers():
    assert _validate_identifier("users") == "users"
    assert _validate_identifier("user_table") == "user_table"
    assert _validate_identifier("_private") == "_private"
    assert _validate_identifier("Table123") == "Table123"


def test_sql_injection_rejected():
    with pytest.raises(ValueError):
        _validate_identifier("users; DROP TABLE users--")
    with pytest.raises(ValueError):
        _validate_identifier("users OR 1=1")
    with pytest.raises(ValueError):
        _validate_identifier("users`")
    with pytest.raises(ValueError):
        _validate_identifier("users\"")
    with pytest.raises(ValueError):
        _validate_identifier("")
```

- [ ] **Step 5: Run tests**

```bash
cd C:/Users/LENOVO/Desktop/framework && python -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add tests/
git commit -m "test: add core tests for sql_parser, yml, and mapper security"
```

---

### Task 9: Sync/Async Bridge Fix (P1 Stability)

**Files:**
- Modify: `framework/ovenware/mybatis/__init__.py`

- [ ] **Step 1: Fix the asyncio bridge in mybatis Main.build()**

```python
def build(self):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # We're inside an already-running loop (e.g., uvicorn)
        # Schedule as a task; it will complete before requests are served
        loop.create_task(self._init_db())
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        asyncio.run(self._init_db())
    logger.info("MyBatis Plus module built")
```

This is actually the current code. The real fix is to ensure the DB is initialized before the web server starts accepting requests. Change to:

```python
def build(self):
    import asyncio
    self._loop = asyncio.new_event_loop()
    self._loop.run_until_complete(self._init_db())
    logger.info("MyBatis Plus module built")

async def shutdown(self):
    await close_database()
```

- [ ] **Step 2: Commit**

```bash
git add framework/ovenware/mybatis/__init__.py
git commit -m "fix: use dedicated event loop for DB initialization"
```
