# Actions 自動分流與 Drive 保存

ChatGPT 準備題材、腳本、分鏡、設定和已審查素材；現有 GitHub Actions 執行 068、句界字幕、官方手繪引擎、MP4 與工程驗證。Work 只用於部署、修復及必要測試。這次沒有另建渲染器或變更 068 設定。

## 狀態（2026-10-20）

分支：feature/actions-routing-20261020。尚未合併 main。
Drive 資料夾已建立：[Facebook_Reels/ACTIONS_VERIFIED](https://drive.google.com/drive/folders/1MYEGF9AgF7nFpTgRZIU-79Vjs6qtDLB5)。此資料夾不在 READY 發布佇列；保存不代表已人工驗收或已發布。

目前缺少 Actions 專用 OAuth 憑證，不能宣稱端到端已完成。ChatGPT 的 Drive 連線不可匯出給 runner；本環境無法開啟 Google Cloud 憑證設定頁（顯示 Site Unavailable）。使用者已同意設定指定資料夾的保存授權，不要再次要求同一項同意；需在可用的 Google 授權介面完成實際 OAuth。

## 同一個既有 workflow 的三種操作

入口：https://github.com/dsf430-stack/short-video-factory/actions/workflows/sweety-handdraw-068.yml
選擇本分支，Run workflow：

- operation=validate：只跑既有與上傳安全測試；不配音、不渲染、不讀 Drive 憑證。
- operation=render：使用已準備的 job_id、seconds、style。save_to_drive 預設 true，先檢查 Drive 授權和目的資料夾可寫入，再開始製片。save_to_drive=false 僅用於隔離製片測試，不能宣稱已自動保存。
- operation=archive：archive_run_id 填已完成渲染的來源 Run ID，下載該次 sweety-068 成片 artifact，核對、完整解碼並保存。只重做保存，不重新產生配音或 MP4。

PR 只跑 routing-checks，render/archive 都跳過。既有 active-job.json push 入口保留；本分支未改動 main。

## Actions 專用授權契約

GitHub Secret 名稱：GDRIVE_AUTHORIZED_USER_JSON。內容為 Google OAuth authorized-user JSON，必須包含 type=authorized_user、client_id、client_secret、refresh_token，以及 scopes 陣列，唯一 scope 為 https://www.googleapis.com/auth/drive.file。

此 scope 只允許該 OAuth app 已建立或經使用者選取授權的檔案。目的資料夾由 ChatGPT 另一個 app 建立，並不因此自動對新 OAuth app 可見；必須用同一個 OAuth app 的 Google Picker 等官方流程選取上述資料夾。僅貼 folder ID 或取得 ChatGPT Drive 連線不能代替此步驟。preflight 會實際讀回資料夾 capabilities.canAddChildren；不通過就不啟動渲染。

不使用全 Drive scope、service-account key、公開上傳網址或對話中的密鑰。Secret 不寫入程式、artifact、快取或日誌。未建立可用 OAuth client 前不應填假憑證；不使用即將過期的 Playground token 冒充永久部署。外部 OAuth app 若仍在 Google Testing 模式，需核對 refresh token 期限，不能宣稱長期有效。

## 保存驗證與恢復

- 只接受一部匹配 acceptance.json SHA256 的 ENGINEERING_PASS / SUCCESS、068 成片，並要求非空字幕。
- 核對 H.264/AAC、1080×1920、30fps、回執片長、無額外字幕軌及完整解碼；保留 human_listening=UNCERTAIN 等原有驗收邊界。
- Drive 以指定資料夾與 appProperties.sha256 查重；同檔重用、不覆寫。上傳採 resumable、有限 chunk 數、num_retries=0；保存作業使用共用 concurrency 避免互撞。
- 保存後讀回 parents、size、md5Checksum、SHA256 屬性與 webViewLink，全部符合才保存 drive-receipt.json。結果不確定就停止，後續 archive-only 先查重；不無限重試。
- 成片 artifact 在保存前已獨立上傳，保留30天；Drive 回執保留90天。僅雲端保存失敗時接續 archive，不重跑成功渲染。

## 官方依據

- https://developers.google.com/workspace/drive/api/guides/manage-uploads
- https://developers.google.com/workspace/drive/api/guides/search-files
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.credentials.html
- https://github.com/actions/download-artifact/tree/v4

## 尚未驗證

Actions 實際 Drive 寫入、全新題材成片測試與新的 MP4 下載連結均未完成。單元測試使用模擬 Drive 回應，不代表 OAuth 或 Google 實際上傳成功。

