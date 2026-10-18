# 2026-10-18｜新增25支生活英文影片完成

25份新旁白均使用main既有 `smart_voice/generate_voice.py`、`voice-068.yml`，068曉臻 zh-TW-HsiaoChenNeural / +20% / +5Hz。沒有修改聲音程式。新任務由25份 `.github/action-requests/new25-*-068-20261018.json` 啟動。

沿用本次對話既有10月9日生活英文系列的素材與原render_batch.py，不改動手繪系列的active-job或畫風。編號ENG-20261018-161至185；25個不同物件／原稿／AI圖像／MP4 SHA。

25支MP4均已完成：1080×1920、24fps、H.264/AAC、17.791667至20.458333秒；中文字幕與英文例句按真實句界對齊；保留原BGM。完整解碼、五階段影片與來源畫面比對、125個實際MP4抽幀看圖、來源、音量／峰值／旁白對BGM音量比皆通過。旁白對影片音軌最小相關度0.99548。主觀／手機試聽UNCERTAIN。auto_ducking unavailable，使用原固定增益。

雲端：https://drive.google.com/drive/folders/1bLpUAL9mP1UlgjIDojnqm0YAQPhX79VD
25份個別MP4、整批MP4 ZIP與來源接續ZIP均已上傳；25個檔名及位元組數逐一核對。詳細run ID、文字與音訊SHA、各片數據見NEW25_FINAL_MANIFEST.json、NEW25_GITHUB_RUNS.json與NEW25_DRIVE_INDEX.json。未發布到社群。

正確入口教訓：舊ZIP的speech.platform.bing.com 403不能代表GitHub已修正版本失敗；先讀main成功checkpoint再執行。Actions dispatch的head_sha可能隨main前進，不能單靠它對應旁白；以輸出檔名、原稿SHA、聲線設定、音訊SHA綁定run ID。

後續直接使用現有GitHub 068與已確認素材，不重配已成功音訊、不重做本批圖片或MP4。
