# 官方手繪影片 + 068｜免額外模型 API

在 ChatGPT 提供「題材或完整腳本、畫風、片長」後，由助手準備並審查新內容的腳本、圖片、分鏡與素材，提交 GitHub，自動接續 068 配音、真實時間戳字幕、官方逐筆動畫、驗證及 MP4 交付。不需要題材範本，也不需要另外設定 Gemini/OpenAI 模型 API Key。

固定引擎 `5206ec0d17f9b353e400b64b9c51ad69e721e02a`；068 保留 `zh-TW-HsiaoChenNeural`、`+20%`、`+5Hz`。使用者既有設定優先；預設官方 4 號、30秒、1080×1920、30fps、繁體大字幕、鮮豔畫布。

## 已有通用入口

- `preparation.py`：保存原腳本、建立獨立 job_id、建立素材結構，無 catalog 限制。
- `produce.py --voice-only`：可先實測整篇旁白，尚未生圖也可使用。
- `check_bundle.py`：檢查圖、審查哈希與語義部位，呼叫未修改的官方 build_illustration；在上傳前攔截缺輪廓、錯部位及未審查圖片。
- `activate.py --job-id`：把已準備素材選為 active-job.json。提交該檔到 main 會啟動原有 Actions；片長、畫風、版本與輸出路徑均取自精確任務。
- 原有 workflow_dispatch 與 Actions request bridge 繼續可用，支援 job_id / topic / seconds / style。catalog.json 僅為已準備題材的查找捷徑。

新任務進入 PREPARATION_REQUIRED 時，由助手接續完成素材、提交、啟動與交付；使用者無須自行補檔。所有 pass 均需真實檢查，不把缺素材當成功。

完整作業規範見根目錄 [WORKFLOW.md](../WORKFLOW.md) 與 [AGENTS.md](../AGENTS.md)。GitHub runner 負責執行已準備任務，腳本理解與內建生圖由 ChatGPT 接力完成。預設無配樂；主觀聽感和工程驗證分開記錄。
