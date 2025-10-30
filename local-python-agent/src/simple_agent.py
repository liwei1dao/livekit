#!/usr/bin/env python3
"""
简化的本地 LiveKit Python 代理 - 用于测试基本连接
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from typing import Optional

import websockets
import jwt
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleLiveKitAgent:
    def __init__(self):
        # 从环境变量获取配置
        self.livekit_url = os.getenv('LIVEKIT_URL', 'ws://livekit:7880')
        self.api_key = os.getenv('LIVEKIT_API_KEY', 'devkey')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET', 'secret')
        self.room_name = os.getenv('ROOM_NAME', 'test-room')
        self.participant_name = os.getenv('PARTICIPANT_NAME', 'local-agent')
        
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
        
        logger.info(f"初始化简化代理 - URL: {self.livekit_url}, Room: {self.room_name}")

    def generate_access_token(self) -> str:
        """生成代理访问令牌"""
        try:
            now = datetime.utcnow()
            payload = {
                'iss': self.api_key,
                'sub': self.participant_name,
                'iat': int(now.timestamp()),
                'exp': int((now + timedelta(hours=6)).timestamp()),  # 延长到6小时
                'nbf': int(now.timestamp()),
                'video': {
                    'agent': True  # 这是代理令牌的关键标识
                }
            }
            
            token = jwt.encode(payload, self.api_secret, algorithm='HS256')
            logger.info(f"代理访问令牌生成成功 - API Key: {self.api_key[:8]}...")
            return token
            
        except Exception as e:
            logger.error(f"生成代理访问令牌失败: {e}")
            raise

    async def connect_to_room(self):
        """连接到 LiveKit 房间"""
        try:
            # 生成访问令牌
            token = self.generate_access_token()
            
            # 构建 WebSocket URL，将令牌作为查询参数
            ws_url = self.livekit_url.replace('http://', 'ws://').replace('https://', 'wss://')
            if not ws_url.endswith('/'):
                ws_url += '/'
            ws_url += f'agent?access_token={token}'  # 将令牌作为查询参数
            
            logger.info(f"正在连接到代理端点: {ws_url.split('?')[0]}?access_token=...")
            
            # 建立 WebSocket 连接，不使用额外的 headers
            self.websocket = await websockets.connect(ws_url)
            
            logger.info("成功连接到 LiveKit 代理端点")
            
            # 代理连接不需要发送额外的连接消息
            # 服务器会自动处理代理注册
            
            return True
            
        except Exception as e:
            logger.error(f"连接到代理端点失败: {e}")
            return False

    async def handle_messages(self):
        """处理接收到的消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"收到消息: {data.get('type', 'unknown')}")
                    
                    # 简单的消息处理
                    if data.get('type') == 'participant_joined':
                        logger.info(f"参与者加入: {data.get('participant', {}).get('identity', 'unknown')}")
                    elif data.get('type') == 'participant_left':
                        logger.info(f"参与者离开: {data.get('participant', {}).get('identity', 'unknown')}")
                    elif data.get('type') == 'track_published':
                        logger.info(f"轨道发布: {data.get('track', {}).get('sid', 'unknown')}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"无法解析消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"WebSocket 连接已关闭: {e}")
            raise
        except Exception as e:
            logger.error(f"消息处理循环出错: {e}")
            raise

    async def send_heartbeat(self):
        """发送心跳"""
        while self.running and self.websocket:
            try:
                heartbeat = {
                    'type': 'ping',
                    'timestamp': int(time.time())
                }
                await self.websocket.send(json.dumps(heartbeat))
                logger.debug("心跳已发送")
                await asyncio.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"发送心跳失败: {e}")
                break

    async def run(self):
        """运行代理"""
        self.running = True
        max_retries = 10
        retry_count = 0
        
        while self.running and retry_count < max_retries:
            try:
                logger.info(f"尝试连接 (第 {retry_count + 1} 次)")
                
                if await self.connect_to_room():
                    logger.info("成功连接到房间，开始处理消息")
                    
                    # 启动心跳任务
                    heartbeat_task = asyncio.create_task(self.send_heartbeat())
                    
                    try:
                        # 处理消息
                        await self.handle_messages()
                    finally:
                        heartbeat_task.cancel()
                        try:
                            await heartbeat_task
                        except asyncio.CancelledError:
                            pass
                    
                    # 连接断开后，增加重试计数并等待
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(10 + (retry_count * 5), 60)  # 10-60秒的延迟
                        logger.warning(f"连接已断开，{wait_time}秒后重试 (尝试 {retry_count}/{max_retries})")
                        await asyncio.sleep(wait_time)
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(5 * retry_count, 30)  # 指数退避，最大30秒
                        logger.warning(f"连接失败，{wait_time}秒后重试 (尝试 {retry_count}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"运行时出错: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(5 * retry_count, 30)
                    logger.warning(f"出现错误，{wait_time}秒后重试 (尝试 {retry_count}/{max_retries})")
                    await asyncio.sleep(wait_time)
            finally:
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except:
                        pass
                    self.websocket = None
        
        if retry_count >= max_retries:
            logger.error("达到最大重试次数，停止运行")
        
        logger.info("代理已停止")

    def stop(self):
        """停止代理"""
        logger.info("正在停止代理...")
        self.running = False

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭代理...")
    agent.stop()

if __name__ == "__main__":
    # 设置信号处理
    agent = SimpleLiveKitAgent()
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        logger.info("启动简化的本地 LiveKit Python 代理...")
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在停止...")
    except Exception as e:
        logger.error(f"代理运行时出错: {e}")
        sys.exit(1)