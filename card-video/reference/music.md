# 背景音乐

## 来源优先级
1. 用户提供的文件 → 放到项目目录（默认文件名 `music.mp3`）。提醒用户：自带音乐的版权自己负责，平台可能识别版权曲并限流。
2. AI 从 sounddino.com 搜索下载。
3. 保底：sounddino 的 **Technological Symphony**（科技/企业风，117 BPM，1:58）。技能已自带在 `assets/technological-symphony.mp3`，离线可用；原始地址 `https://sounddino.com/mp3/cats/1322/technological-symphony_88314.mp3`。

## sounddino.com
- 许可（2026-10 查询，以官网为准）：免费、可商用、无需署名，没有登记 Content ID。
- 只能用英文关键词搜，每次 1~2 个词（3 个词以上经常搜不到结果），多搜几组再挑。按文稿气质组合：
  - 科技/产品发布：`technology corporate`、`futuristic electronic`、`innovation`
  - 励志/成长：`inspiring`、`motivational corporate`、`uplifting piano`
  - 轻松/生活：`happy ukulele`、`upbeat pop`、`chill lofi`
  - 温暖/情感：`emotional piano`、`warm acoustic`
  - 紧张/悬念：`suspense`、`tension cinematic`
  - 节日：`christmas`、`chinese new year`
- 选曲标准：有明显节奏（90~130 BPM）适合卡片翻页；人声歌曲不要用（会抢配音）；时长 ≥ 视频时长更好（不够会自动循环，接缝可能不自然）。
- 站点有每日下载上限，超出时返回网页而不是音频；`music.py` 会提示。可以换一首、隔天再试，或用保底曲。

## 命令
```bash
python3 scripts/music.py search "corporate technology" --limit 8 [--sort popular|new|trend]
python3 scripts/music.py download 3 -o <项目>/music.mp3        # 序号来自上一次 search
python3 scripts/music.py fallback -o <项目>/music.mp3
python3 scripts/music.py clip <项目>/music.mp3 --start 0 --dur 20 --play
```

## 给用户试听的方式
- 本机（macOS/Linux/Windows）：`clip --play` 直接播放 20 秒片段。
- 远程环境或用户想自己听：给出 search 结果里的「在线试听」链接，浏览器直接打开即可播放；或把下载后的文件路径告诉用户。
- 让用户比较 2~3 首时，每首说清：风格、BPM、时长、为什么适合这条视频。

## 混音规则（render.mjs 自动处理）
- 音乐从 `audio.musicStart` 秒开始，不够长就循环，开头淡入 0.6s，结尾淡出 2.5s。
- 有配音时音乐音量减半，并用 sidechain 在人声出现时自动压低。
- 成片整体响度标准化到约 -16 LUFS（短视频平台常用值）。
