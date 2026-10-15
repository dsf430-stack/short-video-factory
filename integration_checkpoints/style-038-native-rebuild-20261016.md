# 038 重製處理紀錄（2026-10-16）

- 固定編號：038
- 原始 catalog ID：lemo-opuscar:tilt-shift
- 原始 commit：fdc46d7f0e20cc953a71d56241a92d1b4cb7298e
- 題材：大樓從開挖地基到完工，40 秒，1080×1920，30 fps，繁體中文字幕與 068 中文旁白
- 測試分支：test/style-038-building-40s
- 前次交付的 038_building_40s.mp4：**不合格，禁止當作原始 038 出片驗證**。原因：未使用 Lemo 官方 tilt-shift Three.js/post.js/city.js/sky.js/traffic.js 渲染流程，且替代 068 配音。
- 分支上的 motion_hub/jobs/038-building-40s/index.html：同樣屬於自製 Canvas 2D 版本，**不得用於 038 正式驗證**。
- 官方原始文件：styles/tilt-shift/STYLE.md、DEMO.md、demo/build.sh、demo/main.js 已查核。
- 官方流程：原始專案 core/render/video.mjs + demo/post.js 等 Three.js 模組，之後 core/render/mux.sh 混音。
- 現況：**失敗／待原生重製**，無合格原生 MP4、無 Actions 渲染 URL、無 068 音檔驗證。
- 阻礙：目前執行容器無法解析 github.com（git ls-remote 顯示 Could not resolve host: github.com）；GitHub connector 可讀寫程式碼，但未提供啟動新 workflow 的操作。不能冒充原生引擎已運行。
- 最小修復：在本測試分支新增使用官方 Three.js 模組的施工場景，配置 Actions 工作流程在 GitHub Runner 以固定 commit 取得 Lemo 原始碼，沿用已驗證的 068 音檔，透過 core/render/video.mjs 和 mux.sh 出片。執行後再檢查 ffprobe、完整解碼、抽幀與風格特徵。
- main、068 流程、既有成片均不修改。
