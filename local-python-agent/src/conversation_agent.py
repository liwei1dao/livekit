#!/usr/bin/env python3
"""
LiveKit AI对话代理
支持语音识别、AI对话和语音合成的完整对话系统
"""

import asyncio
import logging
import os
import sys
from typing import Annotated

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    stt,
    tts,
    vad,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationAgent:
    """AI对话代理类"""
    
    def __init__(self):
        self.setup_ai_services()
    
    def setup_ai_services(self):
        """设置AI服务组件"""
        # 语音转文字 (STT) - 使用Deepgram
        self.stt_service = deepgram.STT(
            model="nova-2-general",
            language="zh-CN",  # 支持中文
            smart_format=True,
        )
        
        # 大语言模型 (LLM) - 使用OpenAI
        self.llm_service = openai.LLM(
            model="gpt-3.5-turbo",
            temperature=0.7,
        )
        
        # 文字转语音 (TTS) - 使用OpenAI TTS
        self.tts_service = openai.TTS(
            model="tts-1",
            voice="alloy",
        )
        
        # 语音活动检测 (VAD) - 使用Silero
        self.vad_service = silero.VAD.load()
        
        logger.info("AI服务组件初始化完成")

async def entrypoint(ctx: JobContext):
    """代理入口点"""
    logger.info(f"连接到房间: {ctx.room.name}")
    
    # 创建对话代理实例
    conversation_agent = ConversationAgent()
    
    # 等待参与者加入
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # 创建语音管道代理
    agent = VoicePipelineAgent(
        vad=conversation_agent.vad_service,
        stt=conversation_agent.stt_service,
        llm=conversation_agent.llm_service,
        tts=conversation_agent.tts_service,
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=(
                "你是一个友好的AI助手。请用简洁、自然的方式与用户对话。"
                "你可以回答问题、进行闲聊，并提供帮助。"
                "请保持对话轻松愉快。"
            ),
        ),
    )
    
    # 启动代理
    agent.start(ctx.room)
    
    # 监听房间事件
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"参与者加入: {participant.identity}")
    
    @ctx.room.on("participant_disconnected") 
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"参与者离开: {participant.identity}")
    
    # 保持代理运行
    await agent.say("你好！我是你的AI助手，有什么可以帮助你的吗？", allow_interruptions=True)

async def prewarm(ctx: JobContext):
    """预热函数 - 预加载模型"""
    logger.info("预热AI模型...")
    
    # 预加载VAD模型
    await silero.VAD.load()
    
    logger.info("AI模型预热完成")

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("LIVEKIT_URL", "ws://livekit:7880")
    os.environ.setdefault("LIVEKIT_API_KEY", "APIcyMmEUQTDGnS")
    os.environ.setdefault("LIVEKIT_API_SECRET", "EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc")
    
    # 设置AI服务的API密钥（需要用户提供）
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("未设置OPENAI_API_KEY环境变量，OpenAI服务将无法使用")
    
    if not os.getenv("DEEPGRAM_API_KEY"):
        logger.warning("未设置DEEPGRAM_API_KEY环境变量，Deepgram STT将无法使用")
    
    logger.info("启动AI对话代理...")
    
    try:
        # 运行代理
        cli.run_app(WorkerOptions(
            entrypoint_fnc=entrypoint, 
            prewarm_fnc=prewarm
        ))
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在停止...")
    except Exception as e:
        logger.error(f"代理运行时出错: {e}")
        sys.exit(1)