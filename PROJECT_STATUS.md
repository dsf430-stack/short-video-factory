# 現行模式：ChatGPT 備料 → GitHub 出片（免額外模型 API）

2026-10-17：依使用者要求，已在 AGENTS.md 與 WORKFLOW.md 加入效率及不中斷規則：素材檢查通過立即提交/啟動、同題換畫風重用已確認配音與時間軸、預先驗證輪廓可描繪性、按實際 run 接續到 MP4 交付。這是執行規範修訂，不更動引擎或聲音設定，不重新製作已交付影片。

使用者已確認維持原本流程：在 ChatGPT 提供題材或完整腳本、畫風、片長，助手完成腳本、內建生圖、看圖、素材與提交，GitHub 執行 068、字幕、官方逐筆動畫與 MP4 驗證。不需要題材範本或額外 Gemini/OpenAI 模型 API Key。未接付費生圖不再列為本流程的剩餘卡點。

## 本次通用入口修復

- 新增精確 job_id，原腳本雜湊、片長、畫風共同識別任務。同名不同稿不再任選一包；catalog 只作捷徑。
- 配音可在圖片未完成前先實測；固定 068 zh-TW-HsiaoChenNeural / +20% / +5Hz，不拉伸或截音。
- 完整快取核對包含原稿、聲線、速度、音高、音訊 SHA、字幕內容與時間結構；缺檔或錯稿重建對應快取，保留其他成功音訊。
- 取消固定 s0/s1 分鏡 ID，保留模型為新腳本設計的自訂 ID。
- 新增本地 check_bundle，使用未修改的官方審查及 build_illustration，先攔截語義部位/輪廓錯誤。
- Actions 從 active-job.json 或明確 inputs 讀取 job_id、topic、seconds、style，片長不再寫死；每個任務有獨立輸出與快取。main 提交 active-job.json 自動出片。
- 渲染回執改為完整驗證及格式/時長通過後才保存；壞掉的渲染回執會重建本任務。
- 統一 WORKFLOW.md、AGENTS.md 與 README，不再把使用者導向付費 API。原金鑰僅保留在 GitHub Secrets，不讀取或輸出；本分支不啟用 provider-readiness workflow。

## 全新腳本驗證：為什麼白天也看得到月亮？

- job_id：job-d7644ceac41308c6810d；官方 4 號完整配方、30秒、1080×1920、068、繁體大字幕、鮮黃背景。
- 此題材不存在於 catalog.json。直接由 ChatGPT 準備兩張全新雙格圖集，未挪用雨或颱風素材；封面使用已看圖素材與可控文字層。
- 原始腳本、NASA 來源、自然長短候選、出圖前分鏡/簡報/提示詞/哈希、實際看圖與語義部位審查均保存在新任務包。
- 先實測完整配音，自然重選後旁白28.656020833秒 + 封面1秒 + 收尾0.343979167秒 = 30秒。已將此 MP3、字幕、聲音設定和 SHA 放入素材包；本地重驗 VOICE_CACHE_HIT，無需重配。
- 本地前兩幕原版檢查通過；第三幕發現 `horizon_sun` 橙色輪廓無可描繪黑線，按官方支援的 aligned outline_mask 保留可見橙色筆畫，原圖像素未變。重新看過遮罩，四幕均通過原版 build_illustration。
- 14項單元測試通過，任務解析/自訂ID/缺漏與錯稿快取/無圖片先測聲音均已驗證。
- 第一輪 Actions SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39019030134 。已實際產出30秒、1080×1920、900幀 H.264/AAC，完整解碼通過，音軌相關度0.99997568、尾句0.99994786。
- 實際看13個時間點後發現首句問號孤立換行；保持52px大字幕、原配音與所有實測句界，新增字幕寬度預檢（不改官方引擎），避免行首閉合標點。新增標點與說明文字/字幕間距回歸測試，合計14項通過。第二輪Actions成功並修好標點；看圖發現末幕兩行字幕與註解太近，加入實際字型高度與48px間距預檢，第三輪已完成實際成片重驗。

## 已完成且保留

颱風影片已交付，Actions SUCCESS： https://github.com/dsf430-stack/short-video-factory/actions/runs/39015702590 。30秒、1080×1920、H.264/AAC，SHA256 c6fc9f10746cd1cbc2def685aaf7a44352ced1cfe3f50793bb1d92a222bbc765。歷史診斷及先前方案釐清保留於 integration_checkpoints/handdraw-20261017-typhoon.md；本次不重做該片。

## 驗收邊界

完成工程及圖片/字幕檢查才回報可交付；沒有實際聽音能力時保留主觀聽感未驗收。預設無配樂。不能保證任意腳本、任意環境永遠零失敗，助手須按實際 Log 修復並接力到成片，不把 PREPARATION_REQUIRED 或「已提交」當完成。

## 最終交付與可接續狀態

- 第三輪 Actions SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39019605523 。
- 成片 Moon_Daylight_Style04_068_30s.mp4：30.000秒、1080×1920、30fps、900幀、H.264/AAC；SHA256 5489093f2a0ec6f7ff1d169c8878bb008b21d32f2dd958eba113d4c91d6bc371。下載後再次完整解碼通過。
- 實際看13個時間點（封面、各幕描線/填色/完成、結尾），已修正問號孤立換行及末幕註解/字幕間距；52px字幕、原始配音與句界保留。
- 官方全部工程檢查通過，音軌與原旁白相關度0.99997568，尾句0.99994786；沒有截音、拉伸或新增模型 API。主觀聽感仍為UNCERTAIN，未偽造人工聽音或官方finalize成功。
- 詳細驗證：handdraw/verification/moon-20261017.json；修復與新素材已透過PR #9合併main（3e6f8dc01700deaeaf60a315113b224133e809ff）。
- 以後在ChatGPT提供題材/腳本、畫風、片長即可接力；GitHub只負責已準備任務的語音、字幕與官方動畫渲染，沒有額外模型API時不會自行理解或生圖。

- main部署後驗證SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39019877970 。14項測試通過，直接使用既有068旁白。交付已更新為main實際MP4，重新完整解碼與13點看圖通過，原分支成片也已驗證；兩次輸出不以位元相同為驗收條件。

## 已完成：官方13號北歐紙雕・月亮冷知識

- 使用者指定「13月亮冷知識」；沿用30秒、1080×1920、30fps、068原設定與已實測的白天月亮腳本/句界，無額外模型API。
- 新job_id：job-d158225f04c9fad3ceaa。兩張全新紙雕圖集，使用完整官方13配方及已核對/看過的官方參考圖；未沿用4號小豆人圖片。
- 出圖前計畫、逐圖簡報、完整提示詞與內容哈希皆先保存；實際看圖後核對反射箭頭、日間地平線及雲層遮擋，對齊輪廓層保留原始3D紙雕像素。
- 四幕原版build_illustration皆通過，素材ASSETS_VALIDATED；配音VOICE_CACHE_HIT，28.656020833秒＋封面1秒＋收尾0.343979167秒。
- main Actions SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39024020289 。14項測試通過，原068旁白快取直接重用。
- 已交付 Moon_Facts_Style13_068_30s.mp4：30.000秒、1080×1920、30fps、900幀、H.264/AAC。SHA256 73ce18fcb8311bc9996c76626fc2a26aebd5637a731198846337bd9105f9cbd5。下載後完整解碼通過，已實際看13個時間點及14.2/29.5秒完整畫面，紙雕描線/填色、反射箭頭、雲層遮擋、繁體大字幕與文字間距通過。
- 詳細證據 handdraw/verification/moon-style13-20261017.json；官方工程檢查通過，主觀聽感仍UNCERTAIN，預設未添加背景音樂。

## 已完成：官方6號原子筆單線塗鴉・鉛筆芯其實沒有鉛

- job_id：job-637378837c79e0ffd659；30秒、1080×1920、068原設定、繁體大字幕，無額外模型API。
- 題材來源為Faber-Castell官方石墨/黏土與硬度說明，限定一般木製黑鉛筆，不擴大為彩色或聚合物筆芯，也不加入醫療或食用安全聲明。
- 已完成81組自然腳本候選；實測後選41，旁白28.488020833秒，封面1秒，收尾0.511979167秒。完整旁白與句界已鎖定，未拉伸/截音。
- 完整官方6號配方、出圖前計畫、逐圖簡報/提示詞/哈希保存；代表畫面先通過原版build_illustration才擴展第二張圖集。實際看過全部四幕及封面。
- 四幕素材ASSETS_VALIDATED後已提交main並啟動既有Actions，SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39031805018 。14項測試通過。
- 已交付 Pencil_Fact_Style06_068_30s.mp4：30.000秒、1080×1920、30fps、900幀、H.264/AAC；下載後完整解碼及13個時間點看圖通過，四幕逐筆動畫、素材/痕跡對應、繁體字幕與註解間距已核對。SHA256 3a31fd9e34d89117ff62cd273afaede727208bf2dc9ab434c7f84454538f69fc。
- 證據 handdraw/verification/pencil-style06-20261017.json。音軌工程檢查通過，主觀聽感仍UNCERTAIN；預設無配樂。

2026-10-17：依使用者用量疑慮，在WORKFLOW.md補充只讀必要變更、只回傳必要摘要、合格素材不額外生圖的規則；無逐項扣量明細，不推算費用占比。


## 已完成：皇太極：從後金到大清帝國（2026-10-19）

- 獨立 job_id：job-huangtaiji-ink08-20261019；完整原稿與史實修訂均保存在任務包。保留權力集中、制度改革、朝鮮蒙古與對明戰略、松錦之戰及身後影響四段主軸。
- 官方 sweety-handdraw-video 固定版本 5206ec0d17f9b353e400b64b9c51ad69e721e02a；官方8號完整水墨寫意規範，八幕全新素材，實際看圖及原版 build_illustration / check_bundle 檢查通過，使用 waner-brush 毛筆揭示。
- 068 zh-TW-HsiaoChenNeural，+20%、+5Hz，完整實測 PCM 176.232秒；封面1秒、收尾0.3秒，影片177.533333秒。依真實 WordBoundary 產生繁體52px大字幕，不截音、不強制30秒，無背景音樂。
- Actions SUCCESS：https://github.com/dsf430-stack/short-video-factory/actions/runs/39223177613 。15項測試通過。修復長篇字幕、自然片長及毛筆選擇，其他任務保留原預設。
- 已下載最終 MP4：1080×1920、30fps、5326幀、H.264/AAC、31,793,494 bytes；SHA256 72bc2bcef33556ab8469a96535a440da7d95afddba5800314f718ec6cabd5f92。下載後再次完整解碼通過，官方全部工程檢查通過。
- 實際檢視封面及各幕畫面，最終11個時間點重驗肖像裁切、單行字幕與結尾；先前26點檢視問題已修正。音軌相關度0.99997477、尾句0.99994774，尾端靜音0.972秒。主觀聽感 UNCERTAIN，未宣稱人工聽音。
- 詳細證據 handdraw/verification/huangtaiji-style08-20261019.json；可直接播放的完整 MP4 已保存交付。
