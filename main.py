#!/usr/bin/env python3
import asyncio
import logging
from bot import JarvisBot
from memory import Memory
from brain import Brain
from tools import Tools

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('JARVIS')

async def main():
    print("""
    ⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
    
       J.A.R.V.I.S  ONLINE
    Just A Rather Very Intelligent System
         Built by Mayur Anand Shah
         
    ⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
    """)
    memory = Memory()
    tools = Tools()
    brain = Brain(memory=memory, tools=tools)
    bot = JarvisBot(brain=brain, memory=memory, tools=tools)
    logger.info("✅ All systems ready")
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ JARVIS shutting down...")
