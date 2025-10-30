#!/usr/bin/env python3
"""
使用 LiveKit 官方 SDK 的简单代理
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAgent(Agent):
    """简单的 LiveKit 代理"""
    
    def __init__(self):
        super().__init__(
            instructions="你是一个简单的测试代理，用于验证 LiveKit 连接。"
        )
        logger.info("SimpleAgent 初始化完成")

def prewarm(proc: JobProcess):
    """预热函数"""
    logger.info("代理预热中...")
    # 这里可以预加载模型或其他资源

async def entrypoint(ctx: JobContext):
    """代理入口点"""
    logger.info(f"代理启动，房间: {ctx.room.name}")
    
    # 设置日志上下文
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # 创建一个最简单的会话，不使用 STT/TTS/LLM
    session = AgentSession()
    
    # 启动会话
    await session.start(
        agent=SimpleAgent(),
        room=ctx.room,
    )
    
    logger.info("代理会话已启动，正在连接到房间...")
    
    # 连接到房间
    await ctx.connect()
    
    logger.info("代理已成功连接到房间")

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault("LIVEKIT_URL", "ws://livekit:7880")
    os.environ.setdefault("LIVEKIT_API_KEY", "APIcyMmEUQTDGnS")
    os.environ.setdefault("LIVEKIT_API_SECRET", "EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc")
    
    logger.info("启动 LiveKit SDK 代理...")
    
    try:
        # 直接使用 CLI 运行
        cli.run_app(WorkerOptions(
            entrypoint_fnc=entrypoint, 
            prewarm_fnc=prewarm
        ))
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在停止...")
    except Exception as e:
        logger.error(f"代理运行时出错: {e}")
        sys.exit(1)