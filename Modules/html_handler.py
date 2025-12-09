import os
import re
import requests
import subprocess
from vars import CREDIT
from pyrogram import Client, filters
from pyrogram.types import Message

# ======================================================================
# Utils
# ======================================================================

def sanitize_filename(name: str, ext: str) -> str:
    """Safe filename generate karo."""
    base = "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()
    if not base:
        base = "file"
    if not ext.startswith("."):
        ext = "." + ext
    return base + ext


def extract_names_and_urls(file_content: str):
    """
    txt se lines read karke `name : url` tuples banata hai.
    ek line = NAME : URL
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

        # akamai / cdn m3u8 style
        if ("akamaized.net/" in url or "rsc.cdn77.org/" in url) and ".pdf" not in url:
            # agar player wrap karna hai to yaha karo
            new_url = url
            videos.append((name, new_url))

        elif "youtu" in url:
            # basic normalise – embed -> watch
            if "youtube.com/embed" in url:
                yt_id = url.split("/")[-1]
                new_url = f"https://www.youtube.com/watch?v={yt_id}"
            videos.append((name, new_url))

        elif ".m3u8" in url:
            videos.append((name, url))

        elif ".mp4" in url or ".mov" in url or ".m4v" in url:
            videos.append((name, url))

        elif ".pdf" in url:
            pdfs.append((name, url))

        else:
            others.append((name, url))

    return videos, pdfs, others


# ======================================================================
# HTML generator (same feature + little cleaning)
# ======================================================================

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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Arial', sans-serif;
        }}

        body {{
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        .header {{
            background: #1c1c1c;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .subheading {{
            font-size: 16px;
            margin-top: 10px;
            color: #ccc;
            font-weight: normal;
        }}

        .subheading a {{
            color: #ffeb3b;
            text-decoration: none;
            font-weight: bold;
        }}

        #video-player {{
            margin: 20px auto;
            width: 90%;
            max-width: 800px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background: #1c1c1c;
            padding: 10px;
        }}

        #url-input-container {{
            display: none;
            margin: 20px auto;
            width: 90%;
            max-width: 600px;
            text-align: center;
        }}

        #url-input-container input {{
            width: 70%;
            padding: 10px;
            border: 2px solid #007bff;
            border-radius: 5px;
            font-size: 16px;
            margin-right: 10px;
        }}

        #url-input-container button {{
            width: 25%;
            padding: 10px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            background: #007bff;
            color: white;
            cursor: pointer;
            transition: background 0.3s ease;
        }}

        #url-input-container button:hover {{
            background: #0056b3;
        }}

        .search-bar {{
            margin: 20px auto;
            width: 90%;
            max-width: 600px;
            text-align: center;
        }}

        .search-bar input {{
            width: 100%;
            padding: 10px;
            border: 2px solid #007bff;
            border-radius: 5px;
            font-size: 16px;
        }}

        .no-results {{
            color: red;
            font-weight: bold;
            margin-top: 20px;
            text-align: center;
            display: none;
        }}

        .container {{
            display: flex;
            justify-content: space-around;
            margin: 20px auto;
            width: 90%;
            max-width: 800px;
        }}

        .tab {{
            flex: 1;
            padding: 15px;
            background: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            margin: 0 5px;
        }}

        .tab:hover {{
            background: #007bff;
            color: white;
            transform: translateY(-5px);
        }}

        .content {{
            display: none;
            margin: 20px auto;
            width: 90%;
            max-width: 800px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .content h2 {{
            font-size: 22px;
            margin-bottom: 15px;
            color: #007bff;
        }}

        .video-list, .pdf-list, .other-list {{
            text-align: left;
        }}

        .video-list a, .pdf-list a, .other-list a {{
            display: block;
            padding: 10px;
            background: #f5f7fa;
            margin: 5px 0;
            border-radius: 5px;
            text-decoration: none;
            color: #007bff;
            font-weight: bold;
            transition: all 0.3s ease;
        }}

        .video-list a:hover, .pdf-list a:hover, .other-list a:hover {{
            background: #007bff;
            color: white;
            transform: translateX(10px);
        }}

        .footer {{
            margin-top: 30px;
            font-size: 16px;
            font-weight: bold;
            padding: 15px;
            background: #1c1c1c;
            color: white;
            text-align: center;
            border-radius: 10px;
        }}

        .footer a {{
            color: #ffeb3b;
            text-decoration: none;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        {file_name_without_extension}
        <div class="subheading">📥 <b>Extracted By : {CREDIT}</b></div>
    </div>

    <div id="video-player">
        <video id="engineer-babu-player" class="video-js vjs-default-skin" controls preload="auto" width="640" height="360">
            <p class="vjs-no-js">
                To view this video please enable JavaScript, and consider upgrading to a web browser that
                <a href="https://videojs.com/html5-video-support/" target="_blank">supports HTML5 video</a>
            </p>
        </video>
    </div>

    <div id="url-input-container">
        <input type="text" id="url-input" placeholder="Enter video URL to play...">
        <button onclick="playCustomUrl()">Play</button>
    </div>

    <button onclick="toggleUrlInput()" style="margin: 20px auto; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; display: block; width: 90%; max-width: 600px;">Enter Custom URL</button>

    <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search for videos, PDFs, or other resources..." oninput="filterContent()">
    </div>

    <div id="noResults" class="no-results">No results found.</div>

    <div class="container">
        <div class="tab" onclick="showContent('videos')">Videos</div>
        <div class="tab" onclick="showContent('pdfs')">PDFs</div>
        <div class="tab" onclick="showContent('others')">Others</div>
    </div>

    <div id="videos" class="content">
        <h2>All Video Lectures</h2>
        <div class="video-list">
            {video_links}
        </div>
    </div>

    <div id="pdfs" class="content">
        <h2>All PDFs</h2>
        <div class="pdf-list">
            {pdf_links}
        </div>
    </div>

    <div id="others" class="content">
        <h2>Other Resources</h2>
        <div class="other-list">
            {other_links}
        </div>
    </div>

    <div class="footer"><b>Extracted By : {CREDIT}</b></div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script>
        const player = videojs('engineer-babu-player', {{
            controls: true,
            autoplay: false,
            preload: 'auto',
            fluid: true,
            controlBar: {{
                children: [
                    'playToggle',
                    'volumePanel',
                    'currentTimeDisplay',
                    'timeDivider',
                    'durationDisplay',
                    'progressControl',
                    'liveDisplay',
                    'remainingTimeDisplay',
                    'customControlSpacer',
                    'playbackRateMenuButton',
                    'chaptersButton',
                    'descriptionsButton',
                    'subsCapsButton',
                    'audioTrackButton',
                    'fullscreenToggle'
                ]
            }}
        }});

        function playVideo(url) {{
            if (url.includes('.m3u8')) {{
                document.getElementById('video-player').style.display = 'block';
                player.src({{ src: url, type: 'application/x-mpegURL' }});
                player.play().catch(() => {{
                    window.open(url, '_blank');
                }});
            }} else {{
                window.open(url, '_blank');
            }}
        }}

        function toggleUrlInput() {{
            const urlInputContainer = document.getElementById('url-input-container');
            urlInputContainer.style.display = urlInputContainer.style.display === 'none' ? 'block' : 'none';
        }}

        function playCustomUrl() {{
            const url = document.getElementById('url-input').value;
            if (url) {{
                playVideo(url);
            }}
        }}

        function showContent(tabName) {{
            const contents = document.querySelectorAll('.content');
            contents.forEach(content => {{
                content.style.display = 'none';
            }});
            const selectedContent = document.getElementById(tabName);
            if (selectedContent) {{
                selectedContent.style.display = 'block';
            }}
            filterContent();
        }}

        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const categories = ['videos', 'pdfs', 'others'];
            let hasResults = false;

            categories.forEach(category => {{
                const items = document.querySelectorAll(`#${{category}} .${{category}}-list a`);
                let categoryHasResults = false;

                items.forEach(item => {{
                    const itemText = item.textContent.toLowerCase();
                    if (itemText.includes(searchTerm)) {{
                        item.style.display = 'block';
                        categoryHasResults = true;
                        hasResults = true;
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});

                const categoryHeading = document.querySelector(`#${{category}} h2`);
                if (categoryHeading) {{
                    categoryHeading.style.display = categoryHasResults ? 'block' : 'none';
                }}
            }});

            const noResultsMessage = document.getElementById('noResults');
            if (noResultsMessage) {{
                noResultsMessage.style.display = hasResults ? 'none' : 'block';
            }}
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            showContent('videos');
        }});
    </script>
</body>
</html>
    """
    return html_template


# ======================================================================
# Download helpers
# ======================================================================

def download_pdf(url: str, output_path: str):
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def download_video(url: str, output_path: str):
    """
    ffmpeg se video (m3u8/mp4) download karta hai.
    system me ffmpeg installed hona chahiye.
    """
    cmd = [
        "ffmpeg",
        "-y",          # overwrite
        "-i", url,
        "-c", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True)


# ======================================================================
# Main handler
# ======================================================================

async def html_handler(bot: Client, message: Message):
    editable = await message.reply_text("📝 .txt file bhejo jisme `Name : URL` ho.")
    input_msg: Message = await bot.listen(editable.chat.id)

    if input_msg.document and input_msg.document.file_name.endswith(".txt"):
        file_path = await input_msg.download()
        file_name, ext = os.path.splitext(os.path.basename(file_path))
        b_name = file_name.replace("_", " ")
    else:
        await message.reply_text("❌ Sirf .txt file support hai.")
        return

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        file_content = f.read()

    urls = extract_names_and_urls(file_content)
    videos, pdfs, others = categorize_urls(urls)

    # 1) HTML generate + send
    html_content = generate_html(file_name, videos, pdfs, others)
    html_file_path = file_path.replace(".txt", ".html")
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    await message.reply_document(
        document=html_file_path,
        caption=(
            f"✅ HTML Ready\n"
            f"`{b_name}`\n"
            f"Chrome me open karo.\n\n"
            f"Extracted by: {CREDIT}"
        ),
    )

    # 2) PDFs download + send
    if pdfs:
        await message.reply_text(f"📚 {len(pdfs)} PDF mil gaye. Ab download + send kar raha hoon…")
    for idx, (name, url) in enumerate(pdfs, start=1):
        safe_name = sanitize_filename(name, ".pdf")
        pdf_path = os.path.join(os.getcwd(), safe_name)

        try:
            await editable.edit(f"⏬ PDF {idx}/{len(pdfs)}\n`{name}`")
            download_pdf(url, pdf_path)
        except Exception as e:
            await message.reply_text(f"❌ PDF fail: `{name}`\n`{e}`")
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            continue

        try:
            await message.reply_document(
                document=pdf_path,
                caption=f"[PDF] {name}\nExtracted by {CREDIT}",
            )
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    # 3) Videos download + send
    if videos:
        await message.reply_text(f"🎬 {len(videos)} video mil gaye. Ab download + send kar raha hoon…\n"
                                 f"⚠️ Time & data thoda zyada lag sakta hai.")

    for idx, (name, url) in enumerate(videos, start=1):
        safe_name = sanitize_filename(name, ".mp4")
        video_path = os.path.join(os.getcwd(), safe_name)

        try:
            await editable.edit(f"⏬ Video {idx}/{len(videos)}\n`{name}`")
            download_video(url, video_path)
        except Exception as e:
            await message.reply_text(f"❌ Video fail: `{name}`\n`{e}`")
            if os.path.exists(video_path):
                os.remove(video_path)
            continue

        try:
            await message.reply_video(
                video=video_path,
                caption=f"[VIDEO] {name}\nExtracted by {CREDIT}",
                supports_streaming=True,
            )
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)

    # final cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(html_file_path):
        os.remove(html_file_path)

    await editable.delete()


# ======================================================================
# Register
# ======================================================================

def register_html_handlers(bot: Client):
    @bot.on_message(filters.command(["t2h"]))
    async def call_html_handler(bot: Client, message: Message):
        await html_handler(bot, message)
