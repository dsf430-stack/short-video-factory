export interface KidsEnglishLesson {
  word: string
  letter: string
  narration: string
  storyboard: string
}

const cleanWord = (value: string) => value.trim().replace(/[^a-zA-Z-]/g, '').toUpperCase()

export const createKidsEnglishLesson = (input: string): KidsEnglishLesson => {
  const word = cleanWord(input) || 'POTATO'
  const letter = word.charAt(0)
  const spelling = word.split('').join('-')
  const prettyWord = word.charAt(0) + word.slice(1).toLowerCase()

  return {
    word,
    letter,
    narration: `${letter} is for ${prettyWord}! ${prettyWord}! ${spelling}! ${prettyWord}! Great job!`,
    storyboard: [
      `[0-3s] Eye-level wide shot: the cute ${prettyWord.toLowerCase()} character waves hello. A rounded red capital ${letter} appears above its head.`,
      `[3-6s] Slightly high-angle close-up: the character looks up and laughs. ${letter} expands into the colorful crayon word ${word}.`,
      `[6-10s] Pull back to full shot: the character holds its straw hat and spins happily on the grass. ${word} gently bobs like a bubble.`,
    ].join('\n'),
  }
}

export const KIDS_ENGLISH_VISUAL_STYLE =
  "Children's crayon picture-book illustration, thick wax-crayon texture, warm handmade feel, cute stable character, clean composition, bright child-friendly colors, no distortion, vertical 9:16."
