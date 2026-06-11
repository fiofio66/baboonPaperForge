<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

// ===================================================================
// i18n
// ===================================================================
const LOCALE_KEY = 'baboon_locale'
const locale = ref(localStorage.getItem(LOCALE_KEY) || 'zh')
watch(locale, v => localStorage.setItem(LOCALE_KEY, v))

const dict = {
  zh: {
    tabs: { templates: '📄 模板', content: '✍️ 编辑', preview: '👁 预览', settings: '⚙️ 设置', pipeline: '🤖 多Agent' },
    createTpl: '创建模板', journalPlaceholder: '期刊名称', chooseFile: '选择 .tex 文件', noFile: '未选择文件',
    formatLatex: 'LaTeX', formatDocx: 'Word', create: '创建', savedTpls: '模板库', noTpls: '暂无模板',
    parsed: '已解析', parse: '解析', delete: '删除', searchDownload: '🔍 搜索并下载模板',
    searching: '搜索中...', searchDone: '搜索完成！已下载到',
    noParsed: '请先解析一个模板', goTemplates: '去模板页', modules: '个模块',
    enterText: '输入{label}...', addFigure: '+ 图片', addTable: '+ 表格',
    figureCaption: '图注', figureLabel: '标签', figurePath: '图片路径', wide: '跨栏',
    assemble: '排版', previewing: '预览中...', exportPDF: '📄 导出 PDF', exportTEX: '📥 导出 .tex',
    copySource: '📋 复制源码', previewEmpty: '先在编辑区填写内容，预览会实时显示', lineCount: '行',
    createProfile: '创建用户档案', profileHint: '选一个昵称，不会被分享', nickname: '昵称',
    save: '创建', profile: '档案', defaultProvider: '默认提供商',
    llmProviders: 'AI 模型配置 (解析失败时自动调用)', noProviders: '未配置模型',
    active: '活跃', inactive: '未激活', addProvider: '添加模型',
    apiKey: 'API Key (加密存储)', baseUrl: 'Base URL (仅 Ollama)',
    modelPlaceholder: '模型名 (如 gpt-4o)', add: '添加',
    downloadPathLabel: '模板下载路径', downloadPathHint: '通过搜索Agent下载的模板将保存到此目录',
    // Pipeline (multi-agent)
    pipelineTitle: '多 Agent 协作流水线',
    pipelineDesc: 'Search → Parse → RAG → Assemble 全自动执行',
    startPipeline: '🚀 启动全流程',
    polling: '轮询中...',
    agentLog: 'Agent 执行日志',
    llmFallback: '已启用 LLM 兜底解析',
    noLlmFallback: '正则解析',
    constraints: '格式约束 (来自 RAG)',
    noConstraints: '暂未检索到约束规则',
    // Messages
    backendOk: '后端已连接', tplCreated: '模板已创建', tplDeleted: '已删除',
    parsedMsg: '解析完成！{count} 个模块', assembleDone: '排版完成',
    userCreated: '用户已创建', providerAdded: '模型已添加', providerRemoved: '已移除',
    fillRequired: '请填写期刊名称', needMapping: '请先解析模板',
    confirmDelete: '确认删除？', previewCopied: '源码已复制到剪贴板',
    pipelineDone: '流水线执行完成',
    pipelineFailed: '流水线执行失败',
    searchStarted: '搜索已开始，轮询中...',
  },
  en: {
    tabs: { templates: '📄 Templates', content: '✍️ Editor', preview: '👁 Preview', settings: '⚙️ Settings', pipeline: '🤖 Pipeline' },
    createTpl: 'Create Template', journalPlaceholder: 'Journal name', chooseFile: 'Choose .tex file', noFile: 'No file chosen',
    formatLatex: 'LaTeX', formatDocx: 'Word', create: 'Create', savedTpls: 'Saved Templates', noTpls: 'No templates yet',
    parsed: 'parsed', parse: 'Parse', delete: 'Delete', searchDownload: '🔍 Search & Download',
    searching: 'Searching...', searchDone: 'Downloaded to',
    noParsed: 'Parse a template first', goTemplates: 'Go to Templates', modules: 'modules',
    enterText: 'Enter {label}...', addFigure: '+ Figure', addTable: '+ Table',
    figureCaption: 'Caption', figureLabel: 'Label', figurePath: 'Image path', wide: 'Wide',
    assemble: 'Assemble', previewing: 'Previewing...', exportPDF: '📄 Export PDF', exportTEX: '📥 Export .tex',
    copySource: '📋 Copy Source', previewEmpty: 'Fill in content in the Editor tab for live preview', lineCount: 'lines',
    createProfile: 'Create Profile', profileHint: 'Choose a nickname (never shared)', nickname: 'Nickname',
    save: 'Create', profile: 'Profile', defaultProvider: 'Default provider',
    llmProviders: 'AI Models (fallback parser)', noProviders: 'No models configured',
    active: 'active', inactive: 'inactive', addProvider: 'Add Model',
    apiKey: 'API Key (encrypted)', baseUrl: 'Base URL (Ollama only)',
    modelPlaceholder: 'Model (e.g. gpt-4o)', add: 'Add',
    downloadPathLabel: 'Template download path', downloadPathHint: 'Search Agent saves templates here',
    pipelineTitle: 'Multi-Agent Pipeline',
    pipelineDesc: 'Search → Parse → RAG → Assemble fully automated',
    startPipeline: '🚀 Run Pipeline',
    polling: 'Polling...',
    agentLog: 'Agent Log',
    llmFallback: 'LLM fallback enabled',
    noLlmFallback: 'Regex parsed',
    constraints: 'Constraints (from RAG)',
    noConstraints: 'No constraints retrieved',
    backendOk: 'Backend connected', tplCreated: 'Template created', tplDeleted: 'Deleted',
    parsedMsg: 'Parsed! {count} modules', assembleDone: 'Assembly complete',
    userCreated: 'User created', providerAdded: 'Provider added', providerRemoved: 'Removed',
    fillRequired: 'Journal name required', needMapping: 'Parse a template first',
    confirmDelete: 'Confirm delete?', previewCopied: 'Source copied to clipboard',
    pipelineDone: 'Pipeline complete',
    pipelineFailed: 'Pipeline failed',
    searchStarted: 'Search started, polling...',
  },
}
function t(key, params) {
  const val = dict[locale.value]?.[key] ?? dict.en[key] ?? key
  return params ? val.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`) : val
}
const typeIcons = { title:'📌', author:'👤', abstract:'📃', section:'§', bibliography:'📚', figure:'🖼', table:'📊', acknowledgments:'🙏', keywords:'🔑' }

// ===================================================================
// State
// ===================================================================
const API = '/api/v1'
const activeTab = ref('templates')
const loading = ref(false)
const message = ref({ text:'', type:'' })
function flash(text, type='success') { message.value={text,type}; setTimeout(()=>message.value={text:'',type:''},4000) }

const templates = ref([])
const templateForm = reactive({ journal_name:'', template_format:'latex', download_path:'' })
const parsedMapping = ref(null)
const userContent = reactive({})
const figures = reactive([])
const assembleResult = ref(null)
const userConfig = ref(null)
const llmConfigs = ref([])
const newLLM = reactive({ provider:'openai', api_key:'', base_url:'', model_name:'' })
const userForm = reactive({ user_identifier:'', default_provider:'openai' })
const downloadPath = ref(localStorage.getItem('baboon_dl_path') || './workdir')

// Preview
const previewText = ref('')
const previewLines = ref(0)
let previewTimer = null

// Pipeline
const pipelineState = ref(null)
const pipelineTaskId = ref('')
let pipelinePollTimer = null
const pipelineLog = ref([])

// File picker
const selectedFile = ref(null)
const fileInputRef = ref(null)

// ===================================================================
// API
// ===================================================================
async function api(path, opts={}) {
  const res = await fetch(`${API}${path}`, { headers:{'Content-Type':'application/json',...opts.headers}, ...opts })
  if (!res.ok) { const e = await res.json().catch(()=>({detail:res.statusText})); throw new Error(e.detail||res.statusText) }
  return res.status===204 ? null : res.json()
}

// ===================================================================
// File picker
// ===================================================================
function triggerFilePicker() { fileInputRef.value?.click() }
function onFilePicked(e) {
  const f = e.target.files[0]
  if (f) {
    selectedFile.value = f
    templateForm.download_path = f.webkitRelativePath || f.name
  }
}

// ===================================================================
// Templates
// ===================================================================
async function loadTemplates() {
  loading.value=true
  try { templates.value = await api('/templates') } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}
async function createTemplate() {
  if (!templateForm.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true
  try {
    await api('/templates',{method:'POST',body:JSON.stringify(templateForm)})
    flash(t('tplCreated')); templateForm.journal_name=''; templateForm.download_path=''
    selectedFile.value=null
    await loadTemplates()
  } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}
async function deleteTemplate(id) {
  if (!confirm(t('confirmDelete'))) return
  try { await api(`/templates/${id}`,{method:'DELETE'}); flash(t('tplDeleted')); await loadTemplates() }
  catch(e) { flash(e.message,'error') }
}
async function parseTemplate(tmpl) {
  loading.value=true
  try {
    parsedMapping.value = await api(`/parser/analyze?template_id=${tmpl.id}`,{method:'POST'})
    for (const m of parsedMapping.value.modules) {
      if (!(m.id in userContent) && m.type!=='figure' && m.type!=='table') userContent[m.id]=''
    }
    flash(t('parsedMsg',{count:parsedMapping.value.modules.length}))
    activeTab.value='content'
    triggerPreview()
  } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}

// ===================================================================
// Search Agent
// ===================================================================
async function searchAndDownload() {
  if (!templateForm.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true; flash(t('searchStarted'),'success')
  try {
    const res = await api('/search/start',{method:'POST',body:JSON.stringify({
      journal_name:templateForm.journal_name,
      template_format:templateForm.template_format,
    })})
    // Poll for results
    let attempts=0
    const poll=setInterval(async()=>{
      attempts++
      try {
        const task = await api(`/tasks/${res.task_id}`)
        if (task.status==='completed'||task.status==='failed') {
          clearInterval(poll)
          loading.value=false
          if (task.status==='completed') {
            const dlPath = task.output_path || task.mapping_json
            flash(t('searchDone')+' '+dlPath)
            templateForm.download_path = dlPath || ''
            await loadTemplates()
          } else { flash(task.error_message||'Search failed','error') }
        }
      } catch {}
      if (attempts>30) { clearInterval(poll); loading.value=false; flash('Timeout','error') }
    },2000)
  } catch(e) { flash(e.message,'error'); loading.value=false }
}

// ===================================================================
// Editor + Preview
// ===================================================================
function addFigure() { figures.push({ caption:'', label:'', image_path:'', is_wide:false }) }
function removeFigure(i) { figures.splice(i,1) }

function triggerPreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(generatePreview, 400)
}
watch(userContent, triggerPreview, { deep:true })
watch(figures, triggerPreview, { deep:true })

async function generatePreview() {
  if (!parsedMapping.value) { previewText.value=''; return }
  const has = Object.values(userContent).some(v=>v&&v.trim())
  if (!has) { previewText.value=''; return }
  try {
    const resp = await api('/preview',{method:'POST',body:JSON.stringify({
      template_path: templateForm.download_path||parsedMapping.value.template_path,
      template_format: templateForm.template_format||'latex',
      mapping_json: JSON.stringify(parsedMapping.value),
      user_content: userContent,
      figures: figures.filter(f=>f.caption||f.image_path),
    })})
    previewText.value=resp.assembled_text; previewLines.value=resp.line_count
  } catch {}
}

// ===================================================================
// Export
// ===================================================================
function copyPreview() {
  navigator.clipboard.writeText(previewText.value).then(()=>flash(t('previewCopied')))
}
function downloadTex() {
  if (!previewText.value) return
  const blob=new Blob([previewText.value],{type:'application/x-tex'})
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob)
  a.download='paper_assembled.tex'; a.click()
}
async function downloadPdf() {
  if (!parsedMapping.value) return flash(t('needMapping'),'error')
  loading.value=true
  try {
    const resp = await fetch(`${API}/export/pdf`,{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        template_path: templateForm.download_path||parsedMapping.value.template_path,
        template_format:'latex', mapping_json:JSON.stringify(parsedMapping.value),
        user_content:userContent, figures:figures.filter(f=>f.caption||f.image_path),
      }),
    })
    const blob=await resp.blob()
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob)
    a.download=resp.headers.get('Content-Disposition')?.match(/filename="?(.+?)"?/)?.[1]||'paper.pdf'
    a.click()
  } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}

// ===================================================================
// Multi-Agent Pipeline
// ===================================================================
async function runPipeline() {
  if (!templateForm.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true; pipelineLog.value=[]
  pipelineLog.value.push('[Supervisor] Dispatching agents...')
  try {
    const res = await api('/pipeline/run',{method:'POST',body:JSON.stringify({
      journal_name:templateForm.journal_name,
      template_format:templateForm.template_format,
      template_path:templateForm.download_path||'',
      user_content:userContent,
      figures:figures.filter(f=>f.caption||f.image_path),
      user_config_id:userConfig.value?.id||null,
    })})
    pipelineTaskId.value=res.task_id
    pipelinePollTimer=setInterval(async()=>{
      try {
        const status=await api(`/pipeline/status?task_id=${pipelineTaskId.value}`)
        pipelineState.value=status
        if (status.agent_log) pipelineLog.value=status.agent_log
        if (status.mapping_json && !parsedMapping.value) {
          parsedMapping.value=JSON.parse(status.mapping_json)
          for (const m of parsedMapping.value.modules) {
            if (!(m.id in userContent) && m.type!=='figure'&&m.type!=='table') userContent[m.id]=''
          }
        }
        if (status.assembled_text) { previewText.value=status.assembled_text }
        if (status.status==='done'||status.status==='failed') {
          clearInterval(pipelinePollTimer)
          loading.value=false
          if (status.status==='done') flash(t('pipelineDone'))
          else flash(status.error||t('pipelineFailed'),'error')
          activeTab.value='preview'
        }
      } catch {}
    },1500)
  } catch(e) { flash(e.message,'error'); loading.value=false }
}
onUnmounted(()=>{ clearInterval(pipelinePollTimer) })

// ===================================================================
// Settings
// ===================================================================
watch(downloadPath, v=>localStorage.setItem('baboon_dl_path',v))
async function initUser() {
  const s=localStorage.getItem('baboon_user_id')
  if (s) { try { userConfig.value=await api(`/users/${s}`); llmConfigs.value=userConfig.value.llm_configs||[] } catch { localStorage.removeItem('baboon_user_id') } }
}
async function createUser() {
  if (!userForm.user_identifier) return flash(t('nickname'),'error')
  loading.value=true
  try {
    const u=await api('/users',{method:'POST',body:JSON.stringify(userForm)})
    userConfig.value=u; localStorage.setItem('baboon_user_id',u.id); llmConfigs.value=[]
    flash(t('userCreated'))
  } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}
async function addLLMConfig() {
  if (!userConfig.value) return
  loading.value=true
  try {
    const c=await api(`/users/${userConfig.value.id}/llm-configs`,{method:'POST',body:JSON.stringify(newLLM)})
    llmConfigs.value.push(c); newLLM.api_key=''; newLLM.model_name=''
    flash(t('providerAdded'))
  } catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}
async function deleteLLMConfig(id) {
  if (!userConfig.value||!confirm(t('confirmDelete'))) return
  try { await api(`/users/${userConfig.value.id}/llm-configs/${id}`,{method:'DELETE'}); llmConfigs.value=llmConfigs.value.filter(c=>c.id!==id); flash(t('providerRemoved')) }
  catch(e) { flash(e.message,'error') }
}

// ===================================================================
// Init
// ===================================================================
onMounted(async()=>{
  await loadTemplates(); await initUser()
  try { const h=await api('/health'); if (h.status==='ok') flash(t('backendOk')) } catch {}
})
</script>

<template>
<div class="app-shell">
  <!-- ====== Header ====== -->
  <header class="app-header">
    <div class="logo">
      <span class="logo-icon">🦧</span>
      <span class="logo-text"><span class="logo-accent">Baboon</span>PaperForge</span>
    </div>
    <nav class="nav-tabs">
      <button v-for="tab in ['templates','content','preview','pipeline','settings']" :key="tab"
        :class="['nav-tab',{active:activeTab===tab}]" @click="activeTab=tab">{{ t(`tabs.${tab}`) }}</button>
    </nav>
    <div class="header-actions">
      <div class="locale-switch">
        <button :class="['locale-btn',{active:locale==='zh'}]" @click="locale='zh'">中</button>
        <button :class="['locale-btn',{active:locale==='en'}]" @click="locale='en'">EN</button>
      </div>
      <span v-if="loading" class="spinner"></span>
      <span class="badge" :class="message.type" v-if="message.text">{{ message.text }}</span>
    </div>
  </header>

  <!-- ====== Templates ====== -->
  <main v-if="activeTab==='templates'" class="panel">
    <section class="card">
      <h2>{{ t('createTpl') }}</h2>
      <div class="form-row">
        <input v-model="templateForm.journal_name" :placeholder="t('journalPlaceholder')" class="input" style="flex:2" />
        <select v-model="templateForm.template_format" class="input select" style="flex:0.5">
          <option value="latex">{{ t('formatLatex') }}</option>
          <option value="docx">{{ t('formatDocx') }}</option>
        </select>
        <input type="file" ref="fileInputRef" @change="onFilePicked" accept=".tex,.cls,.sty,.docx,.zip,.tar.gz" style="display:none" />
        <button @click="triggerFilePicker" class="btn" :disabled="loading" style="flex:0.8">
          📁 {{ selectedFile ? selectedFile.name : t('chooseFile') }}
        </button>
        <button @click="createTemplate" class="btn btn-primary" :disabled="loading">{{ t('create') }}</button>
      </div>
      <div class="form-row" style="margin-top:0.5rem">
        <button @click="searchAndDownload" class="btn btn-primary" :disabled="loading" style="width:100%">
          {{ loading ? t('searching') : t('searchDownload') }}
        </button>
      </div>
    </section>

    <section class="card">
      <h2>{{ t('savedTpls') }}</h2>
      <div v-if="templates.length===0" class="empty">{{ t('noTpls') }}</div>
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

  <!-- ====== Editor ====== -->
  <main v-else-if="activeTab==='content'" class="panel">
    <div v-if="!parsedMapping" class="empty-state">
      <div class="empty-icon">📝</div>
      <p>{{ t('noParsed') }}</p>
      <button @click="activeTab='templates'" class="btn btn-primary">{{ t('goTemplates') }}</button>
    </div>
    <div v-else class="editor-layout">
      <aside class="module-tree card">
        <h3>{{ parsedMapping.modules.length }} {{ t('modules') }}</h3>
        <div v-for="m in parsedMapping.modules" :key="m.id" class="module-item" :class="{active:userContent[m.id]?.length}">
          <span class="module-icon">{{ typeIcons[m.type]||'•' }}</span>
          <span class="module-label">{{ m.label }}</span>
          <span class="tag sm">{{ m.type }}</span>
        </div>
      </aside>
      <section class="content-area">
        <div v-for="m in parsedMapping.modules" :key="m.id" class="card form-card">
          <div class="form-card-header">
            <span class="module-icon">{{ typeIcons[m.type]||'•' }}</span>
            <strong>{{ m.label }}</strong>
            <span class="tag">{{ m.type }}</span>
            <span v-if="m.level" class="tag sm">L{{ m.level }}</span>
          </div>
          <textarea v-if="m.type!=='figure'&&m.type!=='table'" v-model="userContent[m.id]"
            :placeholder="t('enterText',{label:m.label})"
            :rows="m.type==='abstract'?5:m.type==='title'?1:4" class="textarea" />
          <div v-if="m.type==='figure'||m.type==='table'">
            <div v-for="(fig,i) in figures" :key="i" class="figure-card card">
              <div class="form-row">
                <input v-model="fig.caption" :placeholder="t('figureCaption')" class="input" />
                <input v-model="fig.label" :placeholder="t('figureLabel')" class="input" />
                <input v-model="fig.image_path" :placeholder="t('figurePath')" class="input" />
                <label class="checkbox-label"><input type="checkbox" v-model="fig.is_wide"/> {{ t('wide') }}</label>
                <button @click="removeFigure(i)" class="btn btn-sm btn-danger">✕</button>
              </div>
            </div>
            <button @click="addFigure" class="btn btn-sm">{{ m.type==='figure'?t('addFigure'):t('addTable') }}</button>
          </div>
        </div>
      </section>
    </div>
  </main>

  <!-- ====== Preview ====== -->
  <main v-else-if="activeTab==='preview'" class="panel">
    <div v-if="!previewText" class="empty-state">
      <div class="empty-icon">👁</div>
      <p>{{ t('previewEmpty') }}</p>
    </div>
    <div v-else>
      <div class="preview-toolbar card">
        <span class="tag">{{ previewLines }} {{ t('lineCount') }}</span>
        <button @click="copyPreview" class="btn btn-sm">{{ t('copySource') }}</button>
        <button @click="downloadTex" class="btn btn-sm">{{ t('exportTEX') }}</button>
        <button @click="downloadPdf" class="btn btn-sm btn-primary" :disabled="loading">{{ t('exportPDF') }}</button>
      </div>
      <pre class="preview-box card"><code>{{ previewText }}</code></pre>
    </div>
  </main>

  <!-- ====== Pipeline ====== -->
  <main v-else-if="activeTab==='pipeline'" class="panel">
    <section class="card">
      <h2>{{ t('pipelineTitle') }}</h2>
      <p class="muted" style="margin-bottom:1rem">{{ t('pipelineDesc') }}</p>
      <div class="pipeline-flow">
        <div class="pipe-node">🔍<br/>Search</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-node">📝<br/>Parse</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-node">🧠<br/>RAG</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-node">⚡<br/>Assemble</div>
      </div>
      <button @click="runPipeline" class="btn btn-primary btn-lg" :disabled="loading" style="width:100%;margin-top:1rem;justify-content:center">
        {{ loading ? t('polling') : t('startPipeline') }}
      </button>
    </section>

    <section class="card" v-if="pipelineLog.length">
      <h3>{{ t('agentLog') }}</h3>
      <div class="log-box">
        <div v-for="(log,i) in pipelineLog" :key="i" class="log-line">{{ log }}</div>
      </div>
    </section>

    <section class="card" v-if="pipelineState?.rag_constraints?.length">
      <h3>{{ t('constraints') }}</h3>
      <div v-for="(c,i) in pipelineState.rag_constraints" :key="i" class="constraint-item">
        <span class="tag">{{ c.module_label }}</span>
        <span class="muted">{{ c.text?.slice(0,200) }}</span>
      </div>
    </section>

    <section class="card" v-if="pipelineState?.parse_used_llm !== undefined">
      <span class="tag" :class="pipelineState.parse_used_llm?'green':''">
        {{ pipelineState.parse_used_llm ? t('llmFallback') : t('noLlmFallback') }}
      </span>
    </section>
  </main>

  <!-- ====== Settings ====== -->
  <main v-else-if="activeTab==='settings'" class="panel">
    <section class="card" v-if="!userConfig">
      <h2>{{ t('createProfile') }}</h2>
      <p class="muted">{{ t('profileHint') }}</p>
      <div class="form-row">
        <input v-model="userForm.user_identifier" :placeholder="t('nickname')" class="input" />
        <select v-model="userForm.default_provider" class="input select">
          <option value="openai">OpenAI</option><option value="anthropic">Anthropic</option>
          <option value="gemini">Gemini</option><option value="ollama">Ollama</option>
        </select>
        <button @click="createUser" class="btn btn-primary" :disabled="loading">{{ t('save') }}</button>
      </div>
    </section>
    <section v-else>
      <div class="card">
        <h2>{{ t('profile') }}: {{ userConfig.user_identifier }}</h2>
        <p class="muted">{{ t('defaultProvider') }}: {{ userConfig.default_provider }}</p>
      </div>
      <div class="card">
        <h3>{{ t('downloadPathLabel') }}</h3>
        <p class="muted" style="margin-bottom:0.5rem">{{ t('downloadPathHint') }}</p>
        <input v-model="downloadPath" class="input" style="width:100%" />
      </div>
      <div class="card">
        <h3>{{ t('llmProviders') }}</h3>
        <div v-if="llmConfigs.length===0" class="empty">{{ t('noProviders') }}</div>
        <div v-for="cfg in llmConfigs" :key="cfg.id" class="list-row">
          <div class="list-info">
            <strong>{{ cfg.provider }}</strong>
            <span v-if="cfg.model_name" class="tag">{{ cfg.model_name }}</span>
            <span class="tag" :class="cfg.is_active?'green':''">{{ cfg.is_active?t('active'):t('inactive') }}</span>
          </div>
          <div class="list-actions">
            <button @click="deleteLLMConfig(cfg.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button>
          </div>
        </div>
        <h3 style="margin-top:1.5rem">{{ t('addProvider') }}</h3>
        <div class="form-row">
          <select v-model="newLLM.provider" class="input select">
            <option value="openai">OpenAI</option><option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option><option value="ollama">Ollama</option>
          </select>
          <input v-if="newLLM.provider!=='ollama'" v-model="newLLM.api_key" type="password" :placeholder="t('apiKey')" class="input" />
          <input v-if="newLLM.provider==='ollama'" v-model="newLLM.base_url" :placeholder="t('baseUrl')" class="input" />
          <input v-model="newLLM.model_name" :placeholder="t('modelPlaceholder')" class="input" />
          <button @click="addLLMConfig" class="btn btn-primary" :disabled="loading">{{ t('add') }}</button>
        </div>
      </div>
    </section>
  </main>
</div>
</template>

<style>
:root {
  --bg-primary:#fafaf7; --bg-secondary:#fff; --bg-card:#fff; --bg-hover:#f0ece4;
  --border:#d9d4c9; --border-light:#e8e4db; --text-primary:#2c2416; --text-secondary:#6b5e4a;
  --text-muted:#9b8e7a; --accent:#1a5276; --accent-light:#2980b9; --accent-bg:#eaf0f6;
  --success:#1e7e34; --success-bg:#e8f5e9; --danger:#c0392b; --danger-bg:#fdecea;
  --radius:6px; --radius-sm:4px;
  --shadow-sm:0 1px 3px rgba(44,36,22,0.06);
  --shadow-md:0 2px 8px rgba(44,36,22,0.08);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Crimson Text','Source Serif 4','Georgia',serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.7;min-height:100vh;-webkit-font-smoothing:antialiased}
.app-shell{display:flex;flex-direction:column;min-height:100vh}

/* Header */
.app-header{display:flex;align-items:center;gap:2rem;padding:0 2.5rem;height:64px;background:var(--bg-secondary);border-bottom:2px solid var(--border);position:sticky;top:0;z-index:100;box-shadow:var(--shadow-sm)}
.logo{display:flex;align-items:baseline;gap:0.5rem}
.logo-icon{font-size:1.5rem}
.logo-text{font-size:1.2rem;font-weight:700;letter-spacing:-0.01em;font-family:'Crimson Text','Georgia',serif}
.logo-accent{color:var(--accent)}

.nav-tabs{display:flex;gap:0.25rem}
.nav-tab{background:none;border:none;color:var(--text-secondary);padding:0.5rem 0.9rem;border-radius:var(--radius-sm);cursor:pointer;font-size:0.85rem;font-weight:500;transition:all 0.2s;font-family:system-ui,sans-serif;white-space:nowrap}
.nav-tab:hover{background:var(--bg-hover);color:var(--text-primary)}
.nav-tab.active{background:var(--accent);color:#fff}

.header-actions{margin-left:auto;display:flex;align-items:center;gap:1rem}
.locale-switch{display:flex;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border)}
.locale-btn{background:#fff;border:none;color:var(--text-secondary);padding:0.25rem 0.55rem;font-size:0.72rem;cursor:pointer;font-weight:600;transition:all 0.15s;font-family:system-ui,sans-serif}
.locale-btn:hover{color:var(--text-primary);background:var(--bg-hover)}
.locale-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}

/* Panel */
.panel{flex:1;padding:2.5rem 2rem;max-width:1200px;width:100%;margin:0 auto}
.card{background:var(--bg-card);border:1px solid var(--border-light);border-radius:var(--radius);padding:1.75rem 2rem;margin-bottom:1.25rem;box-shadow:var(--shadow-sm)}
.card h2{font-size:1.15rem;margin-bottom:1rem;color:var(--text-primary);font-weight:600;letter-spacing:-0.01em;border-bottom:1px solid var(--border-light);padding-bottom:0.6rem}
.card h3{font-size:1rem;margin-bottom:0.75rem;font-weight:600;color:var(--text-primary)}

/* Forms */
.form-row{display:flex;gap:0.65rem;align-items:center;flex-wrap:wrap}
.input{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:0.6rem 0.85rem;border-radius:var(--radius-sm);font-size:0.9rem;flex:1;min-width:120px;outline:none;transition:all 0.2s;font-family:system-ui,sans-serif}
.input:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,0.08)}
.select{cursor:pointer}
.textarea{width:100%;background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:1rem;border-radius:var(--radius-sm);font-size:0.92rem;line-height:1.7;font-family:'Crimson Text','Georgia',serif;resize:vertical;outline:none;transition:all 0.2s}
.textarea:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,0.08)}
.checkbox-label{display:flex;align-items:center;gap:0.35rem;font-size:0.85rem;color:var(--text-secondary);cursor:pointer;font-family:system-ui,sans-serif}

/* Buttons */
.btn{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:0.55rem 1.1rem;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;cursor:pointer;transition:all 0.2s;white-space:nowrap;font-family:system-ui,sans-serif;display:inline-flex;align-items:center;gap:0.35rem}
.btn:hover{background:var(--bg-hover);border-color:var(--text-muted)}
.btn:disabled{opacity:0.4;cursor:not-allowed}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-light);border-color:var(--accent-light)}
.btn-danger{color:var(--danger)}
.btn-danger:hover{background:var(--danger-bg);border-color:var(--danger)}
.btn-sm{padding:0.3rem 0.65rem;font-size:0.8rem}
.btn-lg{padding:0.85rem 2.2rem;font-size:1rem}

/* Tags */
.tag{display:inline-block;padding:0.15rem 0.55rem;background:var(--bg-primary);border:1px solid var(--border-light);border-radius:3px;font-size:0.7rem;font-weight:500;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;font-family:system-ui,sans-serif}
.tag.green{border-color:var(--success);color:var(--success);background:var(--success-bg)}
.tag.sm{font-size:0.63rem;padding:0.08rem 0.35rem}
.badge{padding:0.3rem 0.85rem;border-radius:var(--radius-sm);font-size:0.8rem;font-weight:500;font-family:system-ui,sans-serif}
.badge.success{background:var(--success-bg);color:var(--success)}
.badge.error{background:var(--danger-bg);color:var(--danger)}
.muted{color:var(--text-muted);font-size:0.85rem;font-family:system-ui,sans-serif}

/* Lists */
.list-row{display:flex;align-items:center;justify-content:space-between;padding:0.85rem 0;border-bottom:1px solid var(--border-light);gap:1rem;transition:background 0.1s}
.list-row:hover{background:var(--accent-bg);margin:0 -0.5rem;padding-left:0.5rem;padding-right:0.5rem;border-radius:var(--radius-sm)}
.list-row:last-child{border-bottom:none}
.list-info{display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap}
.list-actions{display:flex;gap:0.35rem}
.empty{color:var(--text-muted);font-style:italic;padding:1rem 0}
.empty-state{text-align:center;padding:5rem 2rem}
.empty-icon{font-size:3.5rem;margin-bottom:1rem;opacity:0.6}

/* Editor */
.editor-layout{display:flex;gap:1.75rem;align-items:flex-start}
.module-tree{width:260px;flex-shrink:0;position:sticky;top:84px;padding:1.25rem 1rem;max-height:calc(100vh - 120px);overflow-y:auto}
.module-item{display:flex;align-items:center;gap:0.5rem;padding:0.45rem 0.55rem;border-radius:var(--radius-sm);font-size:0.85rem;cursor:default;transition:all 0.15s;border-left:2px solid transparent;font-family:system-ui,sans-serif}
.module-item:hover{background:var(--bg-hover)}
.module-item.active{background:var(--accent-bg);border-left-color:var(--accent)}
.module-icon{font-size:0.9rem;flex-shrink:0}
.module-label{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.content-area{flex:1;display:flex;flex-direction:column;gap:1rem}
.form-card-header{display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem}
.figure-card{border:1px dashed var(--border);padding:0.85rem;background:#fdfdfb;border-radius:var(--radius-sm)}

/* Preview */
.preview-toolbar{display:flex;align-items:center;gap:1rem}
.preview-box{font-family:'Courier New','Consolas',monospace;font-size:0.82rem;line-height:1.5;overflow-x:auto;max-height:70vh;overflow-y:auto;white-space:pre-wrap;word-break:break-all;padding:1.5rem}
.preview-box code{background:none;color:var(--text-primary)}

/* Pipeline */
.pipeline-flow{display:flex;align-items:center;justify-content:center;gap:0.75rem;padding:1rem}
.pipe-node{text-align:center;font-size:0.8rem;padding:0.75rem 1rem;background:var(--accent-bg);border:1px solid var(--accent);border-radius:var(--radius);min-width:70px;font-family:system-ui,sans-serif}
.pipe-arrow{font-size:1.2rem;color:var(--accent)}
.log-box{background:var(--bg-primary);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.75rem;max-height:250px;overflow-y:auto}
.log-line{font-size:0.8rem;color:var(--text-secondary);padding:0.2rem 0;font-family:'Courier New',monospace;border-bottom:1px solid var(--border-light)}
.constraint-item{display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;border-bottom:1px solid var(--border-light)}

/* Spinner */
.spinner{width:18px;height:18px;border:2px solid var(--border-light);border-top-color:var(--accent);border-radius:50%;animation:spin 0.6s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}

::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:var(--bg-primary)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
