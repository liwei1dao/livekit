#!/usr/bin/env python3
import asyncio
import websockets
import logging
import jwt
import time
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_access_token():
    """生成代理访问令牌"""
    api_key = os.getenv('LIVEKIT_API_KEY', 'APIcyMmEUQTDGnS')
    api_secret = os.getenv('LIVEKIT_API_SECRET', 'EfnCKnGxm8dyz8x7kia5UoP8coukwGmoVemUrBSiRBc')
    
    # JWT 载荷
    payload = {
        'iss': api_key,
        'sub': 'test-agent',
        'iat': int(time.time()),
        'exp': int(time.time()) + 21600,  # 6小时
        'video': {'agent': True}
    }
    
    # 生成 JWT 令牌
    token = jwt.encode(payload, api_secret, algorithm='HS256')
    logger.info(f"代理访问令牌生成成功 - API Key: {api_key[:8]}...")
    return token

async def test_websocket_connection():
    """测试 WebSocket 连接"""
    url = "ws://livekit:7880/agent"
    token = generate_access_token()
    
    while True:
        try:
            logger.info("测试带令牌的 WebSocket 连接...")
            logger.info(f"连接到: {url}?access_token=...")
            
            # 尝试连接，将令牌作为查询参数
            async with websockets.connect(f"{url}?access_token={token}") as websocket:
                logger.info("WebSocket 连接成功！")
                
                # 发送一个测试消息
                await websocket.send("Hello LiveKit!")
                logger.info("测试消息已发送")
                
                # 等待响应
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"收到响应: {response}")
                except asyncio.TimeoutError:
                    logger.info("没有收到响应（超时）")
                
                # 保持连接一段时间
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"连接失败: {e}")
            logger.error(f"错误类型: {type(e)}")
            
        # 等待后重试
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())