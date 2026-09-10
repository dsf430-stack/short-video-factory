import { createHash } from 'node:crypto'
import { readFileSync, statSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'

const file = resolve(process.argv[2] ?? 'dist/kids-english/POTATO.mp4')
const probe = spawnSync('ffprobe', [
  '-v', 'error', '-show_entries',
  'format=duration,size,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels',
  '-of', 'json', file,
], { encoding: 'utf8' })
if (probe.status !== 0) {
  process.stderr.write(probe.stderr)
  process.exit(probe.status ?? 1)
}
const info = JSON.parse(probe.stdout)
const video = info.streams.find((stream) => stream.codec_type === 'video')
const audio = info.streams.find((stream) => stream.codec_type === 'audio')
const failures = []
if (!video || video.codec_name !== 'h264') failures.push('H.264 video stream missing')
if (video?.width !== 1080 || video?.height !== 1920) failures.push('video is not 1080x1920')
if (video?.pix_fmt !== 'yuv420p') failures.push('video pixel format is not yuv420p')
if (!audio || audio.codec_name !== 'aac') failures.push('AAC audio stream missing')
const duration = Number(info.format.duration)
if (duration < 9.9 || duration > 10.1) failures.push(`duration is ${duration}, expected 10 seconds`)
if (statSync(file).size < 100_000) failures.push('file is unexpectedly small')
if (failures.length) {
  console.error(`FAIL: ${failures.join('; ')}`)
  process.exit(1)
}
const sha256 = createHash('sha256').update(readFileSync(file)).digest('hex')
console.log(JSON.stringify({ status: 'PASS', file, sha256, format: info.format, streams: info.streams }, null, 2))
