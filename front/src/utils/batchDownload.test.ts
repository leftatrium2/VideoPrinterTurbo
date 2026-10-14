import { describe, expect, it } from 'vitest'
import { validateDownloadFile, validateDownloadUrls } from './batchDownload'

describe('batch download validation', () => {
  it('trims URLs and ignores blank lines with different line endings', () => {
    expect(validateDownloadUrls('\ufeff https://example.com/a \r\n\r\nhttp://example.com/b\r')).toEqual({
      urls: ['https://example.com/a', 'http://example.com/b'],
    })
  })

  it('requires at least one URL and accepts exactly 100 URLs', () => {
    expect(validateDownloadUrls(' \n\t').error).toBe('empty')
    expect(validateDownloadUrls(Array(100).fill('https://example.com').join('\n')).error).toBeUndefined()
    expect(validateDownloadUrls(Array(101).fill('https://example.com').join('\n')).error).toBe('tooMany')
  })

  it.each(['ftp://example.com', 'video_url', 'https://', 'https://example.com/a b', 'https:example.com'])('rejects invalid URL %s and reports the original line', value => {
    expect(validateDownloadUrls(`\nhttps://example.com\n\n${value}`)).toMatchObject({ error: 'invalidUrl', line: 4 })
  })

  it('checks file extensions case insensitively and the exact size boundary', () => {
    expect(validateDownloadFile({ name: 'urls.TXT', size: 100 * 1024 })).toBeUndefined()
    expect(validateDownloadFile({ name: 'urls.CSV', size: 1 })).toBeUndefined()
    expect(validateDownloadFile({ name: 'urls.csv', size: 100 * 1024 + 1 })).toBe('fileSize')
    expect(validateDownloadFile({ name: 'urls.csv.exe', size: 1 })).toBe('fileType')
  })
})
