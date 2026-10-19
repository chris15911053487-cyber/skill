# AI 配音：三种方式

> 价格和额度为 2026-10 查询的结果，云厂商经常调整，给用户报价时要说"以控制台为准"。

## 对比（展示给用户选）

| | edge-tts | 火山引擎 · 豆包语音合成 | 腾讯云 · 语音合成 |
|---|---|---|---|
| 费用 | **完全免费** | 付费；新用户有免费试用额度（豆包语音合成 2.0 约 2 万字符，有效期约半年）；2.0 刊例价约 28 元/10 万字符 | 免费资源包：基础/精品音色 **800 万字符**、大模型音色 10 万字符、超自然大模型音色 2 万字符；后付费：精品 0.3 元/万字符起，大模型 0.55~1.2 元/万字符，超自然大模型 6.5 元/万字符起 |
| 额度过期 | 无 | 试用额度过期作废（约半年） | 资源包**领取后 3 个月**过期，每账号只能领 1 次；用完自动转后付费 |
| 音质 | 好（微软神经网络音色），情感较平 | **中文最自然**，口语感强，支持情感、方言、声音复刻 | 精品音色偏"播音腔"，大模型/超自然音色自然度高 |
| 音色数量 | 中文约 10 个（含东北话、陕西话） | 很多（通用、角色、多情感、方言、多语种） | 多（通用、新闻、客服、童声、方言、大模型） |
| 稳定性 | 非官方接口，微软可能限流（403）或随时停用 | 官方商用服务 | 官方商用服务 |
| 商用 | 授权不明确，商业项目慎用 | 可商用（按服务协议） | 可商用（按服务协议） |
| 需要用户提供 | 无 | 实名火山引擎账号 + **API Key**（新版控制台）或 **App ID + Access Token**（旧版） | 实名腾讯云账号 + **SecretId + SecretKey** |
| 一句话推荐 | 快速出片、预算为 0 | 追求最佳中文效果 | 免费额度最大、长期低成本 |

## 试听途径（最便捷 → 次便捷）

- **edge-tts**
  1. 直接让 AI 合成一句：`python3 scripts/tts.py sample --provider edge --voice zh-CN-YunxiNeural --play`（无需任何账号，10 秒出结果）。
  2. 用 Edge 浏览器打开任意中文网页 → 右键「大声朗读」→ 在语音选项里切换音色。edge-tts 用的就是这些声音。
  - 音色：`python3 scripts/tts.py voices --provider edge`。常用：`zh-CN-XiaoxiaoNeural`（女，温暖，默认）、`zh-CN-YunxiNeural`（男，阳光）、`zh-CN-YunyangNeural`（男，新闻播音）、`zh-CN-XiaoyiNeural`（女，活泼）、`zh-CN-YunjianNeural`（男，激情）。
- **火山引擎**
  1. 不注册就能听：音色列表文档 https://www.volcengine.com/docs/6561/1257544 （每个音色有试听），产品页 https://www.volcengine.com/product/tts 有在线体验。
  2. 拿到 key 后：`python3 scripts/tts.py sample --provider volc --voice zh_female_xiaohe_uranus_bigtts --play`。
- **腾讯云**
  1. 不注册就能听：产品页 https://cloud.tencent.com/product/tts 的「产品体验」可输入文字选音色试听；音色列表 https://cloud.tencent.com/document/product/1073/92668 。
  2. 拿到 key 后：`python3 scripts/tts.py sample --provider tencent --voice 501001 --play`。

## 开通与取 key（告诉用户怎么做）

**火山引擎**
1. 注册火山引擎并完成实名认证。
2. 控制台搜索「豆包语音」→ 开通「豆包语音合成模型 2.0」（领取试用额度）。
3. 在豆包语音控制台的「API Key 管理」创建 API Key（新版控制台只需要这一个）。旧版控制台则在应用管理里取 App ID 和 Access Token。
4. 用户把 key 发给 AI，AI 写入 `~/.config/card-video/keys.env`：
   ```
   VOLC_TTS_API_KEY=xxxxxxxx
   # 旧版控制台改用：
   # VOLC_TTS_APP_ID=123456
   # VOLC_TTS_ACCESS_KEY=xxxxxxxx
   # 用 1.0 音色（*_mars_bigtts / *_moon_bigtts）时：VOLC_TTS_RESOURCE_ID=seed-tts-1.0
   ```
接口文档：https://www.volcengine.com/docs/6561/1598757 （HTTP 单向流式 V3，`tts.py` 已实现）。

**腾讯云**
1. 注册腾讯云并完成实名认证。
2. 打开语音合成控制台 https://console.cloud.tencent.com/tts → 开通服务 → **领取免费资源包**（3 个月有效，别领早了）。
3. 访问管理 → API 密钥 https://console.cloud.tencent.com/cam/capi 创建密钥。更安全的做法：建一个子账号，只授权 `QcloudTTSFullAccess`，用子账号的密钥。
4. 写入 `~/.config/card-video/keys.env`：
   ```
   TENCENT_SECRET_ID=AKIDxxxxxxxx
   TENCENT_SECRET_KEY=xxxxxxxx
   # 可选：TENCENT_REGION=ap-guangzhou
   ```
5. 提醒用户：免费资源包用完会自动按量计费；如需封顶，在控制台关闭后付费或设置预算告警。

写完后执行 `chmod 600 ~/.config/card-video/keys.env`。不要把 key 写进项目目录或回复里。

## 逐词时间戳（口播同步用）
`tts.py build` 会拿到每个词的开始时间，算出旁白里每个 `|` 的时刻，让卡片在念到时出现、字幕按真实时间切换：
- edge-tts：`WordBoundary` 事件（2026-10 实测可用）。
- 火山引擎：V3 响应里的 `sentence.words[].startTime`。
- 腾讯云：请求带 `EnableSubtitle: true`，用返回的 `Subtitles[].BeginTime`（逐字）。
拿不到时间戳时会打印"按字数估算"，同步精度会下降。

## 读法表（避免念错）
`tts.py` 合成前会按读法表替换文字，只影响配音：
- 技能默认 `assets/pronounce.json`：ERP/CRM/MRP/KPI/ROI/App 逐字母念、SaaS→萨斯、≠→不等于、→→到、vs→对比 等；
- 个人常用 `~/.config/card-video/pronounce.json`（同格式，换电脑要单独拷）；
- 项目 `content.js` 的 `audio.pronounce`，例如 `{ 'SAP': 'S A P', '之行AI': '之行 A I' }`。
后者覆盖前者。英文条目只匹配整词。改完重跑 `tts.py build`。

## 用户自录旁白（align.py）
用户照着旁白录一整段，`scripts/align.py` 用本地 faster-whisper 识别出逐字时间，和文稿逐字对齐（对不上的字插值），再按页切开录音、生成 manifest（含 `|` 时刻和字幕时间）。
- 2026-10 实测：用 78 秒的模拟录音，文稿匹配 98%，揭示点与真实时刻相差约 0.2 秒；Intel Mac 上 small 模型识别约 30 秒（不含首次下载模型）。
- 识别结果缓存在 `voice/.align_cache.json`，改了 `|` 位置重跑很快。

## 语速与断句
- `--rate`：语速百分比（-50~100）。短视频建议 `0`~`10`。
- 旁白写法：一句一个意思，多用逗号句号，少用括号、英文缩写和符号（"62%"读得出，"≠"读不出，要写成"不等于"）。
- 数字、英文读法不对时，改写旁白文本（如 "2027年" 没问题，"Q3" 写成 "第三季度"）。

## 实测情况
- edge-tts：2026-10 在 macOS 实测可用，生成速度快。
- 火山引擎、腾讯云：脚本（含时间戳解析）按官方接口文档实现，**首次使用时先跑 sample 和一页 build 验证**，报错信息会原样输出（常见原因：服务未开通、音色与资源 ID 不对应、额度用完）。
