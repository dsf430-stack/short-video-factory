# 圍魏救趙：068 有聲繪本翻頁版

本交付包接續068有聲繪本程式，使用已驗證的GitHub新配音。六張圖片由內建圖片生成工具生成，畫面是古籍水彩插畫；不是人物動態影片。人物對話為兒童版改編。歷史主線已核對教育部成語典與《史記》孫子吳起列傳，見manifest的sources。

## 成品與來源

- 六頁固定插畫；相鄰頁面透視翻頁0.64秒，翻頁在新頁旁白開始前完成。
- 068曉臻：zh-TW-HsiaoChenNeural，+20%，+5Hz。
- 已生成的MP3/SRT/JSON沿用GitHub run38204582549，沒有重新合成語音。
- 字幕14句，依語音事件時間，不平均猜測；排版換行不改原文。
- 混音包含旁白、原創程序生成的五聲音階配樂與合成環境音效。配樂及音效為本次程式生成，不是聲學鋼琴、古琴或實錄素材。
- 環境聲包含柔和風声、馬蹄/腳步節奏、紙張、鳥鳴及翻頁沙沙聲。無爆炸、尖叫或血腥聲效。
- 固定低增益混音，auto_ducking=false，不宣稱自動ducking。
- 字型Noto Sans CJK TC，授權見font-license.txt；來源notofonts/noto-cjk。

## 重新合成

需要Python3、numpy、Pillow、FFmpeg及FFprobe。已有依賴請重用，不需再次配音。解壓後在包根目錄執行：

```bash
python3 render_cached_book.py weiwei_v1/manifest.json
python3 render_flipbook.py weiwei_v1/manifest.json
```

已有已驗證的mixed_audio.wav與QA.json時，直接執行第二步即可；只有缺少這些工件時才執行第一步。第一步產生並校驗音訊混合與字幕，第二步使用相同混合製作固定頁面與透視翻頁。book_media.py沿用原版068的共用FFmpeg函式，不包含舊語音合成入口。要產生新文字配音，必須依GitHub最新main的smart_voice/068_CALL_INSTRUCTIONS.md執行。

輸出：weiwei_v1/output/Weiwei_Jiuzhao_068_flipbook_v1.mp4、Weiwei_Jiuzhao_068_audiobook.mp3、subtitles.srt、獨立背景音樂與音效、QA_flipbook.json。

## 驗證界線

技術完整解碼、音量、時長、音軌、字幕時間及畫面抽樣均須依QA與checkpoint判讀；手機試聽與主觀音色仍需播放確認。不以音軌存在宣稱已人工聽過。未發布到社群。

KB_02_繪本敘事工程規範.md.txt目前只有「12」，沒有完整規範，故本次不宣稱符合未取得的完整KB_02。

## 多角色與地圖版（2026-10-12）

已實測三個聲線：旁白068/zh-TW-HsiaoChenNeural、田忌ZH_Yunjian/zh-CN-YunjianNeural、孫臏ZH_Yunxi/zh-CN-YunxiNeural。全部+20%/+5Hz。原M01-M05為英文，原代號不更改；中文男聲使用明確ZH別名，不與其他技能M02混淆。

`generate_cast.py`沿用smart_voice/generate_voice.py的新服務網址与校驗器，僅合成新角色台詞，依SHA重用原068旁白片段。`.github/workflows/storybook-cast.yml`在更新cast_story.json時執行，可取得068-cast-output。此測試流程的旁白來源固定為本次圍魏救趙run38204582549；該artifact保留至2026-10-19。其他故事或來源過期時，先準備新故事的已驗證旁白，更新來源run、檔名、SHA與旁白時間範圍，不直接套用本次舊素材。

多角色實測run38207878517 SUCCESS。`add_dialogue_map.py`接收`--events narration.json`，依實際角色音訊時間顯示姓名與台詞；地圖動畫依語音事件顯示魏攻趙、齊進逼大梁、魏回援與桂陵迎擊。標示策略示意且不按比例，不宣稱精確古代地理。沒有口型動畫。

新增畫面入口：

```bash
python3 add_dialogue_map.py weiwei_cast_v3/output/Weiwei_Jiuzhao_068_flipbook_v1.mp4 --font weiwei_cast_v3/fonts/NotoSansCJKtc-Regular.otf --events weiwei_cast_v3/narration.json --output weiwei_cast_v3/output/Weiwei_Jiuzhao_Cast_Dialogue_Map_v3.mp4
```

依角色音訊的新時間軸重排六頁及翻頁。可透過manifest的audio_assets指定已存在的配樂及重排音效，避免重新製作成功素材。主觀聲音偏好與手機試聽仍待使用者確認。
