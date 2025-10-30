#!/usr/bin/env python3
"""
本地 LiveKit Python 代理启动脚本
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from local_agent import LocalLiveKitAgent
from config import Config

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AgentRunner:
    """代理运行器"""
    
    def __init__(self):
        self.agent = None
        self.running = False
    
    async def start(self):
        """启动代理"""
        logger.info("正在启动本地 LiveKit Python 代理...")
        
        # 验证配置
        if not Config.validate():
            logger.error("配置验证失败，请检查环境变量")
            return False
        
        # 显示配置信息
        logger.info("配置信息:")
        for key, value in Config.to_dict().items():
            logger.info(f"  {key}: {value}")
        
        try:
            # 创建代理实例
            self.agent = LocalLiveKitAgent()
            
            # 设置信号处理
            self.setup_signal_handlers()
            
            # 启动代理
            self.running = True
            await self.agent.start()
            
            return True
            
        except Exception as e:
            logger.error(f"启动代理失败: {e}")
            return False
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在关闭代理...")
            self.running = False
            if self.agent:
                asyncio.create_task(self.agent.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """运行代理"""
        if await self.start():
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到键盘中断，正在关闭...")
            finally:
                if self.agent:
                    await self.agent.stop()
                logger.info("代理已关闭")
        else:
            logger.error("代理启动失败")
            sys.exit(1)

async def main():
    """主函数"""
    runner = AgentRunner()
    await runner.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)