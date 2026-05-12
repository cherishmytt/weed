import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'lwr-detection-data'

function getDetectionDataFromStorage() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : null
  } catch (e) {
    console.error('Failed to get detection data from storage:', e)
    return null
  }
}

function setDetectionDataToStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.error('Failed to set detection data to storage:', e)
  }
}

export const useDetectionStore = defineStore('detection', () => {
  const storedData = getDetectionDataFromStorage()
  
  const currentResult = ref(storedData?.currentResult || null)
  const detectForm = ref({
    file: null,
    fileName: storedData?.detectForm?.fileName || '',
    conf: storedData?.detectForm?.conf || 0.15,
    classes: storedData?.detectForm?.classes || ''
  })

  function setDetectionResult(result) {
    currentResult.value = result
    persistToStorage()
  }

  function setDetectForm(form) {
    detectForm.value = { ...form }
    persistToStorage()
  }

  function clearDetectionResult() {
    currentResult.value = null
    persistToStorage()
  }

  function clearDetectForm() {
    detectForm.value = {
      file: null,
      fileName: '',
      conf: 0.15,
      classes: ''
    }
    persistToStorage()
  }

  function clearAll() {
    currentResult.value = null
    detectForm.value = {
      file: null,
      fileName: '',
      conf: 0.15,
      classes: ''
    }
    localStorage.removeItem(STORAGE_KEY)
  }

  function persistToStorage() {
    const dataToStore = {
      currentResult: currentResult.value,
      detectForm: {
        fileName: detectForm.value.fileName,
        conf: detectForm.value.conf,
        classes: detectForm.value.classes
      }
    }
    setDetectionDataToStorage(dataToStore)
  }

  return {
    currentResult,
    detectForm,
    setDetectionResult,
    setDetectForm,
    clearDetectionResult,
    clearDetectForm,
    clearAll
  }
})
