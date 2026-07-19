<template>
  <div class="app-container">
    <NavBar />
    <div class="main-wrapper">
      <div class="central-card">
        <router-view />
      </div>
    </div>
    <div class="site-footer">
      <span>© 2026 在线答题系统</span>
    </div>
  </div>
</template>

<script setup>
import NavBar from '@/components/NavBar.vue'
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { min-height: 100vh; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }

:root {
  --x-pos: 50;
  --y-pos: 50;
}

body {
  background: radial-gradient(circle at calc(var(--x-pos) * 1%) calc(var(--y-pos) * 1%), 
              rgba(255, 220, 230, 0.25) 0%, 
              rgba(200, 255, 200, 0.18) 60%,
              #ffffff 100%);
  background-attachment: fixed;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2rem 1rem;
}

.central-card {
  width: 100%;
  max-width: 960px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.site-footer {
  text-align: center;
  padding: 1rem 0;
  color: rgba(108, 108, 108, 0.7);
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .central-card {
    border-radius: 1rem;
    padding: 1.25rem;
  }
  .main-wrapper {
    padding: 1rem 0.5rem;
  }
}
</style>