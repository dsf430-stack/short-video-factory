# 2026-10-13 原始人穿衣 60 秒完成紀錄

狀態：SUCCESS（技術與編碼畫面抽樣）；主觀聽感、手機播放 UNCERTAIN。未發布。

成品：output_prehistoric/人類怎麼開始穿衣服_原始人動畫_60秒_v01.mp4
SHA256: 1f012a13c3806af487aafe3a5aa47bc075f5add4bedfd52118134b6233078e88
60 秒、1080×1920、24 fps、1440 幀、H.264/AAC；完整解碼 PASS。
六段 MP3 文稿雜湊及 068 設定 PASS；第 1 段沿用已完成本故事音訊，2–6 段 GitHub Actions run 38367872337 SUCCESS。
正式 main 104107733424b8d60833ac37a00f3e20210ae9a1；隔離分支 video/clothing-stickman-068-20261013，沒有合併或修改 main。
所有六段原文完整，未剪短、未再加速。音訊逐段相關性 >0.996；限幅器約4.96ms延遲在10ms字幕容差內。
整片實測 -15.17 LUFS、-6.06 dBTP。

過程與修正：
- OpenArt 可用40點，影片最低50點，未啟動付費生成。採既有 Pillow/FFmpeg 原生分層合成，不冒稱外部AI影片模型生成。
- 初版披肩姿勢缺髮，透過 imagegen 修正為同一撮三角黑髮。
- 原背景重複石器與獸皮，改用空桌背景與獨立道具圖集。
- 幾乎透明的圖集邊界造成角色定位偏移，改用 alpha >24 的可見邊界測量；保留原圖集，僅動畫取樣。
- 道具圖集獸皮跨越中心，使用明確取樣窗口而非盲目四等分。
- 項鍊從姿勢層拆出作單一移動圖層，明確由固定腰袋移向手部與頸部。
- PNG 預覽末檔曾讀取為 truncated；改為臨時檔寫入完成再原子 rename，重驗六張 PASS。
- 音訊樣本零位移相關性檢查先失敗；量得全部六段一致約5ms限幅器延遲，改成有限10ms對齊校验；未修改旁白或掩蓋截音。

來源與字幕：sources_prehistoric.md、full_script.txt、output_prehistoric/完整旁白字幕.srt。完整 QA：output_prehistoric/qa.json。
原本10秒幾何火柴人試片、所有旧專案保留。
下一步：使用者觀看60秒成品；若要改人物、動作或節奏，從此包及 render_prehistoric.py 接續，不重製配音、不覆寫v01。
