#!/usr/bin/env bash
# 环境自检：bash check_env.sh [--install]
# --install 会自动安装缺失的 playwright/chromium 与 edge-tts
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL=0; [ "$1" = "--install" ] && INSTALL=1
ok(){ echo "  ✅ $1"; }; bad(){ echo "  ❌ $1"; MISSING=1; }
echo "检查运行环境…"
command -v node >/dev/null && ok "node $(node -v)" || bad "缺 Node.js 18+（https://nodejs.org 或 brew install node）"
command -v ffmpeg >/dev/null && ok "ffmpeg" || bad "缺 ffmpeg（mac: brew install ffmpeg；Windows: winget install ffmpeg；Linux: apt install ffmpeg）"
command -v python3 >/dev/null && ok "python3 $(python3 -V 2>&1 | cut -d' ' -f2)" || bad "缺 python3"
if command -v node >/dev/null; then
  if (cd "$SKILL" && node -e "require('playwright')" 2>/dev/null) || node -e "require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright')" 2>/dev/null; then
    ok "playwright"
  elif [ $INSTALL = 1 ]; then
    (cd "$SKILL" && npm install --no-audit --no-fund && npx playwright install chromium) && ok "playwright 已安装" || bad "playwright 安装失败"
  else bad "缺 playwright（运行: bash $0 --install）"; fi
fi
if python3 -c "import edge_tts" 2>/dev/null; then ok "edge-tts（可选，用于免费配音）"
elif [ $INSTALL = 1 ]; then python3 -m pip install --user -q edge-tts && ok "edge-tts 已安装" || echo "  ⚠️ edge-tts 安装失败（只影响 edge 配音）"
else echo "  ⚠️ 未装 edge-tts（只在需要 edge 配音时安装：python3 -m pip install --user edge-tts）"; fi
python3 -c "import faster_whisper" 2>/dev/null && ok "faster-whisper（可选，自录旁白对齐）" || echo "  ⚠️ 未装 faster-whisper（只在用自己录的旁白做口播时需要：python3 -m pip install --user faster-whisper）"
# 中文字体
case "$(uname)" in
  Darwin) ok "中文字体（macOS 自带苹方）";;
  Linux) fc-list :lang=zh 2>/dev/null | grep -q . && ok "中文字体" || bad "缺中文字体（apt install fonts-noto-cjk）";;
  *) ok "中文字体（Windows 自带微软雅黑）";;
esac
[ -z "$MISSING" ] && echo "环境就绪。" || { echo "请先补齐 ❌ 项。"; exit 1; }
