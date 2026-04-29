<template>
  <div class="map-shell">
    <div ref="containerRef" class="map-container"></div>
    <div ref="creditContainerRef" class="credit-sink" aria-hidden="true"></div>
    <canvas
      ref="heatmapCanvasRef"
      class="heatmap-canvas"
      :class="{ visible: props.showHeatmap }"
    ></canvas>

    <div
      v-if="selectionPopup.visible && selectionPopup.payload"
      class="fire-popup"
      :class="{ hotspot: selectionPopup.kind === 'hotspot' }"
      :style="{ left: `${selectionPopup.left}px`, top: `${selectionPopup.top}px` }"
    >
      <button class="popup-close" @click.stop="closeSelection()">
        <el-icon><Close /></el-icon>
      </button>

      <template v-if="selectionPopup.kind === 'fire'">
        <strong>{{ selectionPopup.payload.country_name || '未知火点' }}</strong>
        <p>{{ selectionPopup.payload.satellite || '--' }} · {{ selectionPopup.payload.daynight || '--' }}</p>
        <div class="popup-metrics">
          <span>FRP {{ selectionPopup.payload.frp ?? '--' }}</span>
          <span>{{ selectionPopup.payload.acq_datetime || '--' }}</span>
        </div>
      </template>

      <template v-else>
        <strong>{{ selectionPopup.payload.major_country || selectionPopup.payload.id || '热点区域' }}</strong>
        <p>{{ selectionPopup.payload.fire_count ?? 0 }} 个火点 · 平均 FRP {{ selectionPopup.payload.avg_frp ?? '--' }}</p>
        <div class="popup-metrics">
          <span>最大 FRP {{ selectionPopup.payload.max_frp ?? '--' }}</span>
          <span>{{ selectionPopup.payload.time_end || selectionPopup.payload.time_start || '--' }}</span>
        </div>
      </template>

      <div class="popup-tag">{{ selectionPopup.kind === 'hotspot' ? '热点区域' : '火点详情' }}</div>
    </div>

    <div
      v-if="selectionPopup.visible && selectionPopup.payload"
      class="popup-anchor"
      :style="{ left: `${selectionPopup.anchorLeft}px`, top: `${selectionPopup.anchorTop}px` }"
    >
      <span></span>
      <i></i>
    </div>
  </div>
</template>

<script setup>
import * as Cesium from 'cesium'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import {
  BASEMAPS,
  DEFAULT_BASEMAP,
  DEFAULT_BASEMAP_OVERLAYS,
  DEFAULT_VIEWS,
  FALLBACK_BASEMAP,
} from '@/utils/mapConfig'

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
  hotspots: {
    type: Array,
    default: () => [],
  },
  heatmapPoints: {
    type: Array,
    default: () => [],
  },
  choropleth: {
    type: Array,
    default: () => [],
  },
  selectedCountry: {
    type: String,
    default: '',
  },
  boundaryUrl: {
    type: String,
    default: '/data/world-countries-lite.json',
  },
  initialView: {
    type: String,
    default: 'global',
  },
  basemap: {
    type: String,
    default: DEFAULT_BASEMAP,
  },
  glowMode: {
    type: Boolean,
    default: false,
  },
  showCountries: {
    type: Boolean,
    default: true,
  },
  showFirePoints: {
    type: Boolean,
    default: true,
  },
  clusterFirePoints: {
    type: Boolean,
    default: true,
  },
  showHotspots: {
    type: Boolean,
    default: true,
  },
  showHeatmap: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select-fire', 'select-hotspot', 'select-country', 'ready'])

const containerRef = ref()
const creditContainerRef = ref()
const heatmapCanvasRef = ref()
let viewer
let fireDataSource
let hotspotDataSource
let boundaryDataSource
let handler
let hoveredCountryEntity = null
let recoverTimer = null
let activeBaseLayerKey = DEFAULT_BASEMAP
const imageryErrorRemovers = []
let countryStyleFrame = null
let scenePostRenderHandler = null
let selectedFireEntity = null
let selectedHotspotEntity = null
let heatmapShadowCanvas = null
let heatmapPalettePixels = null
let heatmapRenderFrame = null

const selectionPopup = reactive({
  visible: false,
  left: 0,
  top: 0,
  anchorLeft: 0,
  anchorTop: 0,
  payload: null,
  kind: 'fire',
})

const FIRE_POINT_CLUSTER_LIMIT = 1600
const FIRE_POINT_ANIMATION_LIMIT = 320
const HEATMAP_RESOLUTION_SCALE = 0.46
const HEATMAP_MIN_ALPHA = 18
const HEATMAP_SCREEN_BUCKET_SIZE = 10

const choroplethMap = computed(() => {
  const mapping = new Map()
  props.choropleth.forEach((item) => {
    if (item.code) mapping.set(item.code, item.value)
    if (item.name) mapping.set(item.name, item.value)
  })
  return mapping
})

const maxChoroplethValue = computed(() => {
  const values = props.choropleth.map((item) => Number(item.value || 0))
  return Math.max(...values, 1)
})

const countryNameFromEntity = (entity) =>
  entity?._countryName ||
  entity?.properties?.NAME_ZH?.getValue?.() ||
  entity?.properties?.ADMIN?.getValue?.() ||
  entity?.properties?.NAME?.getValue?.() ||
  entity?.name

const countryCodeFromEntity = (entity) =>
  entity?._countryCode ||
  entity?.properties?.ISO_A3?.getValue?.() ||
  entity?.properties?.ADM0_A3?.getValue?.() ||
  entity?.properties?.WB_A3?.getValue?.()

const gradientColor = (value) => {
  const ratio = Math.max(0, Math.min(1, value / maxChoroplethValue.value))
  return Cesium.Color.fromBytes(
    Math.round(18 + (255 - 18) * ratio),
    Math.round(58 + (133 - 58) * ratio),
    Math.round(74 + (62 - 74) * ratio),
    Math.round(26 + 154 * ratio),
  )
}

const frpColor = (frp = 0, daynight = 'D') => {
  if (daynight === 'N') {
    return frp >= 50
      ? Cesium.Color.fromCssColorString('#ff9c3d')
      : Cesium.Color.fromCssColorString('#ffd166')
  }
  if (frp >= 100) return Cesium.Color.fromCssColorString('#ff355d')
  if (frp >= 50) return Cesium.Color.fromCssColorString('#ff7438')
  if (frp >= 20) return Cesium.Color.fromCssColorString('#ffae3d')
  return Cesium.Color.fromCssColorString('#ffd166')
}

const frpSize = (frp = 0) => {
  if (frp >= 100) return 18
  if (frp >= 50) return 14
  if (frp >= 20) return 10
  return 6
}

const hotspotRadius = (count = 0) => {
  if (count >= 100) return 180000
  if (count >= 50) return 120000
  if (count >= 20) return 90000
  return 65000
}

const isValidCoordinate = (longitude, latitude) =>
  Number.isFinite(longitude) &&
  Number.isFinite(latitude) &&
  longitude >= -180 &&
  longitude <= 180 &&
  latitude >= -90 &&
  latitude <= 90

const getHeatmapSourceRows = () => (props.heatmapPoints?.length ? props.heatmapPoints : props.points) || []

const syncHeatmapCanvasSize = () => {
  const canvas = heatmapCanvasRef.value
  if (!canvas) return null

  const cssWidth = containerRef.value?.clientWidth || 0
  const cssHeight = containerRef.value?.clientHeight || 0
  if (!cssWidth || !cssHeight) return null

  const renderWidth = Math.max(1, Math.round(cssWidth * HEATMAP_RESOLUTION_SCALE))
  const renderHeight = Math.max(1, Math.round(cssHeight * HEATMAP_RESOLUTION_SCALE))

  if (canvas.width !== renderWidth) canvas.width = renderWidth
  if (canvas.height !== renderHeight) canvas.height = renderHeight

  canvas.style.width = `${cssWidth}px`
  canvas.style.height = `${cssHeight}px`

  if (!heatmapShadowCanvas) {
    heatmapShadowCanvas = document.createElement('canvas')
  }
  if (heatmapShadowCanvas.width !== renderWidth) heatmapShadowCanvas.width = renderWidth
  if (heatmapShadowCanvas.height !== renderHeight) heatmapShadowCanvas.height = renderHeight

  return {
    renderWidth,
    renderHeight,
    scaleX: renderWidth / cssWidth,
    scaleY: renderHeight / cssHeight,
  }
}

const getHeatmapPalette = () => {
  if (heatmapPalettePixels) return heatmapPalettePixels

  const paletteCanvas = document.createElement('canvas')
  paletteCanvas.width = 256
  paletteCanvas.height = 1
  const paletteContext = paletteCanvas.getContext('2d')
  const gradient = paletteContext.createLinearGradient(0, 0, 256, 0)
  gradient.addColorStop(0, 'rgba(0, 0, 0, 0)')
  gradient.addColorStop(0.12, '#213cff')
  gradient.addColorStop(0.28, '#00a9ff')
  gradient.addColorStop(0.44, '#2bffd6')
  gradient.addColorStop(0.64, '#fff05a')
  gradient.addColorStop(0.82, '#ff8a33')
  gradient.addColorStop(1, '#ff2f22')
  paletteContext.fillStyle = gradient
  paletteContext.fillRect(0, 0, paletteCanvas.width, paletteCanvas.height)
  heatmapPalettePixels = paletteContext.getImageData(0, 0, paletteCanvas.width, paletteCanvas.height).data
  return heatmapPalettePixels
}

const heatmapBrushCache = new Map()

const getHeatmapBrush = (radius) => {
  const normalizedRadius = Math.max(12, Math.round(radius))
  if (heatmapBrushCache.has(normalizedRadius)) {
    return heatmapBrushCache.get(normalizedRadius)
  }

  const size = normalizedRadius * 2
  const brushCanvas = document.createElement('canvas')
  brushCanvas.width = size
  brushCanvas.height = size
  const brushContext = brushCanvas.getContext('2d')
  const gradient = brushContext.createRadialGradient(
    normalizedRadius,
    normalizedRadius,
    normalizedRadius * 0.08,
    normalizedRadius,
    normalizedRadius,
    normalizedRadius,
  )
  gradient.addColorStop(0, 'rgba(0, 0, 0, 1)')
  gradient.addColorStop(0.28, 'rgba(0, 0, 0, 0.92)')
  gradient.addColorStop(0.58, 'rgba(0, 0, 0, 0.42)')
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
  brushContext.fillStyle = gradient
  brushContext.fillRect(0, 0, size, size)
  heatmapBrushCache.set(normalizedRadius, brushCanvas)
  return brushCanvas
}

const buildHeatmapSamples = (rows, scaleX, scaleY, renderWidth, renderHeight) => {
  const buckets = new Map()
  const ellipsoid = viewer.scene.globe?.ellipsoid || Cesium.Ellipsoid.WGS84
  const cameraPosition = viewer.camera.positionWC || viewer.camera.position
  const occluder =
    viewer.scene.mode === Cesium.SceneMode.SCENE3D && cameraPosition
      ? new Cesium.EllipsoidalOccluder(ellipsoid, cameraPosition)
      : null

  rows.forEach((item) => {
    const longitude = Number(item.longitude)
    const latitude = Number(item.latitude)
    if (!isValidCoordinate(longitude, latitude)) return

    const worldPosition = Cesium.Cartesian3.fromDegrees(longitude, latitude)
    if (occluder && !occluder.isPointVisible(worldPosition)) return
    const windowPoint = Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene, worldPosition)
    if (!windowPoint) return

    const x = windowPoint.x * scaleX
    const y = windowPoint.y * scaleY
    if (
      !Number.isFinite(x) ||
      !Number.isFinite(y) ||
      x < -40 ||
      y < -40 ||
      x > renderWidth + 40 ||
      y > renderHeight + 40
    ) {
      return
    }

    const bucketX = Math.floor(x / HEATMAP_SCREEN_BUCKET_SIZE)
    const bucketY = Math.floor(y / HEATMAP_SCREEN_BUCKET_SIZE)
    const key = `${bucketX}:${bucketY}`

    if (!buckets.has(key)) {
      buckets.set(key, {
        xSum: 0,
        ySum: 0,
        count: 0,
        frpSum: 0,
        maxFrp: 0,
      })
    }

    const bucket = buckets.get(key)
    const frp = Math.max(0, Number(item.frp || 0))
    bucket.xSum += x
    bucket.ySum += y
    bucket.count += 1
    bucket.frpSum += frp
    bucket.maxFrp = Math.max(bucket.maxFrp, frp)
  })

  return Array.from(buckets.values()).map((bucket) => ({
    x: bucket.xSum / bucket.count,
    y: bucket.ySum / bucket.count,
    count: bucket.count,
    avgFrp: bucket.frpSum / bucket.count,
    maxFrp: bucket.maxFrp,
  }))
}

const resolveHeatmapRadius = (sample, maxCount, maxFrp) => {
  const countRatio = maxCount ? sample.count / maxCount : 0
  const frpRatio = maxFrp ? sample.maxFrp / maxFrp : 0
  return 14 + countRatio * 18 + frpRatio * 10
}

const resolveHeatmapAlpha = (sample, maxCount, maxFrp) => {
  const countRatio = maxCount ? sample.count / maxCount : 0
  const frpRatio = maxFrp ? sample.avgFrp / maxFrp : 0
  return Math.max(0.18, Math.min(0.96, 0.2 + countRatio * 0.52 + frpRatio * 0.18))
}

const requestSceneRender = () => {
  if (viewer && !viewer.isDestroyed?.()) {
    viewer.scene.requestRender()
  }
}

const clearHeatmapCanvas = () => {
  const canvas = heatmapCanvasRef.value
  if (!canvas) return
  canvas.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height)
  heatmapShadowCanvas?.getContext('2d')?.clearRect(0, 0, heatmapShadowCanvas.width, heatmapShadowCanvas.height)
}

const renderHeatmap = () => {
  const canvas = heatmapCanvasRef.value
  if (!canvas || !viewer) return

  const sizing = syncHeatmapCanvasSize()
  if (!sizing) return

  const context = canvas.getContext('2d')
  const shadowContext = heatmapShadowCanvas?.getContext('2d', { willReadFrequently: true })
  if (!context || !shadowContext) return

  context.clearRect(0, 0, canvas.width, canvas.height)
  shadowContext.clearRect(0, 0, heatmapShadowCanvas.width, heatmapShadowCanvas.height)

  if (!props.showHeatmap) return

  const sourceRows = getHeatmapSourceRows()
  if (!sourceRows.length) return

  const samples = buildHeatmapSamples(
    sourceRows,
    sizing.scaleX,
    sizing.scaleY,
    sizing.renderWidth,
    sizing.renderHeight,
  )
  if (!samples.length) return

  const maxCount = Math.max(...samples.map((item) => item.count), 1)
  const maxFrp = Math.max(...samples.map((item) => item.maxFrp || 0), 1)

  samples.forEach((sample) => {
    const radius = resolveHeatmapRadius(sample, maxCount, maxFrp)
    const alpha = resolveHeatmapAlpha(sample, maxCount, maxFrp)
    const brush = getHeatmapBrush(radius)
    shadowContext.globalAlpha = alpha
    shadowContext.drawImage(brush, sample.x - brush.width / 2, sample.y - brush.height / 2)
  })
  shadowContext.globalAlpha = 1

  const palette = getHeatmapPalette()
  const image = shadowContext.getImageData(0, 0, sizing.renderWidth, sizing.renderHeight)
  const pixels = image.data

  for (let index = 0; index < pixels.length; index += 4) {
    const alpha = pixels[index + 3]
    if (alpha < HEATMAP_MIN_ALPHA) {
      pixels[index + 3] = 0
      continue
    }

    const paletteOffset = Math.min(alpha, 255) * 4
    pixels[index] = palette[paletteOffset]
    pixels[index + 1] = palette[paletteOffset + 1]
    pixels[index + 2] = palette[paletteOffset + 2]
    pixels[index + 3] = Math.min(255, Math.round(alpha * 1.08))
  }

  context.putImageData(image, 0, 0)
}

const scheduleHeatmapRender = () => {
  if (heatmapRenderFrame) return
  heatmapRenderFrame = window.requestAnimationFrame(() => {
    heatmapRenderFrame = null
    renderHeatmap()
  })
}

const clearImageryErrorListeners = () => {
  while (imageryErrorRemovers.length) {
    const remove = imageryErrorRemovers.pop()
    remove?.()
  }
}

const createImageryProvider = async (key) => {
  const basemap = BASEMAPS[key] || BASEMAPS[FALLBACK_BASEMAP]
  if (basemap.type === 'template') {
    return new Cesium.UrlTemplateImageryProvider({
      url: basemap.url,
      subdomains: basemap.subdomains,
      minimumLevel: basemap.minimumLevel,
      maximumLevel: basemap.maximumLevel,
      tileWidth: basemap.tileWidth,
      tileHeight: basemap.tileHeight,
      tilingScheme: new Cesium.WebMercatorTilingScheme(),
      enablePickFeatures: basemap.enablePickFeatures ?? false,
      hasAlphaChannel: basemap.hasAlphaChannel ?? true,
      credit: basemap.credit,
    })
  }
  if (basemap.type === 'arcgis') {
    return Cesium.ArcGisMapServerImageryProvider.fromUrl(basemap.url)
  }
  if (basemap.type === 'osm') {
    return new Cesium.UrlTemplateImageryProvider({
      url: basemap.url,
      credit: 'OpenStreetMap',
    })
  }
  return new Cesium.TileMapServiceImageryProvider({
    url: Cesium.buildModuleUrl('Assets/Textures/NaturalEarthII'),
  })
}

const registerImageryErrorHandler = (provider, providerKey) => {
  if (!provider?.errorEvent?.addEventListener) return
  const remove = provider.errorEvent.addEventListener((tileProviderError) => {
    if (tileProviderError?.retry) {
      tileProviderError.retry = false
    }
    scheduleBasemapRecovery(providerKey)
  })
  imageryErrorRemovers.push(remove)
}

const scheduleBasemapRecovery = (failedKey) => {
  if (!viewer || activeBaseLayerKey === FALLBACK_BASEMAP || failedKey === FALLBACK_BASEMAP) return
  clearTimeout(recoverTimer)
  recoverTimer = setTimeout(async () => {
    try {
      await applyBaseLayer(FALLBACK_BASEMAP, [])
      viewer.useDefaultRenderLoop = true
      requestSceneRender()
    } catch (error) {
      viewer.useDefaultRenderLoop = true
    }
  }, 120)
}

const getOverlayKeys = (key) => (key === 'tiandituImage' ? DEFAULT_BASEMAP_OVERLAYS : [])

const applyBaseLayer = async (key = props.basemap, overlayKeys = getOverlayKeys(key)) => {
  if (!viewer) return
  activeBaseLayerKey = key
  clearImageryErrorListeners()
  viewer.imageryLayers.removeAll()
  try {
    const baseProvider = await createImageryProvider(key)
    viewer.imageryLayers.addImageryProvider(baseProvider)
    registerImageryErrorHandler(baseProvider, key)

    for (const overlayKey of overlayKeys) {
      const overlayProvider = await createImageryProvider(overlayKey)
      viewer.imageryLayers.addImageryProvider(overlayProvider)
      registerImageryErrorHandler(overlayProvider, overlayKey)
    }
    requestSceneRender()
  } catch (error) {
    clearImageryErrorListeners()
    const fallbackProvider = await createImageryProvider(FALLBACK_BASEMAP)
    viewer.imageryLayers.addImageryProvider(fallbackProvider)
    registerImageryErrorHandler(fallbackProvider, FALLBACK_BASEMAP)
    activeBaseLayerKey = FALLBACK_BASEMAP
    requestSceneRender()
  }
}

const updateCountryStyles = () => {
  if (!boundaryDataSource) return
  boundaryDataSource.show = props.showCountries
  boundaryDataSource.entities.values.forEach((entity) => {
    if (!entity.polygon) return
    const name = countryNameFromEntity(entity)
    const code = countryCodeFromEntity(entity)
    const metricValue = choroplethMap.value.get(code) ?? choroplethMap.value.get(name) ?? 0
    const isSelected = props.selectedCountry && props.selectedCountry === name
    const isHovered = hoveredCountryEntity === entity
    const fillColor = gradientColor(metricValue).withAlpha(props.showCountries ? (metricValue ? 0.32 : 0.08) : 0)
    entity.polygon.material = isSelected ? Cesium.Color.fromCssColorString('#ff8d43').withAlpha(0.45) : fillColor
    entity.polygon.outline = true
    entity.polygon.outlineColor = isSelected
      ? Cesium.Color.fromCssColorString('#ffb37b')
      : isHovered
        ? Cesium.Color.fromCssColorString('#8deaff')
        : Cesium.Color.fromCssColorString('#2e9fd5').withAlpha(0.52)

    if (entity.polyline) {
      entity.polyline.width = isHovered ? 2.2 : 1.2
      entity.polyline.material = isSelected
        ? Cesium.Color.fromCssColorString('#ff9b55')
        : isHovered
          ? Cesium.Color.fromCssColorString('#85e9ff')
          : Cesium.Color.fromCssColorString('#3dd5ff')
    }
  })
  requestSceneRender()
}

const scheduleCountryStyleUpdate = () => {
  if (!viewer || countryStyleFrame) return
  countryStyleFrame = window.requestAnimationFrame(() => {
    countryStyleFrame = null
    updateCountryStyles()
  })
}

const unloadBoundaries = () => {
  if (!viewer || !boundaryDataSource) return
  viewer.dataSources.remove(boundaryDataSource, true)
  boundaryDataSource = null
  hoveredCountryEntity = null
  requestSceneRender()
}

const activeSelectedEntity = () => selectedFireEntity || selectedHotspotEntity

const updateSelectionPopupPosition = () => {
  if (!viewer || !selectionPopup.visible) return
  const activeEntity = activeSelectedEntity()
  if (!activeEntity) return
  const position = activeEntity.position?.getValue?.(Cesium.JulianDate.now())
  if (!position) return

  const canvasPoint = Cesium.SceneTransforms.worldToWindowCoordinates(viewer.scene, position)
  if (!canvasPoint) return

  const containerRect = containerRef.value?.getBoundingClientRect?.()
  const containerWidth = containerRect?.width || containerRef.value?.clientWidth || 0
  const containerHeight = containerRect?.height || containerRef.value?.clientHeight || 0
  const popupWidth = 284
  const popupHeight = selectionPopup.kind === 'hotspot' ? 132 : 118
  const localX = canvasPoint.x - (containerRect?.left || 0)
  const localY = canvasPoint.y - (containerRect?.top || 0)
  const preferRight = localX < containerWidth * 0.62
  const nextLeft = preferRight ? localX + 22 : localX - popupWidth - 22
  const nextTop = localY - popupHeight - 12

  selectionPopup.left = Math.min(Math.max(nextLeft, 12), Math.max(containerWidth - popupWidth - 12, 12))
  selectionPopup.top = Math.min(Math.max(nextTop, 12), Math.max(containerHeight - popupHeight - 12, 12))
  selectionPopup.anchorLeft = Math.min(Math.max(localX, 16), Math.max(containerWidth - 16, 16))
  selectionPopup.anchorTop = Math.min(Math.max(localY, 16), Math.max(containerHeight - 16, 16))
}

const restoreHotspotVisual = (entity) => {
  if (!entity) return
  if (entity.point) {
    entity.point.pixelSize = entity._basePixelSize || 12
  }
  if (entity.ellipse) {
    entity.ellipse.semiMajorAxis = entity._baseSemiAxis || hotspotRadius(entity._payload?.fire_count)
    entity.ellipse.semiMinorAxis = entity._baseSemiAxis || hotspotRadius(entity._payload?.fire_count)
    entity.ellipse.material = Cesium.Color.fromCssColorString('#ff8d43').withAlpha(props.glowMode ? 0.18 : 0.12)
    entity.ellipse.outlineColor = Cesium.Color.fromCssColorString('#ffb37b').withAlpha(0.64)
  }
}

const zoomBackFromSelection = (fireEntity, hotspotEntity) => {
  const targetPayload = hotspotEntity?._payload || fireEntity?._payload
  if (!viewer || !targetPayload) {
    viewer?.camera.zoomOut(900000)
    return
  }

  const longitude = hotspotEntity
    ? targetPayload.center_longitude ?? targetPayload.longitude
    : targetPayload.longitude
  const latitude = hotspotEntity
    ? targetPayload.center_latitude ?? targetPayload.latitude
    : targetPayload.latitude

  if (!isValidCoordinate(Number(longitude), Number(latitude))) {
    viewer.camera.zoomOut(900000)
    return
  }

  const isWorld = targetPayload.area_label === 'world'
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(
      Number(longitude),
      Number(latitude),
      hotspotEntity ? (isWorld ? 5200000 : 3000000) : (isWorld ? 3200000 : 2000000),
    ),
    duration: 0.95,
  })
}

const closeSelection = ({ zoomOut = true, emitFireEvent = true, emitHotspotEvent = true } = {}) => {
  const hadFireSelection = Boolean(selectedFireEntity)
  const hadHotspotSelection = Boolean(selectedHotspotEntity)
  const hadSelection = Boolean(selectedFireEntity || selectedHotspotEntity)
  const previousFireEntity = selectedFireEntity
  const previousHotspotEntity = selectedHotspotEntity

  if (selectedFireEntity?.point) {
    selectedFireEntity.point.pixelSize = selectedFireEntity._basePixelSize || frpSize(selectedFireEntity._payload?.frp)
  }
  restoreHotspotVisual(selectedHotspotEntity)

  selectedFireEntity = null
  selectedHotspotEntity = null
  selectionPopup.visible = false
  selectionPopup.payload = null

  if (emitFireEvent && hadFireSelection) {
    emit('select-fire', null)
  }
  if (emitHotspotEvent && hadHotspotSelection) {
    emit('select-hotspot', null)
  }
  if (viewer && zoomOut && hadSelection) {
    zoomBackFromSelection(previousFireEntity, previousHotspotEntity)
  }
  requestSceneRender()
}

const renderFirePoints = async () => {
  closeSelection({ zoomOut: false })
  if (fireDataSource) {
    viewer.dataSources.remove(fireDataSource, true)
  }
  fireDataSource = new Cesium.CustomDataSource('fire-points')
  fireDataSource.show = props.showFirePoints
  const enableCluster = props.clusterFirePoints && props.points.length <= FIRE_POINT_CLUSTER_LIMIT
  const animatePoints = props.glowMode && props.points.length <= FIRE_POINT_ANIMATION_LIMIT
  fireDataSource.clustering.enabled = enableCluster
  fireDataSource.clustering.pixelRange = enableCluster ? 36 : 0
  fireDataSource.clustering.minimumClusterSize = 4
  if (enableCluster) {
    fireDataSource.clustering.clusterEvent.addEventListener((clusteredEntities, cluster) => {
      cluster.label.show = true
      cluster.label.text = clusteredEntities.length.toString()
      cluster.label.fillColor = Cesium.Color.WHITE
      cluster.billboard.show = false
      cluster.point.show = true
      cluster.point.pixelSize = 28
      cluster.point.color = Cesium.Color.fromCssColorString('#20c7ff').withAlpha(0.72)
      cluster.point.outlineColor = Cesium.Color.WHITE.withAlpha(0.6)
      cluster.point.outlineWidth = 2
    })
  }

  props.points.forEach((item) => {
    const longitude = Number(item.longitude)
    const latitude = Number(item.latitude)
    if (!isValidCoordinate(longitude, latitude)) {
      return
    }
    const baseColor = frpColor(item.frp, item.daynight)
    const entity = fireDataSource.entities.add({
      id: `fire-${item.id}`,
      position: Cesium.Cartesian3.fromDegrees(longitude, latitude),
      point: {
        pixelSize: frpSize(item.frp),
        color: animatePoints
          ? new Cesium.CallbackProperty(
              () => baseColor.withAlpha(0.45 + Math.abs(Math.sin(Date.now() / 260)) * 0.32),
              false,
            )
          : baseColor.withAlpha(0.88),
        outlineColor: Cesium.Color.WHITE.withAlpha(0.32),
        outlineWidth: 1,
      },
      properties: item,
    })
    entity._layerType = 'fire'
    entity._payload = item
    entity._basePixelSize = frpSize(item.frp)
  })

  await viewer.dataSources.add(fireDataSource)
  requestSceneRender()
}

const renderHotspots = async () => {
  closeSelection({ zoomOut: false })
  if (hotspotDataSource) {
    viewer.dataSources.remove(hotspotDataSource, true)
  }
  hotspotDataSource = new Cesium.CustomDataSource('hotspots')
  hotspotDataSource.show = props.showHotspots
  props.hotspots.forEach((item) => {
    const longitude = Number(item.center_longitude)
    const latitude = Number(item.center_latitude)
    if (!isValidCoordinate(longitude, latitude)) {
      return
    }
    const radius = hotspotRadius(item.fire_count)
    const entity = hotspotDataSource.entities.add({
      id: `hotspot-${item.id}`,
      position: Cesium.Cartesian3.fromDegrees(longitude, latitude),
      ellipse: {
        semiMinorAxis: radius,
        semiMajorAxis: radius,
        material: Cesium.Color.fromCssColorString('#ff8d43').withAlpha(props.glowMode ? 0.18 : 0.12),
        outline: true,
        outlineColor: Cesium.Color.fromCssColorString('#ffb37b').withAlpha(0.64),
        height: 0,
      },
      point: {
        pixelSize: 12,
        color: Cesium.Color.fromCssColorString('#ff8d43'),
        outlineColor: Cesium.Color.WHITE.withAlpha(0.45),
        outlineWidth: 1.5,
      },
      label: {
        text: `${item.fire_count}`,
        font: '600 12px sans-serif',
        fillColor: Cesium.Color.WHITE,
        pixelOffset: new Cesium.Cartesian2(0, -20),
      },
      properties: item,
    })
    entity._layerType = 'hotspot'
    entity._payload = item
    entity._basePixelSize = 12
    entity._baseSemiAxis = radius
  })
  await viewer.dataSources.add(hotspotDataSource)
  requestSceneRender()
}

const loadBoundaries = async () => {
  if (!props.showCountries || !props.boundaryUrl) return
  if (boundaryDataSource) {
    viewer.dataSources.remove(boundaryDataSource, true)
  }
  boundaryDataSource = await Cesium.GeoJsonDataSource.load(props.boundaryUrl, {
    stroke: Cesium.Color.fromCssColorString('#3fd7ff'),
    fill: Cesium.Color.fromCssColorString('#11283f').withAlpha(0.08),
    strokeWidth: 1.2,
  })
  boundaryDataSource.entities.values.forEach((entity) => {
    entity._layerType = 'country'
    entity._countryName = countryNameFromEntity(entity)
    entity._countryCode = countryCodeFromEntity(entity)
  })
  await viewer.dataSources.add(boundaryDataSource)
  updateCountryStyles()
  requestSceneRender()
}

const syncBoundaryLayer = async () => {
  if (!viewer) return
  if (!props.showCountries || !props.boundaryUrl) {
    unloadBoundaries()
    return
  }
  if (!boundaryDataSource) {
    await loadBoundaries()
    return
  }
  boundaryDataSource.show = true
  scheduleCountryStyleUpdate()
}

const flyToView = (viewKey = props.initialView) => {
  const targetView = DEFAULT_VIEWS[viewKey] || DEFAULT_VIEWS.global
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(
      targetView.longitude,
      targetView.latitude,
      targetView.height,
    ),
    duration: 1.8,
  })
}

const flyToCoordinates = ({ longitude, latitude, height = 2800000, duration = 2.2 }) => {
  const lon = Number(longitude)
  const lat = Number(latitude)
  if (!viewer || !isValidCoordinate(lon, lat)) return
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(lon, lat, height),
    duration,
  })
}

const selectFireEntity = (entity) => {
  if (!entity?._payload) return
  closeSelection({ zoomOut: false, emitFireEvent: false })

  selectedFireEntity = entity
  if (selectedFireEntity.point) {
    selectedFireEntity.point.pixelSize = (selectedFireEntity._basePixelSize || frpSize(selectedFireEntity._payload?.frp)) + 9
  }

  selectionPopup.kind = 'fire'
  selectionPopup.payload = selectedFireEntity._payload
  selectionPopup.visible = true
  updateSelectionPopupPosition()

  flyToCoordinates({
    longitude: selectedFireEntity._payload.longitude,
    latitude: selectedFireEntity._payload.latitude,
    height: 1500000,
    duration: 1.35,
  })
  emit('select-fire', selectedFireEntity._payload)
}

const selectHotspotEntity = (entity) => {
  if (!entity?._payload) return
  closeSelection({ zoomOut: false })

  selectedHotspotEntity = entity
  if (selectedHotspotEntity.point) {
    selectedHotspotEntity.point.pixelSize = (selectedHotspotEntity._basePixelSize || 12) + 10
  }
  if (selectedHotspotEntity.ellipse) {
    selectedHotspotEntity.ellipse.semiMajorAxis = (selectedHotspotEntity._baseSemiAxis || 65000) * 1.28
    selectedHotspotEntity.ellipse.semiMinorAxis = (selectedHotspotEntity._baseSemiAxis || 65000) * 1.28
    selectedHotspotEntity.ellipse.material = Cesium.Color.fromCssColorString('#ff8d43').withAlpha(0.24)
    selectedHotspotEntity.ellipse.outlineColor = Cesium.Color.fromCssColorString('#ffd4a7').withAlpha(0.96)
  }

  selectionPopup.kind = 'hotspot'
  selectionPopup.payload = selectedHotspotEntity._payload
  selectionPopup.visible = true
  updateSelectionPopupPosition()

  flyToCoordinates({
    longitude: selectedHotspotEntity._payload.center_longitude,
    latitude: selectedHotspotEntity._payload.center_latitude,
    height: 1800000,
    duration: 1.55,
  })
  emit('select-hotspot', selectedHotspotEntity._payload)
}

const pickEntity = (entity) => {
  if (!entity) return
  if (entity._layerType === 'fire') {
    selectFireEntity(entity)
    return
  }
  if (entity._layerType === 'hotspot') {
    selectHotspotEntity(entity)
    return
  }
  if (entity._layerType === 'country') {
    closeSelection({ zoomOut: false })
    emit('select-country', {
      name: countryNameFromEntity(entity),
      code: countryCodeFromEntity(entity),
      value: choroplethMap.value.get(countryCodeFromEntity(entity)) ?? choroplethMap.value.get(countryNameFromEntity(entity)) ?? 0,
    })
  }
}

const resolvePickedEntity = (windowPosition) => {
  if (!viewer) return null
  const directPicked = viewer.scene.pick(windowPosition)?.id
  if (directPicked?._layerType) {
    return directPicked
  }

  const pickedItems = viewer.scene.drillPick(windowPosition, 10) || []
  if (!pickedItems.length) return null

  const entities = pickedItems.map((item) => item?.id).filter(Boolean)

  return (
    entities.find((entity) => entity._layerType === 'hotspot') ||
    entities.find((entity) => entity._layerType === 'fire') ||
    entities.find((entity) => entity._layerType === 'country') ||
    null
  )
}

const bindViewerEvents = () => {
  handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)
  handler.setInputAction((movement) => {
    if (!boundaryDataSource || !props.showCountries) {
      if (hoveredCountryEntity) {
        hoveredCountryEntity = null
        scheduleCountryStyleUpdate()
      }
      return
    }
    const picked = viewer.scene.pick(movement.endPosition)
    const nextHoveredEntity = picked?.id?._layerType === 'country' ? picked.id : null
    if (nextHoveredEntity !== hoveredCountryEntity) {
      hoveredCountryEntity = nextHoveredEntity
      scheduleCountryStyleUpdate()
    }
  }, Cesium.ScreenSpaceEventType.MOUSE_MOVE)

  handler.setInputAction((movement) => {
    const pickedEntity = resolvePickedEntity(movement.position)
    if (!pickedEntity) {
      closeSelection()
      return
    }
    pickEntity(pickedEntity)
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK)

  viewer.scene.renderError.addEventListener(() => {
    viewer.useDefaultRenderLoop = true
    scheduleBasemapRecovery(activeBaseLayerKey)
  })

  scenePostRenderHandler = () => {
    if (selectionPopup.visible) {
      updateSelectionPopupPosition()
    }
    if (props.showHeatmap) {
      scheduleHeatmapRender()
    }
  }
  viewer.scene.postRender.addEventListener(scenePostRenderHandler)
}

onMounted(async () => {
  viewer = new Cesium.Viewer(containerRef.value, {
    animation: false,
    baseLayerPicker: false,
    creditContainer: creditContainerRef.value,
    fullscreenButton: false,
    geocoder: false,
    homeButton: false,
    timeline: false,
    navigationHelpButton: false,
    infoBox: false,
    sceneModePicker: false,
    selectionIndicator: false,
    requestRenderMode: true,
    maximumRenderTimeChange: Number.POSITIVE_INFINITY,
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
  })
  viewer.resolutionScale = Math.min(window.devicePixelRatio || 1, props.glowMode ? 1.15 : 1)
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#03111d')
  viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#03101b')
  viewer.scene.globe.enableLighting = props.glowMode
  viewer.scene.postProcessStages.fxaa.enabled = true
  viewer.scene.skyBox = undefined
  viewer.scene.sun.show = props.glowMode
  viewer.scene.rethrowRenderErrors = false

  await applyBaseLayer(props.basemap)
  await syncBoundaryLayer()
  await renderFirePoints()
  await renderHotspots()
  renderHeatmap()
  flyToView(props.initialView)
  bindViewerEvents()
  emit('ready', {
    flyToCoordinates,
    flyHome: () => flyToView('global'),
  })
})

watch(
  () => props.points,
  async () => {
    if (viewer) await renderFirePoints()
  },
  { deep: true },
)

watch(
  () => props.hotspots,
  async () => {
    if (viewer) await renderHotspots()
  },
  { deep: true },
)

watch(
  () => props.heatmapPoints,
  () => {
    if (viewer) scheduleHeatmapRender()
  },
  { deep: true },
)

watch(
  () => props.points,
  () => {
    if (viewer && !props.heatmapPoints?.length) {
      scheduleHeatmapRender()
    }
  },
  { deep: true },
)

watch(
  () => [props.choropleth, props.selectedCountry, props.showCountries],
  () => scheduleCountryStyleUpdate(),
  { deep: true },
)

watch(
  () => [props.showCountries, props.boundaryUrl],
  async () => {
    if (viewer) await syncBoundaryLayer()
  },
)

watch(
  () => props.showFirePoints,
  () => {
    if (!props.showFirePoints && selectedFireEntity) {
      closeSelection({ zoomOut: false })
    }
    if (fireDataSource) fireDataSource.show = props.showFirePoints
    requestSceneRender()
  },
)

watch(
  () => props.showHotspots,
  () => {
    if (!props.showHotspots && selectedHotspotEntity) {
      closeSelection({ zoomOut: false })
    }
    if (hotspotDataSource) hotspotDataSource.show = props.showHotspots
    requestSceneRender()
  },
)

watch(
  () => props.showHeatmap,
  () => {
    if (!props.showHeatmap) {
      clearHeatmapCanvas()
    } else {
      scheduleHeatmapRender()
    }
    requestSceneRender()
  },
)

watch(
  () => props.initialView,
  (value) => {
    if (viewer) flyToView(value)
  },
)

watch(
  () => props.basemap,
  async (value) => {
    if (viewer) {
      await applyBaseLayer(value, getOverlayKeys(value))
    }
  },
)

onBeforeUnmount(() => {
  clearTimeout(recoverTimer)
  if (countryStyleFrame) {
    window.cancelAnimationFrame(countryStyleFrame)
    countryStyleFrame = null
  }
  if (heatmapRenderFrame) {
    window.cancelAnimationFrame(heatmapRenderFrame)
    heatmapRenderFrame = null
  }
  if (viewer?.scene && scenePostRenderHandler) {
    viewer.scene.postRender.removeEventListener(scenePostRenderHandler)
  }
  clearImageryErrorListeners()
  handler?.destroy()
  viewer?.destroy()
})

defineExpose({
  flyToCoordinates,
  flyToHotspot: (hotspot, height = 2800000) =>
    flyToCoordinates({
      longitude: hotspot.center_longitude ?? hotspot.longitude,
      latitude: hotspot.center_latitude ?? hotspot.latitude,
      height,
      duration: 2.6,
    }),
  flyHome: () => flyToView('global'),
  closeSelection,
  getViewer: () => viewer,
})
</script>

<style scoped>
.map-shell {
  position: relative;
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 20px;
  overflow: hidden;
}

.credit-sink {
  display: none;
}

.heatmap-canvas {
  position: absolute;
  inset: 0;
  z-index: 4;
  width: 100%;
  height: 100%;
  border-radius: 20px;
  pointer-events: none;
  opacity: 0;
  mix-blend-mode: screen;
  filter: saturate(1.08);
  transition: opacity 0.22s ease;
}

.heatmap-canvas.visible {
  opacity: 0.96;
}

.fire-popup {
  position: absolute;
  z-index: 8;
  width: 284px;
  padding: 14px 16px 12px;
  border-radius: 18px;
  border: 1px solid rgba(99, 195, 255, 0.18);
  background: linear-gradient(180deg, rgba(5, 18, 30, 0.96), rgba(4, 12, 22, 0.94));
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.38);
  backdrop-filter: blur(18px);
}

.fire-popup.hotspot {
  border-color: rgba(255, 164, 102, 0.24);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42), 0 0 0 1px rgba(255, 141, 67, 0.08) inset;
}

.fire-popup strong {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
}

.fire-popup p {
  margin: 0 0 10px;
  color: var(--text-secondary);
}

.popup-metrics {
  display: grid;
  gap: 6px;
  color: #fff;
  font-size: 12px;
}

.popup-tag {
  display: inline-flex;
  align-items: center;
  margin-top: 10px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(89, 214, 255, 0.12);
  color: var(--text-secondary);
  font-size: 12px;
}

.fire-popup.hotspot .popup-tag {
  background: rgba(255, 141, 67, 0.12);
}

.popup-close {
  position: absolute;
  top: 8px;
  right: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: var(--text-secondary);
  border: 1px solid rgba(99, 195, 255, 0.12);
  background: rgba(8, 28, 46, 0.72);
  cursor: pointer;
}

.popup-anchor {
  position: absolute;
  z-index: 7;
  width: 0;
  height: 0;
  pointer-events: none;
}

.popup-anchor span {
  position: absolute;
  left: -6px;
  top: -6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 6px rgba(255, 141, 67, 0.14);
}

.popup-anchor i {
  position: absolute;
  left: -1px;
  top: -32px;
  width: 2px;
  height: 26px;
  background: linear-gradient(180deg, rgba(255, 141, 67, 0.74), rgba(255, 255, 255, 0.1));
}
</style>
