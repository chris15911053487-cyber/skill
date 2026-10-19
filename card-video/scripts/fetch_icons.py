#!/usr/bin/env python3
"""下载微软 Fluent Emoji 3D 图标到 icons/，生成 icons/index.json（emoji → 文件名）。

Fluent Emoji 为 MIT 许可：https://github.com/microsoft/fluentui-emoji
模板渲染时会把文案里的 emoji 自动换成这些 3D 图片，保证在任何系统上外观一致。

  python3 fetch_icons.py                 下载内置清单里的图标（已存在的跳过）
  python3 fetch_icons.py "Hot beverage" "Test tube"   追加指定图标（名称见 Fluent 仓库 assets/ 目录）
"""
import json, os, sys, urllib.parse, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SKILL, 'icons')
RAW = 'https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/'

NAMES = """Bar chart|Chart increasing|Chart decreasing|Light bulb|Hourglass done|Hourglass not done|Telescope|Factory|Briefcase
|Rocket|Money bag|Handshake|Shopping cart|Package|Memo|Receipt|Delivery truck|Abacus|Direct hit|Puzzle piece|Eye
|Repeat button|Gear|Cloud|Robot|Laptop|Mobile phone|Magnifying glass tilted left|Locked|Unlocked|Shield|Calendar
|Spiral calendar|Clipboard|Bookmark tabs|Books|Graduation cap|Trophy|Sparkles|Fire|Check mark button|Cross mark
|Warning|Brain|Globe showing asia-australia|Office building|Department store|Credit card|Coin|Dollar banknote
|Money with wings|File folder|Envelope|Telephone receiver|Speech balloon|Megaphone|Bell|Stopwatch|Alarm clock
|Hammer and wrench|Wrench|Toolbox|Link|Key|Seedling|Star|Glowing star|Thumbs up|Gem stone|Hundred points
|Party popper|Crown|Round pushpin|Pushpin|Card index|Battery|Electric plug|Satellite antenna|Pencil|Shopping bags
|Convenience store|House|Bank|World map|Compass|Chequered flag|Triangular flag|Magic wand|Crystal ball|Gift
|Red heart|Thinking face|Star-struck|Exploding head|Smiling face with sunglasses|Clapping hands|Flexed biceps
|Busts in silhouette|Bust in silhouette|Speaking head|Microscope|Test tube|Rocket|High voltage|Bullseye
|Input numbers|Shuffle tracks button|Counterclockwise arrows button|Up arrow|Down arrow|Right arrow|Mailbox
|Desktop computer|Printer|Floppy disk|Optical disk|Television|Movie camera|Camera|Video camera|Headphone
|Microphone|Studio microphone|Musical note|Artist palette|Hot beverage|Alien monster|Construction|Ship|Airplane
|Globe with meridians|Chart increasing with yen|Heavy dollar sign|Information|Question mark|Exclamation mark
|Rocket""".replace('\n', '').split('|')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'card-video-skill'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def norm(glyph):
    return glyph.replace('️', '')


def fetch(name, index):
    base = RAW + urllib.parse.quote(name) + '/'
    try:
        meta = json.loads(get(base + 'metadata.json'))
    except Exception:
        print(f'  ✗ {name}：找不到（名称要和 Fluent 仓库 assets/ 下的文件夹名一致）')
        return
    glyph = norm(meta.get('glyph', ''))
    snake = name.lower().replace(' ', '_').replace('-', '_')
    fn = snake.replace(':', '').replace("'", '') + '.png'
    dest = os.path.join(OUT, fn)
    if not os.path.exists(dest):
        for path in (f'3D/{snake}_3d.png', f'Default/3D/{snake}_3d_default.png'):
            try:
                data = get(base + urllib.parse.quote(path))
                break
            except Exception:
                data = None
        if not data:
            print(f'  ✗ {name}：没有 3D 图')
            return
        open(dest, 'wb').write(data)
    index[glyph] = fn
    print(f'  ✓ {glyph} {name}')


def main():
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, 'index.json')
    index = json.load(open(idx_path, encoding='utf-8')) if os.path.exists(idx_path) else {}
    names = sys.argv[1:] or list(dict.fromkeys(n.strip() for n in NAMES if n.strip()))
    for n in names:
        fetch(n, index)
    json.dump(index, open(idx_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    print(f'共 {len(index)} 个图标 → {idx_path}')


if __name__ == '__main__':
    main()
