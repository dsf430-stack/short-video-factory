# 中文／英文配音庫

可從此 GitHub 專案下載執行，產生 **MP3、SRT 字幕、JSON 校驗紀錄**。這是獨立命令列配音入口，可把 MP3/SRT 交給既有剪輯流程；尚未新增桌面介面的選聲按鈕。使用 Edge-TTS 線上服務，需網路；不需填寫 API key，但服務可用性由供應端決定。

## 可用中文女聲

| 代號 | 聲線 | 語速 | 音調 |
|---|---|---|---|
| `068` | 曉臻 `zh-TW-HsiaoChenNeural` | +20% | +5Hz |
| `ZH_HsiaoYu` | 曉雨 `zh-TW-HsiaoYuNeural` | +20% | +5Hz |
| `ZH_Xiaoxiao` | 曉曉 `zh-CN-XiaoxiaoNeural` | +20% | +5Hz |

預設偵測中文並選 068。英文 F01–F05 已測通英文，中文實测皆回傳 NoAudioReceived；本入口會在送出前拒絕中文使用英文預設，不會偷偷更換聲音。M01–M05 與原英文選聲規則保留，未在本輪驗證男聲。**此專案的 M02 是英文 Christopher，並非歷史配音技能的雲希。**

## 安裝

先安裝 Python 3.10 以上及 FFmpeg，確認 `ffmpeg` 和 `ffprobe` 都能在終端執行。下載本專案後，在專案根目錄操作。

Windows PowerShell：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r smart_voice/requirements.txt
.\.venv\Scripts\python.exe smart_voice/generate_voice.py --voice-id 068 --text "你好，阿福。這是我的中文影片配音。" --output smart_voice/output/068-test.mp3
```

macOS／Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r smart_voice/requirements.txt
.venv/bin/python smart_voice/generate_voice.py --voice-id 068 --text "你好，阿福。這是我的中文影片配音。" --output smart_voice/output/068-test.mp3
```

## 換聲音與長文字

```powershell
.\.venv\Scripts\python.exe smart_voice/generate_voice.py --voice-id ZH_HsiaoYu --text "你好，這是曉雨的中文配音。" --output smart_voice/output/hsiaoyu.mp3
.\.venv\Scripts\python.exe smart_voice/generate_voice.py --voice-id ZH_Xiaoxiao --text-file narration.txt --output smart_voice/output/xiaoxiao.mp3
```

`narration.txt` 使用 UTF-8。每段最多 300 字元，优先按句尾切分，依真實語音事件產生句子字幕，再串接音訊。輸出檔案已存在時拒絕覆寫，請更換檔名。

每次輸出同名 `.mp3`、`.srt`、`.json`。音訊經 loudnorm（目標 -11 LUFS／-1 dBTP／LRA 7）、完整解碼與實測音量校驗；目標不等於實測數字。失敗退出碼為 1 並寫 `.error.log`，不交付空檔或靜音代替品。TLS 使用系統 CA 加 certifi，不關閉憑證驗證。

## 試聽與驗證

`samples/` 收錄已測通的三個中文試聽 MP3 及其實測 JSON。技術解碼與音量 SUCCESS；手機播放與聲音喜好 UNCERTAIN，需實際試聽。

`VERIFICATION.md` 記錄測試結果與下一步。`python -m unittest discover -s smart_voice -p 'test_*.py'` 可驗證中文誤選、分段內容保留與拒絕覆寫。即時合成測試需要 Edge-TTS 網路。

本元件不會匯出影片或自動發布社群，也不重建現有影片功能。

## 2026-10-12 服務網址修正（已實測）

舊 `speech.platform.bing.com` 語音合成連線回傳403，聲線清單仍可能正常。程式已改用 Microsoft Read Aloud 新服務網址 `api.msedgeservices.com/tts/cognitiveservices/websocket/v1`，沿用 edge-tts 7.2.8 的原始 client token、DRM、headers 和 TLS 驗證。068聲線、+20%/+5Hz、分段、字幕與音量校驗不變。

GitHub 既有「068 曉臻配音」流程接受 narration 和 filename；優先在此流程執行，成功後取得 068-voice-output，包含MP3/SRT/JSON。不要先在其他環境重建配音系統。

驗證：run 38204582549 在相同故事與套件條件下 SUCCESS；生成《圍魏救趙》53.733878秒，音量 -13.38 LUFS、true peak -1.24 dBTP，完整解碼與14句字幕時間校驗通過。主觀與手機試聽 UNCERTAIN。此結果證實新網址可恢復本次合成，不代表供應端永遠可用。

上游調查：https://github.com/rany2/edge-tts/issues/490


## 068 穩定執行與續跑

唯一正式入口是本專案最新 main 的 `smart_voice/generate_voice.py`，雲端使用既有「068 曉臻配音」流程。舊ZIP或舊技能內的生成器不會因 main 更新而自動修正；不要拿它們生成新旁白。

每段成功後，音訊、句子時間和文字／聲線／語速／音調／套件版本校驗碼會保存到輸出資料夾的 `.068-cache/`。失敗後可使用原文字、設定與输出檔名重跑；程式重新校驗已完成段落，只生成缺少的段落。已完成MP3/SRT/JSON仍拒絕覆寫，需使用新檔名。快取損壞時明確記錄，再重新生成原文字。

連線中斷、timeout、429與5xx最多嘗試3次，間隔2秒、4秒，每段有120秒收取上限；403／401與憑證錯誤立即回報，不透過代理、不停用TLS、不更換聲線。每次進度寫入 `.progress.json`；失敗留下完整 `.error.log`，供下一次從最後成功段落接續。

GitHub工作流程在失敗後也保存已完成快取；相同分支後續執行可恢復，快取仍受GitHub容量、清除和存取規則限制。成品保存30天。正式MP3經完整解碼、非靜音與峰值校验、字幕文字覆蓋與時間校验後才發布。

`verify_stability_live.py`驗證新旁白、多段續跑、禁止網路呼叫時重用真實快取，以及刻意破壞快取後恢復。測試不以假音訊代替新配音。
