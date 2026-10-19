#!/usr/bin/env python3
"""背景音乐工具（只用 Python 标准库）。sounddino.com 曲目可免费商用、无需署名（以官网许可为准）。

  python3 music.py search "corporate technology" [--limit 10] [--sort popular|new|trend]
        英文关键词效果最好；结果缓存，供 download 按序号下载
  python3 music.py download 3 -o 项目/music.mp3          按上次搜索结果序号下载
  python3 music.py download /mp3/cats/...mp3 -o music.mp3  按曲目地址下载
  python3 music.py fallback -o 项目/music.mp3            保底曲 Technological Symphony（技能自带，离线可用）
  python3 music.py clip 项目/music.mp3 --start 0 --dur 20 [--play]
        截一段试听片段（music_preview.mp3），--play 直接在本机播放
"""
import argparse, html, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request

BASE = 'https://sounddino.com'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALLBACK_LOCAL = os.path.join(SKILL, 'assets', 'technological-symphony.mp3')
FALLBACK_URL = BASE + '/mp3/cats/1322/technological-symphony_88314.mp3'
CACHE = os.path.join(os.path.expanduser('~'), '.cache', 'card-video', 'sounddino_last.json')


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': BASE + '/', 'X-Requested-With': 'XMLHttpRequest'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode('utf-8', 'replace')


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def grab(pattern, s):
    m = re.search(pattern, s, re.S)
    return text(m.group(1)) if m else ''


def search(q, limit=10, sort='popular'):
    params = {'kind': 'music', 's': q, 'page': 1, 'limit': 36}
    if sort != 'popular':
        params['sort'] = sort
    d = json.loads(get(BASE + '/index.php?r=search/v3TracksAjax&' + urllib.parse.urlencode(params)))
    out = []
    for li in re.findall(r'<li class="playtrack[^"]*".*?</li>', d.get('html', ''), re.S):
        m = re.search(r'data-id="(\d+)" data-duration="(\d+)" data-track="([^"]+)"', li)
        if not m:
            continue
        title = grab(r'<div class="name">(.*?)</div>', li)
        out.append({
            'id': m.group(1), 'duration': int(m.group(2)), 'track': m.group(3),
            'title': title.split('/')[-1].strip(), 'category': title.split('/')[0].strip() if '/' in title else '',
            'bpm': grab(r'trackMeta__bpm">(.*?)<', li),
            'tags': re.findall(r'data-music-tag-filter="([^"]+)"', li),
            'desc': grab(r'musicDesc__text">(.*?)</span>', li),
        })
    return out[:limit]


def download(track, dest):
    url = track if track.startswith('http') else BASE + track
    data = get(url, binary=True)
    if len(data) < 20000 or b'<html' in data[:500].lower():
        raise SystemExit('下载失败：网站返回的不是音频（可能触发了每日下载上限或需要登录）。可换一首、明天再试，或用 fallback。')
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    with open(dest, 'wb') as f:
        f.write(data)
    return dest


def probe(path):
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search'); s.add_argument('query'); s.add_argument('--limit', type=int, default=10); s.add_argument('--sort', default='popular')
    d = sub.add_parser('download'); d.add_argument('which'); d.add_argument('-o', '--out', required=True)
    f = sub.add_parser('fallback'); f.add_argument('-o', '--out', required=True)
    c = sub.add_parser('clip'); c.add_argument('file'); c.add_argument('--start', type=float, default=0); c.add_argument('--dur', type=float, default=20)
    c.add_argument('-o', '--out'); c.add_argument('--play', action='store_true')
    a = ap.parse_args()

    if a.cmd == 'search':
        res = search(a.query, a.limit, a.sort)
        if not res:
            print('没有结果，换个英文关键词试试（如 corporate / technology / upbeat / inspiring / calm piano）')
            return
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(res, open(CACHE, 'w'), ensure_ascii=False, indent=1)
        for i, t in enumerate(res, 1):
            print(f"{i:>2}. {t['title']}  [{t['category']}]  {t['duration'] // 60}:{t['duration'] % 60:02d}  {t['bpm']}")
            print(f"    标签: {', '.join(t['tags'])}")
            if t['desc']:
                print(f"    简介: {t['desc'][:160]}")
            print(f"    在线试听: {BASE}{t['track']}")
    elif a.cmd == 'download':
        track = a.which
        if a.which.isdigit() and len(a.which) <= 3:
            res = json.load(open(CACHE))
            t = res[int(a.which) - 1]
            track = t['track']
            print(f"下载: {t['title']}")
        download(track, a.out)
        print(f"已保存: {a.out}  时长 {probe(a.out):.0f}s")
    elif a.cmd == 'fallback':
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        if os.path.exists(FALLBACK_LOCAL):
            shutil.copy(FALLBACK_LOCAL, a.out)
        else:
            download(FALLBACK_URL, a.out)
        print(f"已保存保底曲 Technological Symphony: {a.out}  时长 {probe(a.out):.0f}s")
    elif a.cmd == 'clip':
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.file)), 'music_preview.mp3')
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(a.start), '-t', str(a.dur), '-i', a.file,
                        '-af', f'afade=t=out:st={max(0, a.dur - 2)}:d=2', out], check=True)
        print(f'试听片段: {out}')
        if a.play:
            player = shutil.which('afplay') or shutil.which('ffplay')
            if player:
                subprocess.run([player] + (['-nodisp', '-autoexit', '-loglevel', 'quiet'] if 'ffplay' in player else []) + [out])
            elif sys.platform.startswith('win'):
                os.startfile(out)


if __name__ == '__main__':
    main()
