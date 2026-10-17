# 手繪影片：免額外模型 API 的直接製作流程

## 使用者只需提供

- 題材或完整腳本
- 畫風（未指定沿用官方 4 號）
- 片長（未指定 30 秒）

固定沿用 068：zh-TW-HsiaoChenNeural、+20%、+5Hz；1080×1920、30fps、繁體中文大字幕。使用者不用手動做素材、改索引、改程式或操作手機部署。

## 助手接力到成片

1. 新腳本直接用 `handdraw/preparation.py` 建任務；保留 source-script.txt 與雜湊。相同主題的不同稿、片長、畫風使用不同 job_id。無須題材範本或 catalog 登錄。
2. 在 ChatGPT 完成因果核查、完整旁白、分鏡與自然長短候選。先用 `produce.py --voice-only` 實測完整 068，素材未完成也能測聲音。若不合秒數，修改自然腳本後繼續；不得停止在「請使用者備素材」。
3. 按固定官方引擎的完整畫風配方、美術指導與 drawing-plan preflight 準備圖；使用 ChatGPT 內建生圖及可用既有素材，無須 Gemini/OpenAI 等額外模型 API Key。新題材重新設計，不改舊片標題充當新片。
4. 實際查看圖片後標註語義部位、遮擋、來源、畫風與敘事審查。用 `handdraw/check_bundle.py` 呼叫原版官方檢查器及 build_illustration，修復所有可重現問題再提交。不要偽造視覺 pass。
5. 使用 `handdraw/activate.py --job-id 實際ID` 寫入 active-job.json，連同本題材素材提交 GitHub。main 的 active-job.json 更新會自動啟動原有 Actions；也可透過既有 Actions request bridge 以 job_id 啟動。
6. Actions 以精確任務、片長及畫風產生獨立輸出與快取，完成整篇旁白、實際句界字幕、官方逐筆動畫、完整解碼與片長驗證。缺字幕/紀錄或設定不符的音訊快取會按原聲音設定重建，不直接停住。
7. 助手追蹤 Actions 到完成，下載成片，檢查全部分鏡的繪製與完成畫面、字幕及音軌，保存免解壓 MP4 並交付 MP4 和 Actions 連結。更新 PROJECT_STATUS.md；不要只給 ZIP 或「已提交」。

## 誠實區分兩個執行環境

內容理解、腳本、生圖與看圖由當前 ChatGPT 助手執行，GitHub 執行已準備任務的配音與渲染。這就是使用者選定的完整流程，沒有額外模型 API Key 也可出新題材。不要改成「需要付費 API 才能繼續」。GitHub runner 單獨收到未準備腳本時會保存 PREPARATION_REQUIRED 供助手接續，它沒有自帶 ChatGPT 生圖能力。

預設無配樂。主觀聽感若無可用聽音能力，必須保留未驗收；不承諾任何腳本在任何環境都零失敗。以具體腳本的完整實測和已知限制為準。
