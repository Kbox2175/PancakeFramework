import sys
import os

disable_check = []

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def init():
    import initialize
    initialize.print_ico()

    init_rask = {"check_environment":initialize.check_environment, # 检查环境
                 "check_struct":initialize.check_struct, # 检查项目结构完整性
                }

    os.chdir(os.sep.join(current_dir.split(os.sep)[:-1]))
    # 检查运行环境
    print("检查运行环境")
    import tool
    progress = tool.ProgressBar(len(init_rask), prefix="初始化环境")
    for task in init_rask.keys():
        if task in disable_check:
            continue
        init_rask[task]()
        progress.update(1, f"{task} 完成")

    progress.finish()
    os.chdir(os.sep.join(current_dir.split(os.sep)[:-1] + ["src"]))

init()

# 资源库(系统) - env
from resource import config
import resource.logging as resource_logging
import logging as std_logging

from .run import run
