#!/usr/bin/env bash
# 一键自检：用一条约 8 秒的小视频把整条流水线跑一遍（建项目 → 音乐 → 配音 → 预览检查 → 渲染 → 校验）。
#   bash selftest.sh          跑完删除临时文件
#   bash selftest.sh --keep   保留测试项目，方便查看成片
# 配音一步需要联网（edge-tts）；没装 edge-tts 或网络不通时自动跳过配音，只测纯音乐版。
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
S="$SKILL/scripts"
DIR="$(mktemp -d "${TMPDIR:-/tmp}/card-video-selftest.XXXXXX")/proj"
pass(){ echo "  ✅ $1"; }; fail(){ echo "  ❌ $1"; FAILED=1; }
echo "== card-video 自检 =="
bash "$S/check_env.sh" || { echo "环境不完整，先按提示安装。"; exit 1; }

echo "[1/5] 新建测试项目"
bash "$S/new_project.sh" "$DIR" >/dev/null && pass "$DIR" || { fail "建项目失败"; exit 1; }
cat > "$DIR/content.js" <<'EOF'
window.CONTENT = {
  theme: 'blue',
  brand: { name: '自检' },
  footnote: '*card-video 自检',
  audio: { music: 'music.mp3', voice: false, subtitles: true },
  scenes: [
    { type: 'hero', dur: 3.5, title: '自检<br>一切正常', props: [{ e: '🚀', x: 120, y: 60, size: 200 }, { e: '✅', x: 640, y: 60, size: 200 }], cta: '卡片视频技能',
      voice: '这是一条自检视频。|画面、|音乐和配音都正常。' },
    { type: 'list', dur: 3.5, num: '01', title: '检查项', items: ['画面渲染', '背景音乐', '配音与字幕'], numbered: false,
      voice: '检查三件事：|画面渲染，|背景音乐，|配音与字幕。' },
  ],
};
EOF

echo "[2/5] 背景音乐（保底曲）"
python3 "$S/music.py" fallback -o "$DIR/music.mp3" >/dev/null && pass "music.mp3" || fail "音乐"

echo "[3/5] 配音（edge-tts，需联网）"
VOICE=0
if python3 -c "import edge_tts" 2>/dev/null && python3 "$S/tts.py" build "$DIR" --provider edge --rate 10 >/dev/null 2>&1; then
  sed -i.bak "s/voice: false/voice: true/" "$DIR/content.js" && rm -f "$DIR/content.js.bak"
  VOICE=1; pass "配音与逐词时间"
else
  echo "  ⚠️ 跳过配音（未装 edge-tts 或网络不通），只测纯音乐版"
fi

echo "[4/5] 预览与版面检查"
node "$S/render.mjs" "$DIR" --stills >/dev/null && pass "版面、口播揭示点检查通过" || fail "预览检查有警告（见 ${DIR}/preview）"

echo "[5/5] 渲染成片"
T0=$(date +%s)
node "$S/render.mjs" "$DIR" --workers 2 >/dev/null 2>"$DIR/render.err" && pass "渲染完成（$(( $(date +%s) - T0 ))s）" || { fail "渲染失败：$(tail -3 "$DIR/render.err")"; }
OUT="$DIR/output.mp4"
if [ -f "$OUT" ]; then
  INFO=$(ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 "$OUT" | tr '\n' ' ')
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
  echo "$INFO" | grep -q "video,1080,1920" && pass "画面 1080×1920" || fail "分辨率不对：$INFO"
  echo "$INFO" | grep -q "audio" && pass "有音轨" || fail "没有音轨"
  awk "BEGIN{exit !($DUR > 6)}" && pass "时长 ${DUR}s" || fail "时长异常：${DUR}s"
  [ -f "$DIR/cover.png" ] && [ -f "$DIR/cover-3x4.png" ] && pass "封面 cover.png / cover-3x4.png" || fail "封面缺失"
  ls "$DIR/icons/"*.png >/dev/null 2>&1 && pass "3D 图标已替换 emoji" || fail "3D 图标未生效"
fi

if [ -z "$FAILED" ]; then echo "== 自检通过 =="; else echo "== 自检未通过，项目保留在 ${DIR} =="; exit 1; fi
if [ "$1" = "--keep" ]; then echo "测试项目：${DIR}（成片 output.mp4）"; else rm -rf "$(dirname "$DIR")"; fi
