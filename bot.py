import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# ================= CONFIG =================
# Heroku environment variables se load kar rahe hain
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_API_ID = os.environ.get("BOT_API_ID")
BOT_API_HASH = os.environ.get("BOT_API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")

# Safety check
if not BOT_TOKEN or not BOT_API_ID or not BOT_API_HASH or not STRING_SESSION:
    raise Exception("❌ One or more environment variables are missing! Check BOT_TOKEN, BOT_API_ID, BOT_API_HASH, STRING_SESSION")

BOT_API_ID = int(BOT_API_ID)
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
    except (IndexError, ValueError):
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
        else:
            await message.reply("❌ Please send a valid number for starting message ID.")

@bot.on_message(filters.command("to") & filters.private)
async def set_destination(_, message):
    try:
        dest_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("❌ Usage: /to <destination_id>")
    if "from" not in DATA or DATA.get("start_id") is None:
        return await message.reply("❌ Please set source and start ID first using /from and message ID.")
    DATA["to"] = dest_id
    await message.reply("🚀 Forwarding started...")
    asyncio.create_task(forward_media(_, message))

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
        except Exception as e:
            print(f"⚠ Skipping message {msg_id}: {e}")
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

if __name__ == "__main__":
    asyncio.run(main())
