# 多人实时模拟交易平台

一个基于 Flask + SocketIO 的多人实时交易模拟平台，支持多用户同时在线交易。

## 🌟 功能特点

- ✅ 多人实时交易
- ✅ WebSocket 实时通信
- ✅ 管理员控制台
- ✅ 交易数据导出
- ✅ 风险管理系统
- ✅ 实时价格图表

## 🚀 在线演示

- 用户界面：[你的部署地址]
- 管理员界面：[你的部署地址]/admin

## 📦 本地运行

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务器

```bash
python server_multiplayer.py
```

访问 http://localhost:1236

## 🌐 部署到云端

详细部署指南请查看 [部署指南.md](部署指南.md)

推荐使用：
- Render（免费）
- Railway（免费额度）
- Fly.io（免费额度）

## ⚙️ 配置

编辑 `server_multiplayer.py` 修改以下参数：

```python
ADMIN_PASSWORD = 'admin123'  # 管理员密码
TOTAL_SECONDS = 280          # 游戏时长（秒）
LOSS_LIMIT = 500             # 亏损限制
```

## 📝 使用说明

### 用户端

1. 打开网站
2. 输入昵称
3. 等待管理员启动游戏
4. 使用 BUY/SELL 按钮进行交易

### 管理员端

1. 访问 `/admin`
2. 输入管理员密码（默认：admin123）
3. 点击"开始游戏"启动倒计时
4. 游戏结束后可导出交易数据

## 🛠️ 技术栈

- **后端**: Python, Flask, Flask-SocketIO
- **前端**: HTML5, CSS3, JavaScript
- **实时通信**: Socket.IO
- **图表**: Canvas API

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
