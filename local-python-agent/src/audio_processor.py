#!/usr/bin/env python3
"""
本地音频处理模块
提供简单的音频分析和处理功能
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioProcessor:
    """本地音频处理器"""
    
    def __init__(self):
        self.is_processing = False
        self.sample_rate = 16000  # 16kHz
        self.chunk_size = 1024
        self.callbacks = []
        
        logger.info("音频处理器初始化完成")

    def add_callback(self, callback: Callable[[dict], None]):
        """添加音频处理结果回调"""
        self.callbacks.append(callback)

    async def process_audio_chunk(self, audio_data: bytes) -> dict:
        """处理音频块"""
        try:
            # 模拟音频处理
            await asyncio.sleep(0.01)  # 模拟处理时间
            
            # 简单的音频分析
            result = {
                'timestamp': datetime.now().isoformat(),
                'data_size': len(audio_data),
                'processed': True,
                'analysis': {
                    'volume_level': self._calculate_volume(audio_data),
                    'has_speech': self._detect_speech(audio_data),
                    'duration_ms': len(audio_data) / (self.sample_rate * 2) * 1000  # 假设16位音频
                }
            }
            
            # 调用回调函数
            for callback in self.callbacks:
                try:
                    await callback(result)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"音频处理失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'processed': False,
                'error': str(e)
            }

    def _calculate_volume(self, audio_data: bytes) -> float:
        """计算音频音量"""
        try:
            # 简单的音量计算
            if len(audio_data) == 0:
                return 0.0
            
            # 模拟音量计算
            volume = min(len(audio_data) / 1000.0, 1.0)
            return round(volume, 2)
            
        except Exception:
            return 0.0

    def _detect_speech(self, audio_data: bytes) -> bool:
        """检测是否包含语音"""
        try:
            # 简单的语音检测逻辑
            # 实际应用中可以使用更复杂的算法
            return len(audio_data) > 100  # 简单判断
            
        except Exception:
            return False

    async def start_processing(self):
        """开始音频处理"""
        if self.is_processing:
            logger.warning("音频处理器已在运行")
            return
        
        self.is_processing = True
        logger.info("音频处理器已启动")

    async def stop_processing(self):
        """停止音频处理"""
        if not self.is_processing:
            return
        
        self.is_processing = False
        logger.info("音频处理器已停止")

class SimpleVoiceActivityDetector:
    """简单的语音活动检测器"""
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.is_speaking = False
        
    def detect(self, volume: float) -> bool:
        """检测是否在说话"""
        was_speaking = self.is_speaking
        self.is_speaking = volume > self.threshold
        
        # 状态变化时记录日志
        if was_speaking != self.is_speaking:
            status = "开始说话" if self.is_speaking else "停止说话"
            logger.info(f"语音活动检测: {status} (音量: {volume})")
        
        return self.is_speaking

class MessageHandler:
    """消息处理器"""
    
    def __init__(self):
        self.message_history = []
        self.max_history = 100
        
    async def handle_text_message(self, message: str, sender: str) -> str:
        """处理文本消息"""
        # 记录消息历史
        self.message_history.append({
            'message': message,
            'sender': sender,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持历史记录在限制范围内
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # 简单的回复逻辑
        response = await self._generate_response(message, sender)
        
        logger.info(f"处理消息 - 发送者: {sender}, 消息: {message}, 回复: {response}")
        
        return response

    async def _generate_response(self, message: str, sender: str) -> str:
        """生成回复"""
        message_lower = message.lower().strip()
        
        # 简单的关键词匹配回复
        if any(word in message_lower for word in ['你好', 'hello', 'hi']):
            return f"你好 {sender}！我是本地代理，很高兴见到你！"
        
        elif any(word in message_lower for word in ['时间', 'time']):
            return f"现在时间是 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif any(word in message_lower for word in ['帮助', 'help']):
            return "我是本地 LiveKit 代理，可以处理音频和文本消息。试试说 '你好' 或询问时间！"
        
        elif any(word in message_lower for word in ['再见', 'bye', 'goodbye']):
            return f"再见 {sender}！期待下次见面！"
        
        else:
            return f"收到你的消息：{message}。我是本地代理，正在学习如何更好地回复！"

    def get_message_history(self, limit: int = 10) -> list:
        """获取消息历史"""
        return self.message_history[-limit:] if self.message_history else []