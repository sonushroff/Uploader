Careerwill lecture EXTRACTOR 
TELEGRAM BOT
SEND m3u8 URL TO bot and see magic



import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "Your bot token"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send m3u8 URL bro 🔥")

async def handle_m3u8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if ".m3u8" not in url:
        await update.message.reply_text("Bhai ye m3u8 nahi hai 💀")
        return

    await update.message.reply_text("Converting… wait kr lulle 😎🔥")

    output = "lecture.mp4"
    cmd = [
        "ffmpeg",
        "-i", url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output
    ]

    subprocess.run(cmd)

    if not os.path.exists(output):
        await update.message.reply_text("FFmpeg ne phir tatti kar di 😭💀")
        return

    await update.message.reply_video(video=open(output, "rb"))
    os.remove(output)

# ↓↓↓ DON’T use asyncio.run() anymore ↓↓↓
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_m3u8))

    app.run_polling()
