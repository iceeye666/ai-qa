<template>
  <div class="page">
    <h2 class="page-title">模型配置</h2>
    <p class="page-desc">
      所有模型通过统一适配器接入：新增模型只需选择 provider 并填写参数，问答核心逻辑零改动。
    </p>

    <div class="card">
      <div class="toolbar">
        <button class="btn primary" @click="openCreate">+ 新增模型</button>
        <span class="tip">未填写 API Key 的模型在被调用时会自动降级到内置演示模型</span>
      </div>

      <table>
        <thead>
          <tr>
            <th>名称 / Key</th>
            <th>适配器</th>
            <th>模型名</th>
            <th>Base URL</th>
            <th>Key 状态</th>
            <th>状态</th>
            <th style="width: 150px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.id">
            <td>
              <div>{{ m.name }}</div>
              <code class="key">{{ m.key }}</code>
            </td>
            <td><span class="tag">{{ m.provider }}</span></td>
            <td>{{ m.model_name || '-' }}</td>
            <td class="url">{{ m.base_url || '默认' }}</td>
            <td>
              <span class="tag" :class="m.has_api_key ? 'user' : 'admin'">
                {{ m.has_api_key ? '已配置' : '未配置' }}
              </span>
            </td>
            <td>
              <span class="tag" :class="m.is_active ? 'user' : 'admin'">
                {{ m.is_active ? '启用' : '停用' }}
              </span>
            </td>
            <td>
              <button class="btn sm" @click="openEdit(m)">编辑</button>
              <button class="btn sm danger" @click="remove(m)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!models.length" class="empty">暂无模型配置</div>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <div v-if="showForm" class="mask" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ form.id ? '编辑模型' : '新增模型' }}</h3>
        <label>展示名称</label>
        <input v-model="form.name" class="input" placeholder="通义千问 Plus" />

        <label>模型 Key（唯一标识）</label>
        <input v-model="form.key" class="input" placeholder="qwen-plus" :disabled="!!form.id" />

        <label>适配器 provider</label>
        <select v-model="form.provider" class="select">
          <option v-for="p in providers" :key="p.provider" :value="p.provider">
            {{ p.provider }}{{ p.require_api_key ? '' : '（无需 Key）' }}
          </option>
        </select>

        <label>上游模型名</label>
        <input v-model="form.model_name" class="input" placeholder="qwen-plus" />

        <label>Base URL（留空用默认值）</label>
        <input v-model="form.base_url" class="input" placeholder="https://..." />

        <label>API Key</label>
        <input v-model="form.api_key" class="input" type="password" placeholder="sk-..." />

        <label>描述</label>
        <input v-model="form.description" class="input" placeholder="可选" />

        <label class="checkbox">
          <input v-model="form.is_active" type="checkbox" /> 启用该模型
        </label>

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
import { modelApi } from '../api'

const models = ref([])
const providers = ref([])
const showForm = ref(false)
const error = ref('')

const emptyForm = () => ({
  id: null, name: '', key: '', provider: 'qwen',
  model_name: '', base_url: '', api_key: '', description: '', is_active: true
})
const form = ref(emptyForm())

async function load() {
  models.value = await modelApi.list()
  providers.value = await modelApi.providers()
}

function openCreate() {
  form.value = emptyForm()
  error.value = ''
  showForm.value = true
}

function openEdit(m) {
  form.value = { ...m, api_key: '' }
  error.value = ''
  showForm.value = true
}

async function submit() {
  error.value = ''
  try {
    const payload = { ...form.value }
    delete payload.id
    if (!payload.api_key) delete payload.api_key
    if (form.value.id) {
      await modelApi.update(form.value.id, payload)
    } else {
      await modelApi.create(payload)
    }
    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(m) {
  if (!confirm(`确定删除模型「${m.name}」？`)) return
  await modelApi.remove(m.id)
  await load()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.tip { font-size: 12px; color: var(--text-mute); }
.key { font-size: 11px; color: var(--text-mute); }
.url { font-size: 12px; color: var(--text-dim); max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
td .btn + .btn { margin-left: 6px; }

.mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.55);
  display: flex; align-items: center; justify-content: center; z-index: 20;
}
.modal {
  width: 460px; max-height: 86vh; overflow-y: auto;
  background: var(--panel); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 22px; box-shadow: var(--shadow);
}
.modal h3 { margin: 0 0 14px; }
label { display: block; font-size: 12px; color: var(--text-dim); margin: 12px 0 6px; }
.checkbox { display: flex; align-items: center; gap: 8px; }
.error { color: var(--danger); font-size: 12px; margin: 12px 0 0; }
.modal-foot { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
</style>
