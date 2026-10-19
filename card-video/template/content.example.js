// 视频配置。字段说明见 reference/content-schema.md
// dur = 该页最短停留秒数；有配音时自动延长到配音读完。voice = 该页旁白（需要配音时填写）。
window.CONTENT = {
  theme: {},   // 可覆盖主题色，如 { primary: '#1f6feb', primary2: '#3b8cff', primary3: '#0b4fc4', ink: '#0b2a6b' }
  brand: { name: '你的品牌', sub: 'Agent 实战营', logo: '', badge: { a: 'Agent', b: '创造季', tag: '启动' } },
  audio: { music: 'music.mp3', musicVolume: 1.0, musicStart: 0, voice: false, subtitles: true, whoosh: true },
  footnote: '*文中数据引用自公开行业报告，仅供参考；活动最终解释以主办方官方说明为准。',
  scenes: [
    {
      type: 'hero', dur: 5,
      title: '造“好”的Agent',
      sub: '其实只需要 <em>「一天」</em>！',
      props: [{ e: '🔭', x: 90, y: 60, size: 200 }, { e: '⏳', x: 420, y: 40, size: 240 }, { e: '💡', x: 730, y: 50, size: 220 }],
      cta: '预约「Agent 实战营」席位', ctaSub: '从能跑，到能扛，来真的！',
    },
    {
      type: 'list', dur: 5.5, num: '01',
      title: '62% 的企业在试 Agent<br>但只有 23% 真正扩展到生产',
      lead: '预测：40% 的 Agentic AI 项目将在 2027 年前被取消。',
      question: '什么样的 Agent 才敢上生产？<br>什么样的 Agent 才算“好”？',
      items: ['Agent 是否理解我的业务？', 'Agent 是否做出了正确的决策？', '是否安全，是否泄露信息？', '成本是否可控？', '响应快吗，稳定吗？'],
      box: ['好的 Agent = 可被信任、能稳定交付的系统'],
    },
    {
      type: 'grid', dur: 4.5, num: '02',
      title: '破解构建 Agent 的 4 大至暗时刻',
      cells: [
        { h: '构建靠手搓', p: '75% 时间耗在环境、逻辑写不了几行' },
        { h: '评估靠直觉', p: 'Demo 跑通就上，没人说得清“够不够好”' },
        { h: '迭代靠运气', p: '模型一更、代码没动，行为却变了' },
        { h: '治理靠祈祷', p: '每个 Agent 一套玩法，统一标准缺位' },
      ],
    },
    {
      type: 'table', dur: 5.5, num: '02',
      title: '传统软件开发的三个前提，<br>在 Agent 上不再天然成立：',
      head: ['前提', '传统软件', 'AI Agent'],
      rows: [
        ['输出<br>可复现', '同一个输入，<br>同一个输出', '同一个输入，<br>可能有不同答案'],
        ['答案<br>能写定', '期望输出可事先<br>写成一个字符串', '非确定性答案，<br>而非单一字符串'],
        ['判定<br>非黑即白', '只有通过<br>和不通过', '“像但是假”的错误<br>落在两者之间'],
      ],
      box: { t: '「Agent 实战营」来真的了', s: ['击溃至暗时刻，一起造“好”的 Agent', '席位招募中 · 文末报名'] },
    },
    {
      type: 'steps', dur: 7.5, num: '03',
      title: '从评估开始重塑<br>Agent 开发的生命周期',
      lead: '六个环节，六个闭环<br>定义→构建→评估→发布→观测→回流',
      core: '黄金标准',
      steps: [
        { name: '定义', en: 'DEFINE', d: '与业务方对齐场景与成功判据，<br>五维标准逐维定义。' },
        { name: '构建', en: 'BUILD', d: '提示词、工具、检索与记忆，<br>造出可运行的 Agent。' },
        { name: '评估', en: 'EVALUATE', d: '确定性代码规则 + 裁判模型打分，<br>有升有降才是真迭代。' },
        { name: '发布', en: 'RELEASE', d: '门禁自动化，达标即发行，<br>未达标即回炉。' },
        { name: '观测', en: 'OBSERVE', d: '上线不是终点，生产流量采样，<br>在线持续打分。' },
        { name: '回流', en: 'FEEDBACK', d: '生产失败样本入集，<br>黄金标准越用越准。' },
      ],
    },
    {
      type: 'cards', dur: 7.5, num: '04', deco: '🤖',
      title: '五维黄金标准：上线前量化衡量<br>“这是不是好 Agent”',
      cards: [
        { h: '认知', q: '它真的懂你的业务吗？', k: '术语、别名、多跳关系、企业内部知识。' },
        { h: '质量', q: '对不对、全不全、前后一致吗？', k: '正确性、完整性、一致性、可引用。' },
        { h: '责任', q: '权限、边界、合规，能不能审计？', k: '越权、泄露、合规红线、可追溯。' },
        { h: '成本', q: '单次多少，规模化之后还划算吗？', k: 'Token 消耗、评估成本、步骤冗余。' },
        { h: '性能', q: '快不快、稳不稳、扛不扛得住？', k: '延迟、吞吐、稳定性、可用性。' },
      ],
    },
    {
      type: 'checklist', dur: 5.5, num: '05',
      title: '「Agent 实战营」<br>1 天实操工作坊，带走全部',
      items: ['业务的 Agent 评估标准', '可落地的 6 步工程闭环流程', '现有 Agent 诊断 + 改进路线图', '团队统一语言，不再各说各话'],
      box: {
        t: '最终帮企业实现',
        items: [
          { h: '极速落地', p: '一天内搬上生产，从能跑到能扛！' },
          { h: '工程师陪跑', p: '你的场景 + 你的公司，工程师入场陪跑，从 Demo 到生产一步到位。' },
        ],
      },
    },
    {
      type: 'hero', dur: 4,
      title: '造“好”的Agent',
      sub: '其实只需要 <em>「一天」</em>！',
      props: [{ e: '🔭', x: 90, y: 60, size: 200 }, { e: '⏳', x: 420, y: 40, size: 240 }, { e: '💡', x: 730, y: 50, size: 220 }],
      cta: '预约「Agent 实战营」席位', ctaSub: '从能跑，到能扛，来真的！',
    },
  ],
};
