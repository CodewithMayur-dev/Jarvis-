import asyncio
import logging
import os
import aiohttp

logger = logging.getLogger('Tools')

class Tools:
    def __init__(self):
        self.env = {
            **os.environ,
            'GOG_KEYRING_PASSWORD': os.getenv('GOG_KEYRING_PASSWORD', ''),
            'GOG_ACCOUNT': os.getenv('GOG_ACCOUNT', ''),
            'PATH': '/usr/local/bin:/root/.bun/bin:/usr/bin:/bin:/root/.nvm/versions/node/v22.22.1/bin:/usr/local/sbin:/usr/sbin:/sbin:/data/data/com.termux/files/usr/bin:/system/bin'
        }
        logger.info("🛠️ Tools initialized")

    async def execute(self, command, timeout=60):
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env,
                cwd='/root'
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='replace').strip(),
                'stderr': stderr.decode('utf-8', errors='replace').strip()
            }
        except asyncio.TimeoutError:
            return {'returncode': -1, 'stdout': '', 'stderr': f'Timed out after {timeout}s'}
        except Exception as e:
            return {'returncode': -1, 'stdout': '', 'stderr': str(e)}

    async def read_file(self, path):
        try:
            return open(path).read()
        except Exception as e:
            return f"Error: {e}"

    async def write_file(self, path, content):
        try:
            from pathlib import Path
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return True
        except Exception as e:
            return False

    async def fetch_url(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    return await resp.text()
        except Exception as e:
            return f"Error: {e}"
