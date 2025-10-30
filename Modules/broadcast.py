import os
import requests
import subprocess
from vars import OWNER, CREDIT, AUTH_USERS, TOTAL_USERS
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

def register_broadcast_handlers(bot):
# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
    @bot.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_handler(client: Client, message: Message):
        if message.chat.id != OWNER:
            return
        if not message.reply_to_message:
            await message.reply_text("**Reply to any message (text, photo, video, or file) with /broadcast to send it to all users.**")
            return
        success = 0
        fail = 0
        for user_id in list(set(TOTAL_USERS)):
            try:
                if message.reply_to_message.text:
                    await client.send_message(user_id, message.reply_to_message.text)
                elif message.reply_to_message.photo:
                    await client.send_photo(
                        user_id,
                        photo=message.reply_to_message.photo.file_id,
                        caption=message.reply_to_message.caption or ""
                    )
                elif message.reply_to_message.video:
                    await client.send_video(
                        user_id,
                        video=message.reply_to_message.video.file_id,
                        caption=message.reply_to_message.caption or ""
                    )
                elif message.reply_to_message.document:
                    await client.send_document(
                        user_id,
                        document=message.reply_to_message.document.file_id,
                        caption=message.reply_to_message.caption or ""
                    )
                else:
                    await client.forward_messages(user_id, message.chat.id, message.reply_to_message.message_id)

                success += 1
            except (FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated):
                fail += 1
                continue
            except Exception as e:
                fail += 1
                continue

        await message.reply_text(f"<b>Broadcast complete!</b>\n<blockquote><b>✅ Success: {success}\n❎ Failed: {fail}</b></blockquote>")
  
# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
    @bot.on_message(filters.command("broadusers") & filters.private)
    async def broadusers_handler(client: Client, message: Message):
        if message.chat.id != OWNER:
            return

        if not TOTAL_USERS:
            await message.reply_text("**No Broadcasted User**")
            return
 
        user_infos = []
        for user_id in list(set(TOTAL_USERS)):
            try:
                user = await client.get_users(int(user_id))
                fname = user.first_name if user.first_name else " "
                user_infos.append(f"[{user.id}](tg://openmessage?user_id={user.id}) | `{fname}`")
            except Exception:
                user_infos.append(f"[{user.id}](tg://openmessage?user_id={user.id})")

        total = len(user_infos)
        text = (
            f"<blockquote><b>Total Users: {total}</b></blockquote>\n\n"
            "<b>Users List:</b>\n"
            + "\n".join(user_infos)
        )
        await message.reply_text(text)
    
# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
