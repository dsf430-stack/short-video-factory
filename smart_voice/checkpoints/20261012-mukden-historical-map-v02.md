# 九一八真實歷史地圖版 v02 接續紀錄

狀態：SUCCESS。使用者認為v01地圖難看，要求上網找地圖。v02已改用真實歷史地圖並完成有聲影片。v01與原068音訊保留。最後完成：七場成片抽查、動態事件箭頭核對、音訊串流與v01相同核對。無阻塞；下一步為使用者檢視新版並依具體回饋調整。手機播放及主觀試聽UNCERTAIN。

## 已完成

- 真實1928年南滿鐵路公司東北地圖與1930年瀋陽市街圖，來源與署名見README_v02.md。
- 數位鏡頭放大移動、短交叉轉場、中文城市標記、動態鐵路高亮與事件箭頭。
- 瀋陽市街圖未含柳條湖爆炸點；事件節點在独立卡片，明示不是圖上精確定位。
- 42秒，1080×1920，24fps，1008幀H.264/AAC，有068旁白與繁中字幕。
- 原旁白MP3 SHA與文字SHA核對PASS；v02的AAC音訊串流SHA与v01完全相同PASS，未重新配音。
- 完整解碼PASS；七個實際成片場景視覺抽查PASS；中文字型完整涵蓋PASS。
- 同一事件卡片23.0秒/25.5秒的箭頭亮色像素877→4078，動態驗證PASS。

MP4 SHA256：8bf6640143fad6bfcbcbe46487f2e9142508cc08eea81f30e81ee0f8784193f6

下載工作流：https://github.com/dsf430-stack/short-video-factory/actions/runs/38266119159
素材artifact SHA256：44742c2579d22371afa3bf9b784e7f3a43ab8a331867b2dc2d9c9c9de33aab5f
分支：video/mukden-map-068-20261012；main與既有聲音程式沒有修改。

## 本輪失敗與修正

1. 本地直接取Wikimedia與LoC返回HTTP403。工作修正：使用已驗證GitHub Actions網路下載已核實來源的原始JPEG，再用connector下載artifact；SHA核對PASS。不要再本地直連同一路徑反覆重試。
2. preview-5.png一次PNG寫入不完整。底層原因UNCERTAIN，未忽略損毀。重新渲染該預覽並用臨時檔加原子替換，所有PNG解碼PASS；預覽存檔程式已改原子替換。
3. 動態檢查的575px奇數crop被yuv420裁成574px，NumPy reshape失敗。根因已定位，改成574px及偶數座標；箭頭像素增加PASS。不要對YUV420輸出假設奇數裁切寬度。

## 重製

按README_v02.md保留包內相對路徑即可運行。沿用output/mixed.wav与配音MP3/JSON/timeline，不再下載依賴或重新配音。程式拒絕覆寫同名成片。改稿需重新建立字型子集并驗證。
