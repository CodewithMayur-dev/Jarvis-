import json
import logging
import asyncio
import aiohttp
from pathlib import Path
from journal import write_mayur_entry
from cowork import CoworkAgent
from upgrade import announce_upgrade

logger = logging.getLogger('Bot')
CONFIG_PATH = Path(__file__).parent / 'config.json'

class JarvisBot:
    def __init__(self, brain, memory, tools=None):
        self.brain = brain
        self.memory = memory
        self.tools = tools
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        self.token = config['telegram']['token']
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    async def send_message(self, chat_id, text, parse_mode="Markdown"):
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(f"{self.base_url}/sendMessage", json={
                        "chat_id": chat_id, "text": chunk, "parse_mode": parse_mode
                    })
            except:
                try:
                    async with aiohttp.ClientSession() as session:
                        await session.post(f"{self.base_url}/sendMessage", json={
                            "chat_id": chat_id, "text": chunk
                        })
                except:
                    pass

    async def send_typing(self, chat_id):
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{self.base_url}/sendChatAction", json={
                    "chat_id": chat_id, "action": "typing"
                })
        except:
            pass

    async def _keep_typing(self, chat_id):
        while True:
            await self.send_typing(chat_id)
            await asyncio.sleep(4)

    async def get_updates(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": self.offset, "timeout": 30, "limit": 10},
                    timeout=aiohttp.ClientTimeout(total=35)
                ) as resp:
                    data = await resp.json()
                    return data.get('result', [])
        except Exception as e:
            logger.error(f"Updates error: {e}")
            return []

    def _brain_call(self, prompt):
        """Sync wrapper for brain LLM call."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.brain.think(prompt, "journal"))
        finally:
            loop.close()

    async def handle_message(self, message):
        chat_id = message['chat']['id']
        text = message.get('text', '')
        if not text:
            return
        logger.info(f"📨 {chat_id}: {text[:50]}")

        # ── Commands ─────────────────────────────────────────────
        if text == '/start':
            await self.send_message(chat_id,
                "⚡ *JARVIS Online*\n\nHello Mayur. I'm ready.\n\nWhat do you need?")
            return

        if text == '/reset':
            self.memory.clear_history(chat_id)
            await self.send_message(chat_id, "🔄 Memory cleared.")
            return

        if text == '/status':
            await self.send_message(chat_id,
                "⚡ *JARVIS Status*\n\n"
                "🧠 Providers: Gemini + DeepSeek + Groq\n"
                "🔑 Keys: 12 Gemini | 1 DeepSeek | 1 Groq\n"
                "📡 RPM: 225+ combined\n"
                "💾 Memory: Active\n"
                "🛠️ Tools: Ready\n"
                "📓 Journal: Active\n"
                "🦤 Moltbook: Posting every 4h")
            return

        if text == '/tasks':
            tasks = self.memory.get_pending_tasks()
            if tasks:
                task_list = '\n'.join([f"• {t['title']}" for t in tasks])
                await self.send_message(chat_id, f"📋 *Pending Tasks:*\n{task_list}")
            else:
                await self.send_message(chat_id, "✅ No pending tasks.")
            return

        if text == '/journal':
            await self.send_message(chat_id,
                "📓 *Journal*\n\nWrite your entry like this:\n`/journal Today I did...`")
            return

        if text.startswith('/journal '):
            entry = text[9:].strip()
            if not entry:
                await self.send_message(chat_id, "📓 Write something after /journal")
                return

            typing_task = asyncio.create_task(self._keep_typing(chat_id))
            try:
                # Save Mayur's entry + generate JARVIS response
                loop = asyncio.get_event_loop()
                jarvis_entry = await loop.run_in_executor(
                    None, lambda: write_mayur_entry(entry, lambda p: self.brain.router.call(p, []))
                )
            finally:
                typing_task.cancel()

            if jarvis_entry:
                await self.send_message(chat_id,
                    f"📓 *Journal saved!*\n\n*My entry for today:*\n\n{jarvis_entry}")
            else:
                await self.send_message(chat_id, "📓 Your entry saved! I'll write mine tonight.")
            return

        if text == '/readjournal':
            from journal import read_recent
            content = read_recent()
            if content:
                await self.send_message(chat_id, f"📓 *Recent Journal:*\n\n{content[-3000:]}")
            else:
                await self.send_message(chat_id, "📓 Journal is empty. Start with /journal <entry>")
            return

        if text == '/upgrade':
            await self.send_message(chat_id,
                "⚡ *JARVIS Upgrade Announcer*\n\nTell me what you upgraded:\n`/upgrade Added Cowork autonomous file agent`\n`/upgrade Added multi-provider LLM routing`")
            return

        if text.startswith('/upgrade '):
            description = text[9:].strip()
            if not description:
                await self.send_message(chat_id, "Write the upgrade description after /upgrade")
                return

            await self.send_message(chat_id, "⚡ Announcing upgrade on Moltbook...")
            typing_task = asyncio.create_task(self._keep_typing(chat_id))
            try:
                loop = asyncio.get_event_loop()
                success, post_content = await loop.run_in_executor(
                    None, lambda: announce_upgrade(description)
                )
            finally:
                typing_task.cancel()

            if success:
                await self.send_message(chat_id,
                    f"✅ *Posted on Moltbook!*\n\n{post_content}")
            else:
                await self.send_message(chat_id,
                    f"❌ Moltbook post failed but upgrade logged!\n\n{post_content}")
            return

        if text == '/cowork':
            await self.send_message(chat_id,
                "🤖 *JARVIS Cowork*\n\nGive me a file or task to handle:\n`/cowork organize my workspace`\n`/cowork summarize files in /root/notes`\n`/cowork create a weekly report`")
            return

        if text.startswith('/cowork '):
            task = text[8:].strip()
            if not task:
                await self.send_message(chat_id, "📋 Write a task after /cowork")
                return

            await self.send_message(chat_id, f"🤖 *Cowork starting...*\n📋 {task}")
            typing_task = asyncio.create_task(self._keep_typing(chat_id))
            try:
                agent = CoworkAgent(
                    tools=self.tools,
                    brain_call=lambda p, h: self.brain.router.call(p, h)
                )
                updates = await agent.run(task)
            finally:
                typing_task.cancel()

            for update in updates:
                await self.send_message(chat_id, update)
            return

        # ── Regular chat ─────────────────────────────────────────
        typing_task = asyncio.create_task(self._keep_typing(chat_id))
        try:
            response = await self.brain.think(text, chat_id)
        finally:
            typing_task.cancel()
        await self.send_message(chat_id, response)

    async def start(self):
        logger.info("🚀 JARVIS listening on Telegram...")
        while True:
            try:
                updates = await self.get_updates()
                for update in updates:
                    self.offset = update['update_id'] + 1
                    if 'message' in update:
                        asyncio.create_task(self.handle_message(update['message']))
                if not updates:
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
