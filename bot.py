from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, FloodWait
from pyrogram.types import Message
import asyncio
import os

BOT_API_ID = int(os.environ.get("BOT_API_ID"))
BOT_API_HASH = os.environ.get("BOT_API_HASH")

bot = Client(
    "master_bot",
    api_id=BOT_API_ID,
    api_hash=BOT_API_HASH
)

USERS = {}

# ================= LOGIN FLOW =================

@bot.on_message(filters.command("login") & filters.private)
async def login_start(_, message: Message):
    uid = message.from_user.id
    USERS[uid] = {"step": "api_id"}
    await message.reply("🔐 Login started\n\n📌 Send your API ID")

@bot.on_message(filters.private & filters.text)
async def login_steps(_, message: Message):
    uid = message.from_user.id
    if uid not in USERS:
        return

    user = USERS[uid]

    if user["step"] == "api_id":
        if message.text.isdigit():
            user["api_id"] = int(message.text)
            user["step"] = "api_hash"
            await message.reply("✅ API ID saved\n\n📌 Send API HASH")
        return

    if user["step"] == "api_hash":
        user["api_hash"] = message.text.strip()
        user["step"] = "phone"
        await message.reply("✅ API HASH saved\n\n📞 Send phone number (+91...)")
        return

    if user["step"] == "phone":
        user["phone"] = message.text.strip()
        user["client"] = Client(
            f"user_{uid}",
            api_id=user["api_id"],
            api_hash=user["api_hash"],
            in_memory=True
        )
        await user["client"].connect()
        await user["client"].send_code(user["phone"])
        user["step"] = "otp"
        await message.reply("📨 OTP sent\n\n📌 Send OTP")
        return

    if user["step"] == "otp":
        try:
            await user["client"].sign_in(
                phone_number=user["phone"],
                phone_code=message.text.strip()
            )
            await login_success(uid, message)
        except SessionPasswordNeeded:
            user["step"] = "2fa"
            await message.reply("🔐 2FA enabled\n\nSend your password")
        return

    if user["step"] == "2fa":
        await user["client"].check_password(message.text.strip())
        await login_success(uid, message)

async def login_success(uid, message):
    user = USERS[uid]
    user["string"] = await user["client"].export_session_string()
    await user["client"].disconnect()

    user["userbot"] = Client(
        f"active_{uid}",
        api_id=user["api_id"],
        api_hash=user["api_hash"],
        session_string=user["string"]
    )
    await user["userbot"].start()

    user["step"] = "logged"
    await message.reply(
        "✅ **LOGIN SUCCESSFUL 🎉**\n\n"
        "🔓 Userbot activated\n"
        "Now use /from command"
    )

# ================= FORWARD FLOW =================

@bot.on_message(filters.command("from") & filters.private)
async def set_source(_, message: Message):
    uid = message.from_user.id
    if uid not in USERS or USERS[uid].get("step") != "logged":
        return await message.reply("❌ Please /login first")

    USERS[uid]["from"] = int(message.command[1])
    USERS[uid]["start_id"] = None
    await message.reply("✅ Source set\n\nSend starting MEDIA message ID")

@bot.on_message(filters.private & filters.text)
async def set_start_id(_, message: Message):
    uid = message.from_user.id
    if uid in USERS and USERS[uid].get("from") and USERS[uid].get("start_id") is None:
        if message.text.isdigit():
            USERS[uid]["start_id"] = int(message.text)
            await message.reply("✅ Start ID saved\n\nUse /to -100xxxxxxxxxx")

@bot.on_message(filters.command("to") & filters.private)
async def set_dest(_, message: Message):
    uid = message.from_user.id
    if uid not in USERS:
        return

    USERS[uid]["to"] = int(message.command[1])
    await message.reply("🚀 Forwarding started...")
    await forward_media(uid, message)

async def forward_media(uid, message):
    user = USERS[uid]
    client = user["userbot"]
    src = user["from"]
    dest = user["to"]
    msg_id = user["start_id"]
    count = 0

    while True:
        try:
            msg = await client.get_messages(src, msg_id)
            if not msg:
                break

            if msg.video or msg.document or msg.photo:
                await msg.forward(dest)
                count += 1

            msg_id += 1
            await asyncio.sleep(0.10)

        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            msg_id += 1
            await asyncio.sleep(0.10)

    await message.reply(f"✅ Done\nTotal media forwarded: {count}")

# ================= RUN =================
bot.run()
