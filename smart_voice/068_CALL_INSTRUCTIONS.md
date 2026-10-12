## 068 配音：使用已驗證的新服務網址

收到製作有聲繪本、影片配音或「用068配音」的要求時，直接接續 GitHub 的既有流程：
https://github.com/dsf430-stack/short-video-factory

先讀取最新 main 的 smart_voice/README.md、smart_voice/generate_voice.py、
smart_voice/voices.json 及最新 smart_voice/checkpoints/ 紀錄，再執行。
優先調用 .github/workflows/voice-068.yml（名稱：068 曉臻配音）。
narration 填本次旁白；filename 使用新的英文檔名。

已驗證的新語音服務網址：
wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1

原程式須使用 edge_tts.constants.TRUSTED_CLIENT_TOKEN，
由程式組成 Ocp-Apim-Subscription-Key 查詢參數；
不得把這個庫內建 client token 當成使用者的 Azure API key。
不再使用 speech.platform.bing.com 的舊語音合成網址。

068 固定設定：
- voice：zh-TW-HsiaoChenNeural（曉臻）
- rate：+20%
- pitch：+5Hz
- 每段最多300字
- 保留TLS憑證驗證與已驗證的音量處理
- 使用實際語音事件產生字幕

GitHub流程成功後，下載 068-voice-output 成果包，
交付本次新生成的 MP3、SRT，核對文字、音訊SHA、完整解碼、
實測音量與字幕時間。需要影片時接回既有合成器，
加入故事圖片、背景音樂與環境音效，驗證MP4音軌。
聲音主觀與手機試聽尚未確認時標示UNCERTAIN。

禁止重新使用舊ZIP內尚未修正的配音入口。
禁止把舊音檔、靜音或只有背景音的影片當成本次新配音。
發生錯誤時讀取checkpoint，診斷、修正、測試並保存接續紀錄；
只有遇到真實外部阻塞才回報BLOCKED。
除登入、權限、費用或不可逆操作的必要門檻外，
在已授權範圍內接續執行，不要求使用者重新交代既有流程。
