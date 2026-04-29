<template>
  <div class="login-page">
    <div class="login-shell">
      <section class="hero-panel">
        <div class="hero-scene" aria-hidden="true">
          <div class="scene-grid"></div>
          <div class="scene-grid scene-grid--minor"></div>
          <div class="scene-scan"></div>

          <svg class="hero-map" viewBox="0 0 1200 760" preserveAspectRatio="xMidYMid meet">
            <g class="map-outline">
              <path
                d="M160 292
                  L222 242 L286 228 L338 246 L382 236 L428 258 L432 308 L398 340
                  L400 380 L364 412 L352 464 L310 520 L258 544 L212 524 L180 478
                  L150 470 L132 420 L144 358 Z"
              />
              <path
                d="M278 548
                  L320 534 L352 544 L360 588 L334 664 L300 644 L286 594 Z"
              />
              <path
                d="M482 248
                  L560 222 L646 230 L708 260 L744 308 L760 348 L734 388 L690 392
                  L648 366 L598 370 L564 338 L520 344 L488 316 Z"
              />
              <path
                d="M634 392
                  L676 384 L720 410 L736 458 L706 504 L684 568 L634 616 L592 576
                  L602 516 L574 470 L590 422 Z"
              />
              <path
                d="M784 270
                  L844 246 L900 256 L968 244 L1024 270 L1080 312 L1092 360 L1056 394
                  L1016 384 L988 350 L942 346 L904 366 L856 350 L818 320 Z"
              />
              <path
                d="M982 512
                  L1024 494 L1072 512 L1114 554 L1102 606 L1060 640 L1014 622 L986 584 Z"
              />
            </g>
          </svg>

          <div class="orbit-field">
            <div
              v-for="orbit in orbitRings"
              :key="orbit.id"
              class="orbit-ring"
              :class="orbit.className"
              :style="{
                width: orbit.width,
                height: orbit.height,
                top: orbit.top,
                left: orbit.left,
                animationDuration: orbit.duration,
                animationDirection: orbit.direction,
              }"
            >
              <span class="orbit-dot" :class="orbit.tone"></span>
            </div>
          </div>

          <div class="hotspot-layer">
            <span
              v-for="node in hotspotNodes"
              :key="node.id"
              class="hotspot-node"
              :class="node.tone"
              :style="{
                top: node.top,
                left: node.left,
                width: node.size,
                height: node.size,
                animationDelay: node.delay,
              }"
            ></span>
          </div>
        </div>

        <div class="hero-copy">
          <h1>
            <span class="hero-line hero-line--primary">全球野火</span>
            <span class="hero-line hero-line--secondary">监测与时空分析平台</span>
          </h1>
        </div>
      </section>

      <section class="access-panel glass-panel">
        <div class="access-toolbar">
          <el-button class="theme-button ghost-btn" @click="uiStore.toggleTheme()">
            <el-icon><component :is="uiStore.themeMode === 'dark' ? 'Sunny' : 'Moon'" /></el-icon>
            <span>{{ uiStore.themeMode === 'dark' ? '浅色模式' : '深色模式' }}</span>
          </el-button>
        </div>

        <transition name="panel-swap" mode="out-in">
          <el-form
            v-if="activeTab === 'login'"
            key="login"
            :model="loginForm"
            label-position="top"
            class="access-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>

            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
            </el-form-item>

            <div class="tab-switch inline-switch" role="tablist" aria-label="登录与注册">
              <button
                type="button"
                class="tab-pill"
                :class="{ active: activeTab === 'login' }"
                @click="activeTab = 'login'"
              >
                系统登录
              </button>
              <button
                type="button"
                class="tab-pill"
                :class="{ active: activeTab === 'register' }"
                @click="activeTab = 'register'"
              >
                创建账号
              </button>
            </div>

            <el-button native-type="submit" class="submit-btn" :loading="loading">进入监测平台</el-button>
          </el-form>

          <el-form
            v-else
            key="register"
            :model="registerForm"
            label-position="top"
            class="access-form"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" placeholder="创建用户名" />
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
            </el-form-item>

            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password placeholder="创建密码" />
            </el-form-item>

            <div class="tab-switch inline-switch" role="tablist" aria-label="登录与注册">
              <button
                type="button"
                class="tab-pill"
                :class="{ active: activeTab === 'login' }"
                @click="activeTab = 'login'"
              >
                系统登录
              </button>
              <button
                type="button"
                class="tab-pill"
                :class="{ active: activeTab === 'register' }"
                @click="activeTab = 'register'"
              >
                创建账号
              </button>
            </div>

            <el-button native-type="submit" class="submit-btn" :loading="loading">创建账号</el-button>
          </el-form>
        </transition>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { authApi } from '@/api/service'
import { useAuthStore } from '@/stores/auth'
import { useOverviewStore } from '@/stores/overview'
import { useUiStore } from '@/stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const overviewStore = useOverviewStore()
const uiStore = useUiStore()
const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
})

const orbitRings = [
  { id: 'ring-1', width: '72%', height: '58%', top: '18%', left: '15%', duration: '24s', direction: 'normal', tone: 'cyan', className: 'ring-a' },
  { id: 'ring-2', width: '56%', height: '44%', top: '25%', left: '24%', duration: '18s', direction: 'reverse', tone: 'amber', className: 'ring-b' },
  { id: 'ring-3', width: '40%', height: '31%', top: '32%', left: '33%', duration: '14s', direction: 'normal', tone: 'cyan', className: 'ring-c' },
]

const hotspotNodes = [
  { id: 'hot-1', top: '30%', left: '20%', size: '14px', delay: '0s', tone: 'cyan' },
  { id: 'hot-2', top: '38%', left: '67%', size: '16px', delay: '1.1s', tone: 'amber' },
  { id: 'hot-3', top: '61%', left: '56%', size: '18px', delay: '0.6s', tone: 'warm' },
  { id: 'hot-4', top: '68%', left: '29%', size: '15px', delay: '1.4s', tone: 'amber' },
  { id: 'hot-5', top: '54%', left: '77%', size: '14px', delay: '0.9s', tone: 'warm' },
]

const handleLogin = async () => {
  loading.value = true
  try {
    await authStore.login(loginForm)
    overviewStore.load(true).catch(() => {})
    ElMessage.success('登录成功')
    router.push('/overview')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  try {
    await authApi.register(registerForm)
    ElMessage.success('注册成功')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  --login-page-bg:
    radial-gradient(circle at 12% 18%, rgba(74, 155, 255, 0.12), transparent 22%),
    radial-gradient(circle at 88% 82%, rgba(255, 148, 73, 0.1), transparent 20%),
    linear-gradient(135deg, #030811 0%, #071221 42%, #081a2b 100%);
  --login-hero-border: rgba(100, 205, 255, 0.12);
  --login-hero-bg:
    linear-gradient(155deg, rgba(6, 18, 31, 0.96), rgba(8, 29, 48, 0.92)),
    radial-gradient(circle at 26% 30%, rgba(88, 199, 255, 0.08), transparent 24%);
  --login-panel-shadow:
    0 24px 70px rgba(0, 0, 0, 0.34),
    inset 0 0 0 1px rgba(100, 205, 255, 0.04);
  --login-grid-major: rgba(101, 205, 255, 0.08);
  --login-grid-minor: rgba(101, 205, 255, 0.035);
  --login-scan: rgba(101, 205, 255, 0.1);
  --login-map-fill: rgba(18, 58, 96, 0.18);
  --login-map-stroke: rgba(108, 214, 255, 0.72);
  --login-map-shadow: rgba(100, 205, 255, 0.16);
  --login-title-gradient: linear-gradient(90deg, #83e1ff 0%, #5ebeff 38%, #ffd28a 76%, #ff9b4e 100%);
  --login-title-shadow: rgba(101, 205, 255, 0.08);
  --login-card-bg: linear-gradient(180deg, rgba(6, 18, 31, 0.9), rgba(4, 13, 23, 0.96));
  --login-card-border: rgba(100, 205, 255, 0.14);
  --login-tab-bg: rgba(8, 22, 38, 0.56);
  --login-tab-text: rgba(221, 232, 255, 0.6);
  --login-form-label: rgba(234, 240, 255, 0.84);
  --login-input-bg: rgba(4, 14, 24, 0.92);
  --login-input-border: rgba(100, 205, 255, 0.14);
  --login-input-focus: rgba(100, 205, 255, 0.42);
  --login-input-text: #f7fbff;
  --login-autofill-fill: rgba(4, 14, 24, 0.92);
  min-height: 100vh;
  overflow: hidden;
  background: var(--login-page-bg);
}

:global(html[data-theme='light']) .login-page {
  --login-page-bg:
    radial-gradient(circle at 12% 18%, rgba(61, 137, 228, 0.14), transparent 24%),
    radial-gradient(circle at 84% 76%, rgba(241, 159, 84, 0.12), transparent 22%),
    linear-gradient(135deg, #eef5fb 0%, #e3eef8 48%, #dce9f5 100%);
  --login-hero-border: rgba(35, 102, 186, 0.14);
  --login-hero-bg:
    linear-gradient(155deg, rgba(255, 255, 255, 0.92), rgba(232, 241, 250, 0.96)),
    radial-gradient(circle at 26% 30%, rgba(61, 137, 228, 0.08), transparent 24%);
  --login-panel-shadow:
    0 24px 60px rgba(33, 71, 115, 0.12),
    inset 0 0 0 1px rgba(35, 102, 186, 0.06);
  --login-grid-major: rgba(35, 102, 186, 0.09);
  --login-grid-minor: rgba(35, 102, 186, 0.04);
  --login-scan: rgba(44, 128, 224, 0.12);
  --login-map-fill: rgba(117, 163, 210, 0.16);
  --login-map-stroke: rgba(45, 122, 214, 0.66);
  --login-map-shadow: rgba(45, 122, 214, 0.12);
  --login-title-gradient: linear-gradient(90deg, #2473d8 0%, #0ea2db 36%, #e8a445 76%, #d57230 100%);
  --login-title-shadow: rgba(45, 122, 214, 0.06);
  --login-card-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(245, 249, 253, 0.94));
  --login-card-border: rgba(35, 102, 186, 0.14);
  --login-tab-bg: rgba(238, 244, 250, 0.9);
  --login-tab-text: rgba(16, 35, 56, 0.58);
  --login-form-label: rgba(16, 35, 56, 0.8);
  --login-input-bg: rgba(248, 251, 255, 0.98);
  --login-input-border: rgba(35, 102, 186, 0.14);
  --login-input-focus: rgba(35, 102, 186, 0.36);
  --login-input-text: #102338;
  --login-autofill-fill: rgba(248, 251, 255, 0.98);
}

.login-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.52fr) minmax(360px, 430px);
  gap: 26px;
  width: min(1520px, calc(100vw - 36px));
  height: min(940px, calc(100vh - 36px));
  margin: 18px auto;
}

.hero-panel,
.access-panel {
  min-height: 0;
}

.hero-panel {
  position: relative;
  overflow: hidden;
  border-radius: 34px;
  border: 1px solid var(--login-hero-border);
  background: var(--login-hero-bg);
  box-shadow: var(--login-panel-shadow);
}

.hero-scene {
  position: absolute;
  inset: 0;
}

.scene-grid,
.scene-grid--minor {
  position: absolute;
  inset: 0;
}

.scene-grid {
  background-image:
    linear-gradient(var(--login-grid-major) 1px, transparent 1px),
    linear-gradient(90deg, var(--login-grid-major) 1px, transparent 1px);
  background-size: 92px 92px;
}

.scene-grid--minor {
  background-image:
    linear-gradient(var(--login-grid-minor) 1px, transparent 1px),
    linear-gradient(90deg, var(--login-grid-minor) 1px, transparent 1px);
  background-size: 16px 16px;
  mask-image: linear-gradient(180deg, transparent, black 16%, black 88%, transparent);
}

.scene-scan {
  position: absolute;
  inset: -10% -16%;
  background: linear-gradient(112deg, transparent 28%, var(--login-scan) 50%, transparent 72%);
  mix-blend-mode: screen;
  animation: scanMove 13s linear infinite;
}

.hero-map {
  position: absolute;
  inset: 9% 9% 12%;
  width: 82%;
  height: 72%;
  opacity: 0.72;
}

.map-outline {
  fill: var(--login-map-fill);
  stroke: var(--login-map-stroke);
  stroke-width: 2.2;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 10px var(--login-map-shadow));
}

.orbit-field {
  position: absolute;
  inset: 0;
}

.orbit-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(100, 205, 255, 0.14);
  animation-name: orbitSpin;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

.orbit-ring::before {
  content: '';
  position: absolute;
  inset: 12%;
  border-radius: 50%;
  border: 1px dashed rgba(100, 205, 255, 0.06);
}

.orbit-dot {
  position: absolute;
  top: -7px;
  left: 50%;
  width: 14px;
  height: 14px;
  margin-left: -7px;
  border-radius: 50%;
  box-shadow: 0 0 16px rgba(255, 161, 77, 0.46);
}

.orbit-dot.cyan {
  background: radial-gradient(circle, rgba(226, 247, 255, 0.98), rgba(101, 205, 255, 0.88) 48%, rgba(101, 205, 255, 0.12) 72%);
  box-shadow: 0 0 18px rgba(101, 205, 255, 0.46);
}

.orbit-dot.amber {
  background: radial-gradient(circle, rgba(255, 246, 214, 0.98), rgba(255, 176, 90, 0.88) 48%, rgba(255, 176, 90, 0.14) 72%);
  box-shadow: 0 0 18px rgba(255, 176, 90, 0.42);
}

.hotspot-layer {
  position: absolute;
  inset: 0;
}

.hotspot-node {
  position: absolute;
  border-radius: 50%;
  animation: hotspotPulse 4.4s ease-in-out infinite;
}

.hotspot-node::before,
.hotspot-node::after {
  content: '';
  position: absolute;
  border-radius: 50%;
}

.hotspot-node::before {
  inset: -10px;
  background: radial-gradient(circle, rgba(255, 192, 108, 0.28), transparent 70%);
  filter: blur(4px);
}

.hotspot-node::after {
  inset: 0;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.96), rgba(255, 171, 82, 0.82) 50%, transparent 76%);
}

.hotspot-node.cyan::after {
  background: radial-gradient(circle, rgba(241, 250, 255, 0.96), rgba(101, 205, 255, 0.86) 50%, transparent 76%);
}

.hotspot-node.amber::after {
  background: radial-gradient(circle, rgba(255, 248, 224, 0.96), rgba(255, 191, 82, 0.84) 50%, transparent 76%);
}

.hero-copy {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
  padding: 0 56px 38px 34px;
}

.hero-copy h1 {
  display: grid;
  gap: 4px;
  max-width: 820px;
  margin: 0;
}

.hero-line {
  display: block;
  background: var(--login-title-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 24px var(--login-title-shadow);
}

.hero-line--primary {
  font-size: clamp(52px, 5.7vw, 88px);
  line-height: 0.98;
  letter-spacing: 0.05em;
}

.hero-line--secondary {
  font-size: clamp(34px, 3.8vw, 60px);
  line-height: 1.08;
  letter-spacing: 0.025em;
}

.access-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 30px 28px;
  border-radius: 32px;
  border: 1px solid var(--login-card-border);
  background: var(--login-card-bg);
  box-shadow: var(--login-panel-shadow);
  backdrop-filter: blur(20px);
}

.access-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 18px;
}

.theme-button {
  padding-inline: 14px;
}

.tab-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 6px;
  margin-bottom: 24px;
  border-radius: 18px;
  border: 1px solid var(--login-card-border);
  background: var(--login-tab-bg);
}

.inline-switch {
  margin: 4px 0 14px;
}

.tab-pill {
  min-height: 46px;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: var(--login-tab-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.22s ease;
}

.tab-pill.active {
  color: #08131f;
  background: linear-gradient(135deg, #64d8ff 0%, #4d93ff 58%, #ffb66c 120%);
  box-shadow: 0 12px 26px rgba(46, 120, 255, 0.2);
}

.access-form {
  display: grid;
}

.access-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.access-form :deep(.el-form-item__label) {
  padding-bottom: 8px;
  color: var(--login-form-label);
  font-weight: 600;
}

.access-form :deep(.el-input__wrapper) {
  min-height: 52px;
  border-radius: 16px;
  background: var(--login-input-bg) !important;
  border: 1px solid var(--login-input-border) !important;
  box-shadow: none !important;
}

.access-form :deep(.el-input__wrapper.is-focus) {
  border-color: var(--login-input-focus) !important;
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--login-input-focus) 55%, transparent) inset,
    0 0 24px color-mix(in srgb, var(--login-input-focus) 32%, transparent) !important;
}

.access-form :deep(.el-input__inner) {
  color: var(--login-input-text) !important;
}

.submit-btn {
  width: 100%;
  min-height: 54px;
  margin-top: 8px;
  border: 0;
  border-radius: 18px;
  background: linear-gradient(135deg, #64d8ff 0%, #4e95ff 54%, #ffb66c 100%);
  color: #07121d;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
  box-shadow:
    0 16px 34px rgba(42, 108, 255, 0.24),
    0 10px 22px rgba(255, 161, 80, 0.14);
}

.submit-btn:hover {
  filter: brightness(1.03);
}

.access-panel :deep(input:-webkit-autofill),
.access-panel :deep(input:-webkit-autofill:hover),
.access-panel :deep(input:-webkit-autofill:focus),
.access-panel :deep(textarea:-webkit-autofill) {
  -webkit-text-fill-color: var(--login-input-text) !important;
  box-shadow: 0 0 0 1000px var(--login-autofill-fill) inset !important;
  transition: background-color 9999s ease-out 0s;
}

.panel-swap-enter-active,
.panel-swap-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.panel-swap-enter-from,
.panel-swap-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@keyframes orbitSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes hotspotPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.76;
  }
  50% {
    transform: scale(1.16);
    opacity: 1;
  }
}

@keyframes scanMove {
  0% {
    transform: translateX(-12%);
  }
  50% {
    transform: translateX(12%);
  }
  100% {
    transform: translateX(-12%);
  }
}

@media (max-width: 1220px) {
  .login-shell {
    grid-template-columns: minmax(0, 1fr) 390px;
    width: min(1400px, calc(100vw - 26px));
    height: min(900px, calc(100vh - 26px));
    gap: 20px;
    margin: 13px auto;
  }

  .hero-copy {
    padding: 0 42px 30px 24px;
  }
}

@media (max-width: 1024px) {
  .login-shell {
    grid-template-columns: 1fr;
    height: auto;
    min-height: calc(100vh - 24px);
  }

  .hero-panel {
    min-height: 520px;
  }
}

@media (max-width: 720px) {
  .login-shell {
    width: calc(100vw - 18px);
    margin: 9px auto;
  }

  .hero-panel {
    min-height: 460px;
  }

  .hero-copy {
    padding: 0 24px 22px 18px;
  }

  .access-panel {
    padding: 22px 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .orbit-ring,
  .scene-scan,
  .hotspot-node {
    animation: none !important;
  }
}
</style>
