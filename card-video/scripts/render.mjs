#!/usr/bin/env node
// 卡片信息视频渲染器
//   node render.mjs <项目目录> --stills          只出关键帧预览 preview/*.png + preview/contact.png，并检查版面和口播揭示点
//   node render.mjs <项目目录> [--out x.mp4]     渲染完整视频（含音乐/配音/转场音效混音）+ cover.png（竖屏另出 cover-3x4.png）
//   node render.mjs <项目目录> --music-only      忽略配音，按内容自动定页长，出纯音乐版（默认 output-音乐版.mp4）
//   可选: --fps 30  --workers 4（并行渲染进程数）  --no-audio
import { createRequire } from 'module';
import { execSync, spawnSync, spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const SKILL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const flag = n => argv.includes(n);
const VALUED = ['--out', '--fps', '--workers'];
const opt = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const proj = path.resolve(argv.find((a, i) => !a.startsWith('--') && !VALUED.includes(argv[i - 1])) || '.');
const fps = +opt('--fps', 30);
const musicOnly = flag('--music-only');
const out = path.resolve(proj, opt('--out', musicOnly ? 'output-音乐版.mp4' : 'output.mp4'));
const workers = Math.max(1, +opt('--workers', Math.min(4, Math.max(1, Math.floor(os.cpus().length / 2)))));

function loadPlaywright() {
  const bases = [path.join(SKILL, 'noop.js')];
  try { bases.push(path.join(execSync('npm root -g').toString().trim(), 'noop.js')); } catch {}
  for (const b of bases) { try { return createRequire(b)('playwright'); } catch {} }
  console.error('找不到 playwright。请先运行: bash ' + path.join(SKILL, 'scripts/check_env.sh') + ' --install');
  process.exit(1);
}
const { chromium } = loadPlaywright();
const sh = (cmd, args) => { const r = spawnSync(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] }); if (r.status) throw new Error(r.stderr.toString().slice(-2000)); };

if (!fs.existsSync(path.join(proj, 'index.html'))) { console.error('项目目录里没有 index.html：' + proj); process.exit(1); }

/* ---------- 把文案里用到的 emoji 对应的 Fluent 3D 图标复制进项目（项目保持自包含） ---------- */
function prepareIcons() {
  const idxFile = path.join(SKILL, 'icons/index.json');
  if (!fs.existsSync(idxFile)) return;
  const index = JSON.parse(fs.readFileSync(idxFile, 'utf8'));
  const text = fs.readFileSync(path.join(proj, 'content.js'), 'utf8').replace(/️/g, '') + '🎯🧩📊🚀👁🔁💡⚙';  // 后者是 steps 默认图标
  const used = Object.fromEntries(Object.entries(index).filter(([k]) => text.includes(k)));
  const dir = path.join(proj, 'icons');
  fs.mkdirSync(dir, { recursive: true });
  for (const f of new Set(Object.values(used))) fs.copyFileSync(path.join(SKILL, 'icons', f), path.join(dir, f));
  fs.writeFileSync(path.join(dir, 'index.js'), '// 由 render.mjs 自动生成：emoji → Fluent 3D 图标（MIT）\nwindow.ICONS = ' + JSON.stringify(used, null, 0) + ';\n');
}
prepareIcons();

async function openPage(browser, viewport) {
  const page = await browser.newPage({ viewport: viewport || { width: 1080, height: 1920 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  if (musicOnly) await page.addInitScript(() => { window.__MUSIC_ONLY = true; });
  await page.goto('file://' + path.join(proj, 'index.html') + '?render');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForLoadState('networkidle');
  if (errors.length) { console.error('页面报错：\n' + errors.join('\n')); process.exit(1); }
  return page;
}

const browser = await chromium.launch();
let page = await openPage(browser);
const stage = await page.evaluate(() => STAGE);
if (stage.w !== 1080 || stage.h !== 1920) { await page.close(); page = await openPage(browser, { width: stage.w, height: stage.h }); }
const viewport = { width: stage.w, height: stage.h };
const info = await page.evaluate(() => ({ total: TOTAL, times: SCENE_TIMES, clips: VOICE_CLIPS, content: CONTENT }));
const C = info.content, audio = C.audio || {};
console.log(`${musicOnly ? '【纯音乐版】' : ''}${stage.w}×${stage.h}，共 ${info.times.length} 页，总时长 ${info.total.toFixed(1)}s` + (info.clips.length ? `（含配音 ${info.clips.length} 段）` : ''));

/* ---------- 关键帧预览 ---------- */
if (flag('--stills')) {
  const dir = path.join(proj, 'preview');
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  let n = 0;
  for (const t of (await page.evaluate(() => STILL_TIMES)).flat()) {  // 每组卡片完全展开的时刻
    await page.evaluate(t => seek(t), t);
    await page.screenshot({ path: path.join(dir, `${String(++n).padStart(2, '0')}.png`) });
  }
  const cols = stage.w > stage.h ? 3 : 6;
  sh('ffmpeg', ['-y', '-v', 'error', '-framerate', '1', '-i', path.join(dir, '%02d.png'),
    '-vf', `scale=${stage.w > stage.h ? 640 : 360}:-1,tile=${Math.min(n, cols)}x${Math.ceil(n / cols)}:padding=8:color=white`, '-frames:v', '1', path.join(dir, 'contact.png')]);
  const warn = await page.evaluate(() => checkOverflow());
  const cueWarn = await page.evaluate(() => checkCues());
  await browser.close();
  console.log(`预览图: ${dir}/contact.png（单张见 01.png…${String(n).padStart(2, '0')}.png）`);
  if (warn.length) { console.log('⚠️ 版面警告：\n  ' + warn.join('\n  ')); process.exitCode = 2; }
  else console.log('版面检查通过：所有页面都在安全区内');
  if (cueWarn.length) { console.log('⚠️ 口播揭示点警告：\n  ' + cueWarn.join('\n  ')); process.exitCode = 2; }
  else if (info.clips.length) console.log('口播揭示点检查通过');
  process.exit();
}

/* ---------- 逐帧渲染：按帧区间分给多个页面并行截图，各自编码成片段后无损拼接 ---------- */
const tmp = path.join(proj, '.render');
fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(tmp, { recursive: true });
const frames = Math.round(info.total * fps);
const n = Math.min(workers, Math.max(1, Math.floor(frames / (fps * 3))));  // 每段至少 3 秒
const t0 = Date.now();
const done = new Array(n).fill(0);
const progress = () => process.stdout.write(`\r画面 ${done.reduce((a, b) => a + b, 0)}/${frames}（${n} 路并行）  ${((Date.now() - t0) / 1000).toFixed(0)}s`);

async function renderRange(w, a, b) {
  const p = w === 0 ? page : await openPage(browser, viewport);
  const seg = path.join(tmp, `seg${w}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-r', String(fps), seg], { stdio: ['pipe', 'ignore', 'inherit'] });
  for (let i = a; i < b; i++) {
    await p.evaluate(t => seek(t), i / fps);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    done[w]++;
    if (w === 0 && i % fps === 0) progress();
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  return seg;
}
const bounds = Array.from({ length: n + 1 }, (_, i) => Math.round(frames * i / n));
const segs = await Promise.all(bounds.slice(0, -1).map((a, w) => renderRange(w, a, bounds[w + 1])));
progress();
const silent = path.join(tmp, 'video.mp4');
fs.writeFileSync(path.join(tmp, 'list.txt'), segs.map(s => `file '${s}'`).join('\n'));
sh('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt'), '-c', 'copy', silent]);

// 封面：指定页（默认第 1 页）完全展开时的画面；竖屏另出小红书用的 3:4 封面
const ci = C.cover != null ? C.cover : 0, cs = info.times[ci];
await page.evaluate(t => seek(t), cs.start + Math.max(0.5, cs.dur - 0.6));
const coverPath = path.join(proj, musicOnly ? 'cover-音乐版.png' : 'cover.png');
await page.screenshot({ path: coverPath });
if (stage.h > stage.w) sh('ffmpeg', ['-y', '-v', 'error', '-i', coverPath, '-vf', 'crop=1080:1440:0:20', coverPath.replace(/\.png$/, '-3x4.png')]);
await browser.close();
console.log('\n画面完成，开始混音…');

/* ---------- 混音 ---------- */
const T = info.total;
const inputs = [], filters = [], mixes = [];
const add = (file, pre = []) => { inputs.push(...pre, '-i', file); return inputs.filter(x => x === '-i').length; }; // 返回输入序号(1起，0是视频)
const norm = 'aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo';
const musicFile = audio.music && path.resolve(proj, audio.music);
const hasVoice = info.clips.length > 0;
if (!flag('--no-audio')) {
  if (musicFile && fs.existsSync(musicFile)) {
    const k = add(musicFile, ['-stream_loop', '-1', '-ss', String(audio.musicStart || 0)]);
    filters.push(`[${k}:a]${norm},atrim=0:${T},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,afade=t=out:st=${Math.max(0, T - 2.5)}:d=2.5,volume=${(audio.musicVolume ?? 1) * (hasVoice ? 0.5 : 1)}[mus]`);
  } else if (audio.music) console.warn('⚠️ 找不到背景音乐文件：' + musicFile + '，将不带音乐');
  if (hasVoice) {
    const vs = info.clips.map((c, j) => {
      const k = add(path.resolve(proj, c.file));
      const ms = Math.round(c.at * 1000);
      filters.push(`[${k}:a]${norm},adelay=${ms}|${ms},volume=${audio.voiceVolume ?? 1.6}[v${j}]`);
      return `[v${j}]`;
    });
    filters.push(`${vs.join('')}amix=inputs=${vs.length}:normalize=0,apad=whole_dur=${T}[vox]`);
    if (filters.some(f => f.endsWith('[mus]'))) {
      filters.push(`[vox]asplit[vox1][voxsc]`, `[mus][voxsc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=450[musd]`);
      mixes.push('[musd]', '[vox1]');
    } else mixes.push('[vox]');
  } else if (filters.some(f => f.endsWith('[mus]'))) mixes.push('[mus]');
  const whoosh = path.join(SKILL, 'assets/whoosh.wav');
  if (audio.whoosh !== false && fs.existsSync(whoosh) && info.times.length > 1) {
    const cuts = info.times.slice(1).map(s => s.start - 0.25);
    const k = add(whoosh);
    filters.push(`[${k}:a]${norm},asplit=${cuts.length}${cuts.map((_, j) => `[w${j}]`).join('')}`);
    cuts.forEach((c, j) => { const ms = Math.round(c * 1000); filters.push(`[w${j}]adelay=${ms}|${ms},volume=${audio.whooshVolume ?? 0.5}[wd${j}]`); });
    filters.push(`${cuts.map((_, j) => `[wd${j}]`).join('')}amix=inputs=${cuts.length}:normalize=0[wsh]`);
    mixes.push('[wsh]');
  }
}
const args = ['-y', '-v', 'error', '-i', silent, ...inputs];
if (mixes.length) {
  filters.push(`${mixes.join('')}amix=inputs=${mixes.length}:normalize=0:duration=longest,atrim=0:${T},loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100[aout]`);
  args.push('-filter_complex', filters.join(';'), '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', String(T));
} else args.push('-c:v', 'copy');
args.push('-movflags', '+faststart', out);
sh('ffmpeg', args);
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`完成: ${out}\n封面: ${coverPath}${stage.h > stage.w ? '（另有 3:4 版 ' + path.basename(coverPath, '.png') + '-3x4.png）' : ''}\n用时 ${((Date.now() - t0) / 1000).toFixed(0)}s`);
