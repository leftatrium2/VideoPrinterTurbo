export type VideoMaterialKeywordValidationError = 'englishOnly' | 'wordLimit'

const ENGLISH_WORD_PATTERN = /^[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*$/

export function validateVideoMaterialKeyword(
  value: string,
): VideoMaterialKeywordValidationError | null {
  const words = value.trim().split(/\s+/).filter(Boolean)

  if (words.length === 0) return null
  if (words.length > 5) return 'wordLimit'
  if (words.some(word => !ENGLISH_WORD_PATTERN.test(word))) return 'englishOnly'

  return null
}
