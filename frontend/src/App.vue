<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

// ===================================================================
// State
// ===================================================================
const API = '/api/v1'
const activeTab = ref('templates')
const loading = ref(false)
const message = ref({ text: '', type: '' })

// ----- Templates -----
const templates = ref([])
const templateForm = reactive({ journal_name: '', template_format: 'latex', download_path: '' })

// ----- Parser -----
const parsedMapping = ref(null)

// ----- User Content -----
const userContent = reactive({})
const figures = reactive([])

// ----- Assembler -----
const assembleResult = ref(null)

// ----- Settings -----
const userConfig = ref(null)
const llmConfigs = ref([])
const newLLM = reactive({ provider: 'openai', api_key: '', base_url: '', model_name: '' })

// ===================================================================
// API helpers
// ===================================================================
async function api(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res.status === 204 ? null : res.json()
}

function flash(text, type = 'success') {
  message.value = { text, type }
  setTimeout(() => message.value = { text: '', type: '' }, 3500)
}

// ===================================================================
// Templates CRUD
// ===================================================================
async function loadTemplates() {
  loading.value = true
  try {
    templates.value = await api('/templates')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

async function createTemplate() {
  if (!templateForm.journal_name || !templateForm.download_path) {
    return flash('Journal name and path are required', 'error')
  }
  loading.value = true
  try {
    await api('/templates', { method: 'POST', body: JSON.stringify(templateForm) })
    flash('Template created!', 'success')
    templateForm.journal_name = ''
    templateForm.download_path = ''
    await loadTemplates()
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

async function deleteTemplate(id) {
  if (!confirm('Delete this template?')) return
  try {
    await api(`/templates/${id}`, { method: 'DELETE' })
    flash('Deleted', 'success')
    await loadTemplates()
  } catch (e) { flash(e.message, 'error') }
}

// ----- Parse -----
async function parseTemplate(tmpl) {
  loading.value = true
  try {
    parsedMapping.value = await api(`/parser/analyze?template_id=${tmpl.id}`, { method: 'POST' })
    // Init user content dict
    for (const m of parsedMapping.value.modules) {
      if (!(m.id in userContent) && m.type !== 'figure' && m.type !== 'table') {
        userContent[m.id] = ''
      }
    }
    flash(`Parsed! Found ${parsedMapping.value.modules.length} modules`, 'success')
    activeTab.value = 'content'
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

// ===================================================================
// Figures
// ===================================================================
function addFigure() {
  figures.push({ caption: '', label: '', image_path: '', is_wide: false })
}

function removeFigure(idx) {
  figures.splice(idx, 1)
}

// ===================================================================
// Assemble
// ===================================================================
async function runAssemble() {
  const templateId = parsedMapping.value?.template_path
  // Extract the UUID from the template metadata
  const tmpl = templates.value.find(t => t.download_path === templateId || t.mapping_json)
  if (!tmpl && parsedMapping.value) {
    // Find template that matches this parsed mapping
    const match = templates.value.find(t => t.mapping_json)
    if (!match) return flash('No parsed template found. Parse a template first.', 'error')
    loading.value = true
    try {
      assembleResult.value = await api('/assembler/assemble', {
        method: 'POST',
        body: JSON.stringify({
          template_id: match.id,
          user_content: userContent,
          figures: figures.filter(f => f.caption || f.image_path),
        }),
      })
      flash('Assembly complete!', 'success')
    } catch (e) { flash(e.message, 'error') }
    finally { loading.value = false }
    return
  }
  if (!tmpl) return flash('No template selected', 'error')
  loading.value = true
  try {
    assembleResult.value = await api('/assembler/assemble', {
      method: 'POST',
      body: JSON.stringify({
        template_id: tmpl.id,
        user_content: userContent,
        figures: figures.filter(f => f.caption || f.image_path),
      }),
    })
    flash('Assembly complete!', 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

// ===================================================================
// Settings
// ===================================================================
const userForm = reactive({ user_identifier: '', default_provider: 'openai' })

async function initUser() {
  const stored = localStorage.getItem('baboon_user_id')
  if (stored) {
    try {
      userConfig.value = await api(`/users/${stored}`)
      llmConfigs.value = userConfig.value.llm_configs || []
    } catch { localStorage.removeItem('baboon_user_id') }
  }
}

async function createUser() {
  if (!userForm.user_identifier) return flash('Enter a user identifier', 'error')
  loading.value = true
  try {
    const u = await api('/users', { method: 'POST', body: JSON.stringify(userForm) })
    userConfig.value = u
    localStorage.setItem('baboon_user_id', u.id)
    llmConfigs.value = []
    flash('User created!', 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

async function addLLMConfig() {
  if (!userConfig.value) return
  loading.value = true
  try {
    const cfg = await api(`/users/${userConfig.value.id}/llm-configs`, {
      method: 'POST',
      body: JSON.stringify(newLLM),
    })
    llmConfigs.value.push(cfg)
    newLLM.api_key = ''
    newLLM.model_name = ''
    flash('Provider added!', 'success')
  } catch (e) { flash(e.message, 'error') }
  finally { loading.value = false }
}

async function deleteLLMConfig(cfgId) {
  if (!userConfig.value || !confirm('Remove this provider?')) return
  try {
    await api(`/users/${userConfig.value.id}/llm-configs/${cfgId}`, { method: 'DELETE' })
    llmConfigs.value = llmConfigs.value.filter(c => c.id !== cfgId)
    flash('Removed', 'success')
  } catch (e) { flash(e.message, 'error') }
}

// ===================================================================
// Init
// ===================================================================
onMounted(async () => {
  await loadTemplates()
  await initUser()
  // Check backend health
  try {
    const h = await api('/health')
    if (h.status === 'ok') flash('Backend connected', 'success')
  } catch { /* offline */ }
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
        <span class="logo-text">Baboon<span class="logo-accent">Paper</span>Forge</span>
      </div>
      <nav class="nav-tabs">
        <button
          v-for="tab in ['templates','content','settings']"
          :key="tab"
          :class="['nav-tab', { active: activeTab === tab }]"
          @click="activeTab = tab"
        >
          {{ { templates: '📄 Templates', content: '✍️ Editor', settings: '⚙️ Settings' }[tab] }}
        </button>
      </nav>
      <div class="header-status">
        <span v-if="loading" class="spinner"></span>
        <span class="badge" :class="message.type">{{ message.text }}</span>
      </div>
    </header>

    <!-- =============================================================== -->
    <!-- Templates Panel -->
    <!-- =============================================================== -->
    <main v-if="activeTab === 'templates'" class="panel">
      <section class="card">
        <h2>Create Template</h2>
        <div class="form-row">
          <input v-model="templateForm.journal_name" placeholder="Journal name (e.g. IEEE IoT)" class="input" />
          <select v-model="templateForm.template_format" class="input select">
            <option value="latex">LaTeX (.tex)</option>
            <option value="docx">Word (.docx)</option>
          </select>
          <input v-model="templateForm.download_path" placeholder="File path (e.g. ./workdir/ieee/main.tex)" class="input" />
          <button @click="createTemplate" class="btn btn-primary" :disabled="loading">+ Create</button>
        </div>
      </section>

      <section class="card">
        <h2>Saved Templates</h2>
        <div v-if="templates.length === 0" class="empty">No templates yet. Create one above.</div>
        <div v-for="tmpl in templates" :key="tmpl.id" class="list-row">
          <div class="list-info">
            <strong>{{ tmpl.journal_name }}</strong>
            <span class="tag">{{ tmpl.template_format }}</span>
            <span class="muted">{{ tmpl.download_path }}</span>
            <span v-if="tmpl.mapping_json" class="tag green">parsed ✓</span>
          </div>
          <div class="list-actions">
            <button @click="parseTemplate(tmpl)" class="btn btn-sm" :disabled="loading">🔍 Parse</button>
            <button @click="deleteTemplate(tmpl.id)" class="btn btn-sm btn-danger">🗑</button>
          </div>
        </div>
      </section>
    </main>

    <!-- =============================================================== -->
    <!-- Content Editor Panel -->
    <!-- =============================================================== -->
    <main v-else-if="activeTab === 'content'" class="panel">
      <div v-if="!parsedMapping" class="empty-state">
        <div class="empty-icon">📝</div>
        <p>Parse a template first to see its module structure.</p>
        <button @click="activeTab = 'templates'" class="btn btn-primary">Go to Templates</button>
      </div>

      <div v-else class="editor-layout">
        <!-- Module tree -->
        <aside class="module-tree card">
          <h3>Modules ({{ parsedMapping.modules.length }})</h3>
          <div v-for="m in parsedMapping.modules" :key="m.id" class="module-item"
               :class="{ active: userContent[m.id]?.length }">
            <span class="module-icon">
              {{ { title:'📌', author:'👤', abstract:'📃', section:'§', bibliography:'📚', figure:'🖼', table:'📊', acknowledgments:'🙏' }[m.type] || '•' }}
            </span>
            <span class="module-label">{{ m.label }}</span>
            <span class="tag sm">{{ m.type }}</span>
          </div>
        </aside>

        <!-- Form area -->
        <section class="content-area">
          <div v-for="m in parsedMapping.modules" :key="m.id" class="card form-card">
            <div class="form-card-header">
              <span class="module-icon">
                {{ { title:'📌', author:'👤', abstract:'📃', section:'§', bibliography:'📚', figure:'🖼', table:'📊', acknowledgments:'🙏' }[m.type] || '•' }}
              </span>
              <strong>{{ m.label }}</strong>
              <span class="tag">{{ m.type }}</span>
              <span v-if="m.level" class="tag sm">L{{ m.level }}</span>
            </div>

            <!-- Text modules -->
            <textarea
              v-if="m.type !== 'figure' && m.type !== 'table'"
              v-model="userContent[m.id]"
              :placeholder="`Enter ${m.label}...`"
              :rows="m.type === 'abstract' ? 5 : m.type === 'title' ? 1 : 4"
              class="textarea"
            />

            <!-- Figures -->
            <div v-if="m.type === 'figure' || m.type === 'table'">
              <div v-for="(fig, idx) in figures" :key="idx" class="figure-card card">
                <div class="form-row">
                  <input v-model="fig.caption" placeholder="Caption" class="input" />
                  <input v-model="fig.label" placeholder="Label (e.g. fig:result)" class="input" />
                  <input v-model="fig.image_path" placeholder="Image path" class="input" />
                  <label class="checkbox-label">
                    <input type="checkbox" v-model="fig.is_wide" /> Wide
                  </label>
                  <button @click="removeFigure(idx)" class="btn btn-sm btn-danger">✕</button>
                </div>
              </div>
              <button @click="addFigure" class="btn btn-sm">+ Add {{ m.type === 'figure' ? 'Figure' : 'Table' }}</button>
            </div>
          </div>

          <!-- Assemble -->
          <div class="assemble-bar card">
            <button @click="runAssemble" class="btn btn-primary btn-lg" :disabled="loading">
              ⚡ Assemble (Zero-Token)
            </button>
            <div v-if="assembleResult" class="assemble-result">
              <span class="tag green">✓ Done</span>
              <span class="muted">Output: {{ assembleResult.output_path }}</span>
              <span class="tag">{{ assembleResult.filled_count }}/{{ assembleResult.module_count }} filled</span>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- =============================================================== -->
    <!-- Settings Panel -->
    <!-- =============================================================== -->
    <main v-else-if="activeTab === 'settings'" class="panel">
      <section class="card" v-if="!userConfig">
        <h2>Create User Profile</h2>
        <p class="muted">Your identifier is never shared. Choose a nickname.</p>
        <div class="form-row">
          <input v-model="userForm.user_identifier" placeholder="Your nickname" class="input" />
          <select v-model="userForm.default_provider" class="input select">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option>
            <option value="ollama">Ollama (local)</option>
          </select>
          <button @click="createUser" class="btn btn-primary" :disabled="loading">Create</button>
        </div>
      </section>

      <section v-else class="card">
        <h2>Profile: {{ userConfig.user_identifier }}</h2>
        <p class="muted">Default provider: {{ userConfig.default_provider }}</p>

        <h3 style="margin-top: 1.5rem">LLM Providers</h3>
        <div v-if="llmConfigs.length === 0" class="empty">No providers configured yet.</div>
        <div v-for="cfg in llmConfigs" :key="cfg.id" class="list-row">
          <div class="list-info">
            <strong>{{ cfg.provider }}</strong>
            <span v-if="cfg.model_name" class="tag">{{ cfg.model_name }}</span>
            <span v-if="cfg.base_url" class="muted">{{ cfg.base_url }}</span>
            <span class="tag" :class="cfg.is_active ? 'green' : ''">{{ cfg.is_active ? 'active' : 'inactive' }}</span>
          </div>
          <div class="list-actions">
            <button @click="deleteLLMConfig(cfg.id)" class="btn btn-sm btn-danger">🗑</button>
          </div>
        </div>

        <h3 style="margin-top: 1.5rem">Add Provider</h3>
        <div class="form-row">
          <select v-model="newLLM.provider" class="input select">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option>
            <option value="ollama">Ollama</option>
          </select>
          <input v-if="newLLM.provider !== 'ollama'" v-model="newLLM.api_key" type="password" placeholder="API Key (encrypted at rest)" class="input" />
          <input v-if="newLLM.provider === 'ollama'" v-model="newLLM.base_url" placeholder="Base URL (e.g. http://localhost:11434)" class="input" />
          <input v-model="newLLM.model_name" placeholder="Model (e.g. gpt-4o, claude-opus-4-8)" class="input" />
          <button @click="addLLMConfig" class="btn btn-primary" :disabled="loading">Add</button>
        </div>
      </section>
    </main>

    <!-- =============================================================== -->
    <!-- Footer -->
    <!-- =============================================================== -->
    <footer class="app-footer">
      <span>BaboonPaperForge v0.1 · paper typesetting agent platform</span>
      <span class="muted">Zero-token · privacy-first · BYOK</span>
    </footer>
  </div>
</template>

<style>
/* ==================================================================
   Design Tokens
   ================================================================== */
:root {
  --bg-primary: #0f0f14;
  --bg-secondary: #1a1a24;
  --bg-card: #222232;
  --bg-hover: #2a2a3a;
  --border: #333348;
  --text-primary: #e8e8f0;
  --text-secondary: #9a9ab8;
  --accent: #7c5cfc;
  --accent-glow: rgba(124, 92, 252, 0.25);
  --success: #34d399;
  --danger: #f87171;
  --warning: #fbbf24;
  --radius: 10px;
  --radius-sm: 6px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}

.app-shell {
  display: flex; flex-direction: column;
  min-height: 100vh;
}

/* ==================================================================
   Header
   ================================================================== */
.app-header {
  display: flex; align-items: center; gap: 2rem;
  padding: 0 2rem; height: 60px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-icon { font-size: 1.5rem; }
.logo-text { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; }
.logo-accent { color: var(--accent); }

.nav-tabs { display: flex; gap: 0.25rem; }
.nav-tab {
  background: none; border: none; color: var(--text-secondary);
  padding: 0.5rem 1rem; border-radius: var(--radius-sm); cursor: pointer;
  font-size: 0.9rem; font-weight: 500; transition: all 0.15s;
}
.nav-tab:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-tab.active { background: var(--accent); color: #fff; }

.header-status { margin-left: auto; display: flex; align-items: center; gap: 0.5rem; }

/* ==================================================================
   Panels
   ================================================================== */
.panel {
  flex: 1; padding: 2rem;
  max-width: 1200px; width: 100%; margin: 0 auto;
}

.card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1rem;
}
.card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: var(--text-primary); }
.card h3 { font-size: 1rem; margin-bottom: 0.75rem; }

/* ==================================================================
   Form elements
   ================================================================== */
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

.checkbox-label {
  display: flex; align-items: center; gap: 0.35rem;
  font-size: 0.85rem; color: var(--text-secondary); cursor: pointer;
}

/* ==================================================================
   Buttons
   ================================================================== */
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

/* ==================================================================
   Tags & Badges
   ================================================================== */
.tag {
  display: inline-block; padding: 0.15rem 0.5rem;
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 4px; font-size: 0.75rem; font-weight: 500;
  color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em;
}
.tag.green { border-color: var(--success); color: var(--success); }
.tag.sm { font-size: 0.65rem; padding: 0.1rem 0.35rem; }

.badge {
  padding: 0.3rem 0.8rem; border-radius: var(--radius-sm);
  font-size: 0.8rem; font-weight: 500;
}
.badge.success { background: rgba(52,211,153,0.12); color: var(--success); }
.badge.error { background: rgba(248,113,113,0.12); color: var(--danger); }

.muted { color: var(--text-secondary); font-size: 0.85rem; }

/* ==================================================================
   Lists
   ================================================================== */
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

/* ==================================================================
   Editor Layout
   ================================================================== */
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

/* ==================================================================
   Footer
   ================================================================== */
.app-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 2rem; border-top: 1px solid var(--border);
  font-size: 0.8rem; color: var(--text-secondary);
}

/* ==================================================================
   Spinner
   ================================================================== */
.spinner {
  width: 16px; height: 16px; border: 2px solid var(--border);
  border-top-color: var(--accent); border-radius: 50%;
  animation: spin 0.6s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ==================================================================
   Scrollbar
   ================================================================== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
