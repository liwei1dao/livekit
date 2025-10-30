#!/usr/bin/env python3
"""
本地 LiveKit Python 代理
完全本地部署，不依赖 LiveKit 云服务
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Dict, Any
import websockets
import jwt
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalLiveKitAgent:
    def __init__(self):
        self.livekit_url = os.getenv('LIVEKIT_URL', 'ws://livekit:7880')
        self.api_key = os.getenv('LIVEKIT_API_KEY', 'APIcyMmEUQTDGnS')
        self.api_secret = os.getenv('LIVEKIT_API_SECRET', 'EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc')
        self.room_name = os.getenv('ROOM_NAME', 'test-room')
        self.participant_name = os.getenv('PARTICIPANT_NAME', 'local-agent')
        
        self.websocket = None
        self.running = False
        
        logger.info(f"初始化本地代理 - URL: {self.livekit_url}, Room: {self.room_name}")

    def generate_access_token(self) -> str:
        """生成 LiveKit 访问令牌"""
        now = datetime.utcnow()
        exp = now + timedelta(hours=6)
        
        payload = {
            'iss': self.api_key,
            'sub': self.participant_name,
            'iat': int(now.timestamp()),
            'exp': int(exp.timestamp()),
            'video': {
                'room': self.room_name,
                'roomJoin': True,
                'canPublish': True,
                'canSubscribe': True,
            }
        }
        
        token = jwt.encode(payload, self.api_secret, algorithm='HS256')
        logger.info(f"生成访问令牌: {token[:20]}...")
        return token

    async def connect_to_room(self):
        """连接到 LiveKit 房间"""
        try:
            token = self.generate_access_token()
            
            # 构建 WebSocket URL
            ws_url = f"{self.livekit_url.replace('ws://', 'ws://').replace('wss://', 'wss://')}"
            if not ws_url.endswith('/'):
                ws_url += '/'
            ws_url += f"?access_token={token}"
            
            logger.info(f"连接到 LiveKit: {ws_url.split('?')[0]}")
            
            self.websocket = await websockets.connect(ws_url)
            logger.info("成功连接到 LiveKit 服务器")
            
            return True
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    async def handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            logger.info(f"收到消息类型: {msg_type}")
            
            if msg_type == 'join':
                await self.on_participant_joined(data)
            elif msg_type == 'leave':
                await self.on_participant_left(data)
            elif msg_type == 'track_published':
                await self.on_track_published(data)
            elif msg_type == 'track_unpublished':
                await self.on_track_unpublished(data)
            elif msg_type == 'data':
                await self.on_data_received(data)
            else:
                logger.debug(f"未处理的消息类型: {msg_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"无法解析消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")

    async def on_participant_joined(self, data: Dict[str, Any]):
        """参与者加入房间"""
        participant = data.get('participant', {})
        name = participant.get('name', 'Unknown')
        logger.info(f"参与者加入: {name}")
        
        # 发送欢迎消息
        welcome_msg = {
            'type': 'data',
            'payload': json.dumps({
                'message': f'欢迎 {name} 加入房间！',
                'timestamp': datetime.now().isoformat(),
                'from': 'local-agent'
            })
        }
        
        if self.websocket:
            await self.websocket.send(json.dumps(welcome_msg))

    async def on_participant_left(self, data: Dict[str, Any]):
        """参与者离开房间"""
        participant = data.get('participant', {})
        name = participant.get('name', 'Unknown')
        logger.info(f"参与者离开: {name}")

    async def on_track_published(self, data: Dict[str, Any]):
        """音频/视频轨道发布"""
        track = data.get('track', {})
        track_type = track.get('type', 'unknown')
        participant = data.get('participant', {})
        name = participant.get('name', 'Unknown')
        
        logger.info(f"参与者 {name} 发布了 {track_type} 轨道")
        
        if track_type == 'audio':
            await self.process_audio_track(track, participant)

    async def on_track_unpublished(self, data: Dict[str, Any]):
        """音频/视频轨道取消发布"""
        track = data.get('track', {})
        track_type = track.get('type', 'unknown')
        participant = data.get('participant', {})
        name = participant.get('name', 'Unknown')
        
        logger.info(f"参与者 {name} 取消发布了 {track_type} 轨道")

    async def on_data_received(self, data: Dict[str, Any]):
        """接收到数据消息"""
        try:
            payload = json.loads(data.get('payload', '{}'))
            message = payload.get('message', '')
            from_user = payload.get('from', 'Unknown')
            
            logger.info(f"收到来自 {from_user} 的消息: {message}")
            
            # 简单的回复逻辑
            if message.lower().startswith('hello'):
                response = {
                    'type': 'data',
                    'payload': json.dumps({
                        'message': f'你好！我是本地代理，很高兴见到你！',
                        'timestamp': datetime.now().isoformat(),
                        'from': 'local-agent'
                    })
                }
                
                if self.websocket:
                    await self.websocket.send(json.dumps(response))
                    
        except Exception as e:
            logger.error(f"处理数据消息时出错: {e}")

    async def process_audio_track(self, track: Dict[str, Any], participant: Dict[str, Any]):
        """处理音频轨道"""
        logger.info("开始处理音频轨道...")
        
        # 这里可以添加音频处理逻辑
        # 例如：语音识别、音频分析等
        
        # 模拟音频处理
        await asyncio.sleep(0.1)
        
        # 发送处理结果
        result_msg = {
            'type': 'data',
            'payload': json.dumps({
                'message': '音频处理完成',
                'timestamp': datetime.now().isoformat(),
                'from': 'local-agent',
                'audio_processed': True
            })
        }
        
        if self.websocket:
            await self.websocket.send(json.dumps(result_msg))

    async def send_heartbeat(self):
        """发送心跳消息"""
        while self.running:
            try:
                if self.websocket:
                    heartbeat = {
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    }
                    await self.websocket.send(json.dumps(heartbeat))
                    logger.debug("发送心跳")
                
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                
            except Exception as e:
                logger.error(f"发送心跳时出错: {e}")
                break

    async def run(self):
        """运行代理"""
        self.running = True
        
        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info("收到停止信号，正在关闭...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.running:
            try:
                # 连接到 LiveKit
                if await self.connect_to_room():
                    logger.info("代理已连接，开始监听消息...")
                    
                    # 启动心跳任务
                    heartbeat_task = asyncio.create_task(self.send_heartbeat())
                    
                    try:
                        # 监听消息
                        async for message in self.websocket:
                            if not self.running:
                                break
                            await self.handle_message(message)
                            
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket 连接已关闭")
                    except Exception as e:
                        logger.error(f"消息处理循环出错: {e}")
                    finally:
                        heartbeat_task.cancel()
                        if self.websocket:
                            await self.websocket.close()
                
                if self.running:
                    logger.info("连接断开，5秒后重试...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"运行时出错: {e}")
                if self.running:
                    await asyncio.sleep(5)
        
        logger.info("代理已停止")

async def main():
    """主函数"""
    logger.info("启动本地 LiveKit Python 代理...")
    
    agent = LocalLiveKitAgent()
    await agent.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)