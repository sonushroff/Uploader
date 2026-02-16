import os
import shutil
import subprocess
import time

def progress(step, total, text):
    percent = int((step / total) * 100)
    bar = "█" * (percent // 5) + "-" * (20 - percent // 5)
    print(f"\r[{bar}] {percent}% | {text}", end="", flush=True)
    time.sleep(0.3)

def run(cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("🔥 GitHub Uploader (MODE V2)\n")

GITHUB_TOKEN = input("🔑 Enter GitHub Token: ").strip()
GITHUB_USERNAME = input("👤 Enter GitHub Username: ").strip()
REPO_NAME = input("📦 Enter Repository Name: ").strip()
TARGET_PATH = input("📁 Enter Local File/Folder Path: ").strip()
REPO_FOLDER = input("📂 Enter Repo Folder Name (new/existing): ").strip()
BRANCH = input("🌿 Branch name (default: main): ").strip() or "main"

TARGET_PATH = os.path.abspath(TARGET_PATH)

if not os.path.exists(TARGET_PATH):
    print("❌ Target path not found")
    exit(1)

CLONE_DIR = os.path.expanduser(f"~/{REPO_NAME}")
TOTAL_STEPS = 7
step = 0

progress(step := step + 1, TOTAL_STEPS, "Cleaning old repo")
if os.path.exists(CLONE_DIR):
    shutil.rmtree(CLONE_DIR)

progress(step := step + 1, TOTAL_STEPS, "Cloning repository")
git_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
run(["git", "clone", git_url, CLONE_DIR])

if not os.path.isdir(CLONE_DIR):
    print("\n❌ Git clone failed")
    exit(1)

progress(step := step + 1, TOTAL_STEPS, "Preparing repo folder")
repo_target_dir = os.path.join(CLONE_DIR, REPO_FOLDER)
os.makedirs(repo_target_dir, exist_ok=True)

progress(step := step + 1, TOTAL_STEPS, "Copying data")
dest = os.path.join(repo_target_dir, os.path.basename(TARGET_PATH))
if os.path.isdir(TARGET_PATH):
    shutil.copytree(TARGET_PATH, dest, dirs_exist_ok=True)
else:
    shutil.copy2(TARGET_PATH, dest)

os.chdir(CLONE_DIR)

progress(step := step + 1, TOTAL_STEPS, "Git staging")
run(["git", "config", "user.name", GITHUB_USERNAME])
run(["git", "config", "user.email", f"{GITHUB_USERNAME}@users.noreply.github.com"])
run(["git", "add", "."])
run(["git", "commit", "-m", f"🚀 Upload to {REPO_FOLDER}"])

progress(step := step + 1, TOTAL_STEPS, "Pushing to GitHub")
run(["git", "push", "origin", BRANCH])

progress(step := step + 1, TOTAL_STEPS, "Completed")

print("\n✅ Upload successful!")
print(f"🔗 https://github.com/{GITHUB_USERNAME}/{REPO_NAME}/tree/{BRANCH}/{REPO_FOLDER}")

#FILE UPLOADER SCRIPT BY @NR_CODEX
