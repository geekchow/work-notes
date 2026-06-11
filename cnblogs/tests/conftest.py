import os
import sys

# 把 cnblogs/ 目录加入 import 路径，使测试可以 `import publish`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
