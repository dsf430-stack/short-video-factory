# 玻璃纖維白板短片

約31秒、9:16、七場景。原始白板逐筆引擎沿用已驗證History_Project_068_Fixed.zip內render.html與scene-dsl.js；新片使用完整繁體中文字型的子集。

068新旁白由short-video-factory commit 104107733424b8d60833ac37a00f3e20210ae9a1的smart_voice/generate_voice.py產生。GitHub run 38249536043。聲線zh-TW-HsiaoChenNeural，語速+20%，音調+5Hz，每段最多300字。MP3/SRT/JSON已取得；七句字幕使用服務真實SentenceBoundary。

## 內容與來源

1. 熔融玻璃抽絲、紗織成布、電子級布用於印刷電路板：台玻產品介紹與年報。
   https://www.taiwanglass.com/tc/pdf/TG2025ANNUAL.pdf
   https://www.taiwanglass.com/tc/pdf/2014annual_brief.pdf
2. 玻纖/FRP用於船身、管線、風電與PCB：巨石官方業務介紹。
   https://www.jushi.com/en/business
3. 玻璃補強材料用於風能、工業與交通：Owens Corning官方資料。
   https://investor.owenscorning.com/investors/stock-performance-and-earnings/press-releases/press-release-details/2025/Owens-Corning-to-Sell-Glass-Reinforcements-Business-to-Praana-Group/default.aspx

本片是概念科普，示意線條不是工廠影像。玻纖本體和玻纖加樹脂成形的FRP有區分；没有宣稱所有玻纖均使用相同樹脂或製程。配樂與提示音由finish.py原創合成，未使用外部音樂。

## 重製

保留output中的本次MP3、SRT及JSON，不重配。已有依賴重用，缺少時npm install --ignore-scripts。需Node24、Python3、FFmpeg/FFprobe、完整繁體中文字型。FIB_FONT設為包含本稿與畫面文字的字型。

FIB_FONT=/absolute/font.otf node --expose-gc render.cjs
python3 finish.py

render.cjs生成畫面、七場景抽查PNG和timeline.json；finish.py生成原創BGM/SFX，側鏈混音、偏移字幕、有聲MP4與QA。輸出另存，不覆寫既有影片。最終狀態以output/qa.json與checkpoint.md為準，手機與主觀試聽未確認時仍標為UNCERTAIN。
