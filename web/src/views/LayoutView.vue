<template>
  <div class="layout">
    <aside class="side">
      <div class="brand">
        <span class="logo">AI</span>
        <div>
          <div class="brand-name">智能问答平台</div>
          <div class="brand-sub">FastAPI + Vue</div>
        </div>
      </div>

      <nav class="nav">
        <router-link to="/" class="nav-item">
          <span>💬</span> 智能问答
        </router-link>
        <router-link v-if="auth.isAdmin" to="/models" class="nav-item">
          <span>🧩</span> 模型配置
        </router-link>
        <router-link v-if="auth.isAdmin" to="/users" class="nav-item">
          <span>👥</span> 用户管理
        </router-link>
      </nav>

      <div class="side-footer">
        <div class="me">
          <div class="avatar">{{ auth.nickname.slice(0, 1).toUpperCase() }}</div>
          <div class="me-info">
            <div class="me-name">{{ auth.nickname }}</div>
            <span class="tag" :class="auth.isAdmin ? 'admin' : 'user'">
              {{ auth.isAdmin ? '管理员' : '普通用户' }}
            </span>
          </div>
        </div>
        <button class="btn sm logout" @click="onLogout">退出登录</button>
      </div>
    </aside>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

function onLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { display: flex; height: 100%; }

.side {
  width: 220px;
  flex-shrink: 0;
  background: var(--bg-soft);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 18px 14px;
}

.brand { display: flex; gap: 10px; align-items: center; padding: 0 6px 18px; }
.logo {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; color: #fff;
}
.brand-name { font-weight: 600; }
.brand-sub { font-size: 11px; color: var(--text-mute); }

.nav { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.nav-item {
  padding: 9px 12px; border-radius: 8px; color: var(--text-dim);
  display: flex; gap: 10px; align-items: center; font-size: 14px;
}
.nav-item:hover { background: var(--panel); color: var(--text); }
.nav-item.router-link-exact-active {
  background: linear-gradient(135deg, rgba(79, 140, 255, 0.18), rgba(124, 92, 255, 0.18));
  color: var(--accent);
}

.side-footer { border-top: 1px solid var(--border); padding-top: 14px; display: grid; gap: 10px; }
.me { display: flex; gap: 10px; align-items: center; }
.avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--panel-2); display: flex; align-items: center; justify-content: center;
  font-weight: 600; color: var(--accent);
}
.me-info { flex: 1; min-width: 0; }
.me-name { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.logout { width: 100%; }

.main { flex: 1; min-width: 0; }
</style>
