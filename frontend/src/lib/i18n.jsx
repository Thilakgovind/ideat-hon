import { createContext, useContext, useEffect, useState } from 'react'

const LangContext = createContext({ lang: 'en', setLang: () => {} })

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('sp_lang') || 'en')
  useEffect(() => {
    localStorage.setItem('sp_lang', lang)
    document.documentElement.lang = lang === 'ta' ? 'ta' : 'en'
  }, [lang])
  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>
}

export function useLang() {
  return useContext(LangContext)
}

/** const t = useT(); t('Start trip', 'பயணம் தொடங்கு') */
export function useT() {
  const { lang } = useLang()
  return (en, ta) => (lang === 'ta' && ta ? ta : en)
}

export function greeting(hour) {
  if (hour < 12) return ['Good morning', 'காலை வணக்கம்']
  if (hour < 17) return ['Good afternoon', 'மதிய வணக்கம்']
  return ['Good evening', 'மாலை வணக்கம்']
}
