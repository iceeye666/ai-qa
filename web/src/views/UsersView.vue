<template>
  <div class="page">
    <h2 class="page-title">用户管理</h2>
    <p class="page-desc">RBAC 权限控制：管理员可管理模型与用户，普通用户仅可使用问答功能。</p>

    <div class="card">
      <div class="toolbar">
        <button class="btn primary" @click="openCreate">+ 新增用户</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>昵称</th>
            <th>角色</th>
            <th>状态</th>
            <th>最近登录</th>
            <th style="width: 160px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.nickname }}</td>
            <td><span class="tag" :class="u.role">{{ u.role === 'admin' ? '管理员' : '普通用户' }}</span></td>
            <td><span class="tag" :class="u.is_active ? 'user' : 'admin'">{{ u.is_active ? '正常' : '禁用' }}</span></td>
            <td class="dim">{{ u.last_login_at || '未登录' }}</td>
            <td>
              <button class="btn sm" @click="openEdit(u)">编辑</button>
              <button class="btn sm danger" @click="remove(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showForm" class="mask" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ form.id ? '编辑用户' : '新增用户' }}</h3>
        <label>用户名</label>
        <input v-model="form.username" class="input" :disabled="!!form.id" />

        <label>昵称</label>
        <input v-model="form.nickname" class="input" />

        <label>{{ form.id ? '重置密码（留空不修改）' : '密码' }}</label>
        <input v-model="form.password" class="input" type="password" />

        <label>角色</label>
        <select v-model="form.role" class="select">
          <option value="user">普通用户</option>
          <option value="admin">管理员</option>
        </select>

        <label class="checkbox"><input v-model="form.is_active" type="checkbox" /> 启用账号</label>

        <p v-if="error" class="error">{{ error }}</p>
        <div class="modal-foot">
          <button class="btn" @click="showForm = false">取消</button>
          <button class="btn primary" @click="submit">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { userApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref([])
const showForm = ref(false)
const error = ref('')

const emptyForm = () => ({
  id: null, username: '', nickname: '', password: '', role: 'user', is_active: true
})
const form = ref(emptyForm())

async function load() {
  users.value = await userApi.list()
}

function openCreate() {
  form.value = emptyForm()
  error.value = ''
  showForm.value = true
}

function openEdit(u) {
  form.value = { ...u, password: '' }
  error.value = ''
  showForm.value = true
}

async function submit() {
  error.value = ''
  try {
    if (form.value.id) {
      const payload = { ...form.value }
      delete payload.id
      delete payload.username
      if (!payload.password) delete payload.password
      await userApi.update(form.value.id, payload)
    } else {
      await userApi.create({ ...form.value })
    }
    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(u) {
  if (u.id === auth.user?.id) {
    alert('不能删除当前登录的用户')
    return
  }
  if (!confirm(`确定删除用户「${u.username}」？`)) return
  await userApi.remove(u.id)
  await load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { margin-bottom: 14px; }
.dim { color: var(--text-mute); font-size: 12px; }
td .btn + .btn { margin-left: 6px; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,.55); display: flex; align-items: center; justify-content: center; z-index: 20; }
.modal { width: 420px; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow); }
.modal h3 { margin: 0 0 14px; }
label { display: block; font-size: 12px; color: var(--text-dim); margin: 12px 0 6px; }
.checkbox { display: flex; align-items: center; gap: 8px; }
.error { color: var(--danger); font-size: 12px; margin: 12px 0 0; }
.modal-foot { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
</style>
