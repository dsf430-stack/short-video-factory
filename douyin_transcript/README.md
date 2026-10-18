# 抖音逐字稿與繁體字幕：獨立整合

本分支沿用官方 douyin-transcript，獨立安裝及執行免費本地 whisper.cpp；不修改既有畫風、068、字幕引擎或製片流程。不需要任何 API Key、登入 Cookie 或付費辨識服務。

## 手機操作：未合併 main 也能啟動

1. 用手機瀏覽器登入 GitHub，開啟 [Actions request bridge](https://github.com/dsf430-stack/short-video-factory/actions/workflows/actions-request.yml)。如果 GitHub App 沒顯示操作按鈕，改用 Safari/Chrome 網頁。
2. 按 **Run workflow**，將 **Use workflow from** 改成 **integration/douyin-transcript**；不可留在 main。
3. 在 **Bridge verification receipt / request_id** 貼上純抖音分享網址（以 `https://` 開頭），再按 **Run workflow**。這個分支把 HTTPS 輸入轉交新轉錄流程；原本 bridge 的非連結收據用途仍保留。
4. 等待該次任務結束，開啟任務頁，向下找 **Artifacts**，下載 `douyin-transcript-執行編號` ZIP。
5. iPhone 在「檔案」點 ZIP 解壓，開啟 `transcript.zh-TW.txt`；字幕是 `transcript.zh-TW.srt`。

可在同一欄輸入 **douyin-local-test**，測試專案既有鉛筆旁白，不會下載抖音。網頁手動入口已實際提交測試，不需要合併 main。

**已知邊界：**入口可啟動不代表任意分享頁都可下載。若官方解析器仍回報「视频信息为空」，任務會失敗並上傳 `link-diagnostic.json`、`run.json` 與 Log，不會用本地範例冒充該影片字幕。

新的 **Douyin transcript** 工作流程已具備 `mode`、`link`、`model` 欄位及完整分享文字支援；GitHub 目前只在預設分支顯示該流程的直接手動按鈕。本 PR 未合併，現在先用上述既有 bridge；不為了顯示按鈕擅自修改 main。

## 依據與固定版本

- douyin-transcript：`421c11c6e167b5e38d9cd8fb4219ae926bd4643b`，本次確認與官方 main 相同。
- whisper.cpp：`0c7be696371069e0baa2515ed7aa08d5a5473aa6`。
- 已讀取官方 [README](https://github.com/CherishLyf/douyin-transcript/blob/421c11c6e167b5e38d9cd8fb4219ae926bd4643b/README.md)、[setup.md](https://github.com/CherishLyf/douyin-transcript/blob/421c11c6e167b5e38d9cd8fb4219ae926bd4643b/references/setup.md) 及 `scripts/douyin_transcript.py` 實際程式。
- Python 3.11；requests、ffmpeg-python、OpenCC；系統 FFmpeg、CMake、CPU 編譯工具。每次實際版本記錄在 Artifact 的 `python-dependencies.txt`。
- 官方 CLI 先實測 `--help`、`--print-config`；透過官方 `get_video_info`、`download_video`、`transcribe_audio_to_srt`、`parse_srt_segments`、`generate_srt`、`generate_markdown` 執行。
- OpenCC 官方 Python API `OpenCC('s2twp.json').convert(...)`：繁體台灣用字，不依賴語言模型 API。

## 修復方式

舊 small 辨識出「簽筆／筆星」且末尾時間超界。新流程使用 medium 多語言模型及 16 kHz 單聲道 PCM 輸入；沒有給模型原稿、沒有文字搜尋取代來修正錯字。既有旁白對應的 `.txt` 僅在辨識完成後計算字元錯誤率，門檻 15%，完整差異保存供檢查；此門檻不代表逐字零錯誤。

保留原始 SRT，不把後處理輸出宣稱為完全未修改的辨識結果。繁體字幕輸出再解析驗證：非空、中文內容、時間順序、不重疊及不超出影片。若解碼器最後時間輕微超界，僅與實際影片時長取交集並記錄 `timestamp_adjustments`；超過 2 秒、整段超界或重疊則失敗，不能放寬判定掩蓋問題。

首輪新整合發現官方函式以 `with_suffix('.srt')` 檢查產物，雙副檔名 `transcript.raw.srt` 會檢查成另一個檔名；只改為 `transcript-raw.srt`，保留官方程式不修改。medium 當時已實際產出 9 段字幕，檔名錯誤仍如實記為失敗。

抖音缺 `videoInfoRes` 時，依次以官方原始識別、Android、桌面識別測試同一解析器；各次結果分開保存，不猜測是刪片或區域限制，也不接第三方付費解析服務。

## 輸出與現有製片流程

| 檔案 | 用途 |
|---|---|
| `transcript-raw.srt` | 原始 ASR，不套用繁體及時間後處理 |
| `transcript.zh-TW.srt` | 已驗證的 UTF-8 繁體中文字幕 |
| `transcript.zh-TW.txt` | 純文字逐字稿 |
| `transcript.zh-TW.md` | 官方 Markdown 格式的逐字稿 |
| `segments.zh-TW.json` | 繁體字幕文字與時間片段 |
| `verification.json` | 實際字幕內容、時間、大小、SHA256；本地自測另有字元錯誤率 |
| `factory-input.json` | 相對路徑交接設定，並非自動製片或既有 UI 匯入 API |
| `run.json` | 本次來源模式及成功／失敗結果 |

既有 `electron/ffmpeg/types.ts` 的 `RenderVideoParams.subtitleFile` 接受標準 SRT。後續製片需把字幕複製到該任務工作目錄，再填入其實際路徑；現有 FFmpeg 渲染結束會刪除該工作字幕，所以保留原始 Artifact 副本。`factory-input.json` 是交接資料，不宣稱已新增一鍵 UI 自動匯入或自動改寫腳本。

## 時間、空間與費用控制

- 僅手動執行，未新增排程，使用標準 `ubuntu-24.04` CPU runner，整體上限 25 分鐘；影片上限 600 秒。medium CPU 實際速度取決於 runner，不承諾十分鐘影片必定在上限內完成。
- medium 模型本輪 Log 約 1533 MB；small/base 可在新工作流程選擇，但本次成功驗收以實際紀錄為準，不把所有選項都宣稱驗收通過。
- 安裝成功立即保存編譯與模型快取；後續分享頁失敗仍可重用，不重複下載模型。快取不是永久安裝，不變更帳號計費或儲存額度。
- Artifact 保留 3 天，含測試用影片／音訊、辨識結果和診斷。逾期前需自行下載。repo 目前是公開的，不應拿私人影音或私人分享連結來此公開專案執行。
- 未新增模型 API、付費解析器、大型付費 runner、帳號訂閱或付款設定。

歷史失敗證據保留於 `verification/failed-small/` 與 `verification/liang-ai-link.json`；新實測以 `verification/integration-20261018.json` 為準。

## 本次實測結果（2026-10-18）

- **本地中文轉錄 PASS**：[實際手動執行](https://github.com/dsf430-stack/short-video-factory/actions/runs/39093733910)、[輸出 ZIP](https://github.com/dsf430-stack/short-video-factory/actions/runs/39093733910/artifacts/12124026541)。28.488005 秒、9 段；尾端 28.2 秒，沒有任何時間修剪。121 個正規化文字字元與真實旁白一致，字元錯誤率 0%，不含標點／空白評比；不外推為任意影片零錯誤。下載後另以獨立解析重新核對 SRT 順序、範圍、文字與雜湊。
- **抖音下載 FAIL**：[實際貼連結執行](https://github.com/dsf430-stack/short-video-factory/actions/runs/39093628808)。原始及 Android 識別回報「视频信息为空」；桌面識別回報「从HTML中解析视频信息失败」。尚未取得該影片，不能宣稱抖音完整流程成功。
- 成功的實際輸出另保存在 `verification/medium/`，與先前失敗證據分開。尚未合併 main，PR 保持草稿；手機可先透過上述 bridge 在本整合分支操作。
