# 002 ASCII／CRT reproducibility
使用既有 motion_hub 入口與固定版本來源；不修改上游。正式旁白已生成，本輪從001重用。
原始 MP3 SHA256: 31537b73b5186710910ed16c98da86ecb7d562cb55678d8abc7cd7e374de38b0。
同文字、聲線、速率、音調，混音僅volume=-1dB以留AAC峰值餘量。原始MP3不覆寫。
引擎：lemo-opuscar/styles/ascii-crt/demo/term.js、crt.js。
字體：VT323（OFL）、Noto Sans TC（OFL），中文字體用於終端LOG，本片未擴充原生ASCII圖集。
安裝：Python Playwright1.51.0、Chromium1161與FFmpeg；依sources.lock bootstrap。
渲染：python motion_hub/render.py motion_hub/films/002/v1/index.html NEW.mp4 --root motion_hub --duration 20 --size 1080x1920 --fps 30 --audio motion_hub/shared/water-cycle/narration-068-comparison-minus1dB.wav
驗證：python motion_hub/.sources/huashu-art-motion/scripts/film_gate.py NEW.mp4 --json --no-template
沒有付費服務，沒有影片公開發布。
