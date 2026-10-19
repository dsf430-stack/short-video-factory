# 統一動畫入口

這是五套真實專案的整合模組，新增於既有短影音工廠。Xilo 統籌製作；Lemo 提供導演與電影風格；MG 提供 motion design 提示詞及評分；大師提供中文解說模板；花叔提供藝術配方、解說語法和影片門禁。

## 已完成能力

- 五來源固定 commit、可接續安裝，已下載相同版本就不重抓；有本地修改拒絕覆蓋。
- `catalog.json` 收錄 111 筆具真實檔案的來源條目：Lemo 43、MG 15、大師 8、花叔藝術 36＋語法 9。這是來源條目數，**不是 111 種去重後風格**；大師 README 寫 7，但當前目錄實際有第 8 套霓虹賽博。
- `brief` 按指定風格、題材、片長、畫幅、現有旁白產生 job.json 與可交給 coding agent 的 brief.md，來源文件按需載入。
- 統一 HTTP 渲染器接收 `render(t)`、`seek(t)`、`renderFrame(t)`，支援素材 prepare、ready 門檻、確定性檢查、頁面錯誤拒絕交付、實際音軌與完整解碼驗證。
- 068 保留既有官方專案入口；只把其已產生的音檔當輸入，不重新實作聲線。

## 使用

```bash
python motion_hub/hub.py bootstrap
python motion_hub/hub.py validate
python motion_hub/hub.py list
python motion_hub/hub.py brief --topic '台灣經濟發展' --style lemo-opuscar:crayon-book --duration 60 --size 1080x1920 --audio /absolute/narration.mp3 --out /absolute/new-film
python -m pip install playwright
python -m playwright install chromium
# coding agent 先讀 brief.md，編寫題材專屬 index.html 後再渲染：
python motion_hub/render.py /absolute/new-film/index.html /absolute/new-film/film.mp4 --duration 60 --size 1080x1920 --audio /absolute/narration.mp3
python motion_hub/.sources/huashu-art-motion/scripts/film_gate.py --help
```

`--root` 可設定 HTTP 素材根目錄，保留 Lemo/MG 以 `/core/`、`/node_modules/` 為起點的資源路徑。重型 Three.js、Blender、原生專案 timeline 等依賴，按所選來源安裝；沒有把不同引擎的內部 API 混成同一個。大師模板须先依原流程生成 timeline.js；花叔參數化 spec 建議直接使用原生 `scripts/engine/render.py --spec ... --out ...`，以保留 spec 資產處理。

## 驗證與限制

`python motion_hub/tests/verify.py` 實際渲染三種頁面契約，每支兩秒，合成已有 068 真音檔；此測試只驗證渲染與音軌串接，不代表每套風格已逐一出片。

這些專案是 AI 製作指南、程式模板和渲染工具，並沒有一個共通「輸入題目自動產生所有動畫」API。題材場景仍須由 coding agent 編寫。未加入 Electron 桌面選單，也未宣稱所有畫風已在 Linux 通過。影片交付前須另過花叔 film_gate、抽幀及聲畫人工檢查。

全部來源程式文件是 MIT；第三方字體、圖像、音樂保留個別授權。大師作者口播、花叔作者角色和 Clawd 示範形象不當作新影片素材。來源只固定引用與下載，不把示範聲音或角色搬進專案。
