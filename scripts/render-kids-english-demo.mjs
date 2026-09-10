import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync, unlinkSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const LESSONS = {
  potato: {
    word: 'POTATO',
    letter: 'P',
    phrase: 'P is for potato!',
    spelling: 'P O T A T O!',
    praise: 'Potato! Great job!',
    colors: ['0xFFF4C7', '0xB9E48C', '0xC98B52'],
    narration: 'assets/kids-english/potato-narration.m4a',
  },
}

function arg(name, fallback) {
  const index = process.argv.indexOf(name)
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback
}

function commandExists(command) {
  const probe = spawnSync(command, ['-version'], { stdio: 'ignore' })
  return probe.status === 0
}

async function resolveFfmpeg() {
  try {
    const imported = await import('ffmpeg-static')
    if (imported.default && existsSync(imported.default)) return imported.default
  } catch {
    // The standalone MVP also works without installing node_modules.
  }
  for (const command of ['ffmpeg', 'ffmpeg.exe']) {
    if (commandExists(command)) return command
  }
  throw new Error('FFmpeg not found. Install FFmpeg or run pnpm install in the full project.')
}

function resolveFont() {
  const candidates = process.platform === 'win32'
    ? ['C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf']
    : process.platform === 'darwin'
      ? ['/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf']
      : ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
  return candidates.find(existsSync)
}

function createPotatoSprite(path) {
  const width = 620
  const height = 720
  const pixels = Buffer.alloc(width * height * 4)
  const set = (x, y, r, g, b, a = 255) => {
    if (x < 0 || y < 0 || x >= width || y >= height) return
    const offset = (y * width + x) * 4
    pixels[offset] = r; pixels[offset + 1] = g; pixels[offset + 2] = b; pixels[offset + 3] = a
  }
  const ellipse = (cx, cy, rx, ry, color) => {
    const [r, g, b, a = 255] = color
    for (let y = Math.max(0, cy - ry); y < Math.min(height, cy + ry); y++) {
      for (let x = Math.max(0, cx - rx); x < Math.min(width, cx + rx); x++) {
        if (((x - cx) ** 2) / rx ** 2 + ((y - cy) ** 2) / ry ** 2 <= 1) set(x, y, r, g, b, a)
      }
    }
  }
  // Soft shadow, potato body, highlights, eyes, smile, cheeks and little arms.
  ellipse(310, 672, 210, 28, [94, 70, 39, 70])
  ellipse(310, 350, 236, 300, [196, 128, 67, 255])
  ellipse(275, 310, 190, 248, [215, 151, 84, 255])
  ellipse(223, 238, 72, 108, [235, 178, 111, 120])
  ellipse(226, 337, 25, 35, [49, 38, 35, 255])
  ellipse(394, 337, 25, 35, [49, 38, 35, 255])
  ellipse(218, 327, 8, 11, [255, 255, 255, 255])
  ellipse(386, 327, 8, 11, [255, 255, 255, 255])
  ellipse(169, 423, 42, 24, [241, 123, 117, 175])
  ellipse(451, 423, 42, 24, [241, 123, 117, 175])
  ellipse(310, 421, 75, 54, [69, 43, 36, 255])
  ellipse(310, 397, 84, 49, [215, 151, 84, 255])
  ellipse(303, 449, 46, 18, [245, 116, 117, 255])
  ellipse(70, 440, 70, 24, [196, 128, 67, 255])
  ellipse(550, 440, 70, 24, [196, 128, 67, 255])
  const header = Buffer.from(`P7\nWIDTH ${width}\nHEIGHT ${height}\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n`)
  writeFileSync(path, Buffer.concat([header, pixels]))
}

const lessonKey = arg('--word', 'potato').toLowerCase()
const lesson = LESSONS[lessonKey]
if (!lesson) throw new Error(`Unknown lesson "${lessonKey}". Available: ${Object.keys(LESSONS).join(', ')}`)

const ffmpeg = await resolveFfmpeg()
const font = resolveFont()
if (!font) throw new Error('A bold Arial-compatible TrueType font is required.')

const output = resolve(arg('--output', `dist/kids-english/${lesson.word}.mp4`))
mkdirSync(dirname(output), { recursive: true })
const sprite = resolve(dirname(output), '.potato-sprite.pam')
createPotatoSprite(sprite)

const escapeText = (text) => text.replaceAll('\\', '\\\\').replaceAll(':', '\\:').replaceAll("'", "’")
const [sky, grass] = lesson.colors
const narration = `${lesson.phrase} ${lesson.spelling} ${lesson.praise}`
const bundledNarration = resolve(lesson.narration)
const useBundledNarration = existsSync(bundledNarration)
const fontPath = font.replaceAll('\\', '/').replace(':', '\\:')
const text = (value, size, y, color, enable) =>
  `drawtext=fontfile='${fontPath}':text='${escapeText(value)}':fontcolor=${color}:fontsize=${size}:borderw=5:bordercolor=white@0.9:x=(w-text_w)/2:y=${y}:enable='${enable}'`

const filter = [
  `[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=${sky}:t=fill,drawbox=x=0:y=ih*0.73:w=iw:h=ih*0.27:color=${grass}:t=fill[bg]`,
  `[1:v]format=rgba,scale=620:720[sprite]`,
  `[bg][sprite]overlay=x=(W-w)/2:y=560+18*sin(2*PI*t):eval=frame[scene]`,
  `[scene]${text(lesson.letter, 230, '170-18*sin(PI*t)', '0xE53935', 'lt(t,3)')},` +
    `${text(lesson.word, 138, '190+12*sin(5*t)', '0xE65100', 'gte(t,3)')},` +
    `${text(lesson.phrase, 72, '1560', '0x283238', 'lt(t,3)')},` +
    `${text(lesson.spelling, 78, '1560', '0x283238', 'between(t,3,6.4)')},` +
    `${text(lesson.praise, 68, '1560', '0x283238', 'gte(t,6.4)')},` +
    `drawtext=fontfile='${fontPath}':text='KIDS ENGLISH':fontcolor=white:fontsize=38:borderw=2:bordercolor=0x4E8E50:x=(w-text_w)/2:y=1780,format=yuv420p[v]`,
  `[2:a]volume=1.0,apad=pad_dur=10[narration]`,
  `[3:a]volume=0.055,afade=t=in:st=0:d=0.6,afade=t=out:st=9:d=1[music]`,
  `[narration][music]amix=inputs=2:duration=longest:dropout_transition=0,alimiter=limit=0.95,atrim=duration=10[a]`,
].join(';')

const args = [
  '-y',
  '-f', 'lavfi', '-i', 'color=c=white:s=1080x1920:r=30:d=10',
  '-loop', '1', '-framerate', '30', '-i', sprite,
  ...(useBundledNarration
    ? ['-i', bundledNarration]
    : ['-f', 'lavfi', '-i', `flite=text='${escapeText(narration)}':voice=slt`]),
  '-f', 'lavfi', '-i', 'sine=frequency=523:sample_rate=44100:duration=10',
  '-filter_complex', filter,
  '-map', '[v]', '-map', '[a]', '-t', '10',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '2',
  '-movflags', '+faststart', output,
]

const result = spawnSync(ffmpeg, args, { stdio: 'inherit' })
try { unlinkSync(sprite) } catch {}
if (result.error) throw result.error
if (result.status !== 0) process.exit(result.status ?? 1)
console.log(`Created ${output}`)
