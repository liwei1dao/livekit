#!/usr/bin/env python3
"""
本地代理配置文件
"""

import os
from typing import Dict, Any

class Config:
    """配置类"""
    
    # LiveKit 连接配置
    LIVEKIT_URL = os.getenv('LIVEKIT_URL', 'ws://livekit:7880')
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY', 'APIcyMmEUQTDGnS')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET', 'EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc')
    
    # 房间配置
    DEFAULT_ROOM_NAME = os.getenv('ROOM_NAME', 'test-room')
    PARTICIPANT_NAME = os.getenv('PARTICIPANT_NAME', 'local-agent')
    
    # 音频配置
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))
    AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', '1024'))
    
    # 语音活动检测配置
    VAD_THRESHOLD = float(os.getenv('VAD_THRESHOLD', '0.3'))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # 心跳配置
    HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', '30'))
    
    # 重连配置
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '5'))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', '10'))
    
    # 消息历史配置
    MAX_MESSAGE_HISTORY = int(os.getenv('MAX_MESSAGE_HISTORY', '100'))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'livekit_url': cls.LIVEKIT_URL,
            'livekit_api_key': cls.LIVEKIT_API_KEY[:10] + '...',  # 隐藏敏感信息
            'default_room_name': cls.DEFAULT_ROOM_NAME,
            'participant_name': cls.PARTICIPANT_NAME,
            'audio_sample_rate': cls.AUDIO_SAMPLE_RATE,
            'audio_chunk_size': cls.AUDIO_CHUNK_SIZE,
            'vad_threshold': cls.VAD_THRESHOLD,
            'log_level': cls.LOG_LEVEL,
            'heartbeat_interval': cls.HEARTBEAT_INTERVAL,
            'reconnect_delay': cls.RECONNECT_DELAY,
            'max_reconnect_attempts': cls.MAX_RECONNECT_ATTEMPTS,
            'max_message_history': cls.MAX_MESSAGE_HISTORY,
        }
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置"""
        required_fields = [
            cls.LIVEKIT_URL,
            cls.LIVEKIT_API_KEY,
            cls.LIVEKIT_API_SECRET,
            cls.DEFAULT_ROOM_NAME,
            cls.PARTICIPANT_NAME
        ]
        
        for field in required_fields:
            if not field or field.strip() == '':
                return False
        
        return True