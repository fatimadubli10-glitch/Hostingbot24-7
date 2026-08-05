import os
import asyncio

import discord
from discord.ext import commands


def _load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    _load_env_file()

token = os.getenv("tokenbro")
guildid = int(os.getenv("guildid"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

async def load_extensions():
    for file in os.listdir("commands"):
        if file.endswith(".py"):
            await bot.load_extension(f"commands.{file[:-3]}")
            print(f"Loaded {file}")

@bot.event
async def on_ready():
    guild = discord.Object(id=guildid)

    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} guild slash commands.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    print(f"Logged in as {bot.user} ({bot.user.id})")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())