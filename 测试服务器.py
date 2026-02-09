#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试服务器是否能正常启动
"""

import sys

print("正在检查Python语法...")
try:
    # 尝试编译检查语法
    with open('server_multiplayer.py', 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, 'server_multiplayer.py', 'exec')
    print("✓ Python语法检查通过")
except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
    print(f"  文件: {e.filename}")
    print(f"  行号: {e.lineno}")
    print(f"  位置: {e.offset}")
    sys.exit(1)
except Exception as e:
    print(f"✗ 检查失败: {e}")
    sys.exit(1)

print("\n正在检查依赖包...")
try:
    import flask
    import flask_socketio
    print("✓ Flask已安装")
    print("✓ Flask-SocketIO已安装")
except ImportError as e:
    print(f"✗ 缺少依赖包: {e}")
    print("  请运行: pip install -r requirements.txt")
    sys.exit(1)

print("\n✓ 所有检查通过！服务器应该可以正常启动。")
print("  现在可以运行: python server_multiplayer.py")
