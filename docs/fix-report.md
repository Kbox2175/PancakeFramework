# Pancake Framework Fix Report

**Date:** 2026-06-02

## Summary

Fixed 7 issues across the Pancake framework, covering security hardening, stability improvements, and code quality. Added 15 unit tests covering SQL parser, mapper security, and YAML config loading.

---

## Fixes Applied

### 1. SQL Identifier Validation (P0 Security)

**Files:** `framework/ovenware/mybatis/mapper.py`, `framework/ovenware/mybatis/wrapper.py`

**Problem:** Table names and column names were directly interpolated into SQL strings via f-strings without validation, enabling potential SQL injection.

**Fix:** Added `_validate_identifier()` function with regex `^[a-zA-Z_][a-zA-Z0-9_]*$` that validates all SQL identifiers at registration time (in `__init_subclass__` and `@Mapper` decorator) and at query time (in `_build_where_from_dict`, `insert`, `insert_batch`, `update_by_id`). Column names in `QueryWrapper` are also validated via `_resolve_column()`.

**Before:**
```python
# Table name injected directly
sql = f"SELECT * FROM {self._table_name} WHERE id = :id"
```

**After:**
```python
# Validated at registration time
_validate_identifier(cls._table_name, "table")

# Column names validated at query time
def _build_where_from_dict(params):
    for key, val in params.items():
        _validate_identifier(key, "column")
```

---

### 2. auto_inject Type Checking (P1 Stability)

**File:** `framework/ovenware/auto_inject.py`

**Problem:** Used `type(x) != T` for type checking, which rejects subclasses. For example, `int` values would be rejected when the parameter annotation is `float`.

**Fix:** Replaced `type(x) != T` with `not isinstance(x, T)` in both the kwargs check (line 67) and positional args check (line 79).

---

### 3. YAML Circular Reference Protection (P1 Stability)

**File:** `framework/resource/yml.py`

**Problem:** The `${key}` placeholder resolver used `while True` with no cycle detection. Circular references like `a: ${b}`, `b: ${a}` would cause an infinite loop. Also had a bare `except:` clause.

**Fix:**
- Added `resolving` set to track keys being resolved, detecting circular references
- Added max 10 iterations as a safety bound
- Replaced bare `except:` with `except (KeyError, TypeError):`

---

### 4. Plugin Module Filtering (P2 Quality)

**File:** `framework/build/load_dlc.py`

**Problem:** `member.__module__ == plugin.__name__` exact match failed for sub-modules (e.g., `ovenware.mybatis.mapper` != `ovenware.mybatis`), causing valid plugin members to be filtered out. Plugin check failures also exited silently.

**Fix:**
- Changed to prefix matching: `member.__module__ == plugin.__name__ or member.__module__.startswith(plugin.__name__ + ".")`
- Added error logging before `sys.exit(1)` so users see which plugin failed and why

---

### 5. Non-Interactive Environment Check (P2 Quality)

**File:** `framework/initialize/check_env.py`

**Problem:** `input()` call would hang in non-interactive environments (CI, Docker, scripts).

**Fix:** Added `PANCAKE_AUTO_INSTALL` environment variable support and `sys.stdin.isatty()` check. In non-interactive mode, exits with a clear error message suggesting the env var.

---

### 6. Optional Dependencies (P2 Quality)

**File:** `pyproject.toml`

**Problem:** Heavy optional dependencies (langgraph, grpcio, redis, aiohttp, websocket-client) were required, bloating install size.

**Fix:** Moved to `[tool.poetry.extras]` with named groups:
- `pip install framework[langgraph]` - LangGraph support
- `pip install framework[grpc]` - gRPC support
- `pip install framework[redis]` - Redis support
- `pip install framework[all]` - Everything

---

### 7. Test Infrastructure

**Files:** `tests/conftest.py`, `tests/test_sql_parser.py`, `tests/test_mapper_security.py`, `tests/test_yml.py`

Added 15 unit tests covering:
- SQL parser: param binding, `<if>`, `<where>`, `<set>`, `<foreach>`, `<choose>` tags
- Mapper security: valid identifiers, SQL injection rejection
- YAML: basic load, placeholder resolution, circular reference safety

**Run tests:** `.venv/Scripts/python -m pytest tests/ -v`

---

## Test Results

```
tests/test_mapper_security.py::test_valid_identifiers PASSED
tests/test_mapper_security.py::test_sql_injection_rejected PASSED
tests/test_mapper_security.py::test_column_injection_rejected PASSED
tests/test_sql_parser.py::test_basic_param_binding PASSED
tests/test_sql_parser.py::test_if_tag_true PASSED
tests/test_sql_parser.py::test_if_tag_false PASSED
tests/test_sql_parser.py::test_where_tag PASSED
tests/test_sql_parser.py::test_set_tag PASSED
tests/test_sql_parser.py::test_foreach PASSED
tests/test_sql_parser.py::test_choose_when PASSED
tests/test_sql_parser.py::test_multiple_params PASSED
tests/test_sql_parser.py::test_if_null_check PASSED
tests/test_yml.py::test_yaml_basic_load PASSED
tests/test_yml.py::test_yaml_placeholder_resolution PASSED
tests/test_yml.py::test_yaml_circular_reference_no_crash PASSED

15 passed in 0.16s
```

## Skipped

- **Builtins injection security** - User chose to skip this fix
- **Sync/async bridge** - Current implementation is correct (build runs before event loop starts)
