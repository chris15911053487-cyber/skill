#!/usr/bin/env python3
"""用户自录旁白 → 口播同步。用语音识别（faster-whisper，本地运行）拿到逐字时间，对齐到 content.js 的旁白，
按页切分录音，生成和 tts.py build 相同格式的 voice/sNN.mp3 + voice/manifest.js（含 | 揭示点时刻和字幕时间）。

  python3 align.py <项目目录> --audio 录音.m4a [--model small]

- 录音按 content.js 的旁白顺序一口气念完即可（念错、停顿、口头禅都没关系，对不上的部分会自动插值）。
- 首次运行会下载识别模型（small 约 480MB）。国内网络下载慢时先设置：export HF_ENDPOINT=https://hf-mirror.com
- 依赖：python3 -m pip install --user faster-whisper
"""
import argparse, difflib, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import split_marks, time_at, load_content, duration  # noqa: E402

PUNCT = re.compile(r'[\s，。！？、；：,.!?;:“”"\'‘’（）()《》<>【】\[\]—\-…·|]')


def norm_chars(text):
    """去掉标点空白、统一小写，返回 [(字符, 原文位置)]。"""
    return [(c.lower(), i) for i, c in enumerate(text) if not PUNCT.match(c)]


def transcribe(audio, model_name, prompt):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit('未安装 faster-whisper：python3 -m pip install --user faster-whisper')
    model = WhisperModel(model_name, device='cpu', compute_type='int8')
    segs, _ = model.transcribe(audio, language='zh', word_timestamps=True, vad_filter=True,
                               initial_prompt=prompt[:200], condition_on_previous_text=False)
    chars = []  # [(字符, 开始秒, 结束秒)]：一个词的时间平均分给它的每个字
    for seg in segs:
        for w in seg.words or []:
            cs = [c for c in w.word if not PUNCT.match(c)]
            for k, c in enumerate(cs):
                d = (w.end - w.start) / len(cs)
                chars.append((c.lower(), w.start + k * d, w.start + (k + 1) * d))
    return chars


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project')
    ap.add_argument('--audio', required=True, help='整段录音文件（mp3/m4a/wav 均可）')
    ap.add_argument('--model', default='small', help='识别模型：base（快）/ small（默认）/ medium（准，慢）')
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    C = load_content(proj)
    scenes = []  # 每页：显示文本、| 位置、在全文中的起点
    full = ''
    for s in C['scenes']:
        text, pos = split_marks(s.get('voice') or '')
        scenes.append({'text': text, 'pos': pos, 'off': len(full)})
        full += text
    if not full:
        raise SystemExit('content.js 里没有任何 voice 旁白，无法对齐。')

    cache = os.path.join(proj, 'voice', '.align_cache.json')  # 同一录音+模型只识别一次，改文稿重对齐很快
    key = f'{os.path.abspath(a.audio)}|{os.path.getmtime(a.audio)}|{a.model}'
    rec = None
    if os.path.exists(cache):
        c = json.load(open(cache, encoding='utf-8'))
        rec = c['chars'] if c.get('key') == key else None
    if rec is None:
        print(f'识别录音中（模型 {a.model}，首次会下载模型；1 分钟录音约需 1~3 分钟）…')
        rec = transcribe(a.audio, a.model, full)
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        json.dump({'key': key, 'chars': rec}, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
    if not rec:
        raise SystemExit('没有识别出任何文字，请检查录音。')
    script = norm_chars(full)
    sm = difflib.SequenceMatcher(None, ''.join(c for c, _ in script), ''.join(r[0] for r in rec), autojunk=False)
    t_of = [None] * len(script)
    matched = 0
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            t_of[b.a + k] = rec[b.b + k][1]
            matched += 1
    rate = matched / len(script)
    print(f'文稿与录音匹配 {rate:.0%}')
    if rate < 0.5:
        print('⚠️ 匹配率偏低：确认录音内容和 content.js 的旁白一致；同步精度会下降。')
    # 对不上的字：在前后已匹配的时间之间线性插值
    known = [i for i, t in enumerate(t_of) if t is not None]
    for i in range(len(t_of)):
        if t_of[i] is None:
            prev = max((k for k in known if k < i), default=None)
            nxt = min((k for k in known if k > i), default=None)
            if prev is None:
                t_of[i] = t_of[nxt]
            elif nxt is None:
                t_of[i] = t_of[prev] + 0.2 * (i - prev)
            else:
                t_of[i] = t_of[prev] + (t_of[nxt] - t_of[prev]) * (i - prev) / (nxt - prev)
    full_time = {}  # 全文字符位置 → 秒
    for (c, idx), t in zip(script, t_of):
        full_time[idx] = t
    total = duration(a.audio)
    rec_end = rec[-1][2]

    # 每页的起止：本页第一个字开始前 0.15 秒，到下一页第一个字前 0.15 秒
    starts = []
    for sc in scenes:
        ts = [full_time[i] for i in range(sc['off'], sc['off'] + len(sc['text'])) if i in full_time]
        starts.append(min(ts) if ts else None)
    vdir = os.path.join(proj, 'voice')
    os.makedirs(vdir, exist_ok=True)
    out = []
    for i, sc in enumerate(scenes):
        if not sc['text'] or starts[i] is None:
            out.append(None)
            continue
        a0 = max(0.0, starts[i] - 0.15)
        nxt = next((s for s in starts[i + 1:] if s is not None), None)
        a1 = min(total, (nxt - 0.15) if nxt is not None else rec_end + 0.4)
        fn = f's{i + 1:02d}.mp3'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{a0:.3f}', '-to', f'{a1:.3f}', '-i', a.audio,
                        '-af', 'afade=t=in:d=0.03', '-c:a', 'libmp3lame', '-q:a', '2', os.path.join(vdir, fn)], check=True)
        marks = [[j, round(float(full_time[sc['off'] + j] - a0), 3)] for j in range(len(sc['text'])) if sc['off'] + j in full_time]
        d = round(a1 - a0, 3)
        cues = [round(float(time_at(marks, p, d)), 3) for p in sc["pos"]]
        out.append({'file': fn, 'duration': d, 'text': sc['text'], 'cues': cues, 'marks': marks})
        print(f'第 {i + 1} 页 {a0:.1f}s–{a1:.1f}s，揭示点 {cues}')
    manifest = {'provider': 'recording', 'source': os.path.basename(a.audio), 'scenes': out}
    with open(os.path.join(vdir, 'manifest.js'), 'w', encoding='utf-8') as f:
        f.write('window.VOICE = ' + json.dumps(manifest, ensure_ascii=False, indent=1) + ';\n')
    print(f'完成：{vdir}/manifest.js。把 content.js 的 audio.voice 设为 true，再 render.mjs --stills 检查。')


if __name__ == '__main__':
    main()
