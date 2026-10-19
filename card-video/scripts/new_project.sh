#!/usr/bin/env bash
# 新建视频项目：bash new_project.sh <项目目录>
# 项目目录自包含（模板+文案+素材+音乐+配音），以后改文案重渲即可。
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:?用法: new_project.sh <项目目录>}"
if [ -e "$DIR/content.js" ]; then echo "已存在项目: $DIR（不覆盖）"; exit 1; fi
mkdir -p "$DIR/assets" "$DIR/voice"
cp "$SKILL/template/index.html" "$DIR/index.html"
cp "$SKILL/template/content.example.js" "$DIR/content.js"
echo "已创建项目: $DIR"
echo "  content.js  ← 文案与配置（写好后运行 render.mjs --stills 出预览）"
echo "  assets/     ← 放 logo、二维码、图片等素材"
echo "  music.mp3   ← 背景音乐（用 music.py 下载或用户提供）"
