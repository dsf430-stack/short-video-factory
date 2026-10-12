# 068 穩定性修正與接續紀錄 — 2026-10-12

狀態：SUCCESS（正式main修正、新配音、技術QA）；UNCERTAIN（主觀／手機試聽、服務未來可用性）。

## 最後完成
修正PR：https://github.com/dsf430-stack/short-video-factory/pull/1 已合併。
正式合併commit：988e114b3ca13bba8667a0ce3fb0ff63a9bcf17f
最終已驗證程式commit：36f59570493bbd08ce06ac90201016bb857f53ea
Python3.10.22最終run：https://github.com/dsf430-stack/short-video-factory/actions/runs/38245699567
Job114798873458，completed/success，Artifact11745821379，SHA25633ade71fc583aca39f1bc9cdcaa7e501df85c5ffbb880a56ae1008ac353f398f。
Python3.11.17前一輪run38245301674也SUCCESS。

## 原因與正確修正
1. 舊speech.platform.bing.com合成網址403：沿用先前已驗證的api.msedgeservices.com新Read Aloud網址。不可重裝同版本、重跑舊網址、關閉TLS或換聲線掩蓋。
2. 舊ZIP與技能內嵌入口未自動同步：新旁白只調用最新main smart_voice/generate_voice.py／既有voice-068.yml；068.txt已補唯一入口規則。舊ZIP和技能檔沒有在此輪全部改寫。
3. 暫時斷線使完成分段消失：逐段真實音訊與句子時間校驗後保存，用文字／設定／版本雜湊尋址，續跑只生成缺少段落。音訊完整解碼與SHA錯誤會拒绝快取並重合成原稿。
4. Python3.10 timeout分類差異：中間run38245510172離線測試FAILED（AssertionError: False is not true），原先只分類asyncio.TimeoutError，漏掉內建TimeoutError；補上兩種例外並由最終run驗證。

## 保留与新增
068曉臻zh-TW-HsiaoChenNeural／+20%／+5Hz，每段<=300字。原聲線設定、既有影片與成品保留。暫時連線／timeout／429／5xx最多3次、2秒與4秒退避，120秒分段收取上限。403／401不盲目重試。使用系統CA加certifi。輸出原MP3/SRT/JSON及.progress.json，失敗保留完整.error.log。GitHub配音流程失敗也保存已完成快取，同分支後續run可恢復；快取仍受GitHub保留／容量／存取規則限制，跨runner快取恢復尚未單獨實測。

## 已驗證
7項離線回歸PASS。新文字068短音訊；319字兩段旁白59.480816秒；先完成第一段後續跑PASS；禁止網路呼叫仍使用真實快取PASS；刻意破壞最後一段快取後重新生成PASS。完整解碼、非靜音音量、字幕文字與時間校驗PASS。新短音訊及319字音訊不是舊故事替代品。

## 阻塞與下一步
無核心技術阻塞。正式main程式已驗證；voice-068.yml新增的Actions跨run快取行為待下次正式旁白執行核對。後續068新稿直接使用最新main既有workflow，保留完成快取和成品；產生影片時把本次MP3/SRT交回既有合成器。主觀／手機試聽UNCERTAIN，不聲稱永不出錯。
