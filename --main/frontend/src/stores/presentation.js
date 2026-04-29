import { defineStore } from 'pinia'

export const usePresentationStore = defineStore('presentation', {
  state: () => ({
    cruising: false,
    demoRunning: false,
    currentCruiseIndex: 0,
    currentCruiseName: '全球视角',
    currentHotspotId: '',
    rightPanelIndex: 0,
    timelineIndex: 0,
    cruiseIntervalSeconds: 8,
    flyDurationSeconds: 3.2,
    autoStartCruise: true,
    demoStage: 'global',
  }),
  actions: {
    startCruise() {
      this.cruising = true
    },
    pauseCruise() {
      this.cruising = false
    },
    resetCruise() {
      this.cruising = false
      this.currentCruiseIndex = 0
      this.currentCruiseName = '全球视角'
      this.currentHotspotId = ''
    },
    setCruiseTarget(index, name, hotspotId = '') {
      this.currentCruiseIndex = index
      this.currentCruiseName = name
      this.currentHotspotId = hotspotId
    },
    setPanelIndex(index) {
      this.rightPanelIndex = index
    },
    setTimelineIndex(index) {
      this.timelineIndex = index
    },
    startDemo() {
      this.demoRunning = true
      this.demoStage = 'global'
    },
    pauseDemo() {
      this.demoRunning = false
    },
    stopDemo() {
      this.demoRunning = false
      this.demoStage = 'global'
      this.timelineIndex = 0
    },
    setDemoStage(stage) {
      this.demoStage = stage
    },
  },
})
