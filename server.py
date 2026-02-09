#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器，用于运行模拟交易平台
端口: 1236
"""

import http.server
import socketserver
import os
import sys

PORT = 1236

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头，允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        sys.stderr.write("%s - - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format%args))

def main():
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = MyHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"=" * 60)
            print(f"模拟交易平台服务器已启动")
            print(f"访问地址: http://localhost:{PORT}")
            print(f"按 Ctrl+C 停止服务器")
            print(f"=" * 60)
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98 or e.errno == 48:  # Address already in use
            print(f"错误: 端口 {PORT} 已被占用，请关闭占用该端口的程序后重试")
        else:
            print(f"错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)

if __name__ == "__main__":
    main()
