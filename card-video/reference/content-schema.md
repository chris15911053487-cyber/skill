# content.js 字段说明

`content.js` 是一个 JS 文件：`window.CONTENT = { ... }`。文字字段都可以写少量 HTML：`<br>` 换行，`<em>重点</em>` 渐变高亮。

## 顶层

```js
window.CONTENT = {
  format: '9:16',                  // 画幅：'9:16' 竖屏 1080×1920（默认）或 '16:9' 横屏 1920×1080
  theme: 'purple',                 // 主题：预设名，或自定义颜色对象（见下）
  brand: {                         // 顶部品牌条；整个设为 null 则不显示
    name: '你的品牌',               // 左侧品牌名
    logo: 'assets/logo.png',       // 可选，左侧 logo 图（高 56px）
    sub: 'Agent 实战营',            // 可选，竖线后的副名
    badge: { a: 'Agent', b: '创造季', tag: '启动' },   // 可选，右上角活动角标
  },
  footnote: '*免责声明 / 数据来源…',  // 底部小字，可留空
  cover: 0,                        // 封面取第几页（从 0 开始）
  audio: {
    music: 'music.mp3',            // 背景音乐，相对项目目录；留空=无音乐
    musicVolume: 1.0,              // 音乐音量倍数（有配音时自动再减半并随人声闪避）
    musicStart: 0,                 // 从音乐第几秒开始（跳过长前奏）
    voice: false,                  // 是否使用 voice/manifest.js 的配音
    voiceVolume: 1.6,              // 人声音量倍数
    subtitles: true,               // 有配音时是否显示字幕
    whoosh: true,                  // 翻页"嗖"音效
    whooshVolume: 0.5,
    pronounce: { 'SAP': 'S A P' }, // 配音读法：屏幕显示左边，配音念右边（见下）
  },
  scenes: [ /* 每页一个对象，见下 */ ],
};
```

### theme
**预设**：`'purple'`（默认，紫色）、`'blue'`（蓝色科技/商务）、`'green'`（绿色健康/环保/财务增长）、`'orange'`（橙色活力/零售/餐饮）、`'dark'`（深色高级感/科技发布）。
预设上可再覆盖个别颜色：`theme: { preset: 'blue', primary: '#0052cc' }`。

**颜色变量**（全部可选）：`primary` 主色、`primary2` 渐变亮端、`primary3` 渐变暗端、`ink` 标题色、`text` 正文色、`muted` 次要文字、`hl1`/`hl2` 高亮渐变两端、`bg1`/`bg2` 背景上下色、`glow1`/`glow2` 背景光晕（rgba）。
，以及 `card` 卡片底色、`cardText` 卡片文字、`line` 分隔线、`tdlast` 表格最后一列底色、`numbg` 页码底色、`brandText` 品牌名颜色、`foot` 脚注颜色、`shadow` 阴影色。

### 图标
文案里的 emoji（props、grid 标题、steps 的 icon、deco 等）会自动换成技能自带的**微软 Fluent 3D 图标**（`icons/`，MIT 许可，128 个常用图标），任何系统上外观一致。没收录的 emoji 保持系统样式；需要更多就运行 `python3 scripts/fetch_icons.py "Hot beverage"`（名称见 github.com/microsoft/fluentui-emoji 的 assets 目录）。

### pronounce（配音读法）
三层合并，后者覆盖前者：技能 `assets/pronounce.json`（已含 ERP、CRM、KPI、≠、→ 等）< `~/.config/card-video/pronounce.json`（个人常用）< 项目 `audio.pronounce`。只影响配音，屏幕和字幕仍显示原文。英文条目只匹配整词（`App` 不会改动 `Apple`）。

## 每页通用字段

| 字段 | 说明 |
|---|---|
| `type` | 页面类型（下表） |
| `dur` | 本页最短秒数。有配音时自动延长为 0.35 + 配音时长 + 0.9 |
| `num` | 左上角页码角标，如 `'01'`，可省略 |
| `title` | 标题（≤ 2 行，约 ≤ 18 字/行） |
| `lead` | 可选，标题下一段说明（≤ 2 行） |
| `rate` | 可选，本页配音语速（覆盖 `tts.py build --rate`），如演示页放慢用 `0` 或 `-5` |
| `hold` | 可选，口播版本页讲完后多停留的秒数（看截图、看效果用；纯音乐版不受影响） |
| `voice` | 可选，本页旁白（配音文本）。字幕按标点自动断句。口播模式下用 `\|` 标记揭示点（见下） |

## 页面类型

### hero —— 钩子大字页 / 结尾回扣页
```js
{ type: 'hero', dur: 5, title: '造“好”的Agent', sub: '其实只需要 <em>「一天」</em>！',
  props: [ { e: '🔭', x: 90, y: 60, size: 200 }, { e: '⏳', x: 420, y: 40, size: 240 }, { img: 'assets/x.png', x: 730, y: 50, size: 260 } ],
  cta: '预约「Agent 实战营」席位', ctaSub: '从能跑，到能扛，来真的！' }
```
`props` 是插画（emoji 或图片，x/y 为相对插画区的像素位置，画布宽 1080），会弹出并轻微漂浮。标题 ≤ 8 个汉字一行。

### list —— 问题清单页
```js
{ type: 'list', num: '01', title: '…', lead: '…', question: '什么样的 Agent 才敢上生产？',
  items: ['…', '…'], numbered: true, box: ['结论第一行', '结论第二行'] }
```
items ≤ 5 条；`box` 是底部紫色结论块（字符串或数组）。

### grid —— 2×N 宫格
```js
{ type: 'grid', num: '02', title: '…', cells: [ { h: '构建靠手搓', p: '一句说明' }, … ], box: '可选结论' }
```
cells 建议 4 个（最多 6 个）。

### table —— 对比表
```js
{ type: 'table', num: '02', title: '…', head: ['前提', '传统软件', 'AI Agent'],
  rows: [ ['输出<br>可复现', '…', '…'], … ], box: { t: '行动号召标题', s: ['副行1', '副行2'] } }
```
3 列 × ≤ 4 行。最后一列浅紫底，突出"新"的一方。

### steps —— 流程步骤（自动分页）
```js
{ type: 'steps', num: '03', title: '…', lead: '…', core: '黄金标准', ring: true, pageSize: 3,
  steps: [ { name: '定义', en: 'DEFINE', d: '说明（≤2 行）', icon: '🎯' }, … ] }
```
步骤多于 `pageSize` 时，前一组掉落、后一组升起，时长平均分配，`dur` 需按组数给够（每组 ≥ 3.5s）。右上角旋转图标环取前 6 个 icon，`ring: false` 关闭。

### cards —— 维度卡片（自动分页）
```js
{ type: 'cards', num: '04', title: '…', deco: '🤖', pageSize: 3,
  cards: [ { h: '认知', q: '它真的懂你的业务吗？', k: '术语、别名、多跳关系。' }, … ] }
```

### checklist —— 收获 / 权益页
```js
{ type: 'checklist', num: '05', title: '…', items: ['…', '…'],
  box: { t: '最终帮企业实现', items: [ { h: '极速落地', p: '说明' }, … ] } }
```

### stats —— 大数字页（数字从 0 滚动到目标值）
```js
{ type: 'stats', num: '06', title: '用数据说话',
  stats: [ { value: 62, suffix: '%', label: '企业在试 Agent', note: '来源：…' }, { value: 1.5, decimals: 1, suffix: '倍', label: '…' } ] }
```
≤ 3 个。

### image —— 图片页（截图、产品图）
```js
{ type: 'image', num: '07', title: '…', img: 'assets/screenshot.png', caption: '一句说明' }
```
图片最高 760px，按比例缩放。

### timeline —— 时间线（发展历程、里程碑）
```js
{ type: 'timeline', num: '01', title: '发展历程', events: [ { time: '2002', h: '产品诞生', p: '一句说明' }, … ], box: '可选结论' }
```
events ≤ 4 个（竖屏）/ ≤ 3 个（横屏）。

### quote —— 金句 / 客户证言
```js
{ type: 'quote', num: '02', title: '客户怎么说', quote: '以前月底对账要三天，现在<em>一个下午</em>就能出报表。', author: '王总', role: '某批发企业 CEO' }
```
quote ≤ 40 字。title 可省略（只显示引言）。

### compare —— 左右对比（以前 vs 现在、竞品 vs 我们）
```js
{ type: 'compare', num: '03', title: '换系统前后', left: { h: '以前', items: ['…', '…'] }, right: { h: '现在', items: ['…', '…'] }, box: '可选结论' }
```
左栏灰底打 ✕，右栏主色打 ✓。每栏 ≤ 4 条、每条 ≤ 10 字。

### image 局部放大
image 页加 `zoom: [x, y, w, h]`（0~1，相对图片框的比例）：先亮出高亮框，再推近到该区域（最多 3 倍）。适合讲解产品界面的某个按钮或数据。
```js
{ type: 'image', num: '04', title: '真实界面', img: 'assets/shot.png', zoom: [0.05, 0.3, 0.9, 0.3], caption: '订单流转一屏看清' }
```

### outro —— 结尾二维码页
```js
{ type: 'outro', title: '扫码预约席位', sub: '名额有限，先到先得', qr: 'assets/qr.png', qrLabel: '长按识别二维码', contact: '品牌 · 活动名' }
```

## 文字特效（可选，默认不用）
在任何文字字段（title、sub、lead、items、cells、quote……）里用标签包住一段文字。特效从所在卡片入场时开始，口播版自动跟着揭示点走。每页最多用一种、全片两三处即可，别满屏都是。

| 标签 | 效果 | 适合 | 可选属性 |
|---|---|---|---|
| `<fx-type>…</fx-type>` | 打字机：逐字打出 + 光标 | 开场标题、AI 回答/追问 | `speed="12"` 每秒字数（默认约 16，最长 1.8 秒打完） |
| `<fx-decrypt>…</fx-decrypt>` | 解密：乱码从左到右解析成真字 | 科技感标题、揭晓答案、数字/型号 | `dur="1.2"` 解析秒数 |
| `<fx-shine>…</fx-shine>` | 流光：高光带周期性扫过 | 品牌名、核心卖点、CTA 文案 | `every="3"` 扫一次的间隔秒数 |
| `<fx-focus>词1 词2 词3</fx-focus>` | 焦点跳词：按**空格**分词，逐个清晰、其余虚化，走完一轮全部清晰 | 一行关键词/流程（报价 转订单 发货） | `step="0.8"` 每词秒数 |

```js
{ type: 'hero', title: '<fx-type>造“好”的Agent</fx-type>', sub: '其实只需要 <em>「一天」</em>！' }
{ type: 'list', title: '<fx-decrypt>AI 正在重写 ERP</fx-decrypt>', lead: '<fx-shine>一句流光说明</fx-shine>', items: [...] }
{ type: 'quote', title: '<fx-focus>报价 转订单 <em>自动采购</em> 发货</fx-focus>', voice: '先报价，然后转订单，接着自动采购，最后发货。', ... }
```
- `fx-focus` 在口播版里：词在旁白中出现（原文一致）就在**念到它的时刻**聚焦，否则按 `step` 顺延。适合短关键词行，不要包长句（词不会换行）。`<em>` 可以放在词里，整个 `<em>` 算一个词。
- `fx-shine` 不要放在 `<em>` 里面（em 文字是透明的，会只剩光带）；它本身就是强调，不必再套 em。
- 字符只隐藏不删除，版面检查照常有效；结束时都停在完整清晰的状态，封面和预览图不受影响。

## 口播揭示点（旁白里的 `|`）
页面标题/副标题在页首出现；之后旁白里每个 `|` 依次揭示下面的一个单元。`|` 只是标记，合成前会去掉。

| 类型 | 揭示单元（按顺序） |
|---|---|
| hero | 插画组（props 一起弹出）→ cta 按钮 |
| list | 每条 item → box |
| grid | 每个 cell → box |
| table | 每行 row → box |
| steps | 每个 step（分页时下一组第一个 cue 前 0.55s 换组） |
| cards | 每张 card（同上） |
| checklist | 每条 item → box |
| stats | 每个 stat（数字从此刻开始滚动）→ box |
| timeline | 每个 event → box |
| quote | 引言 → 作者 |
| compare | 左栏 → 右栏 → box |
| image | 图片 → 放大（有 zoom 时）→ caption |
| outro | 二维码 → contact |

省略的字段不算单元（例如没有 box 就不用给 box 标 `|`）。`|` 比单元少：多出的单元紧跟最后一个依次出现；没写 `|`：单元按配音时长均匀铺开。`render.mjs --stills` 会检查数量。

例：
```js
{ type: 'steps', dur: 3, title: '一张订单<br>全程打通', voice: '一张订单这样走：|报价，|转销售订单，|自动建议采购和生产，|发货，|开票，|收款记账，凭证自动生成。', steps: [ /* 6 项 */ ] }
```

## 版面安全区（`render.mjs --stills` 自动检查）
- 竖屏：正文底部 ≤ y=1380。下面是字幕（1400 起）、脚注（1530）和平台底部文案/按钮遮挡区。
- 横屏：左栏标题、右栏内容；正文底部 ≤ y=910，字幕在 948，脚注在 1040。横屏高度小，列表/卡片每页比竖屏少 1 条左右。
- 也检查：右侧超出画面；hero 页大标题/副标题压到插画。
- 超出时：删字 > 减少条目 > 拆成两页 > 换更紧凑的页面类型。

## 纯音乐版自动页长
`render.mjs --music-only` 忽略配音，每页时长取 `max(dur, 2.4 + 0.7×揭示单元数 + 1.2×(分页数−1))`，限制在 4~12 秒。口播版项目可以直接用它出纯音乐版。

## 配音清单 voice/manifest.js
由 `tts.py build`（AI 配音）或 `align.py`（自录旁白）自动生成；也可手写：
```js
window.VOICE = { provider: 'user', scenes: [ { file: 's01.mp3', duration: 3.2 }, null, { file: 's03.mp3', duration: 6.1 } ] };
```
`scenes` 与 `content.js` 的页一一对应，`null` 表示该页无配音；`duration` 用 `ffprobe` 量。
`tts.py build` 生成的条目还带：`text`（去掉 `|` 的旁白）、`cues`（每个 `|` 对应的秒数，相对本段配音开头）、`marks`（`[字符位置, 秒]` 逐词时间，用于字幕）。带 `marks` 时页尾留白 0.5s（否则 0.9s）。
