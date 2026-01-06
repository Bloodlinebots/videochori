from pyrogram import Client, filters
from pyrogram.errors import FloodWait
import asyncio
import os

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Control bot token
BOT_API_ID = int(os.environ.get("BOT_API_ID"))
BOT_API_HASH = os.environ.get("BOT_API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")  # Userbot string session
# =========================================

# BOT client (control bot)
bot = Client(
    "control_bot",
    bot_token=BOT_TOKEN,
    api_id=BOT_API_ID,
    api_hash=BOT_API_HASH
)

# USERBOT client (forward engine)
userbot = Client(
    "userbot",
    session_string=STRING_SESSION,
    api_id=BOT_API_ID,
    api_hash=BOT_API_HASH
)

# STORE FLOW DATA
DATA = {}

# ================= FORWARD FLOW =================
@bot.on_message(filters.command("from") & filters.private)
async def set_source(_, message):
    try:
        src_id = int(message.command[1])
    except:
        return await message.reply("❌ Usage: /from <channel_id>")
    DATA["from"] = src_id
    DATA["start_id"] = None
    await message.reply("✅ Source set. Send starting media message ID:")

@bot.on_message(filters.private & filters.text)
async def set_start_id(_, message):
    if "from" in DATA and DATA.get("start_id") is None:
        if message.text.isdigit():
            DATA["start_id"] = int(message.text)
            await message.reply("✅ Start ID saved. Send /to <destination_id>")

@bot.on_message(filters.command("to") & filters.private)
async def set_destination(_, message):
    try:
        dest_id = int(message.command[1])
    except:
        return await message.reply("❌ Usage: /to <destination_id>")
    DATA["to"] = dest_id
    await message.reply("🚀 Forwarding started...")
    await forward_media(_, message)

async def forward_media(_, message):
    client = userbot
    src = DATA["from"]
    dest = DATA["to"]
    msg_id = DATA["start_id"]
    count = 0

    while True:
        try:
            msg = await client.get_messages(src, msg_id)
            if not msg:
                break

            if msg.media:
                await msg.forward(dest)
                count += 1

            msg_id += 1
            await asyncio.sleep(0.10)  # anti-spam

        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            msg_id += 1
            await asyncio.sleep(0.10)

    await message.reply(f"✅ Done!\nTotal media forwarded: {count}")

# ================= RUN =================
async def main():
    await userbot.start()
    await bot.start()
    print("🔥 Bot is running...")
    await bot.idle()
    await userbot.stop()

import asyncio
asyncio.run(main())
