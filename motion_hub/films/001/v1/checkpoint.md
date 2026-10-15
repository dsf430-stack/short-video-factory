# 001 v1 checkpoint
狀態：失敗（首張代表靜幀；等待使用者確認最小修復）。尚無MP4，不得標示技術通過。
編號：001；中文：裝飾藝術；catalog ID：lemo-opuscar:art-deco。
來源commit：fdc46d7f0e20cc953a71d56241a92d1b4cb7298e。
基底：integration/motion-hub @ 3e2f721af4a52bab50be8f6db199f64b85984ef1。
獨立本地分支：test/motion-001-v1；尚未推送GitHub。main與068原碼未修改。
最新整合Actions：https://github.com/dsf430-stack/short-video-factory/actions/runs/38667344242，success，只是既有smoke測試。
本輪無Actions，使用官方相容本地渲染入口。
已完成：讀取整合四文件、來源README/STYLE/DIRECTOR/TECHNIQUE及引擎API，固定版本下載成功；068新旁白SUCCESS，16.64秒，完整解碼、字幕覆蓋及非靜音檢查由既有生成器執行；保留原MP3/SRT/JSON及20秒補靜音WAV。新作主觀聽音尚未確認。
001～111依既有catalog原始順序凍結至numbered-catalog.json；未找到先前獨立編號表。本輪001為第一筆Art Deco；002為ASCII CRT。
故障：index.html初始window.render(0)→frame→line→D.gline→offsetPoly→nrm，TypeError: Cannot read properties of null (reading '0')。line包裝預設double:true，首幀part:0，polyPart回傳單點，offsetPoly無相鄰向量。來源未修改。
最小修復提案：本片line包裝遇到o.part<=0直接return；只改本片，不改上游引擎。等待使用者確認後修改，再做三張靜幀、完整20秒有聲渲染、film_gate、抽幀與音量檢查。
畫面、動畫、風格、film_gate、獨立評分：均未通過／未執行。使用者觀看：未確認。
尚未製作音樂、ASR；四種透視鏡頭及完整Lemo藝術門檻未滿足，不聲稱通過。
下一步仍是001，不能直接測002。

2026-10-15接續：使用者「對」已確認最小修復；line包裝僅加o.part<=0時return。still-10.png代表畫面成功、已目視檢查。完整渲染中。新提供測試標號.txt確認001～111與本輪對照完全相同。

## 本輪結果
狀態：失敗（品質門檻）；成片技術通過。
MP4：001_art-deco_v1.mp4，20秒，1080×1920，30fps，600幀，H264/AAC；確定性與完整解碼SUCCESS。
抽查12張成片靜幀：0.5/1.5/3.5/5.8/7.6/9.8/11.8/12.8/14.5/16/18/19.7秒，未見黑畫面、缺素材、亂碼、主體裁切或文字溢出。未完整逐秒人工觀看。
風格可見特徵：暖黑底與金色雕刻線；階梯拱框及放射幾何；中央對稱開合；主角青綠色、金屬漸層體積。僅可見特徵核對通過，非完整Lemo藝術認證。
動畫：抽幀可見上升、收束凝結、成雲、下降降雨與海面波紋。
聲音：真實068旁白，16.64秒，保留20秒內收尾靜音。成片實測-13.15 LUFS、true peak -0.26 dBTP（高於來源建議-1）；未聽音，辨識／截斷／主觀聲畫同步未確認，未執行ASR。
film_gate：RED，fast_ratio=0.0298<0.035，前10秒0.0168；blank_run=0、blue_purple=0；page_frame_share=0.95 黃燈。未執行獨立藝術評分。
最小修復建議：下一版僅調整前10秒主體動作，增加同一水滴從海面上升、凝結的可見位移及聚合動作；不更換風格、不改旁白、不改門檻。聲音峰值與固定外框作另項待修，不混在同一次核心修改中。等待使用者確認後另存v2。
使用者觀看：未確認。下一工作仍001重測；002 ASCII/CRT尚未開始。
