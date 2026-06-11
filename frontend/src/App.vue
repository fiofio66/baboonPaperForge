<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'

// ===================================================================
// i18n
// ===================================================================
const LOCALE_KEY = 'baboon_locale'
const locale = ref(localStorage.getItem(LOCALE_KEY) || 'zh')
watch(locale, v => localStorage.setItem(LOCALE_KEY, v))

const dict = {
  zh: {
    tab_template: '模板',
    tab_editor: '编辑器',
    tab_settings: '设置',
    createTpl: '新建模板',
    journalPlaceholder: '输入期刊名称，如 IEEE Internet of Things Journal',
    chooseFile: '选择文件',
    noFile: '未选择',
    formatLatex: 'LaTeX',
    formatDocx: 'Word',
    create: '创建',
    savedTpls: '模板库',
    noTpls: '还没有模板，请在下方搜索或手动选择 .tex 文件创建',
    searchHint: '不知道模板在哪？输入期刊名，我们帮你从网上搜索并下载',
    searchBtn: '🔍 搜索并下载官方模板',
    searching: '搜索下载中，请稍候...',
    searchDone: '已下载到',
    parsed: '已解析',
    parse: '解析结构',
    delete: '删除',
    saveLocally: '本地模板',
    noParsed: '请先在左侧选择或搜索一个模板，点击「解析结构」开始',
    modules: '模块',
    enterText: '输入{label}...',
    addFigure: '+ 图片',
    addTable: '+ 表格',
    figureCaption: '图注',
    figureLabel: '标签',
    figurePath: '图片路径',
    wide: '跨栏',
    previewLabel: '实时预览',
    previewEmpty: '在左侧填写论文内容，这里会实时显示排版结果',
    lineCount: '行',
    exportPDF: '📄 导出 PDF',
    exportTEX: '📥 导出 .tex',
    copySource: '📋 复制源码',
    createProfile: '创建用户档案',
    profileHint: '选一个昵称，不会被分享。配置 AI 模型后，解析失败时会自动调用大模型兜底。',
    nickname: '昵称',
    save: '创建',
    profile: '档案',
    defaultProvider: '默认提供商',
    llmProviders: '大模型配置（用于解析兜底，日常排版不消耗 Token）',
    noProviders: '暂未配置模型',
    active: '活跃',
    inactive: '未激活',
    addProvider: '添加模型',
    apiKey: 'API Key (加密存储)',
    baseUrl: 'Base URL (仅 Ollama)',
    modelPlaceholder: '模型名，如 gpt-4o / claude-opus-4-8',
    add: '添加',
    downloadPathLabel: '模板下载路径',
    downloadPathHint: '搜索下载的模板将保存到此目录',
    backendOk: '后端已连接',
    tplCreated: '模板已创建',
    tplDeleted: '已删除',
    parsedMsg: '解析完成！发现 {count} 个模块',
    assembleDone: '排版完成',
    userCreated: '用户已创建',
    providerAdded: '模型已添加',
    providerRemoved: '已移除',
    fillRequired: '请填写期刊名称',
    needMapping: '请先解析模板',
    confirmDelete: '确认删除？',
    previewCopied: '源码已复制到剪贴板',
    searchFailed: '搜索失败，请检查网络或手动选择文件',
    searchStarted: '正在搜索并下载模板...',
    searchTimeout: '大文件可能需要 30-60 秒，请耐心等待',
    agentStatus: 'Agent 状态',
    zipExtracting: '正在解压压缩包...',
    zipReady: '解压完成：',
    zipError: '解压失败，请检查文件格式',
    zipHint: 'LaTeX 模板通常是 .zip 压缩包 — 我们会自动解压',
    dirChoose: '选择文件夹',
    choosingDir: '选择下载目录',
    dirNotSupported: '不支持文件夹选择，请手动输入路径',
  },
  en: {
    tab_template: 'Templates',
    tab_editor: 'Editor',
    tab_settings: 'Settings',
    createTpl: 'New Template',
    journalPlaceholder: 'Journal name, e.g. IEEE Internet of Things Journal',
    chooseFile: 'Choose File',
    noFile: 'None',
    formatLatex: 'LaTeX',
    formatDocx: 'Word',
    create: 'Create',
    savedTpls: 'Saved Templates',
    noTpls: 'No templates yet. Search below or pick a local .tex file.',
    searchHint: 'Don\'t have the template? Type the journal name and we\'ll find it online.',
    searchBtn: '🔍 Search & Download Official Template',
    searching: 'Searching and downloading...',
    searchDone: 'Downloaded to',
    parsed: 'parsed',
    parse: 'Parse Structure',
    delete: 'Delete',
    saveLocally: 'Local Template',
    noParsed: 'Select or search a template on the left, then click "Parse Structure"',
    modules: 'modules',
    enterText: 'Enter {label}...',
    addFigure: '+ Figure',
    addTable: '+ Table',
    figureCaption: 'Caption',
    figureLabel: 'Label',
    figurePath: 'Image path',
    wide: 'Wide',
    previewLabel: 'Live Preview',
    previewEmpty: 'Fill in your paper content on the left. Live preview will appear here.',
    lineCount: 'lines',
    exportPDF: '📄 Export PDF',
    exportTEX: '📥 Export .tex',
    copySource: '📋 Copy Source',
    createProfile: 'Create Profile',
    profileHint: 'Pick a nickname. Configure an AI model for auto-fallback parsing (no tokens used otherwise).',
    nickname: 'Nickname',
    save: 'Create',
    profile: 'Profile',
    defaultProvider: 'Default provider',
    llmProviders: 'AI Models (fallback parser — not used for typesetting)',
    noProviders: 'No models configured',
    active: 'active',
    inactive: 'inactive',
    addProvider: 'Add Model',
    apiKey: 'API Key (encrypted at rest)',
    baseUrl: 'Base URL (Ollama only)',
    modelPlaceholder: 'Model, e.g. gpt-4o / claude-opus-4-8',
    add: 'Add',
    downloadPathLabel: 'Download path',
    downloadPathHint: 'Search Agent saves templates here',
    backendOk: 'Backend connected',
    tplCreated: 'Template created',
    tplDeleted: 'Deleted',
    parsedMsg: 'Parsed! {count} modules found',
    assembleDone: 'Assembly complete',
    userCreated: 'User created',
    providerAdded: 'Model added',
    providerRemoved: 'Removed',
    fillRequired: 'Journal name required',
    needMapping: 'Parse a template first',
    confirmDelete: 'Confirm delete?',
    previewCopied: 'Source copied',
    searchFailed: 'Search failed. Check your connection or pick a file manually.',
    searchStarted: 'Searching & downloading...',
    searchTimeout: 'Large files may take 30-60s. Please wait.',
    agentStatus: 'Agent Status',
    zipExtracting: 'Extracting archive...',
    zipReady: 'ZIP extracted:',
    zipError: 'Failed to extract archive',
    zipHint: 'LaTeX templates are usually .zip files — we auto-extract.',
    dirChoose: 'Choose Folder',
    choosingDir: 'Choose download folder',
    dirNotSupported: 'Folder picker not supported, type path manually',
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
const selectedFile = ref(null)
const fileInputRef = ref(null)
const dirInputRef = ref(null)

// Live preview
const previewText = ref('')
const previewLines = ref(0)
let previewTimer = null

// Agent status bar
const agentStatus = ref({ text:'', type:'' })

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
async function onFilePicked(e) {
  const f = e.target.files[0]
  if (!f) return
  selectedFile.value = f
  const isZip = f.name.match(/\.(zip|tar\.gz|tgz|tar\.bz2|tar\.xz)$/i)
  if (isZip) {
    agentStatus.value={text:t('zipExtracting'),type:'info'}
    flash(t('zipHint'))
    try {
      const resp = await api('/files/extract-zip',{method:'POST',body:JSON.stringify({zip_path:f.name})})
      agentStatus.value={text:`${t('zipReady')} ${resp.tex_files.length} .tex`,type:'success'}
      templateForm.download_path = resp.main_tex || resp.extract_dir
      if (resp.main_tex) flash(`✓ ${t('zipReady')} ${resp.main_tex}`)
      setTimeout(()=>agentStatus.value={text:'',type:''},3000)
    } catch(e) {
      agentStatus.value={text:t('zipError'),type:'error'}
      templateForm.download_path = f.name
    }
  } else {
    templateForm.download_path = f.name
  }
}

// ===================================================================
// Templates
// ===================================================================
async function loadTemplates() {
  try { templates.value = await api('/templates') } catch(e) { /* offline */ }
}
async function createTemplate() {
  if (!templateForm.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true
  try {
    await api('/templates',{method:'POST',body:JSON.stringify(templateForm)})
    flash(t('tplCreated')); templateForm.journal_name=''; templateForm.download_path=''
    selectedFile.value=null; await loadTemplates()
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
  agentStatus.value={text:t('parse'),type:'info'}
  try {
    parsedMapping.value = await api(`/parser/analyze?template_id=${tmpl.id}`,{method:'POST'})
    for (const m of parsedMapping.value.modules) {
      if (!(m.id in userContent) && m.type!=='figure' && m.type!=='table') userContent[m.id]=''
    }
    flash(t('parsedMsg',{count:parsedMapping.value.modules.length}))
    activeTab.value='editor'
    agentStatus.value={text:'',type:''}
    triggerPreview()
  } catch(e) {
    flash(e.message,'error')
    agentStatus.value={text:'Parse failed, trying LLM fallback...',type:'warning'}
    // Auto pipeline fallback — try full pipeline with LLM
    try {
      const res = await api('/pipeline/run',{method:'POST',body:JSON.stringify({
        journal_name:tmpl.journal_name,
        template_format:tmpl.template_format,
        template_path:tmpl.download_path,
        user_content:userContent,
        user_config_id:userConfig.value?.id||null,
      })})
      pollPipelineResult(res.task_id)
    } catch {
      agentStatus.value={text:'',type:''}
    }
  }
  finally { loading.value=false }
}

// ===================================================================
// Search Agent → auto pipeline
// ===================================================================
async function searchAndDownload() {
  if (!templateForm.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true
  agentStatus.value={text:t('searching'),type:'info'}
  flash(t('searchStarted'))
  setTimeout(() => flash(t('searchTimeout')), 5000)  // delayed hint for slow connections
  try {
    const res = await api('/search/start',{method:'POST',body:JSON.stringify({
      journal_name:templateForm.journal_name,
      template_format:templateForm.template_format,
    })})
    pollSearchResult(res.task_id)
  } catch(e) { flash(e.message,'error'); loading.value=false; agentStatus.value={text:'',type:''} }
}

function pollSearchResult(taskId) {
  let attempts=0
  const poll=setInterval(async()=>{
    attempts++
    try {
      const task = await api(`/tasks/${taskId}`)
      if (task.status==='completed'||task.status==='failed') {
        clearInterval(poll); loading.value=false
        if (task.status==='completed') {
          flash(t('searchDone')+' '+(task.output_path||''))
          templateForm.download_path = task.output_path || ''
          await loadTemplates()
          // If we got a template, auto-parse it after creation
          const created = await api('/templates',{method:'POST',body:JSON.stringify({
            journal_name:templateForm.journal_name,
            template_format:templateForm.template_format,
            download_path:task.output_path||templateForm.download_path
          })})
          agentStatus.value={text:'Parsing...',type:'info'}
          await parseTemplate(created)
        } else {
          flash(task.error_message||t('searchFailed'),'error')
        }
        agentStatus.value={text:'',type:''}
      }
    } catch {}
    if (attempts>60) { clearInterval(poll); loading.value=false; agentStatus.value={text:'',type:''}; flash('Timeout — network may be slow','error') }
  },2000)
}

// ===================================================================
// Pipeline (background, no tab)
// ===================================================================
function pollPipelineResult(taskId) {
  let attempts=0
  const poll=setInterval(async()=>{
    attempts++
    try {
      const status=await api(`/pipeline/status?task_id=${taskId}`)
      if (status.agent_log?.length) {
        const last=status.agent_log[status.agent_log.length-1]
        agentStatus.value={text:last,type:'info'}
      }
      if (status.mapping_json && !parsedMapping.value) {
        parsedMapping.value=JSON.parse(status.mapping_json)
        for (const m of parsedMapping.value.modules) {
          if (!(m.id in userContent) && m.type!=='figure'&&m.type!=='table') userContent[m.id]=''
        }
        activeTab.value='editor'
        triggerPreview()
      }
      if (status.status==='done'||status.status==='failed') {
        clearInterval(poll)
        if (status.status==='done') {
          flash(t('parsedMsg',{count:parsedMapping.value?.modules?.length||0}))
          if (status.parse_used_llm) agentStatus.value={text:'✓ LLM fallback succeeded',type:'success'}
          else agentStatus.value={text:'✓ Parse complete',type:'success'}
          setTimeout(()=>agentStatus.value={text:'',type:''},3000)
        } else {
          agentStatus.value={text:'✗ '+((status.error||'').slice(0,80)),type:'error'}
        }
        loading.value=false
      }
    } catch {}
    if (attempts>60) { clearInterval(poll); loading.value=false; agentStatus.value={text:'',type:''} }
  },1500)
}

// ===================================================================
// Editor + Live Preview
// ===================================================================
function addFigure() { figures.push({ caption:'', label:'', image_path:'', is_wide:false }) }
function removeFigure(i) { figures.splice(i,1) }

function triggerPreview() {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(generatePreview, 500)
}
watch(userContent, triggerPreview, { deep:true })
watch(figures, triggerPreview, { deep:true })

async function generatePreview() {
  if (!parsedMapping.value) return
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

function copyPreview() { navigator.clipboard.writeText(previewText.value).then(()=>flash(t('previewCopied'))) }
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
    const resp=await fetch(`${API}/export/pdf`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        template_path:templateForm.download_path||parsedMapping.value.template_path,
        template_format:'latex',mapping_json:JSON.stringify(parsedMapping.value),
        user_content:userContent,figures:figures.filter(f=>f.caption||f.image_path),
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
// Settings
// ===================================================================
watch(downloadPath, v=>localStorage.setItem('baboon_dl_path',v))
function pickDirectory() {
  const inp = dirInputRef.value
  if (!inp) return
  if ('showDirectoryPicker' in window) {
    window.showDirectoryPicker().then(handle => {
      // Web API can't give full path — browser sandboxes it
      // Best we can do: show the handle name and prompt user
      downloadPath.value = handle.name
    }).catch(() => {})
  } else {
    inp.click()
  }
}
function onDirPicked(e) {
  const files = e.target.files
  if (files.length) downloadPath.value = files[0].webkitRelativePath.split('/')[0]
}
async function initUser() {
  const s=localStorage.getItem('baboon_user_id')
  if (s) { try { userConfig.value=await api(`/users/${s}`); llmConfigs.value=userConfig.value.llm_configs||[] } catch { localStorage.removeItem('baboon_user_id') } }
}
async function createUser() {
  if (!userForm.user_identifier) return
  loading.value=true
  try { const u=await api('/users',{method:'POST',body:JSON.stringify(userForm)}); userConfig.value=u; localStorage.setItem('baboon_user_id',u.id); llmConfigs.value=[]; flash(t('userCreated')) }
  catch(e) { flash(e.message,'error') }
  finally { loading.value=false }
}
async function addLLMConfig() {
  if (!userConfig.value) return
  loading.value=true
  try { const c=await api(`/users/${userConfig.value.id}/llm-configs`,{method:'POST',body:JSON.stringify(newLLM)}); llmConfigs.value.push(c); newLLM.api_key=''; newLLM.model_name=''; flash(t('providerAdded')) }
  catch(e) { flash(e.message,'error') }
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
onUnmounted(()=>{ clearTimeout(previewTimer) })
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
      <button v-for="tab in ['templates','editor','settings']" :key="tab"
        :class="['nav-tab',{active:activeTab===tab}]" @click="activeTab=tab">{{ t(`tab_${tab}`) }}</button>
    </nav>
    <div class="header-actions">
      <div class="locale-switch">
        <button :class="['locale-btn',{active:locale==='zh'}]" @click="locale='zh'">中</button>
        <button :class="['locale-btn',{active:locale==='en'}]" @click="locale='en'">EN</button>
      </div>
      <span v-if="loading" class="spinner"></span>
      <span v-if="agentStatus.text" class="agent-status" :class="agentStatus.type">{{ agentStatus.text }}</span>
      <span class="badge" :class="message.type" v-if="message.text">{{ message.text }}</span>
    </div>
  </header>

  <!-- ====== Templates ====== -->
  <main v-if="activeTab==='templates'" class="panel">
    <section class="card highlight-card">
      <h2>{{ t('searchBtn') }}</h2>
      <p class="muted" style="margin-bottom:0.75rem">{{ t('searchHint') }}</p>
      <div class="form-row">
        <input v-model="templateForm.journal_name" :placeholder="t('journalPlaceholder')" class="input" style="flex:3" />
        <select v-model="templateForm.template_format" class="input select" style="flex:0.6">
          <option value="latex">{{ t('formatLatex') }}</option>
          <option value="docx">{{ t('formatDocx') }}</option>
        </select>
        <button @click="searchAndDownload" class="btn btn-primary" :disabled="loading" style="flex:1.2">
          {{ loading ? t('searching') : t('searchBtn') }}
        </button>
      </div>
    </section>

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
    </section>

    <section class="card">
      <h2>{{ t('savedTpls') }}</h2>
      <div v-if="templates.length===0" class="empty-hint">
        <p>{{ t('noTpls') }}</p>
      </div>
      <div v-for="tmpl in templates" :key="tmpl.id" class="list-row">
        <div class="list-info">
          <strong>{{ tmpl.journal_name }}</strong>
          <span class="tag">{{ tmpl.template_format }}</span>
          <span class="muted">{{ tmpl.download_path }}</span>
          <span v-if="tmpl.mapping_json" class="tag green">{{ t('parsed') }}</span>
        </div>
        <div class="list-actions">
          <button @click="parseTemplate(tmpl)" class="btn btn-sm btn-primary">{{ t('parse') }}</button>
          <button @click="deleteTemplate(tmpl.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button>
        </div>
      </div>
    </section>
  </main>

  <!-- ====== Editor (split: left forms + right preview) ====== -->
  <main v-else-if="activeTab==='editor'" class="panel editor-split">
    <!-- LEFT: Content forms -->
    <div class="editor-left">
      <div v-if="!parsedMapping" class="empty-state">
        <div class="empty-icon">📝</div>
        <p>{{ t('noParsed') }}</p>
        <button @click="activeTab='templates'" class="btn btn-primary" style="margin-top:1rem">{{ t('tab_template') }}</button>
      </div>
      <div v-else class="content-area">
        <div v-for="m in parsedMapping.modules" :key="m.id" class="card form-card">
          <div class="form-card-header">
            <span class="module-icon">{{ typeIcons[m.type]||'•' }}</span>
            <strong>{{ m.label }}</strong>
            <span class="tag">{{ m.type }}</span>
            <span v-if="m.level" class="tag sm">L{{ m.level }}</span>
          </div>
          <textarea v-if="m.type!=='figure'&&m.type!=='table'" v-model="userContent[m.id]"
            :placeholder="t('enterText',{label:m.label})"
            :rows="m.type==='abstract'?5:m.type==='title'?1:3" class="textarea" />
          <div v-if="m.type==='figure'||m.type==='table'">
            <div v-for="(fig,i) in figures" :key="i" class="figure-card">
              <div class="form-row">
                <input v-model="fig.caption" :placeholder="t('figureCaption')" class="input" />
                <input v-model="fig.label" :placeholder="t('figureLabel')" class="input" />
                <input v-model="fig.image_path" :placeholder="t('figurePath')" class="input" />
                <label class="checkbox-label"><input type="checkbox" v-model="fig.is_wide"/> {{ t('wide') }}</label>
                <button @click="removeFigure(i)" class="btn btn-sm btn-danger">✕</button>
              </div>
            </div>
            <button @click="addFigure" class="btn btn-sm" style="margin-top:0.3rem">{{ m.type==='figure'?t('addFigure'):t('addTable') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT: Live preview -->
    <div class="editor-right">
      <div class="preview-header card">
        <h3>{{ t('previewLabel') }}</h3>
        <div class="preview-actions">
          <span class="tag sm" v-if="previewLines">{{ previewLines }} {{ t('lineCount') }}</span>
          <button @click="copyPreview" class="btn btn-sm" :disabled="!previewText">{{ t('copySource') }}</button>
          <button @click="downloadTex" class="btn btn-sm" :disabled="!previewText">{{ t('exportTEX') }}</button>
          <button @click="downloadPdf" class="btn btn-sm btn-primary" :disabled="loading">{{ t('exportPDF') }}</button>
        </div>
      </div>
      <div class="preview-body card" v-if="previewText">
        <pre><code>{{ previewText }}</code></pre>
      </div>
      <div class="preview-body card empty-preview" v-else>
        <div class="empty-icon">👁</div>
        <p class="muted">{{ t('previewEmpty') }}</p>
      </div>
    </div>
  </main>

  <!-- ====== Settings ====== -->
  <main v-else-if="activeTab==='settings'" class="panel">
    <section class="card" v-if="!userConfig">
      <h2>{{ t('createProfile') }}</h2>
      <p class="muted" style="margin-bottom:0.75rem">{{ t('profileHint') }}</p>
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
        <div class="form-row">
          <input v-model="downloadPath" class="input" style="flex:1" />
          <input type="file" ref="dirInputRef" @change="onDirPicked" webkitdirectory directory style="display:none" />
          <button @click="pickDirectory" class="btn">{{ t('dirChoose') }}</button>
        </div>
      </div>
      <div class="card">
        <h3>{{ t('llmProviders') }}</h3>
        <p class="muted" style="margin-bottom:0.75rem">{{ t('profileHint').split('。')[1] || '' }}</p>
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
          <select v-model="newLLM.provider" class="input select" style="flex:0.6">
            <option value="openai">OpenAI</option><option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option><option value="ollama">Ollama</option>
          </select>
          <input v-if="newLLM.provider!=='ollama'" v-model="newLLM.api_key" type="password" :placeholder="t('apiKey')" class="input" style="flex:1" />
          <input v-if="newLLM.provider==='ollama'" v-model="newLLM.base_url" :placeholder="t('baseUrl')" class="input" style="flex:1" />
          <input v-model="newLLM.model_name" :placeholder="t('modelPlaceholder')" class="input" style="flex:1" />
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

.nav-tabs{display:flex;gap:0.25rem;margin-left:1rem}
.nav-tab{background:none;border:none;color:var(--text-secondary);padding:0.5rem 1.1rem;border-radius:var(--radius-sm);cursor:pointer;font-size:0.9rem;font-weight:500;transition:all 0.2s;font-family:system-ui,sans-serif;white-space:nowrap}
.nav-tab:hover{background:var(--bg-hover);color:var(--text-primary)}
.nav-tab.active{background:var(--accent);color:#fff}

.header-actions{margin-left:auto;display:flex;align-items:center;gap:0.8rem}
.locale-switch{display:flex;border-radius:var(--radius-sm);overflow:hidden;border:1px solid var(--border)}
.locale-btn{background:#fff;border:none;color:var(--text-secondary);padding:0.22rem 0.5rem;font-size:0.72rem;cursor:pointer;font-weight:600;transition:all 0.15s;font-family:system-ui,sans-serif}
.locale-btn:hover{color:var(--text-primary);background:var(--bg-hover)}
.locale-btn.active{background:var(--accent);color:#fff}

.agent-status{font-size:0.75rem;color:var(--accent);font-family:system-ui,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px}
.agent-status.warning{color:#b8860b}
.agent-status.error{color:var(--danger)}
.agent-status.success{color:var(--success)}

/* Panels */
.panel{flex:1;padding:2rem 2.5rem;max-width:100%;width:100%;margin:0 auto}
.card{background:var(--bg-card);border:1px solid var(--border-light);border-radius:var(--radius);padding:1.5rem;margin-bottom:1rem;box-shadow:var(--shadow-sm)}
.card h2{font-size:1.1rem;margin-bottom:0.75rem;color:var(--text-primary);font-weight:600;letter-spacing:-0.01em;border-bottom:1px solid var(--border-light);padding-bottom:0.5rem}
.card h3{font-size:0.95rem;margin-bottom:0.5rem;font-weight:600;color:var(--text-primary)}
.highlight-card{border:1px solid var(--accent-light);background:linear-gradient(135deg,#f8fafc 0%,var(--accent-bg) 100%)}

/* Forms */
.form-row{display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap}
.input{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:0.55rem 0.75rem;border-radius:var(--radius-sm);font-size:0.88rem;flex:1;min-width:100px;outline:none;transition:all 0.2s;font-family:system-ui,sans-serif}
.input:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,0.08)}
.select{cursor:pointer}
.textarea{width:100%;background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:0.85rem;border-radius:var(--radius-sm);font-size:0.9rem;line-height:1.7;font-family:'Crimson Text','Georgia',serif;resize:vertical;outline:none;transition:all 0.2s}
.textarea:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,0.08)}
.checkbox-label{display:flex;align-items:center;gap:0.3rem;font-size:0.82rem;color:var(--text-secondary);cursor:pointer;font-family:system-ui,sans-serif;white-space:nowrap}

/* Buttons */
.btn{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:0.5rem 1rem;border-radius:var(--radius-sm);font-size:0.84rem;font-weight:500;cursor:pointer;transition:all 0.2s;white-space:nowrap;font-family:system-ui,sans-serif;display:inline-flex;align-items:center;gap:0.3rem}
.btn:hover{background:var(--bg-hover);border-color:var(--text-muted)}
.btn:disabled{opacity:0.5;cursor:not-allowed}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn-primary:hover{background:var(--accent-light);border-color:var(--accent-light)}
.btn-danger{color:var(--danger)}
.btn-danger:hover{background:var(--danger-bg);border-color:var(--danger)}
.btn-sm{padding:0.25rem 0.55rem;font-size:0.78rem}

/* Tags */
.tag{display:inline-block;padding:0.12rem 0.5rem;background:var(--bg-primary);border:1px solid var(--border-light);border-radius:3px;font-size:0.68rem;font-weight:500;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;font-family:system-ui,sans-serif}
.tag.green{border-color:var(--success);color:var(--success);background:var(--success-bg)}
.tag.sm{font-size:0.62rem;padding:0.06rem 0.3rem}
.badge{padding:0.25rem 0.75rem;border-radius:var(--radius-sm);font-size:0.78rem;font-weight:500;font-family:system-ui,sans-serif}
.badge.success{background:var(--success-bg);color:var(--success)}
.badge.error{background:var(--danger-bg);color:var(--danger)}
.muted{color:var(--text-muted);font-size:0.85rem;font-family:system-ui,sans-serif}

/* Lists */
.list-row{display:flex;align-items:center;justify-content:space-between;padding:0.75rem 0;border-bottom:1px solid var(--border-light);gap:1rem;transition:background 0.1s}
.list-row:hover{background:var(--accent-bg);margin:0 -0.5rem;padding-left:0.5rem;padding-right:0.5rem;border-radius:var(--radius-sm)}
.list-row:last-child{border-bottom:none}
.list-info{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap}
.list-actions{display:flex;gap:0.3rem}
.empty{color:var(--text-muted);font-style:italic;padding:1rem 0}
.empty-hint{text-align:center;padding:2rem 1rem;color:var(--text-muted)}
.empty-hint p{font-size:0.95rem;margin-bottom:0.5rem}
.empty-state{text-align:center;padding:3rem 2rem}
.empty-icon{font-size:3rem;margin-bottom:0.75rem;opacity:0.5}

/* Editor Split Layout (Overleaf-like) */
.editor-split{display:flex;gap:0;padding:0;max-width:100%;height:calc(100vh - 64px);overflow:hidden}
.editor-left{flex:1;overflow-y:auto;padding:1.5rem;border-right:1px solid var(--border-light);background:var(--bg-primary)}
.editor-right{flex:1;display:flex;flex-direction:column;overflow:hidden;background:var(--bg-secondary)}
.editor-right .preview-header{display:flex;align-items:center;justify-content:space-between;margin:0;border-radius:0;border-bottom:1px solid var(--border-light)}
.editor-right .preview-header h3{font-size:0.95rem;margin:0}
.preview-actions{display:flex;align-items:center;gap:0.4rem}
.preview-body{flex:1;margin:0;border-radius:0;border:none;overflow-y:auto;font-family:'Courier New','Consolas',monospace;font-size:0.78rem;line-height:1.45;padding:1.25rem}
.preview-body pre{white-space:pre-wrap;word-break:break-all;margin:0}
.preview-body code{background:none;color:var(--text-primary)}
.empty-preview{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem}
.content-area{display:flex;flex-direction:column;gap:0.75rem}
.form-card{padding:1.25rem}
.form-card-header{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem}
.module-icon{font-size:0.85rem;flex-shrink:0}
.figure-card{border:1px dashed var(--border);padding:0.75rem;margin-bottom:0.4rem;border-radius:var(--radius-sm);background:#fdfdfb}

/* Settings */
.panel > .card { max-width:900px; }

/* Spinner */
.spinner{width:16px;height:16px;border:2px solid var(--border-light);border-top-color:var(--accent);border-radius:50%;animation:spin 0.6s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}

::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
