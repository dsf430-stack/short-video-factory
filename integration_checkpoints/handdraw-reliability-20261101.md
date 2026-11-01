# 手繪穩定性修復驗證｜2026-11-01

使用者授權直接修改，允許結構調整。保留原官方Sweety引擎 `5206ec0d17f9b353e400b64b9c51ad69e721e02a`、068與既有已審查素材。

## 可重現根因

1. check_bundle原先未檢查pixel_sha256，正式produce卻在配音後直接讀取此欄位；造成素材宣告通過但下游仍失敗。
2. 素材檢查未覆蓋正式官方美術/敘事設計檢查；啟用僅依檔案存在，缺少可驗證的當前檢查回執。
3. 每次嘗試缺少一致階段狀態；渲染完成到最終驗收間中斷時，缺少能安全接續的輸入回執。
4. 同一路徑既有voice檔案被無條件保留，可能忽略任務包更新的已授權母帶；舊design與input檔案也可能殘留。
5. ubuntu-latest、寬鬆Python依賴會漂移。run41267990364證實runner已變成Ubuntu26.04；這次鎖定24.04與已實測依賴，未把漂移虛指為該run根因。
6. 最新佛教起源失敗其實缺備料：run41267990364第2次在resolve即報PREPARATION_REQUIRED，與渲染或配音故障不同。

## 已合併修復

- 共用bundle_contract檢查；正式製作在配音前執行與check_bundle一致的完整官方素材驗證；不補造看圖pass。
- 新啟用必須有與當前素材、設定及驗證程式匹配的asset-validation.json；舊已啟用任務仍完整前置重驗。
- pipeline-state.json保存每階段狀態與原始錯誤；外部製作命令上限30分鐘，逾時終止程序群組，Actions上限60分鐘。
- 配音成功快取保留；任務提供的音訊優先，並再次驗證內容與設定。修復壞JSON聲音快取、voice-only缺畫風素材、seconds=0偷偷沿用舊秒數等分支。
- 渲染完成保存render-input.json，輸入與官方render-record完全相符才能重用；最終驗收失敗撤銷回執；新嘗試不殘留舊acceptance。
- 固定Ubuntu24.04、Python3.11、Bun1.3.0及19項Python依賴；記錄實際FFmpeg/套件版本。系統套件仍由apt提供，未宣稱容器級或位元級重製。
- PR對製作程式變動執行三案例真實MP4回歸；保留主觀看圖/聽音與工程檢查的區分。

## 實際驗證

程式提交：4307ac5e9ad776b1ef2154ddb9a8ff77f87eabf9  
PR：https://github.com/dsf430-stack/short-video-factory/pull/14  
main合併：339900c8636292320cd81ec7ba2c8db4ba191ad4  
最終Actions：https://github.com/dsf430-stack/short-video-factory/actions/runs/41269238666 （SUCCESS）

28項本地及Actions測試通過；三部均真正重新渲染，1080×1920、30fps、H.264/AAC，官方verify及ffmpeg -xerror完整解碼通過。

| 案例 | 實測片長 | MP4 SHA256 | 正式證據工件 |
| --- | --- | --- | --- |
| 一號自然片長 | 25.533333秒 | ea42581a7ca807c492153f457d8b68fdd73b80b49d2ca7ab62a0ef8821581578 | 13068856323 |
| 十三號目標片長 | 30.000秒 | 513442aa2405d23009fd93637cb1d9d81a509152e1931f4edd8ff2b8621f031b | 13068756482 |
| 十七號含授權靜音動畫 | 220.000秒 | 097ddb4afb2185a210fa68786a1c19c8ce1e7fc72345afbf8cf3c33defd41ce3 | 13067804616 |

短片先執行voice-only得到24.24秒完整旁白，再正式成片；刪除最終驗收回執模擬中斷後，STAGE_DONE render reused=True，重驗MP4 SHA不變。短片已下載再次完整解碼並查看3/8/13/18/23/25秒六點，確認實際描線與單一字幕；來源第二輪工件13067639341的MP4 SHA與最終版相同。十三號未另宣稱人工逐幀重驗；十七號SHA與既有已驗收成片完全一致。human_listening均UNCERTAIN。

首輪41268972989因新增回歸工作流漏裝Bun於layout失敗；已依官方clean_image需求補Bun並加入前置工具測試。第二輪41269100724與最終版41269238666三案例全部SUCCESS。沒有啟用額外模型API、重新生成素材、重新合成旁白或發布社群。

## 接續

佛教起源目前active-job為8號，仍缺正式素材，不屬於已出片。先依官方配方備料、審查、跑check_bundle取得新回執，再activate。不要重試未準備任務、移除門檻或用舊圖冒充。配音外部服務原有每段最多三次重試與成功段快取保留。
