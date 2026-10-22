# 三皇是哪三個？｜已確認製作稿

狀態：腳本及提示詞完成；未生成影片、未生成068音訊、未啟動Actions。
設定：30秒，9:16，2B彩色電影故事風，繁體中文字幕。配音使用既有068：zh-TW-HsiaoChenNeural，rate +20%，pitch +5Hz。無配樂。

## 完整中文配音稿

三皇是哪三個？先別急著背，答案其實不只一種！其中一種說法，是伏羲、女媧、神農。

傳說伏羲畫八卦，女媧補天，神農嘗百草。他們代表古人對文明起源的想像。

但也有版本，把燧人列入三皇。所以問三皇是誰，得先看採用哪種說法。你聽過哪一版？

實測要求：先生成完整068配音並量測，按實際句界分段；三段各10秒是分鏡目標，不是已驗證的音訊時長。未經確認不改旁白，不拉伸、不截音。

## 全片連續性

主角始終是紅色無毛球針織帽、黃色T恤、黑色短褲與細黑四肢的2D火柴人，無寫實五官。森林綠、夕陽金、夜空藍構成彩色場景。伏羲是青綠古風衣袍人物，女媧是珊瑚色衣袍神話人物，神農是赭色衣袍與草藥籃人物，燧人是土色衣服的取火人物；全部為簡化卡通人物。場景為傳說的視覺詮釋，不聲稱復原史實。

旁白統一由外部068音軌提供。影片模型不配旁白、不配角色對白、不加音樂；僅輕微環境音效。字幕與姓名於後製加入，避開底部平台介面。

## Clip 1 — standalone generation prompt

Create a 10-second vertical 9:16 animated clip, target 720p, 24 fps. Style 2B Cinematic Story: rich full-color ancient fantasy mountains, atmospheric depth, sunset volumetric light, and smooth 2D animated characters.

A minimalist 2D animated stick figure wearing a bright red beanie (smooth knit, no pom-pom) and a yellow t-shirt, with simple black stick limbs and shorts. Simple black lines, vibrant colors, smooth 2D animation style. Maintain constant character proportions and line weight. Fuxi wears a muted teal ancient robe; Nuwa wears a coral robe; Shennong wears an ochre robe and carries an herb basket. These are mythological cartoon interpretations, not documentary reconstructions.

Forest green means the ancient landscape, sunset gold means discovery, night blue means mystery. Use vertical reveals and foreground depth, keeping the lower fifth uncluttered for later subtitles.

Opening: the red-beanie explorer braces both hands against the cover of an enormous ancient book.
[0–3s] The explorer pushes the book open; a tracking camera passes through its pages into a deep mountain valley, with softly drifting dust.
[3–7s] The explorer steps along a foreground stone path; three distinct legendary figures appear one after another on different terraces. Use a motivated upward camera move and parallax, not shape morphing.
[7–10s] The explorer turns toward Fuxi, who kneels beside a flat stone and begins drawing a simple trigram diagram. Push the camera toward his drawing hand.

Narrative timing guide, not model speech: 三皇是哪三個？先別急著背，答案其實不只一種！其中一種說法，是伏羲、女媧、神農。

External narration lock: Use only the separately supplied continuous 068 zh-TW-HsiaoChenNeural Mandarin narration, rate +20%, pitch +5Hz, at final assembly. Do not synthesize speech, imitate that voice, add dialogue, or change its speed. No background music. Soft page-turn and mountain-wind effects only, mixed below the later narration.

End on Fuxi's hand moving over the stone, allowing a matching close-up at the next opening. No readable writing, labels, captions, subtitles, speech bubbles, dialogue boxes, logos or watermarks. No photorealistic human skin, no 3D humanoid CGI models, no chaotic line glitches, no extra limbs, no abstract morphing, no changes in character design.

## Clip 2 — standalone generation prompt

Create a 10-second vertical 9:16 animated clip, target 720p, 24 fps. Style 2B Cinematic Story: rich full-color ancient fantasy landscape, atmospheric depth, sunset volumetric light, smooth 2D animation.

A minimalist 2D animated stick figure wearing a bright red beanie (smooth knit, no pom-pom) and a yellow t-shirt, with simple black stick limbs and shorts. Simple black lines, vibrant colors, smooth 2D animation style. Maintain constant character proportions and line weight. Fuxi wears a muted teal ancient robe; Nuwa wears a coral robe; Shennong wears an ochre robe and carries an herb basket. These are mythological cartoon interpretations, not documentary reconstructions.

Forest green means the ancient landscape, sunset gold means discovery, night blue means mystery. Use vertical camera movement and readable foreground action; keep the lower fifth uncluttered for later subtitles.

Opening: a close view of Fuxi's hand drawing simple trigram lines on a flat stone, with the red-beanie explorer watching from the side.
[0–3s] Fuxi completes the diagram and lifts his hand; the explorer points upward as warm light illuminates the stone.
[3–7s] A motivated upward tilt reveals Nuwa placing a luminous colored stone into a crack in the sky. The explorer shields their eyes; small gold sparks descend into the foreground.
[7–10s] Follow one falling spark through a deliberate cut to a lush valley. Shennong kneels to collect a medicinal herb beside a woven basket; the explorer follows him along the path. End with the basket and valley foliage prominent.

Narrative timing guide, not model speech: 傳說伏羲畫八卦，女媧補天，神農嘗百草。他們代表古人對文明起源的想像。

External narration lock: Use only the separately supplied continuous 068 zh-TW-HsiaoChenNeural Mandarin narration, rate +20%, pitch +5Hz, at final assembly. Do not synthesize speech, imitate that voice, add dialogue, or change its speed. No background music. Soft wind, stone contact, and foliage effects only, mixed below the later narration.

End on the herb valley with warm firelight beginning to illuminate the basket from off-screen. No readable writing, labels, captions, subtitles, speech bubbles, dialogue boxes, logos or watermarks. No photorealistic human skin, no 3D humanoid CGI models, no chaotic line glitches, no extra limbs, no abstract morphing, no changes in character design.

## Clip 3 — standalone generation prompt

Create a 10-second vertical 9:16 animated clip, target 720p, 24 fps. Style 2B Cinematic Story: a rich full-color ancient fantasy valley at dusk, atmospheric depth, warm firelight against a night-blue sky, smooth 2D animation.

A minimalist 2D animated stick figure wearing a bright red beanie (smooth knit, no pom-pom) and a yellow t-shirt, with simple black stick limbs and shorts. Simple black lines, vibrant colors, smooth 2D animation style. Maintain constant character proportions and line weight. Suiren wears earth-brown simple ancient clothing and works with a wooden fire-making tool. Scroll portraits use Fuxi in muted teal, Nuwa in coral, Shennong in ochre with an herb basket, and Suiren in earth brown. These are mythological cartoon interpretations, not documentary reconstructions.

Forest green means the ancient landscape, sunset gold means discovery, night blue means mystery. Stage the scrolls vertically and use foreground depth, keeping the lower fifth uncluttered for later subtitles.

Opening: valley foliage and an herb basket illuminated from one side by warm firelight.
[0–3s] A short camera pan reveals Suiren beside a small campfire; the red-beanie explorer walks toward him and reacts with curiosity.
[3–7s] The explorer unrolls two illustrated scrolls: one visibly groups Fuxi, Nuwa and Shennong, the other groups Fuxi, Shennong and Suiren. Portraits only, no writing. Alternate a clear overhead insert and a medium reaction shot.
[7–10s] The explorer holds both scrolls open toward the viewer, then the camera pulls backward through the giant book's frame. The explorer gently closes the book, ending on a stable composition.

Narrative timing guide, not model speech: 但也有版本，把燧人列入三皇。所以問三皇是誰，得先看採用哪種說法。你聽過哪一版？

External narration lock: Use only the separately supplied continuous 068 zh-TW-HsiaoChenNeural Mandarin narration, rate +20%, pitch +5Hz, at final assembly. Do not synthesize speech, imitate that voice, add dialogue, or change its speed. No background music. Soft fire crackle, scroll rustle, and a final book-close effect only, mixed below the later narration.

End with the closed book and red-beanie explorer stable in frame. No readable writing, labels, captions, subtitles, speech bubbles, dialogue boxes, logos or watermarks. No photorealistic human skin, no 3D humanoid CGI models, no chaotic line glitches, no extra limbs, no abstract morphing, no changes in character design.

## 剪接與驗證

按1→2→3排列。第一接點核對伏羲畫卦的手勢與石面；第二接點核對山谷、草藥籃與營火光線。先量測完整068配音，對齊實際句界後調整畫面剪點；不能假設三段旁白剛好各10秒。畫面需實際生成與檢查角色、動作、接點，並保留字幕空間。輸出目標為1080×1920、30fps、H.264/AAC；來源720p素材升頻輸出不代表原生1080p。

現有GitHub handdraw流程是逐筆插畫引擎，不能將其輸出宣稱為本稿要求的2B角色動畫。後續完整查找發現另有Hypit本地程式動畫渲染入口：HYPIT.md、.github/workflows/hypit-render.yml。固定版本dc2b7a8f31b1ef1443a79ca448548d69e3ceb6a0，已有8秒540×960官方聊天動畫成功紀錄（run 38993046914）。可接續撰寫本題獨立元件並整合068；目前工作流程固定渲染官方範例，不能直接以現有workflow重跑宣稱已完成本題。這不是已接通的Omni/Flow影片模型，2B場景及角色動作需另外製作及驗證。尚未建立任何付費服務。

## 查核來源

- https://dict.revised.moe.edu.tw/dictView.jsp?ID=144559&la=0&powerMode=0 （三皇說法不一）
- https://github.com/dsf430-stack/short-video-factory/blob/main/WORKFLOW.md （068設定與現有引擎流程）

