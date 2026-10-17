# 最新結果（2026-10-17）

- 已完成颱風測試影片：官方 4 號完整配方、068 固定聲線/+20%/+5Hz、繁體大字幕、鮮黃畫布。
- 最終放大版 Actions SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39015702590 。前一版 SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39015459420 。
- 實際下載 MP4 完整解碼通過：H.264/AAC、1080×1920、30fps、900幀、音視訊各30.000秒、無額外字幕軌。SHA256 `c6fc9f10746cd1cbc2def685aaf7a44352ced1cfe3f50793bb1d92a222bbc765`。
- 已查看封面、四幕完成畫面（4.5/10.9/19.5/29.4秒）及四幕繪製過程（2/3、7/8、13/15、22/24秒）。修正主圖大小、空框標示及關鍵字，字幕與圖文無重疊；預覽是官方逐筆輪廓/上色，不是靜態替代。
- 最終版與前一版的 AAC 音訊資料完全一致；保留完整旁白及真實句界，PCM28.56秒+封面1秒+收尾0.44秒。官方聲音完整性、時間線及工程檢查通過；主觀聽感未驗收，未添加背景音樂。
- 已保存免解壓 MP4：Typhoon_Radius_Style04_068_30s.mp4（libfile_0a6135ce2b8c8191a9533b111c1b7ae3）。
- 三個單元測試通過，四格使用原版 build_illustration 的本地檢查通過。首輪手臂重疊失敗及修正保留於下方紀錄。

## 尚未完成：GitHub獨立任意腳本製作

這次已修復準備任務、素材驗證、實測旁白重選、字幕、圖集、快取及渲染；不能將本片成功擴大宣稱「任意腳本都能獨立全自動出片」。新題材仍需助手或接入的通用文字/圖片/視覺審查供應者備料。

無費用 readiness run SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39015557509 。只確認 GEMINI_API_KEY 存在，未驗證金鑰有效性、額度、付費狀態或呼叫生成 API，未列印金鑰。其他檢查名稱沒有配置。Google目前的 Gemini 3.1 Flash Lite Image 沒有免費層，1K輸出 US$0.0336/張，另計文字及重試（來源 https://ai.google.dev/gemini-api/docs/pricing ）。已向使用者告知，付費通用生圖尚未啟用。不可改用其他來源冒充官方素材或偽造圖片審查。

---

# 手繪製作診斷與颱風驗證

本次修復分支：fix/handdraw-topic-pipeline。官方引擎固定 5206ec0d17f9b353e400b64b9c51ad69e721e02a，聲音沿用 068 zh-TW-HsiaoChenNeural / +20% / +5Hz。

已證實原因：
- main 用 catalog 當允許清單，未知題材直接被拒。
- 素材準備原本完全依賴助手，沒有新題材 request 與缺項紀錄。
- 旁白不合短收尾範圍時直接停止，沒有自然腳本候選與實測重選。
- main 未帶入其他分支已驗證的字幕短句對齊、畫布色及標題設定。
- MP3 編碼長度與解碼 PCM 長度可不一致（歷史 run 38994415677）；以實際 PCM 測量。
- 快取指紋原本未包含指定片長與完整聲音設定。

已修改：新題材建立可續作 request、完整素材缺項回報及安全路徑檢查；自然腳本候選依實測語速重選及整篇重新配音；PCM 時長、固定聲音設定核對；圖集裁切和圖集審查 SHA 更新；短句字幕與大字；Actions 自動測試與新分支觸發、通用成片名稱及診斷上傳。

颱風素材：已按完整官方 4 號配方生成四格圖集並逐格看圖，保存生成前計畫、完整提示詞、美術指導哈希及實際圖片審查；封面獨立文字層；鮮黃色畫布。七級風定義依氣象署 W-C0034-005 文件 circle_of_15ms；圖為示意，不是實際颱風預報。

本地 3 個單元測試通過。完整渲染及 Actions：待本次真實執行結果，未標示成功。

尚未具備的能力：GitHub runner 沒有已配置的通用腳本/圖片生成與視覺審查供應者；ChatGPT 助手可準備新題材並提交後自動渲染，但不可將缺素材任務宣稱完整自動生成成功。原有雨題材與其他分支成果保留，不重做。

## 實際執行 39015296470

- GitHub Actions 已啟動：https://github.com/dsf430-stack/short-video-factory/actions/runs/39015296470
- 安裝、三項單元測試、068 整篇配音、素材/畫風/分鏡審查紀錄驗證及 doctor 通過。
- 自然腳本候選 24 解碼 PCM 23.0880208333 秒；自動重選候選 39 為 28.56 秒，收尾 0.44 秒，符合30秒要求。聲音設定未變，未拉伸或截音。
- build 真實失敗：`Part has no drawable outline; prepare a contour layer/mask before generation: s0_right_arm`。根因為第一幕兩手臂區域重疊，前方區域吃掉下臂輪廓。修正上下手臂 y 邊界，不更動已生成圖片或配音；本地使用原版 build_illustration 逐格重驗後再提交。
- 尚未產生最終 MP4，不回報成功。
