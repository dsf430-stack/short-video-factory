# 官方手繪影片 + 068

此入口不需要 Gemini 或其他模型 API Key。

在 ChatGPT 提供主題後，由助手依官方 sweety-handdraw-video 規範準備腳本、插畫、繪製計畫和實際素材審查，提交到 prepared/。Actions 讀取已備妥的任務，沿用既有 smart_voice/generate_voice.py 的 068 曉臻（+20%、+5Hz），再執行原版官方手繪引擎與 FFmpeg 驗證。

## 啟動

開啟 Actions → Sweety 手繪影片 · 068 → Run workflow；主題填「一滴水如何變成雨」。

完成後在該次執行的 Artifacts 下載 sweety-068-rain-1080x1920-執行編號。未知主題會明確要求先備妥素材，不會用舊影片或改標題充當新作品。

## 固定來源

- 官方程式：https://github.com/threerocks/sweety-handdraw-video
- 固定提交：5206ec0d17f9b353e400b64b9c51ad69e721e02a（完整原始碼與內置依賴由 Actions 取得）
- 068：本專案既有 smart_voice/generate_voice.py 與 voices.json
- 原創插畫：本次內建 imagegen 生成，保留逐圖簡報、實際提示詞、SHA、語義部位與實際看圖證據。
- 封面字型：notofonts/noto-cjk，SIL Open Font License；封面為可控字型圖層合成，規格保留在 design/cover-prompt.txt。字型本體未重複打包。

不更改上游手繪引擎、不使用 runtime_fixture 交付、不更換配音聲線。字幕使用實際 Edge 事件時間，沒有平均猜測；完整旁白不截斷或加速以湊片長。預設只有旁白。

工程驗證與實際視聽審查分開記錄，未聽音不宣稱已通過人耳驗收。
