# Hypit 遠端影片製作

## 採用狀態

2026-10-17 已完成官方範例的實際 MP4 渲染。Hypit 作為本專案可持續使用的影片製作選項保留；適合程式動畫或使用者指定 Hypit 的工作，從這個已驗證流程接續。不要重新建立另一套安裝流程。

這是 GitHub Actions 按需執行的流程，並非全天運行的伺服器或網頁編輯器。自訂影片仍需提供或撰寫對應的 Source、Run 與元件；已通過的範例不代表所有生成模型、配音或中文排版都已驗證。

## 已驗證的完整流程

- 工作流程：.github/workflows/hypit-render.yml
- 官方來源：https://github.com/hypit-ai/hypit
- 固定提交：dc2b7a8f31b1ef1443a79ca448548d69e3ceb6a0（0.3.1）
- Node.js 22、pnpm 10.33.0、官方 frozen lockfile。
- 官方範例：examples/semantic-composition/chat.svml 及 chat.svrun。
- 順序：安裝 → 型別與元件編譯 → FFmpeg 安裝 → HTML 瀏覽器準備 → check → plan → build → get → MP4 驗證。
- 已驗證成片：8 秒、540×960、30 fps、240 幀、H.264 MP4。
- 檢查：解碼、片長、尺寸與幀內容變化；檢視逐秒畫面，四則聊天訊息依序出現。
- 範例沒有旁白；AAC 軌是靜音，不能當作配音已驗證。
- 完整成功紀錄：https://github.com/dsf430-stack/short-video-factory/actions/runs/38993046914
- Build：bld_20261017T015916137Z_462D90698B
- Artifact：hypit-render-delivery，GitHub 保留 90 天。

## 下次如何接續

1. 讀取此文件及現有工作流程。
2. 使用者指定題材後，新增該影片的獨立可編輯專案，不覆蓋既有影片與原始素材。
3. 依官方 Skill 與固定版本的文件撰寫 Source/Run；先 check、plan，再 build。
4. 既有 068 等配音流程須按其已驗證設定接續，不因採用 Hypit 而擅自更換聲音。
5. 預設使用本地程式渲染，不需要 Gemini。付費生成服務需要另行確認帳號與預算。
6. 交付前檢查實際 MP4，不能把安裝通過或 build 提交成功當作出片完成。
7. 成片由 Actions artifact 取回，交付可觀看的 MP4；保存重要交付物，不能依賴 90 天 artifact 作永久存放。

在 GitHub 的 Actions → Hypit render → Run workflow 可重跑官方範例。也可由具備遠端操作能力的助手替使用者執行，不要求使用者在手機輸入命令。

## 已確認的環境問題

第一輪失敗是執行環境沒有 ffprobe（spawn ffprobe ENOENT）。工作流程已明確安裝 ffmpeg 套件，第二輪完整成功。保留這個步驟，不需要改動畫元件或改換渲染引擎。

官方文件：
- https://github.com/hypit-ai/hypit/blob/main/skills/hypit/SKILL.md
- https://github.com/hypit-ai/hypit/blob/main/examples/semantic-composition/README.md
