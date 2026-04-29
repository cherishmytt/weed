import { defineStore } from 'pinia'

const THEME_KEY = 'fire-theme-mode'

const resolveInitialTheme = () => {
  if (typeof window === 'undefined') return 'dark'
  const saved = window.localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return 'dark'
}

const applyThemeToDocument = (mode) => {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.theme = mode
  document.documentElement.style.colorScheme = mode
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    sidebarCollapsed: false,
    themeMode: resolveInitialTheme(),
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    setSidebarCollapsed(value) {
      this.sidebarCollapsed = value
    },
    initializeTheme() {
      applyThemeToDocument(this.themeMode)
    },
    setTheme(mode) {
      this.themeMode = mode === 'light' ? 'light' : 'dark'
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(THEME_KEY, this.themeMode)
      }
      applyThemeToDocument(this.themeMode)
    },
    toggleTheme() {
      this.setTheme(this.themeMode === 'dark' ? 'light' : 'dark')
    },
  },
})
