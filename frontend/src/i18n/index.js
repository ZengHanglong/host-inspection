import { createI18n } from 'vue-i18n'

import zhCN from './messages/zh-CN'
import enUS from './messages/en-US'

const LOCALE_KEY = 'host-inspection.locale'
const DEFAULT_LOCALE = 'zh-CN'

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

const getInitialLocale = () => {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE
  }
  const savedLocale = window.localStorage.getItem(LOCALE_KEY)
  return messages[savedLocale] ? savedLocale : DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages,
})

export const setLocale = (locale) => {
  const nextLocale = messages[locale] ? locale : DEFAULT_LOCALE
  i18n.global.locale.value = nextLocale
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(LOCALE_KEY, nextLocale)
  }
}

export const getLocale = () => i18n.global.locale.value

export const availableLocales = Object.keys(messages)
