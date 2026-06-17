import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

const STORAGE_KEY = 'vpt_lang'

function detectLocale(): string {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'zh' || stored === 'en') return stored
  const browser = navigator.language || (navigator as any).userLanguage || 'zh'
  return browser.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

export const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'zh',
  messages: { zh, en },
})

export function setLocale(locale: 'zh' | 'en') {
  ;(i18n.global.locale as any).value = locale
  localStorage.setItem(STORAGE_KEY, locale)
}
