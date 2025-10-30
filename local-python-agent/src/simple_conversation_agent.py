#!/usr/bin/env python3
"""
简化版AI对话代理
使用免费的本地服务，无需外部API密钥
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
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import silero

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleLLM(llm.LLM):
    """简单的本地LLM实现"""
    
    def __init__(self):
        super().__init__()
    
    async def agenerate(
        self,
        *,
        chat_ctx: llm.ChatContext,
        fnc_ctx: llm.FunctionContext | None = None,
        temperature: float | None = None,
        n: int | None = None,
    ) -> llm.LLMStream:
        """生成回复"""
        # 获取最后一条用户消息
        user_message = ""
        for msg in chat_ctx.messages:
            if msg.role == "user":
                user_message = msg.content
        
        # 简单的回复逻辑
        response = self._generate_simple_response(user_message)
        
        # 创建流式响应
        stream = llm.LLMStream(
            llm=self,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
        )
        
        # 模拟流式输出
        asyncio.create_task(self._stream_response(stream, response))
        
        return stream
    
    def _generate_simple_response(self, user_input: str) -> str:
        """生成简单回复"""
        user_input = user_input.lower().strip()
        
        # 简单的关键词匹配回复
        if "你好" in user_input or "hello" in user_input:
            return "你好！很高兴见到你！有什么可以帮助你的吗？"
        elif "再见" in user_input or "bye" in user_input:
            return "再见！祝你有美好的一天！"
        elif "谢谢" in user_input or "thank" in user_input:
            return "不客气！很高兴能帮助你。"
        elif "天气" in user_input:
            return "我无法获取实时天气信息，建议你查看天气应用或网站。"
        elif "时间" in user_input:
            return "我无法获取当前时间，请查看你的设备时钟。"
        elif "名字" in user_input or "name" in user_input:
            return "我是你的AI助手，你可以叫我小助手。"
        elif "帮助" in user_input or "help" in user_input:
            return "我可以和你聊天，回答简单的问题。试试问我关于天气、时间或者和我打招呼吧！"
        else:
            return f"我听到你说：{user_input}。这很有趣！还有什么想聊的吗？"
    
    async def _stream_response(self, stream: llm.LLMStream, response: str):
        """模拟流式响应"""
        try:
            # 模拟逐字输出
            for i, char in enumerate(response):
                chunk = llm.ChatChunk(
                    choices=[
                        llm.Choice(
                            delta=llm.ChoiceDelta(content=char),
                            index=0,
                        )
                    ]
                )
                stream._event_ch.send_nowait(chunk)
                await asyncio.sleep(0.05)  # 模拟延迟
            
            # 发送结束信号
            stream._event_ch.send_nowait(None)
        except Exception as e:
            logger.error(f"流式响应出错: {e}")
            stream._event_ch.send_nowait(None)

class SimpleConversationAgent:
    """简化版AI对话代理类"""
    
    def __init__(self):
        self.setup_ai_services()
    
    def setup_ai_services(self):
        """设置AI服务组件"""
        # 语音活动检测 (VAD) - 使用Silero (免费)
        self.vad_service = silero.VAD.load()
        
        # 语音转文字 (STT) - 使用Silero (免费)
        self.stt_service = silero.STT()
        
        # 大语言模型 (LLM) - 使用简单本地实现
        self.llm_service = SimpleLLM()
        
        # 文字转语音 (TTS) - 使用Silero (免费)
        self.tts_service = silero.TTS()
        
        logger.info("简化版AI服务组件初始化完成")

async def entrypoint(ctx: JobContext):
    """代理入口点"""
    logger.info(f"连接到房间: {ctx.room.name}")
    
    # 创建对话代理实例
    conversation_agent = SimpleConversationAgent()
    
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
                "你可以回答简单问题、进行闲聊，并提供帮助。"
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
    
    logger.info("启动简化版AI对话代理...")
    
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