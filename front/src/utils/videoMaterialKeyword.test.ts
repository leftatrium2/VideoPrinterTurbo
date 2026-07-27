import { describe, expect, it } from 'vitest'
import { validateVideoMaterialKeyword } from './videoMaterialKeyword'

describe('validateVideoMaterialKeyword', () => {
  it('accepts an empty keyword', () => {
    expect(validateVideoMaterialKeyword('   ')).toBeNull()
  })

  it('accepts up to five English words with numbers, hyphens, and apostrophes', () => {
    expect(validateVideoMaterialKeyword("4k city-night traveler's 2026 ocean")).toBeNull()
  })

  it('rejects a keyword with more than five words', () => {
    expect(validateVideoMaterialKeyword('one two three four five six')).toBe('wordLimit')
  })

  it('rejects non-English characters and unsupported punctuation', () => {
    expect(validateVideoMaterialKeyword('城市 night')).toBe('englishOnly')
    expect(validateVideoMaterialKeyword('city, night')).toBe('englishOnly')
  })
})
