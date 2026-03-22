#!/usr/bin/env python3
"""
JARVIS Cowork — Simple agentic file & task automation
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger("Cowork")

COWORK_SYSTEM = """You are JARVIS Cowork — an autonomous file and task manager for Mayur.
You have been given real file information. Use it to complete the task accurately.
Do NOT make up file names or contents. Only describe what you actually see.
Be specific, practical, and helpful."""


class CoworkAgent:
    def __init__(self, tools, brain_call):
        self.tools = tools
        self.brain_call = brain_call

    async def _list_files(self, path):
        try:
            p = Path(path)
            if not p.exists():
                return f"Path does not exist: {path}"
            if p.is_file():
                return f"File: {path}"
            files = []
            for f in sorted(p.iterdir()):
                if f.is_file():
                    files.append(f"  📄 {f.name} ({f.stat().st_size} bytes)")
                else:
                    files.append(f"  📁 {f.name}/")
            return "\n".join(files) if files else "Empty directory"
        except Exception as e:
            return f"Error: {e}"

    async def _read_file(self, path):
        try:
            content = Path(path).read_text(errors="replace")
            return content[:1000]
        except Exception as e:
            return f"Error reading {path}: {e}"

    async def run(self, task):
        updates = []
        updates.append(f"🤖 **JARVIS Cowork**\n📋 {task}\n\n⚙️ Working...")

        # Detect relevant paths from task
        paths = re.findall(r"/[\w/.-]+", task)
        if not paths:
            paths = ["/root/jarvis", "/root/jarvis-workspace"]

        # Actually gather real file info
        file_info = ""
        for path in paths[:3]:
            listing = await self._list_files(path)
            file_info += f"\n📁 {path}:\n{listing}\n"

        updates.append(f"**Files found:**\n{file_info[:800]}")

        # If task involves reading files, read them
        all_files = []
        for path in paths[:2]:
            p = Path(path)
            if p.is_dir():
                for f in sorted(p.iterdir()):
                    if f.is_file() and f.suffix in [".py", ".json", ".md", ".txt", ".sh"]:
                        all_files.append(str(f))

        file_contents = ""
        for fpath in all_files[:6]:
            content = await self._read_file(fpath)
            file_contents += f"\n--- {fpath} ---\n{content[:400]}\n"

        # Now ask LLM with REAL data
        prompt = (
            f"{COWORK_SYSTEM}\n\n"
            f"Task: {task}\n\n"
            f"Real file listing:\n{file_info}\n\n"
            f"Real file contents (first 400 chars each):\n{file_contents}\n\n"
            f"Now complete the task based on the REAL files above. Be specific."
        )

        response = self.brain_call(prompt, [])

        # Execute any tool calls in the response
        tool_pattern = r'<tool>(.*?)</tool><arg>(.*?)</arg>(?:<content>(.*?)</content>)?'
        import re as _re
        matches = _re.findall(tool_pattern, response, _re.DOTALL)
        exec_results = []
        for tool, arg, content_val in matches:
            tool = tool.strip()
            arg = arg.strip()
            if tool == "exec":
                result = await self.tools.execute(arg, timeout=30)
                out = result['stdout'] or result['stderr'] or "(no output)"
                exec_results.append(f"✅ Executed: `{arg[:60]}`\n{out[:300]}")
            elif tool == "write_file":
                success = await self.tools.write_file(arg, content_val)
                exec_results.append(f"✅ Written: `{arg}`" if success else f"❌ Failed: `{arg}`")
            elif tool == "read_file":
                out = await self.tools.read_file(arg)
                exec_results.append(f"📄 `{arg}`:\n{out[:300]}")

        # Clean tool tags from response
        clean = _re.sub(r'<tool>.*?</tool><arg>.*?</arg>(?:<content>.*?</content>)?', '', response, flags=_re.DOTALL).strip()
        updates.append(f"✅ **Result:**\n\n{clean}")
        if exec_results:
            updates.append("⚙️ **Executed:**\n" + "\n\n".join(exec_results))
        return updates
