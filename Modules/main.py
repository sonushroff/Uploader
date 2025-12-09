# bot.py

import os
import requests
import subprocess

from pyromod import listen  # important: pyrogram me .listen add karta hai
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from vars import API_ID, API_HASH, BOT_TOKEN, CREDIT


# ================== Helper functions =====================

def sanitize_filename(name: str, ext: str) -> str:
    """Safe filename generate kare (special chars hata ke)."""
    base = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()
    if not base:
        base = "file"
    if not ext.startswith("."):
        ext = "." + ext
    return base + ext


def extract_names_and_urls(file_content: str):
    """
    txt se lines read karke `name : url` tuples banata hai.
    Har line ka format:  NAME : URL
    """
    lines = file_content.strip().splitlines()
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data


def categorize_urls(urls):
    videos = []
    pdfs = []
    others = []

    for name, url in urls:
        new_url = url

        if "youtu" in url:
            # embed ko normal watch link me convert
            if "youtube.com/embed" in url:
                yt_id = url.split("/")[-1]
                new_url = f"https://www.youtube.com/watch?v={yt_id}"
            videos.append((name, new_url))

        elif ".m3u8" in url:
            videos.append((name, url))

        elif any(ext in url for ext in (".mp4", ".mov", ".m4v", ".webm")):
            videos.append((name, url))

        elif ".pdf" in url:
            pdfs.append((name, url))

        else:
            others.append((name, url))

    return videos, pdfs, others


def generate_html(file_name, videos, pdfs, others):
    file_name_without_extension = os.path.splitext(file_name)[0]

    video_links = "".join(
        f'<a href="#" onclick="playVideo(\'{url}\')">{name}</a>'
        for name, url in videos
    )
    pdf_links = "".join(
        f'<a href="{url}" target="_blank">{name}</a>'
        for name, url in pdfs
    )
    other_links = "".join(
        f'<a href="{url}" target="_blank">{name}</a>'
        for name, url in others
    )

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name_without_extension}</title>
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        body {{
            background: #f5f7fa;
            font-family: Arial, sans-serif;
        }}
        .header {{
            background: #1c1c1c;
            color: #fff;
            padding: 15px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
        }}
        .subheading {{
            font-size: 15px;
            color: #ccc;
            margin-top: 5px;
        }}
        .container {{
            max-width: 900px;
            margin: 20px auto;
        }}
        .section {{
            background: #fff;
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #007bff;
            margin-bottom: 10px;
        }}
        .section a {{
            display: block;
            padding: 8px;
            margin: 3px 0;
            background: #f0f2f5;
            border-radius: 5px;
            text-decoration: none;
            color: #007bff;
            font-weight: 500;
        }}
        .section a:hover {{
            background: #007bff;
            color: #fff;
        }}
        #video-player {{
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            padding: 15px;
            margin-top: 20px;
            background: #1c1c1c;
            color: #fff;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
<div class="header">
    {file_name_without_extension}
    <div class="subheading">📥 Extracted by: {CREDIT}</div>
</div>

<div class="container">

    <div class="section">
        <h2>Video Player</h2>
        <div id="video-player">
            <video id="cw-player" class="video-js vjs-default-skin" controls preload="auto">
                <p class="vjs-no-js">
                    JavaScript enable karo ya browser update karo.
                </p>
            </video>
        </div>
    </div>

    <div class="section">
        <h2>Videos</h2>
        <div class="video-list">
            {video_links}
        </div>
    </div>

    <div class="section">
        <h2>PDFs</h2>
        <div class="pdf-list">
            {pdf_links}
        </div>
    </div>

    <div class="section">
        <h2>Others</h2>
        <div class="other-list">
            {other_links}
        </div>
    </div>

    <div class="footer">
        Extracted by {CREDIT}
    </div>

</div>

<script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
<script>
    const player = videojs('cw-player', {{
        controls: true,
        autoplay: false,
        preload: 'auto',
        fluid: true
    }});

    function playVideo(url) {{
        if (url.includes('.m3u8')) {{
            player.src({{ src: url, type: 'application/x-mpegURL' }});
            player.play().catch(() => {{
                window.open(url, '_blank');
            }});
        }} else {{
            window.open(url, '_blank');
        }}
    }}
</script>
</body>
</html>
    """
    return html_template


def download_pdf(url: str, output_path: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, stream=True, timeout=120, headers=headers)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def download_video(url: str, output_path: str):
    """
    ffmpeg se video (m3u8 / mp4) download kare.
    ffmpeg PATH me installed hona chahiye.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", url,
        "-c", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True)


# ================== BOT setup =====================

bot = Client(
    "course_wallah_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


start_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("📂 TXT → HTML / Download", callback_data="t2h_help")],
    ]
)


@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, m: Message):
    text = (
        "Hello 🎬👋\n\n"
        "➤ I am a **Text Downloader Bot**.\n"
        "➤ Can extract **Videos & PDFs** from your `.txt` file and upload to Telegram.\n\n"
        f"👨‍💻 Credit: **{CREDIT}**"
    )
    await m.reply_text(text, reply_markup=start_keyboard)


@bot.on_callback_query(filters.regex("t2h_help"))
async def t2h_help(client, cq):
    await cq.answer()
    await cq.message.reply_text(
        "Use /t2h command:\n"
        "1️⃣ /t2h bhejo\n"
        "2️⃣ Bot bolega: `.txt` file send karo\n"
        "3️⃣ TXT format:  `Name : URL`\n"
        "   Example:\n"
        "   `Video 1 : https://example.com/video.m3u8`\n"
        "   `PDF 1   : https://example.com/file.pdf`"
    )


@bot.on_message(filters.command("t2h") & filters.private)
async def t2h_command(client: Client, m: Message):
    ask = await m.reply_text("📄 Kripya ek `.txt` file bhejo (Name : URL format).")
    # pyromod.listen use kar rahe, next message ka wait
    file_msg: Message = await bot.listen(m.chat.id)

    if not file_msg.document or not file_msg.document.file_name.lower().endswith(".txt"):
        await m.reply_text("❌ Yeh .txt file nahi hai. Dubara /t2h bhejo.")
        return

    # file download
    file_path = await file_msg.download()
    file_name = os.path.basename(file_path)
    base_name, _ = os.path.splitext(file_name)

    # read content
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    urls = extract_names_and_urls(content)
    videos, pdfs, others = categorize_urls(urls)

    # 1) HTML generate + send
    html_content = generate_html(file_name, videos, pdfs, others)
    html_file_path = file_path.replace(".txt", ".html")
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    await m.reply_document(
        document=html_file_path,
        caption=f"✅ HTML Ready\n`{base_name}`\n\nOpen in Chrome.\nExtracted by {CREDIT}",
    )

    # 2) PDFs
    if pdfs:
        await m.reply_text(f"📚 {len(pdfs)} PDF mil gaye. Download shuru kar raha hoon...")
    for idx, (name, url) in enumerate(pdfs, start=1):
        safe_name = sanitize_filename(name, ".pdf")
        pdf_path = os.path.join(os.getcwd(), safe_name)
        try:
            await ask.edit(f"⏬ PDF {idx}/{len(pdfs)}: `{name}`")
            download_pdf(url, pdf_path)
        except Exception as e:
            await m.reply_text(f"❌ PDF download failed:\n`{name}`\n`{e}`")
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            continue

        try:
            await m.reply_document(
                document=pdf_path,
                caption=f"[PDF] {name}\nExtracted by {CREDIT}",
            )
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    # 3) Videos
    if videos:
        await m.reply_text(f"🎬 {len(videos)} video mil gaye. Download shuru kar raha hoon...\n"
                           "⚠️ Thoda time lag sakta hai.")
    for idx, (name, url) in enumerate(videos, start=1):
        safe_name = sanitize_filename(name, ".mp4")
        video_path = os.path.join(os.getcwd(), safe_name)
        try:
            await ask.edit(f"⏬ Video {idx}/{len(videos)}: `{name}`")
            download_video(url, video_path)
        except Exception as e:
            await m.reply_text(f"❌ Video download failed:\n`{name}`\n`{e}`")
            if os.path.exists(video_path):
                os.remove(video_path)
            continue

        try:
            await m.reply_video(
                video=video_path,
                caption=f"[VIDEO] {name}\nExtracted by {CREDIT}",
                supports_streaming=True,
            )
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)

    # cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(html_file_path):
        os.remove(html_file_path)

    await ask.delete()


if __name__ == "__main__":
    print("Bot started as COURSE WALLAH txt-downloader")
    bot.run()

