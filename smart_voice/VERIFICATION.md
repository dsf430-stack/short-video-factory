# 配音庫接續紀錄

## 2026-10-09：最新 main 接續

基底 commit：af5760d9a377b34f94e7c47fa3274cbba383a419。

上一輪實測 068 中文 SUCCESS，F01 Jenny／F02 Aria／F03 Michelle／F04 Sonia／F05 Ana 中文全部 FAILED，錯誤都是 NoAudioReceived；五個英文對照全部 SUCCESS。問題為此批英文聲線與中文不相容，不能把英文成功當中文成功。額外中文女聲 zh-TW-HsiaoYuNeural／zh-CN-XiaoxiaoNeural 都 SUCCESS。

## 本次局部修改

- 保留 068 聲線、語速 +20%、音調 +5Hz。
- 新增 ZH_HsiaoYu、ZH_Xiaoxiao；不覆寫歷史 F/M 代號。
- 中文自動選 068；英文聲線讀中文提前拒絕。
- 使用系統 CA 加 certifi，TLS 驗證保持開啟。
- 最多 300 字元分段，使用句子事件產生 SRT。
- 輸出 loudnorm 後 MP3、字幕、實測 JSON；完整解碼並校驗音量。
- 在暫存檔合成與校驗，通過後發布；拒絕覆寫既有成品。
- 補上 requirements.txt、Windows 指令和三個中文試聽範例。

Python 配音元件未直接呼叫 Electron TTS。原 Electron／影片剪輯功能保持原樣；此輪未驗證桌面程式或 Windows 實際執行。

## 經驗與禁踩雷

原 Python 生成器只檢查檔案非空，不包含 Electron 的穩定性修正。環境的歷史 venv 已消失；新建隔離環境並固定 edge-tts 7.2.8。已知 managed runtime 憑證需系統 CA，單獨 certifi 不能代替；不要關閉 SSL 驗證。服務錯誤不以靜音、假音訊或偷偷換聲線掩蓋。

本專案 M02 是英文 Christopher，歷史技能 M02 是 zh-CN-YunxiNeural；沒有自動合併或重映射。

聲音喜好、手機播放與字幕主觀同步：UNCERTAIN，需使用者試聽。技術實測數值收於 samples/*.json，不把 loudnorm 目標當實測值。

## 最後完成 checkpoint
狀態：SUCCESS（技術驗證）；主觀試聽 UNCERTAIN。
四個離線測試通過：分段字元保留、中文自動 068、中文選英文拒絕、保護已有音檔。
新版入口即時測試：
| 預設／測試 | 時長 | 分段 | 實測 LUFS | 實測 true peak | 結果 |
|---|---:|---:|---:|---:|---|
| 068 | 6.139s | 1 | -13.16 | -1.25 | SUCCESS |
| ZH_HsiaoYu | 5.329s | 1 | -14.78 | -1.08 | SUCCESS |
| ZH_Xiaoxiao | 4.362s | 1 | -12.44 | -1.22 | SUCCESS |
| 068 超過300字 | 61.571s | 2 | -13.36 | -1.24 | SUCCESS |

四次新文字合成均產生 MP3、句子 SRT、JSON；完整解碼通過，字幕事件覆蓋輸入文字且在音訊時間範圍內。

阻塞：無技術阻塞。下一步：使用者下載 samples 試聽，再用自己的 narration.txt 產生旁白。桌面選單整合是另一步，尚未實作。
