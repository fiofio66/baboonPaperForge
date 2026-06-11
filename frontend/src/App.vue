<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'

// ===================================================================
// i18n — lightweight, zero-dependency, reactive
// ===================================================================
const LOCALE_KEY = 'baboon_locale'
const locale = ref(localStorage.getItem(LOCALE_KEY) || 'zh')
watch(locale, v => localStorage.setItem(LOCALE_KEY, v))

const dict = {
  zh: {
    appName: 'BaboonPaperForge',
    appDesc: '论文智能排版与模板适配平台',
    slogan: '零 Token · 隐私优先 · BYOK',
    tabs: { templates: '📄 模板', content: '✍️ 编辑', settings: '⚙️ 设置' },
    // Templates
    createTpl: '创建模板',
    journalPlaceholder: '期刊名称 (如 IEEE Internet of Things Journal)',
    formatLatex: 'LaTeX (.tex)',
    formatDocx: 'Word (.docx)',
    filePath: '文件路径 (如 ./workdir/ieee/main.tex)',
    create: '创建',
    savedTpls: '已保存的模板',
    noTpls: '暂无模板。请在上方创建。',
    parsed: '已解析 ✓',
    parse: '🔍 解析',
    parsing: '解析',
    delete: '🗑',
    // Content
    noParsed: '请先在模板页解析一个模板，查看其模块结构。',
    goTemplates: '前往模板页',
    modules: '个模块',
    enterText: '请输入{label}...',
    addFigure: '+ 添加图片',
    addTable: '+ 添加表格',
    figureCaption: '图注',
    figureLabel: '标签 (如 fig:result)',
    figurePath: '图片路径',
    wide: '跨栏',
    assemble: '⚡ 一键排版 (零 Token)',
    done: '✓ 完成',
    output: '输出',
    filled: '已填充',
    // Settings
    createProfile: '创建用户档案',
    profileHint: '你的标识符不会被分享。请选择一个昵称。',
    nickname: '你的昵称',
    save: '创建',
    profile: '档案',
    defaultProvider: '默认提供商',
    llmProviders: '大模型配置',
    noProviders: '暂未配置任何模型提供商。',
    active: '活跃',
    inactive: '未激活',
    addProvider: '添加提供商',
    apiKey: 'API Key (加密存储)',
    baseUrl: 'Base URL',
    modelPlaceholder: '模型名称 (如 gpt-4o, claude-opus-4-8)',
    add: '添加',
    remove: '移除',
    // Messages
    backendOk: '后端已连接',
    tplCreated: '模板创建成功！',
    tplDeleted: '已删除',
    parsedMsg: '解析完成！发现 {count} 个模块',
    assembleDone: '排版完成！',
    userCreated: '用户创建成功！',
    providerAdded: '提供商已添加！',
    providerRemoved: '已移除',
    fillRequired: '期刊名称和文件路径为必填项',
    enterId: '请输入用户标识符',
    noParsedForAssemble: '未找到已解析的模板。请先解析。',
    noTplSelected: '未选择模板',
    confirmDeleteTpl: '确定要删除此模板吗？',
    confirmRemoveProvider: '确定要移除此提供商吗？',
    status: '状态',
    type: '类型',
    level: '层级',
  },
  en: {
    appName: 'BaboonPaperForge',
    appDesc: 'Paper Intelligent Typesetting & Template Adaptation Platform',
    slogan: 'Zero-Token · Privacy-First · BYOK',
    tabs: { templates: '📄 Templates', content: '✍️ Editor', settings: '⚙️ Settings' },
    // Templates
    createTpl: 'Create Template',
    journalPlaceholder: 'Journal name (e.g. IEEE Internet of Things Journal)',
    formatLatex: 'LaTeX (.tex)',
    formatDocx: 'Word (.docx)',
    filePath: 'File path (e.g. ./workdir/ieee/main.tex)',
    create: 'Create',
    savedTpls: 'Saved Templates',
    noTpls: 'No templates yet. Create one above.',
    parsed: 'parsed ✓',
    parse: '🔍 Parse',
    parsing: 'Parse',
    delete: '🗑',
    // Content
    noParsed: 'Parse a template first to see its module structure.',
    goTemplates: 'Go to Templates',
    modules: 'modules',
    enterText: 'Enter {label}...',
    addFigure: '+ Add Figure',
    addTable: '+ Add Table',
    figureCaption: 'Caption',
    figureLabel: 'Label (e.g. fig:result)',
    figurePath: 'Image path',
    wide: 'Wide',
    assemble: '⚡ Assemble (Zero-Token)',
    done: '✓ Done',
    output: 'Output',
    filled: 'filled',
    // Settings
    createProfile: 'Create User Profile',
    profileHint: 'Your identifier is never shared. Choose a nickname.',
    nickname: 'Your nickname',
    save: 'Create',
    profile: 'Profile',
    defaultProvider: 'Default provider',
    llmProviders: 'LLM Providers',
    noProviders: 'No providers configured yet.',
    active: 'active',
    inactive: 'inactive',
    addProvider: 'Add Provider',
    apiKey: 'API Key (encrypted at rest)',
    baseUrl: 'Base URL',
    modelPlaceholder: 'Model (e.g. gpt-4o, claude-opus-4-8)',
    add: 'Add',
    remove: 'Remove',
    // Messages
    backendOk: 'Backend connected',
    tplCreated: 'Template created!',
    tplDeleted: 'Deleted',
    parsedMsg: 'Parsed! Found {count} modules',
    assembleDone: 'Assembly complete!',
    userCreated: 'User created!',
    providerAdded: 'Provider added!',
    providerRemoved: 'Removed',
    fillRequired: 'Journal name and file path are required',
    enterId: 'Enter a user identifier',
    noParsedForAssemble: 'No parsed template found. Parse a template first.',
    noTplSelected: 'No template selected',
    confirmDeleteTpl: 'Delete this template?',
    confirmRemoveProvider: 'Remove this provider?',
    status: 'Status',
    type: 'Type',
    level: 'Level',
  },
}

function t(key, params) {
  const val = dict[locale.value]?.[key] ?? dict.en[key] ?? key
  return params ? val.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`) : val
}

const typeIcons = { title: '📌', author: '👤', abstract: '📃', section: '§', bibliography: '📚', figure: '🖼', table: '📊', acknowledgments: '🙏', keywords: '🔑' }

// ===================================================================
// State
// ===================================================================
const API = '/api/v1'
const activeTab = ref('templates')
const loading = ref(false)
const message = ref({ text: '', type: '' })

function flash(text, type = 'success') {
  message.value = { text, type }
  setTimeout(() => message.value = { text: '', type: '' }, 3500)
}

// ----- Templates -----
const templates = ref([])
const templateForm = reactive({ journal_name: '', template_format: 'latex', download_path: '' })
const parsedMapping = ref(null)

// ----- Editor -----
const userContent = reactive({})
const figures = reactive([])
const assembleResult = ref(null)

// ----- Settings -----
const userConfig = ref(null)
const llmConfigs = ref([])
const newLLM = reactive({ provider: 'openai', api_key: '', base_url: '', model_name: '' })
const userForm = reactive({ user_identifier: '', default_provider: 'openai' })

// ===================================================================
// API helpers
// ===================================================================
async function api(path, opts = {}) {
  const res = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json', ...opts.headers }, ...opts })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.status === 204 ? null : res.json()
}

// ===================================================================
// Templates
// ===================================================================
async function loadTemplates() {
  loading.value = true
  try { templates.value = await api('/templates') } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}
async function createTemplate() {
  if (!templateForm.journal_name || !templateForm.download_path) return flash(t('fillRequired'), 'error')
  loading.value = true
  try {
    await api('/templates', { method: 'POST', body: JSON.stringify(templateForm) })
    flash(t('tplCreated'), 'success')
    templateForm.journal_name = ''; templateForm.download_path = ''
    await loadTemplates()
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}
async function deleteTemplate(id) {
  if (!confirm(t('confirmDeleteTpl'))) return
  try { await api(`/templates/${id}`, { method: 'DELETE' }); flash(t('tplDeleted'), 'success'); await loadTemplates() }
  catch (e) { flash(e.message, 'error') }
}
async function parseTemplate(tmpl) {
  loading.value = true
  try {
    parsedMapping.value = await api(`/parser/analyze?template_id=${tmpl.id}`, { method: 'POST' })
    for (const m of parsedMapping.value.modules) {
      if (!(m.id in userContent) && m.type !== 'figure' && m.type !== 'table') userContent[m.id] = ''
    }
    flash(t('parsedMsg', { count: parsedMapping.value.modules.length }), 'success')
    activeTab.value = 'content'
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

// ===================================================================
// Editor
// ===================================================================
function addFigure() { figures.push({ caption: '', label: '', image_path: '', is_wide: false }) }
function removeFigure(idx) { figures.splice(idx, 1) }

async function runAssemble() {
  const match = templates.value.find(t => !!t.mapping_json)
  if (!match) return flash(t('noParsedForAssemble'), 'error')
  loading.value = true
  try {
    assembleResult.value = await api('/assembler/assemble', {
      method: 'POST',
      body: JSON.stringify({ template_id: match.id, user_content: userContent, figures: figures.filter(f => f.caption || f.image_path) }),
    })
    flash(t('assembleDone'), 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

// ===================================================================
// Settings
// ===================================================================
async function initUser() {
  const stored = localStorage.getItem('baboon_user_id')
  if (stored) {
    try { userConfig.value = await api(`/users/${stored}`); llmConfigs.value = userConfig.value.llm_configs || [] }
    catch { localStorage.removeItem('baboon_user_id') }
  }
}
async function createUser() {
  if (!userForm.user_identifier) return flash(t('enterId'), 'error')
  loading.value = true
  try {
    const u = await api('/users', { method: 'POST', body: JSON.stringify(userForm) })
    userConfig.value = u; localStorage.setItem('baboon_user_id', u.id); llmConfigs.value = []
    flash(t('userCreated'), 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}
async function addLLMConfig() {
  if (!userConfig.value) return
  loading.value = true
  try {
    const cfg = await api(`/users/${userConfig.value.id}/llm-configs`, { method: 'POST', body: JSON.stringify(newLLM) })
    llmConfigs.value.push(cfg); newLLM.api_key = ''; newLLM.model_name = ''
    flash(t('providerAdded'), 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}
async function deleteLLMConfig(cfgId) {
  if (!userConfig.value || !confirm(t('confirmRemoveProvider'))) return
  try {
    await api(`/users/${userConfig.value.id}/llm-configs/${cfgId}`, { method: 'DELETE' })
    llmConfigs.value = llmConfigs.value.filter(c => c.id !== cfgId)
    flash(t('providerRemoved'), 'success')
  } catch (e) { flash(e.message, 'error') }
}

// ===================================================================
// Init
// ===================================================================
onMounted(async () => {
  await loadTemplates(); await initUser()
  try { const h = await api('/health'); if (h.status === 'ok') flash(t('backendOk'), 'success') } catch { /* offline */ }
})
</script>

<template>
  <div class="app-shell">
    <!-- =============================================================== -->
    <!-- Header -->
    <!-- =============================================================== -->
    <header class="app-header">
      <div class="logo">
        <span class="logo-icon">🦧</span>
        <span class="logo-text">
          <span class="logo-accent">Baboon</span>PaperForge
        </span>
        <span class="logo-sub">{{ t('appDesc') }}</span>
      </div>
      <nav class="nav-tabs">
        <button v-for="tab in ['templates','content','settings']" :key="tab"
          :class="['nav-tab', { active: activeTab === tab }]" @click="activeTab = tab">{{ t(`tabs.${tab}`) }}</button>
      </nav>
      <div class="header-actions">
        <div class="locale-switch">
          <button :class="['locale-btn', { active: locale === 'zh' }]" @click="locale = 'zh'">中</button>
          <button :class="['locale-btn', { active: locale === 'en' }]" @click="locale = 'en'">EN</button>
        </div>
        <span v-if="loading" class="spinner"></span>
        <span class="badge" :class="message.type" v-if="message.text">{{ message.text }}</span>
      </div>
    </header>

    <!-- =============================================================== -->
    <!-- Templates -->
    <!-- =============================================================== -->
    <main v-if="activeTab === 'templates'" class="panel">
      <section class="card">
        <h2>{{ t('createTpl') }}</h2>
        <div class="form-row">
          <input v-model="templateForm.journal_name" :placeholder="t('journalPlaceholder')" class="input" />
          <select v-model="templateForm.template_format" class="input select">
            <option value="latex">{{ t('formatLatex') }}</option>
            <option value="docx">{{ t('formatDocx') }}</option>
          </select>
          <input v-model="templateForm.download_path" :placeholder="t('filePath')" class="input" />
          <button @click="createTemplate" class="btn btn-primary" :disabled="loading">{{ t('create') }}</button>
        </div>
      </section>

      <section class="card">
        <h2>{{ t('savedTpls') }}</h2>
        <div v-if="templates.length === 0" class="empty">{{ t('noTpls') }}</div>
        <div v-for="tmpl in templates" :key="tmpl.id" class="list-row">
          <div class="list-info">
            <strong>{{ tmpl.journal_name }}</strong>
            <span class="tag">{{ tmpl.template_format }}</span>
            <span class="muted">{{ tmpl.download_path }}</span>
            <span v-if="tmpl.mapping_json" class="tag green">{{ t('parsed') }}</span>
          </div>
          <div class="list-actions">
            <button @click="parseTemplate(tmpl)" class="btn btn-sm" :disabled="loading">{{ t('parse') }}</button>
            <button @click="deleteTemplate(tmpl.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button>
          </div>
        </div>
      </section>
    </main>

    <!-- =============================================================== -->
    <!-- Editor -->
    <!-- =============================================================== -->
    <main v-else-if="activeTab === 'content'" class="panel">
      <div v-if="!parsedMapping" class="empty-state">
        <div class="empty-icon">📝</div>
        <p>{{ t('noParsed') }}</p>
        <button @click="activeTab = 'templates'" class="btn btn-primary">{{ t('goTemplates') }}</button>
      </div>
      <div v-else class="editor-layout">
        <aside class="module-tree card">
          <h3>{{ parsedMapping.modules.length }} {{ t('modules') }}</h3>
          <div v-for="m in parsedMapping.modules" :key="m.id" class="module-item"
               :class="{ active: userContent[m.id]?.length }">
            <span class="module-icon">{{ typeIcons[m.type] || '•' }}</span>
            <span class="module-label">{{ m.label }}</span>
            <span class="tag sm">{{ m.type }}</span>
          </div>
        </aside>
        <section class="content-area">
          <div v-for="m in parsedMapping.modules" :key="m.id" class="card form-card">
            <div class="form-card-header">
              <span class="module-icon">{{ typeIcons[m.type] || '•' }}</span>
              <strong>{{ m.label }}</strong>
              <span class="tag">{{ m.type }}</span>
              <span v-if="m.level" class="tag sm">L{{ m.level }}</span>
            </div>
            <textarea v-if="m.type !== 'figure' && m.type !== 'table'" v-model="userContent[m.id]"
              :placeholder="t('enterText', { label: m.label })"
              :rows="m.type === 'abstract' ? 5 : m.type === 'title' ? 1 : 4" class="textarea" />
            <div v-if="m.type === 'figure' || m.type === 'table'">
              <div v-for="(fig, idx) in figures" :key="idx" class="figure-card card">
                <div class="form-row">
                  <input v-model="fig.caption" :placeholder="t('figureCaption')" class="input" />
                  <input v-model="fig.label" :placeholder="t('figureLabel')" class="input" />
                  <input v-model="fig.image_path" :placeholder="t('figurePath')" class="input" />
                  <label class="checkbox-label"><input type="checkbox" v-model="fig.is_wide" /> {{ t('wide') }}</label>
                  <button @click="removeFigure(idx)" class="btn btn-sm btn-danger">✕</button>
                </div>
              </div>
              <button @click="addFigure" class="btn btn-sm">{{ m.type === 'figure' ? t('addFigure') : t('addTable') }}</button>
            </div>
          </div>
          <div class="assemble-bar card">
            <button @click="runAssemble" class="btn btn-primary btn-lg" :disabled="loading">{{ t('assemble') }}</button>
            <div v-if="assembleResult" class="assemble-result">
              <span class="tag green">{{ t('done') }}</span>
              <span class="muted">{{ t('output') }}: {{ assembleResult.output_path }}</span>
              <span class="tag">{{ assembleResult.filled_count }}/{{ assembleResult.module_count }} {{ t('filled') }}</span>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- =============================================================== -->
    <!-- Settings -->
    <!-- =============================================================== -->
    <main v-else-if="activeTab === 'settings'" class="panel">
      <section class="card" v-if="!userConfig">
        <h2>{{ t('createProfile') }}</h2>
        <p class="muted">{{ t('profileHint') }}</p>
        <div class="form-row">
          <input v-model="userForm.user_identifier" :placeholder="t('nickname')" class="input" />
          <select v-model="userForm.default_provider" class="input select">
            <option value="openai">OpenAI</option><option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option><option value="ollama">Ollama (local)</option>
          </select>
          <button @click="createUser" class="btn btn-primary" :disabled="loading">{{ t('save') }}</button>
        </div>
      </section>
      <section v-else class="card">
        <h2>{{ t('profile') }}: {{ userConfig.user_identifier }}</h2>
        <p class="muted">{{ t('defaultProvider') }}: {{ userConfig.default_provider }}</p>
        <h3 style="margin-top: 1.5rem">{{ t('llmProviders') }}</h3>
        <div v-if="llmConfigs.length === 0" class="empty">{{ t('noProviders') }}</div>
        <div v-for="cfg in llmConfigs" :key="cfg.id" class="list-row">
          <div class="list-info">
            <strong>{{ cfg.provider }}</strong>
            <span v-if="cfg.model_name" class="tag">{{ cfg.model_name }}</span>
            <span v-if="cfg.base_url" class="muted">{{ cfg.base_url }}</span>
            <span class="tag" :class="cfg.is_active ? 'green' : ''">{{ cfg.is_active ? t('active') : t('inactive') }}</span>
          </div>
          <div class="list-actions">
            <button @click="deleteLLMConfig(cfg.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button>
          </div>
        </div>
        <h3 style="margin-top: 1.5rem">{{ t('addProvider') }}</h3>
        <div class="form-row">
          <select v-model="newLLM.provider" class="input select">
            <option value="openai">OpenAI</option><option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option><option value="ollama">Ollama</option>
          </select>
          <input v-if="newLLM.provider !== 'ollama'" v-model="newLLM.api_key" type="password" :placeholder="t('apiKey')" class="input" />
          <input v-if="newLLM.provider === 'ollama'" v-model="newLLM.base_url" :placeholder="t('baseUrl')" class="input" />
          <input v-model="newLLM.model_name" :placeholder="t('modelPlaceholder')" class="input" />
          <button @click="addLLMConfig" class="btn btn-primary" :disabled="loading">{{ t('add') }}</button>
        </div>
      </section>
    </main>

    <!-- =============================================================== -->
    <!-- Footer -->
    <!-- =============================================================== -->
    <footer class="app-footer">
      <span>BaboonPaperForge v0.1 · {{ t('appDesc') }}</span>
      <span class="muted">{{ t('slogan') }}</span>
    </footer>
  </div>
</template>

<style>
/* ==================================================================
   Design Tokens
   ================================================================== */
:root {
  --bg-primary: #0f0f14; --bg-secondary: #1a1a24; --bg-card: #222232;
  --bg-hover: #2a2a3a; --border: #333348;
  --text-primary: #e8e8f0; --text-secondary: #9a9ab8;
  --accent: #7c5cfc; --accent-glow: rgba(124,92,252,0.25);
  --success: #34d399; --danger: #f87171; --warning: #fbbf24;
  --radius: 10px; --radius-sm: 6px;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg-primary); color: var(--text-primary);
  line-height: 1.6; min-height: 100vh;
}
.app-shell { display: flex; flex-direction: column; min-height: 100vh; }

/* Header */
.app-header {
  display: flex; align-items: center; gap: 1.5rem;
  padding: 0 2rem; height: 60px;
  background: var(--bg-secondary); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.logo { display: flex; align-items: baseline; gap: 0.5rem; }
.logo-icon { font-size: 1.4rem; }
.logo-text { font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em; }
.logo-accent { color: var(--accent); }
.logo-sub { font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.35rem; }

.nav-tabs { display: flex; gap: 0.25rem; }
.nav-tab {
  background: none; border: none; color: var(--text-secondary);
  padding: 0.5rem 1rem; border-radius: var(--radius-sm); cursor: pointer;
  font-size: 0.9rem; font-weight: 500; transition: all 0.15s;
}
.nav-tab:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-tab.active { background: var(--accent); color: #fff; }

.header-actions { margin-left: auto; display: flex; align-items: center; gap: 0.75rem; }

.locale-switch { display: flex; border-radius: var(--radius-sm); overflow: hidden; border: 1px solid var(--border); }
.locale-btn {
  background: var(--bg-primary); border: none; color: var(--text-secondary);
  padding: 0.25rem 0.6rem; font-size: 0.75rem; cursor: pointer; font-weight: 600;
  transition: all 0.15s;
}
.locale-btn:hover { color: var(--text-primary); }
.locale-btn.active { background: var(--accent); color: #fff; }

/* Panels */
.panel { flex: 1; padding: 2rem; max-width: 1200px; width: 100%; margin: 0 auto; }
.card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1rem;
}
.card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: var(--text-primary); }
.card h3 { font-size: 1rem; margin-bottom: 0.75rem; }

/* Forms */
.form-row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.input {
  background: var(--bg-primary); border: 1px solid var(--border);
  color: var(--text-primary); padding: 0.6rem 0.85rem;
  border-radius: var(--radius-sm); font-size: 0.9rem;
  flex: 1; min-width: 120px; outline: none; transition: border-color 0.15s;
}
.input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
.select { cursor: pointer; }
.textarea {
  width: 100%; background: var(--bg-primary); border: 1px solid var(--border);
  color: var(--text-primary); padding: 0.85rem;
  border-radius: var(--radius-sm); font-size: 0.9rem; font-family: inherit;
  resize: vertical; outline: none; transition: border-color 0.15s;
}
.textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
.checkbox-label { display: flex; align-items: center; gap: 0.35rem; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; }

/* Buttons */
.btn {
  background: var(--bg-hover); border: 1px solid var(--border);
  color: var(--text-primary); padding: 0.55rem 1rem;
  border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.btn:hover { background: var(--border); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn-primary:hover { background: #6d4ff0; }
.btn-danger { color: var(--danger); }
.btn-danger:hover { background: rgba(248,113,113,0.1); }
.btn-sm { padding: 0.3rem 0.65rem; font-size: 0.8rem; }
.btn-lg { padding: 0.8rem 2rem; font-size: 1rem; }

/* Tags */
.tag {
  display: inline-block; padding: 0.15rem 0.5rem;
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 4px; font-size: 0.75rem; font-weight: 500;
  color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em;
}
.tag.green { border-color: var(--success); color: var(--success); }
.tag.sm { font-size: 0.65rem; padding: 0.1rem 0.35rem; }
.badge {
  padding: 0.3rem 0.8rem; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 500;
}
.badge.success { background: rgba(52,211,153,0.12); color: var(--success); }
.badge.error { background: rgba(248,113,113,0.12); color: var(--danger); }
.muted { color: var(--text-secondary); font-size: 0.85rem; }

/* Lists */
.list-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 0; border-bottom: 1px solid var(--border); gap: 1rem;
}
.list-row:last-child { border-bottom: none; }
.list-info { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.list-actions { display: flex; gap: 0.35rem; }
.empty { color: var(--text-secondary); font-style: italic; padding: 1rem 0; }
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }

/* Editor Layout */
.editor-layout { display: flex; gap: 1.5rem; align-items: flex-start; }
.module-tree { width: 260px; flex-shrink: 0; position: sticky; top: 80px; }
.module-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.5rem; border-radius: var(--radius-sm);
  font-size: 0.85rem; cursor: default; transition: background 0.1s;
}
.module-item:hover { background: var(--bg-hover); }
.module-item.active { background: rgba(124,92,252,0.08); }
.module-icon { font-size: 0.9rem; }
.module-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.content-area { flex: 1; display: flex; flex-direction: column; gap: 0.75rem; }
.form-card-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.figure-card { border: 1px dashed var(--border); padding: 0.75rem; }
.assemble-bar {
  display: flex; align-items: center; gap: 1.5rem;
  position: sticky; bottom: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.assemble-result { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }

/* Footer */
.app-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 2rem; border-top: 1px solid var(--border);
  font-size: 0.8rem; color: var(--text-secondary);
}

/* Spinner */
.spinner {
  width: 16px; height: 16px; border: 2px solid var(--border);
  border-top-color: var(--accent); border-radius: 50%;
  animation: spin 0.6s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
