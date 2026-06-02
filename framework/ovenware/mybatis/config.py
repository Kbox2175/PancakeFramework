"""
MyBatis 配置加载
从 YAML 读取数据库配置
"""

import logging

import oven

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = {
    "url": "sqlite:///src/resource/db/app.db",
    "min_size": 1,
    "max_size": 5,
}


def load_config() -> dict:
    """加载 mybatis 配置"""
    config = {}

    # 从 pancake_yaml 读取
    for key, default in _DEFAULT_CONFIG.items():
        yaml_key = f"mybatis.database.{key}"
        config[key] = oven.pancake_yaml.get(yaml_key, default)

    logger.info(f"MyBatis 配置: url={config['url']}")
    return config
