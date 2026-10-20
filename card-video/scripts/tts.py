#!/usr/bin/env python3
"""配音合成：edge-tts / 火山引擎（豆包语音）/ 腾讯云语音合成。除 edge-tts 外只用标准库。

  python3 tts.py voices --provider edge                     列出可选音色
  python3 tts.py sample --provider edge [--voice X] [--rate 10] [--text "…"] -o sample.mp3 [--play]
                                                            合成一句试听
  python3 tts.py build <项目目录> --provider edge [--voice X] [--rate 10]
                                                            按 content.js 每页的 voice 字段逐页合成，
                                                            生成 voice/sNN.mp3 与 voice/manifest.js

--rate：语速百分比，0 = 正常，10 = 快 10%，-10 = 慢 10%。

口播同步：旁白里的 | 表示"念到这里出下一张卡"，合成前会去掉；build 用逐词时间戳
算出每个 | 的时刻（manifest 里的 cues），页面据此让卡片跟着说话出现，字幕也按真实时间断句。

密钥从环境变量或 ~/.config/card-video/keys.env（KEY=VALUE 每行一个）读取，绝不写进项目文件：
  火山引擎（新版控制台）: VOLC_TTS_API_KEY
  火山引擎（旧版控制台）: VOLC_TTS_APP_ID + VOLC_TTS_ACCESS_KEY
  可选: VOLC_TTS_RESOURCE_ID（默认 seed-tts-2.0，须与音色版本对应）
  腾讯云: TENCENT_SECRET_ID + TENCENT_SECRET_KEY，可选 TENCENT_REGION（默认 ap-guangzhou）
"""
import argparse, asyncio, base64, datetime, hashlib, hmac, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request, uuid

KEYFILE = os.path.join(os.path.expanduser('~'), '.config', 'card-video', 'keys.env')
PRON_FILES = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'pronounce.json'),
              os.path.join(os.path.expanduser('~'), '.config', 'card-video', 'pronounce.json')]
DEFAULT_VOICE = {'edge': 'zh-CN-XiaoxiaoNeural', 'volc': 'zh_female_xiaohe_uranus_bigtts', 'tencent': '101027'}
VOICE_HINTS = {
    'volc': """常用音色（豆包语音合成 2.0，资源 ID seed-tts-2.0）：
  zh_female_xiaohe_uranus_bigtts   小何（女，通用，默认）
  zh_female_vv_uranus_bigtts       Vivi（女，支持方言/多语种）
完整音色列表与在线试听：https://www.volcengine.com/docs/6561/1257544
注意：1.0 音色（*_mars_bigtts / *_moon_bigtts）要设 VOLC_TTS_RESOURCE_ID=seed-tts-1.0""",
    'tencent': """常用音色 VoiceType：
  101027 智梅（女，通用，精品音色，默认）   101004 智云（男，通用，精品）
  101013 智辉（男，新闻，精品）              101030 智柯（男，通用，精品）
  501001 智兰（女，资讯，大模型音色）        501000 智斌（男，阅读，大模型音色）
  501004 月华（女，聊天，大模型音色）        501005 飞镜（男，聊天，大模型音色）
完整音色列表：https://cloud.tencent.com/document/product/1073/92668
在线试听：https://cloud.tencent.com/product/tts 页面的「产品体验」""",
}


def env(name, default=None):
    if os.environ.get(name):
        return os.environ[name]
    if os.path.exists(KEYFILE):
        for line in open(KEYFILE, encoding='utf-8'):
            k, _, v = line.strip().partition('=')
            if k.strip() == name and v.strip():
                return v.strip().strip('"\'')
    return default


def need(*names):
    miss = [n for n in names if not env(n)]
    if miss:
        raise SystemExit(f"缺少密钥：{', '.join(miss)}。请写入 {KEYFILE}（每行 KEY=VALUE），或设为环境变量。")


def clean(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()


def split_marks(text):
    """去掉 | 标记，返回 (纯文本, 每个 | 在纯文本中的字符位置)。"""
    segs = clean(text).split('|')
    plain, pos = '', []
    for i, seg in enumerate(segs):
        if i:
            pos.append(len(plain))
        plain += seg
    return plain, pos


def load_pronounce(extra=None):
    """读法表：技能默认 < ~/.config/card-video/pronounce.json < 项目 audio.pronounce。"""
    d = {}
    for f in PRON_FILES:
        if os.path.exists(f):
            d.update(json.load(open(f, encoding='utf-8')))
    d.update(extra or {})
    return {k: v for k, v in d.items() if not k.startswith('_') and v is not None}


def whole(text, i, k):
    """英文条目只匹配整词（App 不匹配 Apple）。"""
    if not re.match(r'[A-Za-z0-9]', k):
        return True
    before = text[i - 1] if i else ' '
    after = text[i + len(k)] if i + len(k) < len(text) else ' '
    return not (re.match(r'[A-Za-z0-9]', before) or re.match(r'[A-Za-z0-9]', after))


def apply_pronounce(display, dic):
    """把屏幕文字换成配音读法，返回 (配音文本, 配音文本每个字符对应的屏幕文字位置)。"""
    keys = sorted(dic, key=len, reverse=True)
    spoken, smap, i = '', [], 0
    while i < len(display):
        k = next((k for k in keys if display.startswith(k, i) and whole(display, i, k)), None)
        if k:
            spoken += dic[k]
            smap += [i] * len(dic[k])
            i += len(k)
        else:
            spoken += display[i]
            smap.append(i)
            i += 1
    return spoken, smap


def align(plain, words, total):
    """把逐词时间戳对齐到纯文本字符位置，返回 [[字符位置, 秒], ...]。没有时间戳时按字数比例估算。"""
    marks, cur = [], 0
    for w in words:
        t = (w.get('text') or '').strip()
        if not t:
            continue
        i = plain.find(t, cur)
        if i < 0 or i - cur > 12:  # 对不上（数字读法、符号等）就跳过这个词
            continue
        marks.append([i, round(w['t'], 3)])
        cur = i + len(t)
    if len(marks) < 2:
        n = max(1, len(plain))
        marks = [[i, round(total * i / n, 3)] for i in range(0, n, 2)]
        return marks, False
    return marks, True


def time_at(marks, pos, total):
    for i, t in marks:
        if i >= pos:
            return t
    return total


def split_text(text, limit):
    """按句子切分，每段不超过 limit 个字符。"""
    parts, cur = [], ''
    for s in re.split(r'(?<=[。！？!?；;\n])', text):
        if len(cur) + len(s) > limit and cur:
            parts.append(cur)
            cur = ''
        while len(s) > limit:
            parts.append(s[:limit])
            s = s[limit:]
        cur += s
    if cur.strip():
        parts.append(cur)
    return [p for p in parts if p.strip()]


def concat_parts(parts, dest):
    """parts = [(文件, 词列表)]；拼接音频并把后面各段的词时间加上前面各段的时长。"""
    words, off = [], 0.0
    for f, ws in parts:
        words += [dict(w, t=w['t'] + off) for w in ws]
        off += duration(f)
    concat([f for f, _ in parts], dest)
    return words


def concat(files, dest):
    if len(files) == 1:
        shutil.move(files[0], dest)
        return
    lst = dest + '.txt'
    with open(lst, 'w') as f:
        f.writelines(f"file '{os.path.abspath(x)}'\n" for x in files)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'libmp3lame', '-q:a', '2', dest], check=True)
    os.remove(lst)


def duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
    return float(r.stdout.strip())


# ---------------- edge-tts（免费，无需 key） ----------------
def edge_tts_synth(text, voice, rate, dest):
    try:
        import edge_tts
    except ImportError:
        raise SystemExit('未安装 edge-tts：python3 -m pip install --user edge-tts')
    async def run():
        words = []
        c = edge_tts.Communicate(text, voice, rate=f'{int(rate):+d}%', boundary='WordBoundary')
        with open(dest, 'wb') as f:
            async for ch in c.stream():
                if ch['type'] == 'audio':
                    f.write(ch['data'])
                elif ch['type'] in ('WordBoundary', 'SentenceBoundary'):
                    words.append({'t': ch['offset'] / 1e7, 'd': ch['duration'] / 1e7, 'text': ch['text']})
        return words
    for attempt in range(4):
        try:
            return asyncio.run(run())
        except Exception as e:  # 微软偶发 403/限流，退避重试
            if attempt == 3:
                raise SystemExit(f'edge-tts 失败：{e}\n多为微软服务限流（403），稍后重试，或改用火山引擎/腾讯云。')
            time.sleep(3 * (attempt + 1))


def edge_voices():
    try:
        import edge_tts
    except ImportError:
        raise SystemExit('未安装 edge-tts：python3 -m pip install --user edge-tts')
    vs = asyncio.run(edge_tts.list_voices())
    for v in vs:
        if v['Locale'].startswith('zh-'):
            tag = v.get('VoiceTag', {})
            print(f"{v['ShortName']:<34} {v['Gender']:<7} {', '.join(tag.get('ContentCategories', []))}  {', '.join(tag.get('VoicePersonalities', []))}")


# ---------------- 火山引擎 豆包语音合成（HTTP 单向流式 V3） ----------------
def volc_synth(text, voice, rate, dest):
    headers = {'Content-Type': 'application/json', 'X-Api-Resource-Id': env('VOLC_TTS_RESOURCE_ID', 'seed-tts-2.0'),
               'X-Api-Request-Id': str(uuid.uuid4())}
    if env('VOLC_TTS_API_KEY'):
        headers['X-Api-Key'] = env('VOLC_TTS_API_KEY')
    else:
        if not (env('VOLC_TTS_APP_ID') and env('VOLC_TTS_ACCESS_KEY')):
            raise SystemExit(f'缺少火山引擎密钥：在 {KEYFILE} 写入 VOLC_TTS_API_KEY=…（新版控制台），'
                             '或 VOLC_TTS_APP_ID=… 与 VOLC_TTS_ACCESS_KEY=…（旧版控制台）。')
        headers['X-Api-App-Id'] = env('VOLC_TTS_APP_ID')
        headers['X-Api-Access-Key'] = env('VOLC_TTS_ACCESS_KEY')
    tmp = []
    for part in split_text(text, 300):
        body = {'user': {'uid': 'card-video'}, 'req_params': {'text': part, 'speaker': voice,
                'audio_params': {'format': 'mp3', 'sample_rate': 24000, 'speech_rate': max(-50, min(100, int(rate)))}}}
        req = urllib.request.Request('https://openspeech.bytedance.com/api/v3/tts/unidirectional',
                                     data=json.dumps(body).encode(), headers=headers, method='POST')
        try:
            raw = urllib.request.urlopen(req, timeout=120).read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            raise SystemExit(f'火山引擎请求失败 HTTP {e.code}: {e.read().decode("utf-8", "replace")[:500]}')
        audio, words, dec, i = b'', [], json.JSONDecoder(), 0
        while i < len(raw):  # 响应是一串连续的 JSON 对象
            while i < len(raw) and raw[i] in ' \r\n\t':
                i += 1
            if i >= len(raw):
                break
            obj, i = dec.raw_decode(raw, i)
            code = obj.get('code', 0)
            if code not in (0, 20000000):
                raise SystemExit(f"火山引擎返回错误 {code}: {obj.get('message')}")
            if obj.get('data'):
                audio += base64.b64decode(obj['data'])
            sent = obj.get('sentence') or {}
            ws = sent.get('words') or []
            # 时间戳可能按句从 0 计，也可能是全局时间；比上一词还早就视为按句计，加上偏移
            base = words[-1]['t'] + words[-1]['d'] if ws and words and ws[0].get('startTime', 0) < words[-1]['t'] else 0
            for w in ws:
                words.append({'t': base + w.get('startTime', 0), 'd': w.get('endTime', 0) - w.get('startTime', 0), 'text': w.get('word', '')})
        if not audio:
            raise SystemExit('火山引擎没有返回音频，请检查音色与 VOLC_TTS_RESOURCE_ID 是否对应。')
        f = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        f.write(audio)
        f.close()
        tmp.append((f.name, words))
    return concat_parts(tmp, dest)


# ---------------- 腾讯云 语音合成 TextToVoice（TC3 签名） ----------------
def tencent_call(payload):
    need('TENCENT_SECRET_ID', 'TENCENT_SECRET_KEY')
    sid, skey = env('TENCENT_SECRET_ID'), env('TENCENT_SECRET_KEY')
    host, service, ts = 'tts.tencentcloudapi.com', 'tts', int(time.time())
    date = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    body = json.dumps(payload)
    sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
    sign = lambda k, m: hmac.new(k, m.encode(), hashlib.sha256).digest()
    canonical = f'POST\n/\n\ncontent-type:application/json; charset=utf-8\nhost:{host}\n\ncontent-type;host\n{sha(body)}'
    scope = f'{date}/{service}/tc3_request'
    to_sign = f'TC3-HMAC-SHA256\n{ts}\n{scope}\n{sha(canonical)}'
    key = sign(sign(sign(('TC3' + skey).encode(), date), service), 'tc3_request')
    sig = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    headers = {'Authorization': f'TC3-HMAC-SHA256 Credential={sid}/{scope}, SignedHeaders=content-type;host, Signature={sig}',
               'Content-Type': 'application/json; charset=utf-8', 'Host': host, 'X-TC-Action': 'TextToVoice',
               'X-TC-Timestamp': str(ts), 'X-TC-Version': '2019-08-23', 'X-TC-Region': env('TENCENT_REGION', 'ap-guangzhou')}
    req = urllib.request.Request('https://' + host, data=body.encode(), headers=headers, method='POST')
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())['Response']
    if 'Error' in r:
        raise SystemExit(f"腾讯云返回错误 {r['Error']['Code']}: {r['Error']['Message']}")
    words = [{'t': x['BeginTime'] / 1000, 'd': (x['EndTime'] - x['BeginTime']) / 1000, 'text': x['Text']} for x in r.get('Subtitles') or []]
    return base64.b64decode(r['Audio']), words


def tencent_synth(text, voice, rate, dest):
    tmp = []
    for part in split_text(text, 140):  # 单次请求中文上限约 150 字
        audio, words = tencent_call({'Text': part, 'SessionId': str(uuid.uuid4()), 'VoiceType': int(voice), 'Codec': 'mp3',
                                     'SampleRate': 16000, 'PrimaryLanguage': 1, 'ModelType': 1, 'EnableSubtitle': True,
                                     'Speed': max(-2, min(6, round(rate / 20, 1)))})
        f = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        f.write(audio)
        f.close()
        tmp.append((f.name, words))
    return concat_parts(tmp, dest)


SYNTH = {'edge': edge_tts_synth, 'volc': volc_synth, 'tencent': tencent_synth}


def load_content(proj):
    js = os.path.join(proj, 'content.js')
    code = "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.CONTENT))"
    r = subprocess.run(['node', '-e', code, os.path.abspath(js)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('content.js 解析失败：\n' + r.stderr[-1500:])
    return json.loads(r.stdout)


def play(path):
    player = shutil.which('afplay') or shutil.which('ffplay')
    if player:
        subprocess.run([player] + (['-nodisp', '-autoexit', '-loglevel', 'quiet'] if 'ffplay' in player else []) + [path])
    elif sys.platform.startswith('win'):
        os.startfile(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('voices', 'sample', 'build'):
        p = sub.add_parser(name)
        p.add_argument('--provider', choices=SYNTH, default='edge')
        if name != 'voices':
            p.add_argument('--voice')
            p.add_argument('--rate', type=int, default=0)
        if name == 'sample':
            p.add_argument('--text', default='大家好，这是配音试听。一分钟，带你看懂这件事的来龙去脉。')
            p.add_argument('-o', '--out', default='voice_sample.mp3')
            p.add_argument('--play', action='store_true')
        if name == 'build':
            p.add_argument('project')
    a = ap.parse_args()

    if a.cmd == 'voices':
        edge_voices() if a.provider == 'edge' else print(VOICE_HINTS[a.provider])
        return
    voice = a.voice or DEFAULT_VOICE[a.provider]
    if a.cmd == 'sample':
        SYNTH[a.provider](apply_pronounce(split_marks(a.text)[0], load_pronounce())[0], voice, a.rate, a.out)
        print(f'试听文件: {os.path.abspath(a.out)}（{duration(a.out):.1f}s，{a.provider} / {voice}）')
        if a.play:
            play(a.out)
        return

    proj = os.path.abspath(a.project)
    C = load_content(proj)
    vdir = os.path.join(proj, 'voice')
    os.makedirs(vdir, exist_ok=True)
    scenes = []
    pron = load_pronounce((C.get('audio') or {}).get('pronounce'))
    for i, s in enumerate(C['scenes']):
        text, pos = split_marks(s.get('voice') or '')
        if not text:
            scenes.append(None)
            continue
        fn = f's{i + 1:02d}.mp3'
        spoken, smap = apply_pronounce(text, pron)
        rate = s.get('rate', a.rate)  # 页面可单独设语速（content.js 每页 rate）
        words = SYNTH[a.provider](spoken, voice, rate, os.path.join(vdir, fn)) or []
        d = duration(os.path.join(vdir, fn))
        marks, exact = align(spoken, words, d)
        marks = [[smap[i] if i < len(smap) else len(text), t] for i, t in marks]  # 换回屏幕文字位置
        cues = [time_at(marks, p, d) for p in pos]
        scenes.append({'file': fn, 'duration': round(d, 3), 'text': text, 'cues': cues, 'marks': marks})
        print(f'第 {i + 1} 页配音 {d:.1f}s，揭示点 {len(cues)} 个 {cues}' + ('' if exact else '（未拿到逐词时间，按字数估算）'))
        if a.provider == 'edge':
            time.sleep(1)  # 降低被限流概率
    manifest = {'provider': a.provider, 'voice': voice, 'rate': a.rate, 'scenes': scenes}
    with open(os.path.join(vdir, 'manifest.js'), 'w', encoding='utf-8') as f:
        f.write('window.VOICE = ' + json.dumps(manifest, ensure_ascii=False, indent=1) + ';\n')
    print(f'完成：{vdir}/manifest.js。确认 content.js 里 audio.voice 为 true，各页时长会自动按配音延长。')


if __name__ == '__main__':
    main()
