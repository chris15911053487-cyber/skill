# 外部动效素材：motion-anything 配方库

现有模板的动效（浮入、下坠转场、数字滚动、ring、局部放大）不够用，或用户想要某种特效（流光字、打字机、解密字、焦点跳词……）时，从这里取材移植。**不需要安装或运行它的应用**，只读源码。

- 仓库：`https://github.com/chris15911053487-cyber/motion-anything`（上游 `nexu-io/motion-anything`，Apache-2.0）
- 取源码：`git clone --depth 1 <仓库> <scratchpad>/motion-anything`（放 scratchpad，不进项目目录）
- 配方位置：`recipes/web/<名字>/`，每个含 `recipe.motion.yaml`（意图、avoid_when）、`<名字>.js/.css`（实现）、`preview.html`（效果）
- 按意图找：`grep -l "<关键词>" recipes/*/*/recipe.motion.yaml`

## 移植铁律：必须改写成 seek(t) 驱动

本模板按帧确定性渲染：`render.mjs` 每帧调 `seek(t)`，多 worker 并行。配方原代码大多靠 CSS `@keyframes`、`requestAnimationFrame`、IntersectionObserver 或真实时钟驱动，**原样粘贴会冻住/跳帧/各 worker 不一致**。

做法：只借它的视觉算法，改成纯函数 `f(元素, lt)`，在 `template/index.html` 的 `window.seek` 循环里按本页局部时间 `lt` 调用（参照已有的 `s.counts` 数字滚动写法），并在 `content.js` 里做成可选字段（默认关闭，不改变现有视频风格）。字段加好后同步更新 `reference/content-schema.md`。

- 随机效果（解密字、乱码）用 t 做种子的伪随机，不能用 `Math.random()`
- 着色器背景（silk、strands 等）可把 t 传给 time uniform，但渲染变慢、易抢内容，信息卡视频慎用
- 改完用 `render.mjs --stills` 和抽帧检查，确认并行渲染画面连续
- 在模板注释里注明来源配方名（Apache-2.0 署名）

## 适合卡片视频的候选

已内置的用法见 `reference/content-schema.md`「文字特效」；新增特效照 `template/index.html` 里的 `FX` 对象加一项（标签名 → 返回 `lt => {}` 的构建函数）。

| 配方 | 用途 | 备注 |
|---|---|---|
| count-up | 数据卡数字滚动 | 模板已有（`data-count`），无需移植 |
| shiny-text | 标题/重点词流光 | **已内置** `<fx-shine>` |
| fx-typewriter-multi（`recipes/slides/`） | 开场标题、AI 追问 | **已内置** `<fx-type>` |
| decrypted-text | 科技感标题、揭晓 | **已内置** `<fx-decrypt>` |
| true-focus | 口播时逐词聚焦关键词 | **已内置** `<fx-focus>`，口播版按念到时刻聚焦 |
| text-scramble | 两段文字之间乱码切换 | 可参照 `FX-DECRYPT` 实现 |
| rotating-text | 一句话轮换多个卖点 | 当前词 = floor(lt / 间隔) |
| kinetic-headline | 逐字 rise/pop/blur/wave 等 | 预设多，挑一两种 |
