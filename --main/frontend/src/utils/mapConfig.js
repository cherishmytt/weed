export const TIANDITU_KEY = import.meta.env.VITE_TIANDITU_KEY || ''

export const BASEMAPS = {
  tiandituImage: {
    id: 'tiandituImage',
    type: 'template',
    subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
    url: `https://t{s}.tianditu.gov.cn/DataServer?T=img_w&x={x}&y={y}&l={z}&tk=${TIANDITU_KEY}`,
    credit: 'Tianditu',
    minimumLevel: 1,
    maximumLevel: 18,
    tileWidth: 256,
    tileHeight: 256,
    enablePickFeatures: false,
    hasAlphaChannel: false,
  },
  tiandituLabel: {
    id: 'tiandituLabel',
    type: 'template',
    subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
    url: `https://t{s}.tianditu.gov.cn/DataServer?T=cia_w&x={x}&y={y}&l={z}&tk=${TIANDITU_KEY}`,
    credit: 'Tianditu',
    minimumLevel: 1,
    maximumLevel: 18,
    tileWidth: 256,
    tileHeight: 256,
    enablePickFeatures: false,
    hasAlphaChannel: true,
  },
  arcgisImage: {
    id: 'arcgisImage',
    type: 'arcgis',
    url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
  },
  osm: {
    id: 'osm',
    type: 'osm',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  },
  naturalEarth: {
    id: 'naturalEarth',
    type: 'naturalEarth',
  },
}

export const DEFAULT_BASEMAP = TIANDITU_KEY ? 'tiandituImage' : 'naturalEarth'
export const DEFAULT_BASEMAP_OVERLAYS = TIANDITU_KEY ? ['tiandituLabel'] : []
export const FALLBACK_BASEMAP = 'naturalEarth'

export const DEFAULT_VIEWS = {
  global: {
    longitude: 102,
    latitude: 24,
    height: 18000000,
  },
  world: {
    longitude: 102,
    latitude: 24,
    height: 18000000,
  },
  seasia: {
    longitude: 110,
    latitude: 13,
    height: 6500000,
  },
  australia: {
    longitude: 133,
    latitude: -25,
    height: 8500000,
  },
  south_america: {
    longitude: -60,
    latitude: -18,
    height: 9800000,
  },
}
