# 官方手繪影片 + 068｜免額外模型 API

在 ChatGPT 提供「題材或完整腳本、畫風、片長」後，由助手準備並審查新內容的腳本、圖片、分鏡與素材，提交 GitHub，自動接續 068 配音、真實時間戳字幕、官方逐筆動畫、驗證及 MP4 交付。不需要題材範本，也不需要另外設定 Gemini/OpenAI 模型 API Key。

固定引擎 `5206ec0d17f9b353e400b64b9c51ad69e721e02a`；068 保留 `zh-TW-HsiaoChenNeural`、`+20%`、`+5Hz`。使用者既有設定優先；預設官方 4 號、依完整旁白實測片長、1080×1920、30fps、繁體大字幕、鮮豔畫布。

## 已有通用入口

- `preparation.py`：保存原腳本、建立獨立 job_id、建立素材結構，無 catalog 限制。
- `produce.py --voice-only`：可先實測整篇旁白，尚未生圖也可使用。
- `check_bundle.py`：檢查圖、審查哈希與語義部位，呼叫未修改的官方 build_illustration；在上傳前攔截缺輪廓、錯部位及未審查圖片。
- `activate.py --job-id`：把已準備素材選為 active-job.json。提交該檔到 main 會啟動原有 Actions；片長依新任務要求：未指定時由實測068旁白決定；明確指定時使用目標片長模式。畫風、版本與輸出路徑均取自精確任務。
- 原有 workflow_dispatch 與 Actions request bridge 繼續可用，支援 job_id / topic / seconds / style。catalog.json 僅為已準備題材的查找捷徑。

新任務進入 PREPARATION_REQUIRED 時，由助手接續完成素材、提交、啟動與交付；使用者無須自行補檔。所有 pass 均需真實檢查，不把缺素材當成功。

完整作業規範見根目錄 [WORKFLOW.md](../WORKFLOW.md) 與 [AGENTS.md](../AGENTS.md)。GitHub runner 負責執行已準備任務，腳本理解與內建生圖由 ChatGPT 接力完成。預設無配樂；主觀聽感和工程驗證分開記錄。

## 穩定性修復（2026-11-01）

- `bundle_contract.py` 是啟用、素材檢查與製作共用的像素/檔案雜湊檢查，缺少 `pixel_sha256` 在配音前失敗，不自動補造審查。
- 正式製作先執行與 `check_bundle.py` 相同的官方美術/敘事/部位驗證，再進入配音；未完成素材不能啟用。
- `pipeline-state.json` 逐階段記錄 RUNNING/DONE/FAILED 與原始錯誤；重跑仍驗證檔案，不能僅憑 checkpoint 跳過驗收。
- 保留已生成的聲音快取；任務包提供的聲音優先，避免換已授權靜音母帶時誤用舊音訊。刪除的舊設計與圖片不殘留。
- 正式 MP4 渲染後、驗收前保存 `render-input.json`；驗收中斷可重驗原片。驗收失敗即撤銷回執，下次重建；損壞影片不能視為成功。
- 每個外部製作命令最多30分鐘，逾時終止包含FFmpeg的子程序；Actions仍保留整體60分鐘上限。068既有每段三次有界重試與成功段快取保留。
- 固定 Ubuntu 24.04、Python 3.11 與 `requirements.lock` 直接及間接依賴，保存 `pip freeze`/FFmpeg版本供追查。系統套件尚非完整容器鎖定，不宣稱位元級可重製。
- `Handdraw production regression` 對自然片長一號、30秒十三號、220秒十七號含授權靜音動畫執行正式MP4重製；短片另驗證渲染後中斷接續。修改製作程式的PR會執行。既有人工看圖/聽音要求保留，工程回歸不冒稱主觀驗收。

啟用前必須重新執行 `check_bundle.py`，取得匹配本次素材與驗證程式的 `asset-validation.json`；缺少或過期即拒絕啟用。舊的已啟用任務仍由正式製作入口完整重驗，不要求回填虛假審查。
