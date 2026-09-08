<template>
  <div class="login-page">
    <div class="login-card">
      <div class="head">
        <div class="logo">AI</div>
        <h1>智能问答平台</h1>
        <p>FastAPI + Vue 前后端分离 · JWT 鉴权 · 多模型可插拔</p>
      </div>

      <form @submit.prevent="onSubmit">
        <label>用户名</label>
        <input v-model="form.username" class="input" placeholder="admin" autocomplete="username" />

        <label>密码</label>
        <input
          v-model="form.password"
          class="input"
          type="password"
          placeholder="admin123"
          autocomplete="current-password"
          @keyup.enter="onSubmit"
        />

        <p v-if="error" class="error">{{ error }}</p>

        <button class="btn primary block" :disabled="loading" type="submit">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <div class="demo">
        演示账号：<code>admin / admin123</code>（管理员）· 未配置模型 Key 时自动使用内置演示模型
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.username, form.password)
    router.push('/')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex; align-items: center; justify-content: center;
  background:
    radial-gradient(900px 500px at 15% 10%, rgba(79, 140, 255, 0.12), transparent),
    radial-gradient(700px 400px at 85% 90%, rgba(124, 92, 255, 0.12), transparent),
    var(--bg);
}
.login-card {
  width: 380px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow);
}
.head { text-align: center; margin-bottom: 24px; }
.logo {
  width: 48px; height: 48px; margin: 0 auto 12px; border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 18px; color: #fff;
}
h1 { font-size: 20px; margin: 0 0 6px; }
.head p { margin: 0; font-size: 12px; color: var(--text-mute); }

label { display: block; font-size: 12px; color: var(--text-dim); margin: 12px 0 6px; }
.error { color: var(--danger); font-size: 12px; margin: 10px 0 0; }
.block { width: 100%; margin-top: 20px; padding: 10px; }
.demo {
  margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border);
  font-size: 12px; color: var(--text-mute); text-align: center; line-height: 1.8;
}
code { color: var(--accent); background: var(--bg-soft); padding: 1px 6px; border-radius: 4px; }
</style>
