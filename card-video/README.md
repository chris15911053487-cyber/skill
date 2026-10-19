# card-video：卡片信息视频技能

给主题或文稿，AI 按固定流程做出卡片动画短视频：渐变背景、卡片逐张浮入、页面下坠转场、3D 图标，可选**纯音乐版**或**口播版**（讲到哪张卡哪张卡出现 + 字幕），竖屏 9:16 / 横屏 16:9，输出 MP4 + 封面（含小红书 3:4）。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 给 AI 看的工作流程（agent 的入口） |
| `reference/` | 页面字段说明、音乐来源、三种配音方案对比 |
| `template/` | 视频模板（HTML 动画）和示例文案 |
| `scripts/` | 环境自检、一键自检、建项目、音乐、配音、自录旁白对齐、渲染、图标下载 |
| `assets/` | 保底音乐 Technological Symphony、翻页音效、配音读法表 |
| `icons/` | 微软 Fluent Emoji 3D 图标 128 个（MIT 许可，见 icons/LICENSE） |

## 安装到新电脑

1. 拉取：`git clone git@github.com:chris15911053487-cyber/skill.git`，技能在 `skill/card-video/`。
2. 放到 agent 能找到的位置：
   - **Claude Code**：`ln -s "$(pwd)/skill/card-video" ~/.claude/skills/card-video`（所有项目可用；以后 `git pull` 即可更新）。
   - **其他支持 SKILL.md 的 agent**：链接或拷贝到它们各自的 skills 目录。
   - **不支持 skill 的 agent**：对它说"先阅读 /路径/card-video/SKILL.md，按里面的流程帮我做视频"。
3. 装依赖并自检（只需一次）：
   ```bash
   bash card-video/scripts/check_env.sh --install   # 装 playwright + chromium、edge-tts
   bash card-video/scripts/selftest.sh              # 30 秒跑通整条流水线
   ```
   需要提前装好 Node.js 18+、ffmpeg、python3；Linux 还要中文字体（`apt install fonts-noto-cjk`）。
   用自己录的旁白做口播时再装：`python3 -m pip install --user faster-whisper`。
4. 个人配置不在仓库里，每台电脑单独放：配音密钥 `~/.config/card-video/keys.env`、个人读法表 `~/.config/card-video/pronounce.json`。

## 用法

对 agent 说：「用 card-video 技能，帮我做一条关于 XXX 的卡片视频」，或附上文稿。agent 会先问你要哪种模式：

- **纯音乐版**：卡片 + 背景音乐，出片最快；
- **口播版**：AI 配音（或你自己录）讲解，讲到哪张卡哪张卡出现，带字幕，音乐自动压低；
- **两版都要**。

然后依次和你确认：文稿 → 补充需求（画幅、配色、品牌、结尾…）→ 分镜预览 → 背景音乐试听 →（口播版）配音试听 → 出片。直接说「做个口播视频」或「只要配乐」可以跳过模式提问。

## 手动命令速查

```bash
bash scripts/new_project.sh ./my-video                     # 新建项目，编辑 ./my-video/content.js
node scripts/render.mjs ./my-video --stills                # 关键帧预览 + 版面/口播检查
python3 scripts/music.py search "corporate technology"     # 搜音乐（sounddino，可商用）
python3 scripts/music.py download 1 -o ./my-video/music.mp3
python3 scripts/tts.py build ./my-video --provider edge    # AI 配音（再把 audio.voice 设为 true）
python3 scripts/align.py ./my-video --audio 我的录音.m4a     # 或：自录旁白对齐
node scripts/render.mjs ./my-video                         # 出片 output.mp4 + cover.png + cover-3x4.png
node scripts/render.mjs ./my-video --music-only            # 同一项目出纯音乐版
```

## 第三方素材

- 图标：[Microsoft Fluent Emoji](https://github.com/microsoft/fluentui-emoji)，MIT 许可。
- 保底音乐与翻页音效：Technological Symphony 来自 [sounddino.com](https://sounddino.com/)（免费可商用、无需署名，以其官网许可为准）；翻页音效为脚本合成。
