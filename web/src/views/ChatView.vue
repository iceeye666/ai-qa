<template>
  <div class="chat">
    <!-- 会话列表 -->
    <aside class="conv">
      <button class="btn primary new" @click="newChat">+ 新建对话</button>
      <div class="conv-list">
        <div
          v-for="c in conversations"
          :key="c.id"
          class="conv-item"
          :class="{ active: c.id === currentId }"
          @click="openConversation(c.id)"
        >
          <div class="conv-title">{{ c.title }}</div>
          <div class="conv-meta">
            {{ c.message_count }} 条 · {{ formatTime(c.updated_at) }}
          </div>
          <span class="del" @click.stop="removeConversation(c.id)">×</span>
        </div>
        <div v-if="!conversations.length" class="empty">暂无对话记录</div>
      </div>
    </aside>

    <!-- 对话区 -->
    <section class="stage">
      <header class="topbar">
        <div class="topbar-left">
          <strong>{{ currentTitle }}</strong>
          <span v-if="currentModel" class="tag">{{ currentModel.name }}</span>
        </div>
        <div class="topbar-right">
          <select v-model="modelKey" class="select model-select">
            <option v-for="m in models" :key="m.key" :value="m.key">
              {{ m.name }}（{{ m.provider }}）
            </option>
          </select>
        </div>
      </header>

      <div class="messages" ref="msgBox">
        <div v-if="!messages.length" class="welcome">
          <div class="welcome-logo">AI</div>
          <h2>有什么可以帮您？</h2>
          <p>当前模型：<b>{{ currentModel?.name || '加载中' }}</b>。可在右上角切换模型，对话记录自动留存。</p>
          <div class="suggests">
            <button v-for="s in suggests" :key="s" class="btn sm" @click="send(s)">{{ s }}</button>
          </div>
        </div>

        <div
          v-for="(m, i) in messages"
          :key="m.id || i"
          class="msg-row"
          :class="m.role === 'user' ? 'me' : 'ai'"
        >
          <div class="avatar">{{ m.role === 'user' ? '我' : 'AI' }}</div>
          <div class="bubble">
            <div class="content">{{ m.content }}</div>
            <div v-if="m.role === 'assistant'" class="meta">
              {{ m.model_key }} · {{ m.tokens }} tokens · {{ m.latency_ms }} ms
            </div>
          </div>
        </div>

        <div v-if="sending" class="msg-row ai">
          <div class="avatar">AI</div>
          <div class="bubble">
            <span class="typing"><i></i><i></i><i></i></span>
          </div>
        </div>
      </div>

      <footer class="composer">
        <textarea
          v-model="input"
          class="textarea"
          rows="3"
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          @keydown.enter.exact.prevent="send()"
        ></textarea>
        <div class="composer-bar">
          <span class="hint">提示：未配置 API Key 时会自动使用内置演示模型</span>
          <button class="btn primary" :disabled="sending || !input.trim()" @click="send()">
            {{ sending ? '生成中…' : '发送' }}
          </button>
        </div>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { chatApi, modelApi } from '../api'

const conversations = ref([])
const messages = ref([])
const models = ref([])
const modelKey = ref('')
const currentId = ref(null)
const input = ref('')
const sending = ref(false)
const msgBox = ref(null)

const suggests = ['介绍一下 JWT 认证流程', 'FastAPI 后端是怎么组织的？', '模型怎么切换？', '项目如何部署？']

const currentModel = computed(() => models.value.find((m) => m.key === modelKey.value))
const currentTitle = computed(
  () => conversations.value.find((c) => c.id === currentId.value)?.title || '新的对话'
)

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t.replace(' ', 'T'))
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(
    d.getMinutes()
  ).padStart(2, '0')}`
}

async function scrollBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

async function loadModels() {
  models.value = await modelApi.list()
  if (!modelKey.value || !models.value.some((m) => m.key === modelKey.value)) {
    modelKey.value = models.value[0]?.key || ''
  }
}

async function loadConversations() {
  conversations.value = await chatApi.listConversations()
}

async function openConversation(id) {
  currentId.value = id
  const detail = await chatApi.getConversation(id)
  messages.value = detail.messages
  if (detail.model_key) modelKey.value = detail.model_key
  scrollBottom()
}

function newChat() {
  currentId.value = null
  messages.value = []
  input.value = ''
}

async function removeConversation(id) {
  await chatApi.deleteConversation(id)
  if (currentId.value === id) newChat()
  await loadConversations()
}

/** 流式发送：优先 SSE 逐字输出，失败自动降级为一次性返回 */
async function send(text) {
  const question = (text || input.value || '').trim()
  if (!question || sending.value) return

  input.value = ''
  sending.value = true
  messages.value.push({ role: 'user', content: question })
  const placeholder = { role: 'assistant', content: '', model_key: modelKey.value, tokens: 0, latency_ms: 0 }
  messages.value.push(placeholder)
  await scrollBottom()

  const payload = {
    message: question,
    conversation_id: currentId.value,
    model_key: modelKey.value
  }

  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload)
    })
    if (!res.ok || !res.body) throw new Error('stream unavailable')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let streamed = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split(/\r?\n\r?\n/)
      buffer = blocks.pop() || ''
      for (const block of blocks) {
        const evt = /event:\s*(\S+)/.exec(block)?.[1]
        const rawData = /data:\s*([\s\S]*)/.exec(block)?.[1]
        if (!evt || !rawData) continue
        const data = JSON.parse(rawData)
        if (evt === 'meta') {
          currentId.value = data.conversation_id
        } else if (evt === 'delta') {
          streamed = true
          placeholder.content += data.content
          await scrollBottom()
        } else if (evt === 'done') {
          placeholder.tokens = data.tokens
          placeholder.latency_ms = data.latency_ms
        } else if (evt === 'error') {
          placeholder.content = `⚠️ ${data.message}`
        }
      }
    }
    if (!streamed && !placeholder.content) throw new Error('empty stream')
  } catch (e) {
    // 降级：一次性返回
    try {
      const data = await chatApi.ask(payload)
      currentId.value = data.conversation_id
      placeholder.content = data.answer
      placeholder.tokens = data.tokens
      placeholder.latency_ms = data.latency_ms
      placeholder.model_key = data.model_key
    } catch (err) {
      placeholder.content = `⚠️ 请求失败：${err.message}`
    }
  } finally {
    sending.value = false
    await loadConversations()
    await scrollBottom()
  }
}

onMounted(async () => {
  await loadModels()
  await loadConversations()
})
</script>

<style scoped>
.chat { display: flex; height: 100%; }

.conv {
  width: 240px; flex-shrink: 0;
  background: var(--bg-soft); border-right: 1px solid var(--border);
  padding: 14px; display: flex; flex-direction: column; gap: 12px;
}
.new { width: 100%; }
.conv-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.conv-item {
  position: relative; padding: 9px 24px 9px 10px; border-radius: 8px;
  cursor: pointer; border: 1px solid transparent;
}
.conv-item:hover { background: var(--panel); }
.conv-item.active { background: var(--panel); border-color: var(--accent); }
.conv-title { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-meta { font-size: 11px; color: var(--text-mute); }
.del {
  position: absolute; right: 8px; top: 8px; color: var(--text-mute);
  font-size: 16px; line-height: 1; display: none;
}
.conv-item:hover .del { display: block; }
.del:hover { color: var(--danger); }

.stage { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.topbar {
  height: 56px; padding: 0 20px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.topbar-left { display: flex; align-items: center; gap: 10px; }
.model-select { width: 220px; }

.messages { flex: 1; overflow-y: auto; padding: 24px; }

.welcome { text-align: center; padding: 80px 20px; color: var(--text-dim); }
.welcome-logo {
  width: 56px; height: 56px; margin: 0 auto 16px; border-radius: 16px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700;
}
.welcome h2 { margin: 0 0 8px; color: var(--text); font-size: 20px; }
.suggests { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 20px; }

.msg-row { display: flex; gap: 12px; margin-bottom: 20px; }
.msg-row.me { flex-direction: row-reverse; }
.avatar {
  width: 30px; height: 30px; flex-shrink: 0; border-radius: 8px;
  background: var(--panel-2); display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: var(--accent);
}
.msg-row.me .avatar { background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff; }
.bubble { max-width: 70%; }
.msg-row.me .bubble { text-align: right; }
.content {
  display: inline-block; padding: 10px 14px; border-radius: 12px;
  background: var(--panel); border: 1px solid var(--border);
  white-space: pre-wrap; word-break: break-word; text-align: left;
}
.msg-row.me .content { background: rgba(79, 140, 255, 0.14); border-color: rgba(79, 140, 255, 0.35); }
.meta { font-size: 11px; color: var(--text-mute); margin-top: 4px; }

.typing i {
  display: inline-block; width: 6px; height: 6px; margin-right: 4px;
  border-radius: 50%; background: var(--text-mute); animation: blink 1.2s infinite;
}
.typing i:nth-child(2) { animation-delay: 0.2s; }
.typing i:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 60%, 100% { opacity: 0.25; } 30% { opacity: 1; } }

.composer { padding: 14px 24px 20px; border-top: 1px solid var(--border); }
.textarea { resize: none; }
.composer-bar { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.hint { font-size: 12px; color: var(--text-mute); }
</style>
