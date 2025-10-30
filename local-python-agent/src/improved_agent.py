#!/usr/bin/env python3
"""
---
title: 本地 LiveKit Python 代理
category: 基础代理
tags: [voice, local, websocket, basic]
difficulty: 初级
description: 完全本地部署的 LiveKit Python 代理，不依赖云服务
demonstrates:
  - 本地 WebSocket 连接
  - 基础音频处理
  - 简单的语音活动检测
  - 消息处理和响应
---

改进的本地 LiveKit Python 代理
基于 python-agents-examples 项目的最佳实践
完全本地部署，不依赖 LiveKit 云服务
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Dict, Any, Optional
import websockets
import jwt
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

# 导入配置和处理器
from config import Config
from audio_processor import AudioProcessor, MessageHandler

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ParticipantInfo:
    """参与者信息"""
    sid: str
    identity: str
    name: str
    metadata: Dict[str, Any]
    joined_at: datetime

class ImprovedLocalAgent:
    """改进的本地 LiveKit 代理"""
    
    def __init__(self):
        self.config = Config()
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
        self.room_connected = False
        self.participants: Dict[str, ParticipantInfo] = {}
        
        # 初始化处理器
        self.audio_processor = AudioProcessor()
        self.message_handler = MessageHandler()
        
        # 统计信息
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'audio_frames_processed': 0,
            'connection_time': None,
            'last_heartbeat': None
        }
        
        logger.info(f"初始化改进的本地代理 - URL: {self.config.LIVEKIT_URL}, Room: {self.config.DEFAULT_ROOM_NAME}")
    
    def generate_access_token(self, room_name: str, participant_name: str) -> str:
        """生成访问令牌"""
        try:
            now = datetime.utcnow()
            payload = {
                'iss': self.config.LIVEKIT_API_KEY,
                'sub': participant_name,
                'iat': int(now.timestamp()),
                'exp': int((now + timedelta(hours=24)).timestamp()),
                'room': room_name,
                'grants': {
                    'room': room_name,
                    'roomJoin': True,
                    'roomList': True,
                    'roomRecord': False,
                    'roomAdmin': False,
                    'roomCreate': False,
                    'canPublish': True,
                    'canSubscribe': True,
                    'canPublishData': True,
                    'canUpdateOwnMetadata': True
                }
            }
            
            token = jwt.encode(payload, self.config.LIVEKIT_API_SECRET, algorithm='HS256')
            logger.debug(f"生成访问令牌成功 - Room: {room_name}, Participant: {participant_name}")
            return token
            
        except Exception as e:
            logger.error(f"生成访问令牌失败: {e}")
            raise
    
    async def connect_to_room(self) -> bool:
        """连接到 LiveKit 房间"""
        try:
            # 生成访问令牌
            token = self.generate_access_token(
                self.config.DEFAULT_ROOM_NAME, 
                self.config.PARTICIPANT_NAME
            )
            
            # 构建 WebSocket URL
            ws_url = f"{self.config.LIVEKIT_URL}/rtc"
            
            # 连接参数
            connect_params = {
                'access_token': token,
                'room': self.config.DEFAULT_ROOM_NAME,
                'participant': self.config.PARTICIPANT_NAME,
                'protocol': 'websocket',
                'version': '1.0'
            }
            
            logger.info(f"正在连接到房间: {self.config.DEFAULT_ROOM_NAME}")
            
            # 建立 WebSocket 连接
            # 使用简化的连接方式，避免版本兼容性问题
            self.websocket = await websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            # 发送连接消息
            connect_message = {
                'type': 'connect',
                'data': connect_params
            }
            
            await self.websocket.send(json.dumps(connect_message))
            
            # 等待连接确认
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            
            if response_data.get('type') == 'connected':
                self.room_connected = True
                self.stats['connection_time'] = datetime.now()
                logger.info(f"成功连接到房间: {self.config.DEFAULT_ROOM_NAME}")
                return True
            else:
                logger.error(f"连接失败: {response_data}")
                return False
                
        except asyncio.TimeoutError:
            logger.error("连接超时")
            return False
        except Exception as e:
            logger.error(f"连接到房间失败: {e}")
            return False
    
    async def handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            self.stats['messages_received'] += 1
            
            if message_type == 'participant_joined':
                await self.handle_participant_joined(data)
            elif message_type == 'participant_left':
                await self.handle_participant_left(data)
            elif message_type == 'track_published':
                await self.handle_track_published(data)
            elif message_type == 'track_unpublished':
                await self.handle_track_unpublished(data)
            elif message_type == 'data_received':
                await self.handle_data_received(data)
            elif message_type == 'audio_frame':
                await self.handle_audio_frame(data)
            elif message_type == 'ping':
                await self.handle_ping(data)
            else:
                logger.debug(f"未处理的消息类型: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"无法解析消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    async def handle_participant_joined(self, data: Dict[str, Any]):
        """处理参与者加入"""
        participant_data = data.get('participant', {})
        sid = participant_data.get('sid')
        identity = participant_data.get('identity')
        name = participant_data.get('name', identity)
        
        if sid and identity:
            participant = ParticipantInfo(
                sid=sid,
                identity=identity,
                name=name,
                metadata=participant_data.get('metadata', {}),
                joined_at=datetime.now()
            )
            
            self.participants[sid] = participant
            logger.info(f"参与者加入: {name} ({identity})")
            
            # 发送欢迎消息
            welcome_message = f"欢迎 {name} 加入房间！"
            await self.send_text_message(welcome_message)
    
    async def handle_participant_left(self, data: Dict[str, Any]):
        """处理参与者离开"""
        participant_data = data.get('participant', {})
        sid = participant_data.get('sid')
        
        if sid in self.participants:
            participant = self.participants.pop(sid)
            logger.info(f"参与者离开: {participant.name} ({participant.identity})")
            
            # 发送告别消息
            goodbye_message = f"再见 {participant.name}！"
            await self.send_text_message(goodbye_message)
    
    async def handle_track_published(self, data: Dict[str, Any]):
        """处理轨道发布"""
        track_data = data.get('track', {})
        track_type = track_data.get('type')
        track_name = track_data.get('name')
        
        logger.info(f"轨道发布: {track_name} ({track_type})")
        
        if track_type == 'audio':
            # 订阅音频轨道
            await self.subscribe_to_track(track_data)
    
    async def handle_track_unpublished(self, data: Dict[str, Any]):
        """处理轨道取消发布"""
        track_data = data.get('track', {})
        track_name = track_data.get('name')
        track_type = track_data.get('type')
        
        logger.info(f"轨道取消发布: {track_name} ({track_type})")
    
    async def handle_data_received(self, data: Dict[str, Any]):
        """处理数据消息"""
        message_data = data.get('data', {})
        sender = data.get('sender', {})
        content = message_data.get('content', '')
        
        logger.info(f"收到数据消息 from {sender.get('identity', 'unknown')}: {content}")
        
        # 使用消息处理器生成回复
        response = await self.message_handler.process_message(content, sender)
        
        if response:
            await self.send_text_message(response)
    
    async def handle_audio_frame(self, data: Dict[str, Any]):
        """处理音频帧"""
        audio_data = data.get('audio_data')
        
        if audio_data:
            self.stats['audio_frames_processed'] += 1
            
            # 使用音频处理器分析音频
            analysis = await self.audio_processor.process_audio_frame(audio_data)
            
            if analysis.get('speech_detected'):
                logger.debug("检测到语音活动")
                
                # 可以在这里添加语音识别或其他处理逻辑
                # 例如：触发语音转文本，然后生成回复
    
    async def handle_ping(self, data: Dict[str, Any]):
        """处理心跳"""
        self.stats['last_heartbeat'] = datetime.now()
        
        # 发送 pong 响应
        pong_message = {
            'type': 'pong',
            'timestamp': int(datetime.now().timestamp())
        }
        
        await self.send_message(pong_message)
    
    async def subscribe_to_track(self, track_data: Dict[str, Any]):
        """订阅轨道"""
        subscribe_message = {
            'type': 'subscribe',
            'track': track_data
        }
        
        await self.send_message(subscribe_message)
        logger.info(f"订阅轨道: {track_data.get('name')}")
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(json.dumps(message))
                self.stats['messages_sent'] += 1
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
    
    async def send_text_message(self, text: str):
        """发送文本消息"""
        message = {
            'type': 'data',
            'data': {
                'content': text,
                'timestamp': int(datetime.now().timestamp())
            }
        }
        
        await self.send_message(message)
        logger.info(f"发送文本消息: {text}")
    
    async def send_heartbeat(self):
        """发送心跳"""
        while self.running and self.room_connected:
            try:
                heartbeat_message = {
                    'type': 'ping',
                    'timestamp': int(datetime.now().timestamp()),
                    'stats': {
                        'messages_sent': self.stats['messages_sent'],
                        'messages_received': self.stats['messages_received'],
                        'audio_frames_processed': self.stats['audio_frames_processed'],
                        'participants_count': len(self.participants)
                    }
                }
                
                await self.send_message(heartbeat_message)
                logger.debug("发送心跳")
                
                await asyncio.sleep(self.config.HEARTBEAT_INTERVAL)
                
            except Exception as e:
                logger.error(f"发送心跳失败: {e}")
                break
    
    async def message_loop(self):
        """消息循环"""
        try:
            while self.running and self.websocket and not self.websocket.closed:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    await self.handle_message(message)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket 连接已关闭")
                    break
                    
        except Exception as e:
            logger.error(f"消息循环出错: {e}")
        finally:
            self.room_connected = False
    
    async def start(self):
        """启动代理"""
        logger.info("启动改进的本地 LiveKit Python 代理...")
        
        # 验证配置
        if not self.config.validate():
            logger.error("配置验证失败")
            return False
        
        self.running = True
        
        # 重连循环
        reconnect_attempts = 0
        
        while self.running and reconnect_attempts < self.config.MAX_RECONNECT_ATTEMPTS:
            try:
                # 连接到房间
                if await self.connect_to_room():
                    reconnect_attempts = 0  # 重置重连计数
                    
                    # 启动任务
                    tasks = [
                        asyncio.create_task(self.message_loop()),
                        asyncio.create_task(self.send_heartbeat())
                    ]
                    
                    # 等待任务完成
                    done, pending = await asyncio.wait(
                        tasks, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 取消未完成的任务
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                
                # 如果连接失败或断开，尝试重连
                if self.running:
                    reconnect_attempts += 1
                    logger.warning(f"连接断开，{self.config.RECONNECT_DELAY}秒后重连 (尝试 {reconnect_attempts}/{self.config.MAX_RECONNECT_ATTEMPTS})")
                    await asyncio.sleep(self.config.RECONNECT_DELAY)
                
            except Exception as e:
                logger.error(f"代理运行出错: {e}")
                reconnect_attempts += 1
                if reconnect_attempts < self.config.MAX_RECONNECT_ATTEMPTS:
                    await asyncio.sleep(self.config.RECONNECT_DELAY)
        
        if reconnect_attempts >= self.config.MAX_RECONNECT_ATTEMPTS:
            logger.error("达到最大重连次数，停止代理")
        
        return True
    
    async def stop(self):
        """停止代理"""
        logger.info("正在停止代理...")
        self.running = False
        self.room_connected = False
        
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"关闭 WebSocket 连接时出错: {e}")
        
        logger.info("代理已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'participants_count': len(self.participants),
            'room_connected': self.room_connected,
            'running': self.running
        }

# 主函数
async def main():
    """主函数"""
    agent = ImprovedLocalAgent()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭代理...")
        asyncio.create_task(agent.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("收到键盘中断")
    except Exception as e:
        logger.error(f"代理异常退出: {e}")
    finally:
        await agent.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)