# douyin-transcript 獨立安裝測試

本分支只新增獨立測試，不接入或修改既有影片生成流程，不合併 main。
不使用付費或雲端語音辨識 API；語音辨識由 GitHub runner 的 whisper.cpp 在本機執行。
網路僅用於下載依賴、模型及請求抖音網頁/影片。

## 固定官方版本
- CherishLyf/douyin-transcript: 421c11c6e167b5e38d9cd8fb4219ae926bd4643b
- ggml-org/whisper.cpp: 0c7be696371069e0baa2515ed7aa08d5a5473aa6
- Python 3.11、requests、ffmpeg-python、系統 FFmpeg、CMake
- 多語言 small 模型；官方建議 base 已實測有「鉛筆→牽筆」等錯字，所以測試改用官方亦支援的 small。

依據：https://github.com/CherishLyf/douyin-transcript/blob/421c11c6e167b5e38d9cd8fb4219ae926bd4643b/references/setup.md

## 執行
GitHub Actions 的「Douyin transcript isolated test」可手動執行。
每次 runner 依照官方 setup 安裝、編譯、下載模型及配置絕對路徑；runner 不是永久電腦，程式與模型不宣稱永久保留。
測試結果上傳到該次 run 的 douyin-transcript-verification artifact，保留 7 天。

測試順序：
1. 實測抖音 https://v.douyin.com/lAfxhR2XUe8/ 解析。
2. 解析成功才執行官方下載及 SRT/Markdown 輸出。
3. 獨立以專案既有鉛筆旁白建立黑畫面測試影片，透過官方 extract_audio、transcribe_audio_to_srt、parse_srt_segments、generate_markdown 驗證本機辨識。
4. 驗證 SRT 非空、時間範圍、鉛筆與石墨關鍵字、實際檔案大小與 SHA256。關鍵字通過不等於逐字完全正確，仍須檢視原始文字。
5. 真實抖音解析失敗時，整個 workflow 維持 failure，不用獨立測試冒稱抖音下載成功。

## 已觀測問題
- 第一輪 https://github.com/dsf430-stack/short-video-factory/actions/runs/39091027435 ：依賴、編譯和 base 模型下載成功；抖音回報「视频信息为空」。獨立測試漏呼叫官方 ensure_dependencies，已只在測試入口補上。
- 第二輪 https://github.com/dsf430-stack/short-video-factory/actions/runs/39091316258 ：頁面 HTTP 200，可解析影片 ID 7656789298096241103，但 router_data 的 video_(id)/page 缺少 videoInfoRes；尚無證據證明是刪片、區域或風控。base 實際生成中文 SRT，但關鍵字錯誤，品質檢查失敗。未修改官方解析器或偽造下載結果。
- 第三輪 https://github.com/dsf430-stack/short-video-factory/actions/runs/39091480406 ：small 模型實際生成 7 段 SRT，但「鉛筆→簽筆」「筆芯→筆星」等錯字仍在，且最後字幕 29.9 秒超出影片 28.488005 秒，未通過驗收。原始 SRT、由官方 generate_markdown 另行產生且保留錯字的 Markdown、結果 JSON 已保存於 verification/failed-small/。抖音頁面依然缺少 videoInfoRes，未下載成功。不得宣稱完整安裝驗收通過。
- 下一步需先取得可讀取的影片來源（有效分享頁或原始 MP4），本機辨識品質與時間戳則需受控實驗改善；不放寬驗收、不用原稿覆寫辨識內容。
