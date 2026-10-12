# 068 根因、修正與接續紀錄

狀態：SUCCESS（新配音、GitHub主分支修正）；UNCERTAIN（主觀/手機試聽）。

## 原因與排除
10月9日 run37929275694成功、10月12日run38203829954失敗，兩者相同commit4b5238af、Edge TTS7.2.8、Python3.11.17、Ubuntu24.04映像20261004.327.1、區域eastus2。套件差異：aiohttp3.14.4→3.14.5、multidict6.9.1→7.1.0。此次只改服務網址，用今天套件成功，因此不需先降套件。上游issue490自10月10日起同類403、且有人使用舊套件也失敗；回報Microsoft新Read Aloud服務網址可用。服務內部切換政策非Microsoft正式聲明，不推斷所有IP行為。

## 已驗證修正
只將smart_voice/generate_voice.py的edge_tts.communicate.WSS_URL改為wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?Ocp-Apim-Subscription-Key=<edge_tts.constants.TRUSTED_CLIENT_TOKEN>。沿用庫的原始token、DRM、headers、TLS；未偽裝新版UA、代理或關閉憑證驗證。主分支修正commit5a6d88c41a03cfb1b75e17a53913cdbb8c1b120d，content blob a2c0c7a24444cdd4a26e7d58dcd6a14f2aa648b0。沒有重建影片功能。

## 成功證據
Run：https://github.com/dsf430-stack/short-video-factory/actions/runs/38204582549
分支：fix/068-service-endpoint-20261012
執行commit：516b8d1f351932f0a5caf8489b9a4b4fa749f7f6
Job：114665123571 completed/success
Artifact：068-voice-output，11726318836
ZIP SHA256：2ae80dd197367806e7468e00e72c766d02f17f1dd1024b8a2a92b559f625a77e
MP3 SHA256：896e60ee1f244cef63c3e25fd8c552c8de922b9d687e5810ad44bd5d5c928477
文字SHA256：475ca57852f365c583a59c76df9f898b55199c07cc894c3256eb0d9a026dff65
《圍魏救趙》新旁白：53.733878秒，068/zh-TW-HsiaoChenNeural/+20%/+5Hz。JSON與本地複測音量一致：-13.38 LUFS、-1.24 dBTP。完整解碼exit0，字幕14句，末尾53.635秒，時間合法且不超出音訊。只有一段，<=300字。

## 禁踩雷
不要把403歸因於尚未登入GitHub；不要重裝同版本或重跑舊網址；不要用舊MP3充當新故事。修正網址只在目前GitHub配音入口驗證；其他ZIP/技能內嵌的舊腳本尚未同步，不宣稱全部修好。後續優先從GitHub main調用既有workflow。

## 下一步
使用已產生MP3/SRT製作繪本，保留故事插畫/BGM/SFX、音訊與字幕同步。KB_02_繪本敘事工程規範.md.txt實際只有「12」，完整KB規範缺失不能宣稱已讀全。供應端若再次拒絕，讀此checkpoint與upstream新狀態再處理。不要自動發布社群。
