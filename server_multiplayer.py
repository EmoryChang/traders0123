#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多人实时模拟交易平台服务器
使用Flask + SocketIO实现实时通信
端口: 1236
"""

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading-platform-secret-key'
# 使用eventlet模式以获得更好的性能（支持更多并发连接）
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', 
                    max_http_buffer_size=1e6, ping_timeout=60, ping_interval=25)

# --- 配置参数 ---
LAMBDA = 0.125
INITIAL_VALUE = 500
TOTAL_SECONDS = 280
QUIET_PERIOD_START = 270
LOSS_LIMIT = 500
ADMIN_PASSWORD = 'admin123'  # 管理员密码，可以修改

# --- 全局状态 ---
class GameState:
    def __init__(self):
        self.time_left = TOTAL_SECONDS
        self.time_elapsed = 0
        self.is_running = False
        self.countdown = 5  # 倒计时准备阶段（5秒）
        self.is_countdown = False  # 是否在倒计时阶段
        self.fundamental_value = INITIAL_VALUE
        self.last_news_direction = 0
        self.robot_demand = 0
        self.market_price = 500
        self.history = []
        self.users = {}  # {user_id: {name, demand, cash, avg_price, buys, sells, net, connected, trade_history}}
        self.user_names = {}  # {user_id: name} 用于快速查找
        self.admins = set()  # 管理员Socket ID集合
        self.game_start_time = None  # 游戏开始时间
        self.market_buys = 0
        self.market_sells = 0
        self.cur_sec_buy = 0
        self.cur_sec_sell = 0
        self.tick_thread = None
        self.lock = threading.Lock()
        
        # 初始化历史数据点
        self.history.append({
            't': 0,
            'p': self.market_price,
            'volBuy': 0,
            'volSell': 0,
            'b': self.market_price - 1,
            'a': self.market_price + 1
        })

game_state = GameState()

# --- 计算总用户需求 ---
def get_total_user_demand():
    total = 0
    for user_data in game_state.users.values():
        total += user_data.get('demand', 0)
    return total

# --- 更新市场价格 ---
def update_market_price():
    total_demand = game_state.robot_demand + get_total_user_demand()
    offset = int(LAMBDA * total_demand)
    game_state.market_price = 500 + offset

# --- 计算未实现盈亏 ---
def calculate_unrealized_pl(user_data):
    demand = user_data.get('demand', 0)
    avg_price = user_data.get('avg_price', 0)
    if demand == 0 or avg_price == 0:
        return 0
    return demand * (game_state.market_price - avg_price)

# --- 检查风险并平仓 ---
def check_risk(user_id, user_data):
    unrealized = calculate_unrealized_pl(user_data)
    if unrealized < -LOSS_LIMIT:
        # 强制平仓
        demand = user_data.get('demand', 0)
        if demand != 0:
            close_qty = -demand
            close_price = (game_state.market_price + 1) if close_qty > 0 else (game_state.market_price - 1)
            
            user_data['cash'] -= (close_qty * close_price)
            user_data['demand'] = 0
            user_data['avg_price'] = 0
            
            abs_close = abs(close_qty)
            if close_qty > 0:
                user_data['buys'] += abs_close
                game_state.market_buys += abs_close
                game_state.cur_sec_buy += abs_close
            else:
                user_data['sells'] += abs_close
                game_state.market_sells += abs_close
                game_state.cur_sec_sell += abs_close
            
            update_market_price()
            return True
    return False

# --- 游戏循环 ---
def game_tick():
    # 主循环：等待管理员操作
    while True:
        # 等待管理员启动游戏（不再自动开始）
        while not game_state.is_countdown and not game_state.is_running:
            time.sleep(0.5)
        
        # 倒计时准备阶段（由管理员触发）
        if game_state.is_countdown and not game_state.is_running:
            # 倒计时5秒
            for i in range(5, 0, -1):
                time.sleep(1)
                with game_state.lock:
                    if not game_state.is_countdown:  # 如果管理员取消了倒计时
                        break
                    game_state.countdown = i
                    broadcast_state()
            
            # 倒计时结束，开始游戏
            with game_state.lock:
                if game_state.is_countdown:  # 确保倒计时正常完成
                    game_state.is_countdown = False
                    game_state.is_running = True
                    game_state.time_left = TOTAL_SECONDS
                    game_state.time_elapsed = 0
                    game_state.game_start_time = datetime.now()  # 记录游戏开始时间
                    print(f'游戏开始！剩余时间: {game_state.time_left}秒')
                    broadcast_state()
        
        # 游戏主循环（必须在倒计时处理之后，在while True循环内部）
        while game_state.is_running and game_state.time_left > 0:
            with game_state.lock:
                game_state.time_left -= 1
                game_state.time_elapsed += 1
                
                # 1. 新闻过程
                if game_state.time_elapsed <= QUIET_PERIOD_START:
                    direction = 0
                    if game_state.time_elapsed == 1:
                        direction = 1 if random.random() < 0.5 else -1
                    else:
                        if random.random() < 0.95:
                            direction = game_state.last_news_direction
                        else:
                            direction = -game_state.last_news_direction
                    game_state.fundamental_value += direction
                    game_state.last_news_direction = direction
                
                # 2. 机器人交易者逻辑
                target_robot_demand = (game_state.fundamental_value - 500) / LAMBDA
                robot_trade = target_robot_demand - game_state.robot_demand
                game_state.robot_demand = target_robot_demand
                
                if robot_trade > 0:
                    game_state.market_buys += robot_trade
                    game_state.cur_sec_buy += robot_trade
                elif robot_trade < 0:
                    amt = abs(robot_trade)
                    game_state.market_sells += amt
                    game_state.cur_sec_sell += amt
                
                # 3. 更新市场价格
                update_market_price()
                
                # 4. 检查所有用户的风险
                for user_id, user_data in list(game_state.users.items()):
                    if check_risk(user_id, user_data):
                        socketio.emit('risk_liquidated', {'user_id': user_id}, room='game')
                
                # 5. 记录历史（限制历史数据大小，避免内存溢出）
                game_state.history.append({
                    't': game_state.time_elapsed,
                    'p': game_state.market_price,
                    'volBuy': game_state.cur_sec_buy,
                    'volSell': game_state.cur_sec_sell,
                    'b': game_state.market_price - 1,
                    'a': game_state.market_price + 1
                })
                
                # 限制历史数据大小（保留最近500个点）
                if len(game_state.history) > 500:
                    game_state.history = game_state.history[-500:]
                
                # 重置秒级计数器
                game_state.cur_sec_buy = 0
                game_state.cur_sec_sell = 0
                
                # 6. 广播更新
                broadcast_state()
            
            time.sleep(1)
            
            # 检查游戏是否结束（在锁外检查，避免死锁）
            if game_state.time_left <= 0:
                break
        
        # 游戏结束处理（在while True循环内部）
        if game_state.time_left <= 0:
            with game_state.lock:
                game_state.is_running = False
                print(f'游戏结束！总时长: {game_state.time_elapsed}秒')
                # 计算最终财富
                final_results = {}
                for user_id, user_data in game_state.users.items():
                    demand = user_data.get('demand', 0)
                    cash = user_data.get('cash', 0)
                    final_wealth = cash + (demand * game_state.fundamental_value)
                    final_results[user_id] = {
                        'final_wealth': final_wealth,
                        'fundamental_value': game_state.fundamental_value
                    }
                
                socketio.emit('game_ended', {
                    'fundamental_value': game_state.fundamental_value,
                    'results': final_results
                }, room='game')

# --- 广播状态 ---
def broadcast_state():
    # 计算所有用户的总交易统计
    total_user_buys = sum(u.get('buys', 0) for u in game_state.users.values())
    total_user_sells = sum(u.get('sells', 0) for u in game_state.users.values())
    total_user_net = total_user_buys - total_user_sells
    
    state = {
        'time_left': game_state.time_left,
        'time_elapsed': game_state.time_elapsed,
        'is_running': game_state.is_running,
        'is_countdown': game_state.is_countdown,
        'countdown': game_state.countdown,
        'market_price': game_state.market_price,
        'fundamental_value': game_state.fundamental_value,
        'market_buys': int(game_state.market_buys),
        'market_sells': int(game_state.market_sells),
        'market_net': int(game_state.market_buys - game_state.market_sells),
        'total_user_buys': total_user_buys,
        'total_user_sells': total_user_sells,
        'total_user_net': total_user_net,
        'history': list(game_state.history[-100:]) if len(game_state.history) > 0 else [],  # 发送最近100个数据点，确保转换为列表
        'users': {}
    }
    
    # 添加每个用户的详细信息（仅用于当前用户自己的数据）
    online_users = []
    for user_id, user_data in game_state.users.items():
        # 排除管理员，只统计普通用户
        if user_data.get('connected', False) and user_id not in game_state.admins:
            # 收集在线用户列表（只包含ID和昵称）
            online_users.append({
                'id': user_id,
                'name': user_data.get('name', f'用户{user_id[:8]}')
            })
            
            # 只向对应用户发送其自己的详细交易数据（排除管理员）
            if user_id not in game_state.admins:
                demand = user_data.get('demand', 0)
                avg_price = user_data.get('avg_price', 0)
                unrealized = calculate_unrealized_pl(user_data)
                total_equity = user_data.get('cash', 0) + (demand * game_state.market_price)
                realized = total_equity - unrealized
                
                user_info = {
                    'id': user_id,
                    'name': user_data.get('name', f'用户{user_id[:8]}'),
                    'demand': demand,
                    'buys': user_data.get('buys', 0),
                    'sells': user_data.get('sells', 0),
                    'net': user_data.get('buys', 0) - user_data.get('sells', 0),
                    'avg_price': avg_price,
                    'realized': realized,
                    'unrealized': unrealized,
                    'exposure': demand,
                    'total_equity': total_equity
                }
                state['users'][user_id] = user_info
    
    # 添加在线用户统计（只发送用户昵称，不包含交易信息）
    state['online_count'] = len(online_users)
    state['online_users'] = online_users  # 只包含ID和昵称
    
    # 使用压缩发送以减少网络传输
    try:
        socketio.emit('state_update', state, room='game', compress=True)
    except:
        socketio.emit('state_update', state, room='game')

# --- WebSocket 事件处理 ---
@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    print(f'客户端连接: {user_id}')
    join_room('game')
    
    # 发送当前状态
    with game_state.lock:
        # 初始化用户数据（如果不存在）
        if user_id not in game_state.users:
            game_state.users[user_id] = {
                'name': f'用户{user_id[:8]}',
                'demand': 0,
                'cash': 0,
                'avg_price': 0,
                'buys': 0,
                'sells': 0,
                'connected': True,
                'trade_history': []  # 交易历史记录
            }
        else:
            game_state.users[user_id]['connected'] = True
        
        # 如果游戏还没开始，启动倒计时和游戏循环
        if not game_state.is_running and not game_state.is_countdown and game_state.tick_thread is None:
            game_state.tick_thread = threading.Thread(target=game_tick, daemon=True)
            game_state.tick_thread.start()
        
        # 发送完整状态
        broadcast_state()

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    print(f'客户端断开: {user_id}')
    leave_room('game')
    # 标记为离线，但保留数据（用户可能重新连接）
    with game_state.lock:
        if user_id in game_state.users:
            game_state.users[user_id]['connected'] = False
        # 更新市场价格（移除该用户的需求）
        update_market_price()
        broadcast_state()

@socketio.on('set_username')
def handle_set_username(data):
    user_id = request.sid
    username = data.get('name', '').strip()
    
    if not username:
        username = f'用户{user_id[:8]}'
    
    # 限制用户名长度
    if len(username) > 20:
        username = username[:20]
    
    with game_state.lock:
        if user_id not in game_state.users:
            game_state.users[user_id] = {
                'name': username,
                'demand': 0,
                'cash': 0,
                'avg_price': 0,
                'buys': 0,
                'sells': 0,
                'connected': True,
                'trade_history': []  # 交易历史记录
            }
        else:
            game_state.users[user_id]['name'] = username
            if 'trade_history' not in game_state.users[user_id]:
                game_state.users[user_id]['trade_history'] = []
        
        emit('username_set', {'name': username})
        broadcast_state()

@socketio.on('admin_login')
def handle_admin_login(data):
    user_id = request.sid
    password = data.get('password', '')
    
    if password == ADMIN_PASSWORD:
        game_state.admins.add(user_id)
        emit('admin_login_success', {'message': '管理员登录成功'})
        print(f'管理员登录: {user_id}')
        broadcast_state()
    else:
        emit('admin_login_failed', {'message': '密码错误'})

@socketio.on('admin_start_game')
def handle_admin_start_game():
    user_id = request.sid
    
    if user_id not in game_state.admins:
        emit('error', {'message': '无管理员权限'})
        return
    
    with game_state.lock:
        if game_state.is_running:
            emit('error', {'message': '游戏已在进行中'})
            return
        
        if game_state.is_countdown:
            emit('error', {'message': '倒计时已在进行中'})
            return
        
        # 开始倒计时
        game_state.is_countdown = True
        game_state.countdown = 5
        print(f'管理员 {user_id} 启动游戏')
        broadcast_state()

@socketio.on('admin_reset_game')
def handle_admin_reset_game():
    user_id = request.sid
    
    if user_id not in game_state.admins:
        emit('error', {'message': '无管理员权限'})
        return
    
    with game_state.lock:
        # 重置游戏状态
        game_state.is_running = False
        game_state.is_countdown = False
        game_state.countdown = 5
        game_state.time_left = TOTAL_SECONDS
        game_state.time_elapsed = 0
        game_state.fundamental_value = INITIAL_VALUE
        game_state.last_news_direction = 0
        game_state.robot_demand = 0
        game_state.market_price = 500
        game_state.market_buys = 0
        game_state.market_sells = 0
        game_state.history = [{
            't': 0,
            'p': game_state.market_price,
            'volBuy': 0,
            'volSell': 0,
            'b': game_state.market_price - 1,
            'a': game_state.market_price + 1
        }]
        
        # 重置所有用户数据
        for user_data in game_state.users.values():
            user_data['demand'] = 0
            user_data['cash'] = 0
            user_data['avg_price'] = 0
            user_data['buys'] = 0
            user_data['sells'] = 0
        
        game_state.game_start_time = None
        print(f'管理员 {user_id} 重置游戏')
        broadcast_state()
        emit('admin_reset_success', {'message': '游戏已重置'})

@socketio.on('admin_export_data')
def handle_admin_export_data():
    user_id = request.sid
    
    if user_id not in game_state.admins:
        emit('error', {'message': '无管理员权限'})
        return
    
    with game_state.lock:
        # 导出所有普通用户的交易数据
        export_data = {
            'game_info': {
                'start_time': game_state.game_start_time.strftime('%Y-%m-%d %H:%M:%S') if game_state.game_start_time else None,
                'duration': game_state.time_elapsed,
                'final_fundamental_value': game_state.fundamental_value,
                'is_completed': game_state.time_left <= 0 and game_state.time_elapsed > 0
            },
            'users': []
        }
        
        # 收集所有普通用户（排除管理员）的数据
        for user_id_key, user_data in game_state.users.items():
            if user_id_key not in game_state.admins:  # 排除管理员
                user_export = {
                    'user_id': user_id_key[:8],  # 只显示前8位
                    'name': user_data.get('name', f'用户{user_id_key[:8]}'),
                    'final_stats': {
                        'demand': user_data.get('demand', 0),
                        'cash': user_data.get('cash', 0),
                        'avg_price': user_data.get('avg_price', 0),
                        'total_buys': user_data.get('buys', 0),
                        'total_sells': user_data.get('sells', 0),
                        'net_transactions': user_data.get('buys', 0) - user_data.get('sells', 0)
                    },
                    'trade_history': user_data.get('trade_history', [])
                }
                
                # 计算最终财富
                demand = user_data.get('demand', 0)
                cash = user_data.get('cash', 0)
                final_wealth = cash + (demand * game_state.fundamental_value)
                user_export['final_stats']['final_wealth'] = final_wealth
                
                export_data['users'].append(user_export)
        
        # 按昵称排序
        export_data['users'].sort(key=lambda x: x['name'])
        
        emit('admin_export_data', export_data)

@socketio.on('user_trade')
def handle_trade(data):
    user_id = request.sid
    qty = int(data.get('qty', 0))
    
    if not game_state.is_running or game_state.is_countdown:
        emit('error', {'message': '游戏未开始，请等待管理员启动'})
        return
    
    if qty == 0:
        return
    
    with game_state.lock:
        # 确保用户数据存在
        if user_id not in game_state.users:
            game_state.users[user_id] = {
                'name': f'用户{user_id[:8]}',
                'demand': 0,
                'cash': 0,
                'avg_price': 0,
                'buys': 0,
                'sells': 0,
                'connected': True,
                'trade_history': []  # 交易历史记录
            }
        
        user_data = game_state.users[user_id]
        if 'trade_history' not in user_data:
            user_data['trade_history'] = []
        
        is_buy = qty > 0
        abs_qty = abs(qty)
        
        exec_price = (game_state.market_price + 1) if is_buy else (game_state.market_price - 1)
        
        # 记录交易历史
        trade_record = {
            'time': game_state.time_elapsed,  # 游戏内时间（秒）
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 实际时间戳
            'action': 'BUY' if is_buy else 'SELL',
            'quantity': abs_qty,
            'price': exec_price,
            'market_price': game_state.market_price,
            'demand_before': user_data['demand'],
            'demand_after': user_data['demand'] + qty
        }
        user_data['trade_history'].append(trade_record)
        
        # 更新交易统计
        if is_buy:
            user_data['buys'] += abs_qty
            game_state.market_buys += abs_qty
            game_state.cur_sec_buy += abs_qty
        else:
            user_data['sells'] += abs_qty
            game_state.market_sells += abs_qty
            game_state.cur_sec_sell += abs_qty
        
        # 更新持仓
        old_pos = user_data['demand']
        new_pos = old_pos + qty
        
        user_data['cash'] -= (qty * exec_price)
        
        # 更新平均价格
        if old_pos == 0:
            user_data['avg_price'] = exec_price
        elif (old_pos > 0 and qty > 0) or (old_pos < 0 and qty < 0):
            old_val = abs(old_pos) * user_data['avg_price']
            new_val = abs_qty * exec_price
            user_data['avg_price'] = (old_val + new_val) / abs(new_pos)
        else:
            if (new_pos > 0 and old_pos < 0) or (new_pos < 0 and old_pos > 0):
                user_data['avg_price'] = exec_price
            elif new_pos == 0:
                user_data['avg_price'] = 0
        
        user_data['demand'] = new_pos
        
        # 更新市场价格
        update_market_price()
        
        # 检查风险
        if check_risk(user_id, user_data):
            emit('risk_liquidated', {'user_id': user_id})
        
        # 广播更新
        broadcast_state()

# --- 静态文件服务 ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 1236))
    print("=" * 60)
    print("多人实时模拟交易平台服务器")
    print(f"访问地址: http://localhost:{port}")
    print(f"支持最多100+用户同时在线")
    print("=" * 60)
    # 使用0.0.0.0允许局域网访问，port_reuse=True允许端口重用
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True, 
                 use_reloader=False, log_output=False)
