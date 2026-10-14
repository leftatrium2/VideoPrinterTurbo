export const MAX_DOWNLOAD_URLS = 100
export const MAX_DOWNLOAD_FILE_SIZE = 100 * 1024

export function validateDownloadUrls(text: string): {
  urls: string[]
  error?: 'empty' | 'tooMany' | 'invalidUrl'
  line?: number
} {
  const lines = text.split(/\r\n|\n|\r/).map((value, index) => ({ value: value.trim(), line: index + 1 }))
    .filter(item => item.value)
  const urls = lines.map(item => item.value)
  if (!urls.length) return { urls, error: 'empty' }
  if (urls.length > MAX_DOWNLOAD_URLS) return { urls, error: 'tooMany' }
  for (const item of lines) {
    try {
      const url = new URL(item.value)
      if (!/^https?:\/\//i.test(item.value) || !['http:', 'https:'].includes(url.protocol) || /\s/.test(item.value)) {
        return { urls, error: 'invalidUrl', line: item.line }
      }
    } catch {
      return { urls, error: 'invalidUrl', line: item.line }
    }
  }
  return { urls }
}

export function validateDownloadFile(file: Pick<File, 'name' | 'size'>): 'fileType' | 'fileSize' | undefined {
  if (!/\.(txt|csv)$/i.test(file.name)) return 'fileType'
  if (file.size > MAX_DOWNLOAD_FILE_SIZE) return 'fileSize'
}
