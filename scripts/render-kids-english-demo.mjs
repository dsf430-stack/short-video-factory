import { spawnSync } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import ffmpegPath from 'ffmpeg-static'

mkdirSync('dist/kids-english', { recursive: true })
const out = 'dist/kids-english/POTATO-demo.mp4'
const font = process.platform === 'win32' ? 'C\\:/Windows/Fonts/arialbd.ttf' : '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
const vf = [
  "drawbox=x=0:y=0:w=iw:h=ih:color=0xFFF3C4:t=fill",
  "drawbox=x=0:y=h*0.72:w=iw:h=h*0.28:color=0xB9E48C:t=fill",
  "drawbox=x=w*0.25:y=h*0.34:w=w*0.5:h=h*0.32:color=0xC98B52:t=fill",
  `drawtext=fontfile='${font}':text='P':fontcolor=0xE53935:fontsize=180:x=(w-text_w)/2:y=h*0.12:enable='lt(t,3)'`,
  `drawtext=fontfile='${font}':text='POTATO':fontcolor=0xE65100:fontsize=112:x=(w-text_w)/2:y=h*0.14+12*sin(t*5):enable='gte(t,3)'`,
  `drawtext=fontfile='${font}':text='P is for potato!':fontcolor=0x333333:fontsize=64:x=(w-text_w)/2:y=h*0.82:enable='lt(t,3)'`,
  `drawtext=fontfile='${font}':text='P-O-T-A-T-O!':fontcolor=0x333333:fontsize=62:x=(w-text_w)/2:y=h*0.82:enable='between(t,3,6)'`,
  `drawtext=fontfile='${font}':text='Potato! Great job!':fontcolor=0x333333:fontsize=58:x=(w-text_w)/2:y=h*0.82:enable='gte(t,6)'`,
].join(',')

const args = ['-y','-f','lavfi','-i','color=c=white:s=1080x1920:r=30:d=10','-vf',vf,'-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',out]
const r = spawnSync(ffmpegPath, args, { stdio: 'inherit' })
if (r.status !== 0) process.exit(r.status ?? 1)
console.log(`Created ${out}`)
