import { defineStore } from 'pinia'

import { analysisApi } from '@/api/service'

const CACHE_KEY = 'fire-overview-cache-v2'
const CACHE_TTL_MS = 5 * 60 * 1000

const getInitialState = () => {
  if (typeof window === 'undefined') {
    return {
      overview: null,
      topCountries: [],
      fetchedAt: 0,
    }
  }

  try {
    const cached = JSON.parse(window.localStorage.getItem(CACHE_KEY) || 'null')
    return {
      overview: cached?.overview || null,
      topCountries: Array.isArray(cached?.topCountries) ? cached.topCountries : [],
      fetchedAt: Number(cached?.fetchedAt || 0),
    }
  } catch {
    return {
      overview: null,
      topCountries: [],
      fetchedAt: 0,
    }
  }
}

export const useOverviewStore = defineStore('overview', {
  state: () => ({
    overview: getInitialState().overview,
    topCountries: getInitialState().topCountries,
    fetchedAt: getInitialState().fetchedAt,
    loading: false,
    pending: null,
  }),
  getters: {
    hasData: (state) => Boolean(state.overview),
    isFresh: (state) => Date.now() - state.fetchedAt < CACHE_TTL_MS,
  },
  actions: {
    persist() {
      if (typeof window === 'undefined') return
      window.localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          overview: this.overview,
          topCountries: this.topCountries,
          fetchedAt: this.fetchedAt,
        }),
      )
    },
    async load(force = false) {
      if (!force && this.hasData && this.isFresh) {
        return this.overview
      }
      if (this.pending) {
        return this.pending
      }

      this.loading = true
      this.pending = Promise.all([
        analysisApi.overview({ area_label: 'world' }),
        analysisApi.countryTop({ limit: 6, area_label: 'world' }),
      ])
        .then(([overviewData, countryTopData]) => {
          this.overview = overviewData
          this.topCountries = countryTopData
          this.fetchedAt = Date.now()
          this.persist()
          return overviewData
        })
        .finally(() => {
          this.loading = false
          this.pending = null
        })

      return this.pending
    },
  },
})
