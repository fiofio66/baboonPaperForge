<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'

// ========== 纯中文 ==========
const T = {
  tpl:'模板', editor:'编辑器', settings:'设置',
  searchBtn:'🔍 搜索并下载', searchHint:'支持缩写：iotj → IEEE IoT, eswa → Expert Systems',
  journalPlaceholder:'期刊名或缩写', searching:'搜索下载中...',
  createTpl:'手动添加', chooseFile:'选择文件',
  formatLatex:'LaTeX', formatDocx:'Word', create:'添加',
  savedTpls:'模板库', noTpls:'还没有模板，在上方搜索或选择本地文件',
  parsed:'已解析', parse:'解析结构', delete:'删除',
  noMatches:'未匹配到预设模板，输入完整名将用 AI 解析',
  fillRequired:'请填写期刊名称', confirmDelete:'确认删除？',
  searchFailed:'下载失败', dlTimeout:'下载较大，请耐心等待...',
  noParsed:'请先选择或搜索模板，点击「解析结构」',
  previewLabel:'实时预览', previewCompiling:'正在编译 PDF...',
  previewFallback:'pdflatex 未安装，显示 LaTeX 源码',
  exportPDF:'📄 下载 PDF', exportTEX:'📥 下载 .tex',
  copySource:'📋 复制源码', copyOk:'已复制',
  modules:'模块',
  addModule:'+ 添加模块', moduleTypeSection:'正文', moduleTypeAbstract:'摘要',
  moduleName:'模块名', moduleLevel:'层级', addModuleBtn:'添加',
  enterText:'输入内容...', figCaption:'图注', figLabel:'标签 (如 fig:xxx)',
  figPath:'图片文件路径', figWide:'跨栏',
  addFigure:'+ 图片', addTable:'+ 表格', removeFigure:'删除',
  createProfile:'创建用户档案', profileHint:'配置 AI 后，搜索缩写会自动解析',
  nickname:'昵称', save:'创建', profile:'档案', defaultProvider:'默认提供商',
  llmProviders:'大模型配置', noProviders:'暂未配置',
  active:'活跃', inactive:'未激活', addProvider:'添加模型',
  apiKey:'API Key', baseUrl:'Base URL', modelPlaceholder:'模型名',
  add:'添加', downloadPathLabel:'模板下载路径',
  downloadPathHint:'搜索下载的模板保存到此目录',
  dirChoose:'选择文件夹', backendOk:'✓ 后端已连接',
  tplCreated:'已添加', tplDeleted:'已删除',
  parsedMsg:'解析完成！{count} 个模块', userCreated:'已创建',
  providerAdded:'已添加', providerRemoved:'已移除',
  zipExtracting:'解压中...', zipReady:'解压完成', zipError:'解压失败',
  zipHint:'检测到压缩包，自动解压',
}
const t = k => T[k]||k
const typeIcons = { title:'📌', author:'👤', abstract:'📃', section:'§', bibliography:'📚', figure:'🖼', table:'📊', acknowledgments:'🙏', keywords:'🔑' }

// ========== State ==========
const API = '/api/v1'
const activeTab = ref('tpl')
const loading = ref(false)
const msg = ref({ text:'', type:'' })
const flash = (t, tp='success') => { msg.value={text:t,type:tp}; setTimeout(()=>msg.value={text:'',type:''},4000) }

const templates = ref([])
const tf = reactive({ journal_name:'', template_format:'latex', download_path:'' })
const parsedMapping = ref(null)
const parsedModules = ref([])  // editable module list
const userConfig = ref(null)
const llmConfigs = ref([])
const newLLM = reactive({ provider:'openai', api_key:'', base_url:'', model_name:'' })
const userForm = reactive({ user_identifier:'', default_provider:'openai' })
const dlPath = ref(localStorage.getItem('baboon_dl_path')||'./workdir')
const selectedFile = ref(null)
const fileInputRef = ref(null)
const dirInputRef = ref(null)

// Preview state
const previewPdf = ref('')     // base64 PDF
const previewTex = ref('')     // fallback source
const previewMode = ref('tex') // 'pdf' | 'tex'
const previewLines = ref(0)
let previewTimer = null

const suggestions = ref([])
const showSuggestions = ref(false)
const agentStatus = ref({ text:'', type:'' })

// ========== API ==========
async function api(path, opts={}) {
  const r = await fetch(`${API}${path}`, { headers:{'Content-Type':'application/json',...opts.headers}, ...opts })
  if (!r.ok) { const e = await r.json().catch(()=>({detail:r.statusText})); throw new Error(e.detail||r.statusText) }
  return r.status===204 ? null : r.json()
}

// ========== Suggestions ==========
let st = null
watch(()=>tf.journal_name, v=>{
  clearTimeout(st)
  if (!v||v.length<1) { suggestions.value=[]; showSuggestions.value=false; return }
  st = setTimeout(async()=>{
    try { const r=await api(`/search/suggest?q=${encodeURIComponent(v)}`); suggestions.value=r; showSuggestions.value=r.length>0 }
    catch { suggestions.value=[] }
  },250)
})
function pickSuggestion(s) { tf.journal_name=s.name; suggestions.value=[]; showSuggestions.value=false }

// ========== File picker ==========
function triggerFilePicker() { fileInputRef.value?.click() }
async function onFilePicked(e) {
  const f = e.target.files[0]; if (!f) return
  selectedFile.value = f
  if (f.name.match(/\.(zip|tar\.gz|tgz|tar\.bz2|tar\.xz)$/i)) {
    agentStatus.value={text:t('zipExtracting'),type:'info'}; flash(t('zipHint'))
    try {
      const form = new FormData(); form.append('file', f)
      const r = await (await fetch(`${API}/files/extract-zip`,{method:'POST',body:form})).json()
      agentStatus.value={text:`${t('zipReady')} ${r.tex_files.length} .tex`,type:'success'}
      tf.download_path = r.main_tex || r.extract_dir
      if (r.main_tex) flash(`✓ ${t('zipReady')}: ${r.main_tex}`)
      setTimeout(()=>agentStatus.value={text:'',type:''},3000)
    } catch(e) { agentStatus.value={text:t('zipError'),type:'error'}; tf.download_path = f.name }
  } else { tf.download_path = f.name }
}

// ========== Templates ==========
async function loadTemplates() { try { templates.value = await api('/templates') } catch {} }
async function createTemplate() {
  if (!tf.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true
  try { await api('/templates',{method:'POST',body:JSON.stringify(tf)}); flash(t('tplCreated')); tf.journal_name=''; tf.download_path=''; selectedFile.value=null; await loadTemplates() }
  catch(e) { flash(e.message,'error') } finally { loading.value=false }
}
async function deleteTemplate(id) {
  if (!confirm(t('confirmDelete'))) return
  try { await api(`/templates/${id}`,{method:'DELETE'}); flash(t('tplDeleted')); await loadTemplates() }
  catch(e) { flash(e.message,'error') }
}
async function parseTemplate(tmpl) {
  loading.value=true; agentStatus.value={text:t('parse'),type:'info'}
  try {
    const r = await api(`/parser/analyze?template_id=${tmpl.id}`,{method:'POST'})
    parsedMapping.value = r
    // Clone modules into editable list with user content + per-module figures
    parsedModules.value = r.modules.map(m=>({...m, userText:'', figures:[]}))
    flash(t('parsedMsg',{count:r.modules.length})); activeTab.value='editor'; agentStatus.value={text:'',type:''}; triggerPreview()
  } catch(e) {
    flash(e.message,'error')
    agentStatus.value={text:'解析失败，尝试用 AI 兜底...',type:'warning'}
    try {
      const r = await api('/pipeline/run',{method:'POST',body:JSON.stringify({journal_name:tmpl.journal_name,template_format:tmpl.template_format,template_path:tmpl.download_path,user_content:{},figures:[],user_config_id:userConfig.value?.id||null})})
      pollPipeline(r.task_id)
    } catch { agentStatus.value={text:'',type:''} }
  } finally { loading.value=false }
}

// ========== Search & Download ==========
async function searchAndDownload() {
  if (!tf.journal_name) return flash(t('fillRequired'),'error')
  loading.value=true; agentStatus.value={text:t('searching'),type:'info'}; flash(t('searching'))
  try {
    const r = await api('/search/start',{method:'POST',body:JSON.stringify({
      journal_name:tf.journal_name, template_format:tf.template_format,
      user_config_id:userConfig.value?.id||null, use_llm_resolve:true,
      download_path:dlPath.value,
    })})
    loading.value=false
    if (r.status==='completed') {
      flash('已下载到 '+(r.extract_dir||'')); tf.download_path=r.extract_dir||''
      await loadTemplates()
      const created = await api('/templates',{method:'POST',body:JSON.stringify({
        journal_name:r.journal_resolved||tf.journal_name,
        template_format:tf.template_format, download_path:r.extract_dir||'',
      })})
      agentStatus.value={text:'解析中...',type:'info'}; await parseTemplate(created)
    } else { flash(r.error||t('searchFailed'),'error'); agentStatus.value={text:'',type:''} }
  } catch(e) { loading.value=false; flash(e.message||t('searchFailed'),'error'); agentStatus.value={text:'',type:''} }
}

function pollPipeline(tid) {
  const iv = setInterval(async()=>{
    try {
      const s=await api(`/pipeline/status?task_id=${tid}`)
      if (s.agent_log?.length) agentStatus.value={text:s.agent_log.at(-1),type:'info'}
      if (s.mapping_json) {
        parsedMapping.value=JSON.parse(s.mapping_json)
        parsedModules.value=parsedMapping.value.modules.map(m=>({...m,userText:'',figures:[]}))
        activeTab.value='editor'; triggerPreview()
      }
      if (s.status==='done'||s.status==='failed') {
        clearInterval(iv); loading.value=false
        if (s.status==='done') { flash(t('parsedMsg',{count:parsedModules.value.length})); agentStatus.value={text:'✓',type:'success'} }
        else { flash(s.error||'', 'error'); agentStatus.value={text:'✗',type:'error'} }
        setTimeout(()=>agentStatus.value={text:'',type:''},3000)
      }
    } catch {}
  },1500)
}

// ========== Module management ==========
function removeModule(idx) { parsedModules.value.splice(idx,1); triggerPreview() }
function addCustomModule() {
  const nm = window.prompt('模块名称（如 "实验结果"）：')?.trim()
  if (!nm) return
  parsedModules.value.push({
    id: `custom-${Date.now()}`, type:'section', label:nm,
    anchor_type:'regex', anchor_pattern:'', content:'', level:1,
    constraints:[], userText:'', figures:[], _custom:true,
  })
  triggerPreview()
}
function addFigureToModule(mi) {
  parsedModules.value[mi].figures.push({ caption:'', label:'', image_path:'', is_wide:false })
  triggerPreview()
}
function removeFigureFromModule(mi, fi) {
  parsedModules.value[mi].figures.splice(fi,1); triggerPreview()
}

// ========== Preview ==========
watch(parsedModules, ()=>{ triggerPreview() }, { deep:true })
function triggerPreview() { clearTimeout(previewTimer); previewTimer = setTimeout(doPreview, 600) }

async function doPreview() {
  if (!parsedMapping.value || !parsedModules.value.length) return
  const content = {}; const allFigs = []
  for (const m of parsedModules.value) {
    if (m.userText?.trim()) content[m.id] = m.userText
    if (m.figures?.length) allFigs.push(...m.figures)
  }
  if (!Object.values(content).some(v=>v?.trim()) && !allFigs.length) {
    previewPdf.value=''; previewTex.value=''; return
  }
  try {
    const r = await api('/preview/render',{method:'POST',body:JSON.stringify({
      template_path:tf.download_path||parsedMapping.value.template_path,
      template_format:tf.template_format||'latex',
      mapping_json:JSON.stringify({...parsedMapping.value,modules:parsedModules.value}),
      user_content:content, figures:allFigs,
    })})
    if (r.rendered && r.pdf_base64) {
      previewPdf.value = r.pdf_base64; previewMode.value = 'pdf'
    } else {
      previewTex.value = r.tex_source||''; previewMode.value = 'tex'
    }
    if (r.tex_source) previewLines.value = r.tex_source.split('\n').length
  } catch {}
}

function copyPreview() { navigator.clipboard.writeText(previewTex.value).then(()=>flash(t('copyOk'))) }
function downloadTex() {
  const b=new Blob([previewTex.value],{type:'application/x-tex'})
  const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='paper.tex'; a.click()
}
async function downloadPdf() {
  if (!parsedMapping.value) return
  const content={}; const allFigs=[]
  for (const m of parsedModules.value) {
    if (m.userText?.trim()) content[m.id]=m.userText
    if (m.figures?.length) allFigs.push(...m.figures)
  }
  const r = await fetch(`${API}/export/pdf`,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({template_path:tf.download_path||parsedMapping.value.template_path,
      template_format:'latex',mapping_json:JSON.stringify({...parsedMapping.value,modules:parsedModules.value}),
      user_content:content,figures:allFigs})})
  const blob=await r.blob(); const a=document.createElement('a')
  a.href=URL.createObjectURL(blob); a.download='paper.pdf'; a.click()
}

// ========== Settings ==========
watch(dlPath, v=>localStorage.setItem('baboon_dl_path',v))
function pickDirectory() {
  const d=dirInputRef.value; if (!d) return
  if ('showDirectoryPicker' in window) { window.showDirectoryPicker().then(h=>{dlPath.value=h.name}).catch(()=>{}) }
  else { d.click() }
}
function onDirPicked(e) { const f=e.target.files; if (f.length) dlPath.value=f[0].webkitRelativePath.split('/')[0] }
async function initUser() {
  const s=localStorage.getItem('baboon_user_id')
  if (s) { try { userConfig.value=await api(`/users/${s}`); llmConfigs.value=userConfig.value.llm_configs||[] } catch { localStorage.removeItem('baboon_user_id') } }
}
async function createUser() {
  if (!userForm.user_identifier) return; loading.value=true
  try { const u=await api('/users',{method:'POST',body:JSON.stringify(userForm)}); userConfig.value=u; localStorage.setItem('baboon_user_id',u.id); llmConfigs.value=[]; flash(t('userCreated')) }
  catch(e){flash(e.message,'error')} finally{loading.value=false}
}
async function addLLMConfig() {
  if (!userConfig.value) return; loading.value=true
  try { const c=await api(`/users/${userConfig.value.id}/llm-configs`,{method:'POST',body:JSON.stringify(newLLM)}); llmConfigs.value.push(c); newLLM.api_key=''; newLLM.model_name=''; flash(t('providerAdded')) }
  catch(e){flash(e.message,'error')} finally{loading.value=false}
}
async function deleteLLMConfig(id) {
  if (!userConfig.value||!confirm(t('confirmDelete'))) return
  try { await api(`/users/${userConfig.value.id}/llm-configs/${id}`,{method:'DELETE'}); llmConfigs.value=llmConfigs.value.filter(c=>c.id!==id); flash(t('providerRemoved')) }
  catch(e){flash(e.message,'error')}
}

onMounted(async()=>{ await loadTemplates(); await initUser(); try{const h=await api('/health');if(h.status==='ok')flash(t('backendOk'))}catch{} })
onUnmounted(()=>{ clearTimeout(previewTimer) })
</script>

<template>
<div class="app-shell">
  <header class="app-header">
    <div class="logo"><span class="logo-icon">🦧</span><span class="logo-text"><span class="logo-accent">Baboon</span>PaperForge</span></div>
    <nav class="nav-tabs">
      <button :class="['nav-tab',{active:activeTab==='tpl'}]" @click="activeTab='tpl'">{{ T.tpl }}</button>
      <button :class="['nav-tab',{active:activeTab==='editor'}]" @click="activeTab='editor'">{{ T.editor }}</button>
      <button :class="['nav-tab',{active:activeTab==='settings'}]" @click="activeTab='settings'">{{ T.settings }}</button>
    </nav>
    <div class="header-actions">
      <span v-if="loading" class="spinner"></span>
      <span v-if="agentStatus.text" class="agent-status" :class="agentStatus.type">{{ agentStatus.text }}</span>
      <span class="badge" :class="msg.type" v-if="msg.text">{{ msg.text }}</span>
    </div>
  </header>

  <!-- ====== 模板 ====== -->
  <main v-if="activeTab==='tpl'" class="panel">
    <section class="card highlight-card">
      <h2>{{ t('searchBtn') }}</h2>
      <p class="muted" style="margin-bottom:0.5rem">{{ t('searchHint') }}</p>
      <div class="form-row" style="position:relative">
        <div style="flex:3;position:relative">
          <input v-model="tf.journal_name" :placeholder="t('journalPlaceholder')" class="input" @focus="showSuggestions=suggestions.length>0" @blur="setTimeout(()=>showSuggestions=false,200)" style="width:100%" />
          <div class="suggestions-dropdown" v-if="showSuggestions&&suggestions.length">
            <div v-for="s in suggestions" :key="s.id" class="suggestion-item" @mousedown="pickSuggestion(s)"><strong>{{ s.name }}</strong><span class="tag sm">{{ s.id }}</span></div>
          </div>
        </div>
        <select v-model="tf.template_format" class="input select" style="flex:0.5"><option value="latex">{{ T.formatLatex }}</option><option value="docx">{{ T.formatDocx }}</option></select>
        <button @click="searchAndDownload" class="btn btn-primary" :disabled="loading" style="flex:1.2">{{ loading?t('searching'):t('searchBtn') }}</button>
      </div>
      <div v-if="!suggestions.length&&tf.journal_name.length>1" class="muted" style="margin-top:0.5rem;font-size:0.8rem">{{ t('noMatches') }}</div>
    </section>

    <section class="card">
      <h2>{{ t('createTpl') }}</h2>
      <div class="form-row">
        <input v-model="tf.journal_name" :placeholder="t('journalPlaceholder')" class="input" style="flex:2" />
        <select v-model="tf.template_format" class="input select" style="flex:0.5"><option value="latex">{{ T.formatLatex }}</option><option value="docx">{{ T.formatDocx }}</option></select>
        <input type="file" ref="fileInputRef" @change="onFilePicked" accept=".tex,.zip,.tar.gz,.docx" style="display:none" />
        <button @click="triggerFilePicker" class="btn" :disabled="loading" style="flex:0.8">📁 {{ selectedFile?selectedFile.name:T.chooseFile }}</button>
        <button @click="createTemplate" class="btn btn-primary" :disabled="loading">{{ T.create }}</button>
      </div>
    </section>

    <section class="card">
      <h2>{{ t('savedTpls') }}</h2>
      <div v-if="!templates.length" class="empty-hint"><p>{{ t('noTpls') }}</p></div>
      <div v-for="tmpl in templates" :key="tmpl.id" class="list-row">
        <div class="list-info"><strong>{{ tmpl.journal_name }}</strong><span class="tag">{{ tmpl.template_format }}</span><span class="muted">{{ tmpl.download_path }}</span><span v-if="tmpl.mapping_json" class="tag green">{{ t('parsed') }}</span></div>
        <div class="list-actions"><button @click="parseTemplate(tmpl)" class="btn btn-sm btn-primary">{{ t('parse') }}</button><button @click="deleteTemplate(tmpl.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button></div>
      </div>
    </section>
  </main>

  <!-- ====== 编辑器 (左表单 + 右预览) ====== -->
  <main v-else-if="activeTab==='editor'" class="panel editor-split">
    <!-- 左：模块列表 -->
    <div class="editor-left">
      <div v-if="!parsedModules.length" class="empty-state"><div class="empty-icon">📝</div><p>{{ t('noParsed') }}</p><button @click="activeTab='tpl'" class="btn btn-primary" style="margin-top:1rem">{{ T.tpl }}</button></div>
      <div v-else class="content-area">
        <div class="editor-toolbar card" style="padding:0.75rem 1rem;margin-bottom:0.75rem">
          <span class="muted">{{ parsedModules.length }} {{ t('modules') }}</span>
          <button @click="addCustomModule" class="btn btn-sm">+ 自定义模块</button>
        </div>
        <div v-for="(m,mi) in parsedModules" :key="m.id" class="card form-card">
          <div class="form-card-header">
            <span class="module-icon">{{ typeIcons[m.type]||'•' }}</span>
            <strong>{{ m.label }}</strong>
            <span class="tag">{{ m.type }}</span>
            <span v-if="m.level" class="tag sm">L{{ m.level }}</span>
            <div style="margin-left:auto;display:flex;gap:0.3rem">
              <button v-if="m.type!=='figure'&&m.type!=='table'" @click="addFigureToModule(mi)" class="btn btn-sm" :title="t('addFigure')">+🖼</button>
              <button v-if="m.type!=='figure'&&m.type!=='table'" @click="addFigureToModule(mi)" class="btn btn-sm" :title="t('addTable')">+📊</button>
              <button @click="removeModule(mi)" class="btn btn-sm btn-danger">✕</button>
            </div>
          </div>

          <!-- 文本输入 -->
          <textarea v-if="m.type!=='figure'&&m.type!=='table'" v-model="m.userText"
            :placeholder="t('enterText')"
            :rows="m.type==='abstract'?4:m.type==='title'?1:3" class="textarea" />

          <!-- 本模块的图片/表格 -->
          <div v-if="m.figures&&m.figures.length" style="margin-top:0.5rem">
            <div v-for="(fig,fi) in m.figures" :key="fi" class="figure-card">
              <div class="figure-card-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem">
                <span class="tag sm">{{ fig.is_wide?'跨栏图':'图片' }} #{{ fi+1 }}</span>
                <button @click="removeFigureFromModule(mi,fi)" class="btn btn-sm btn-danger" style="font-size:0.7rem">✕</button>
              </div>
              <div class="form-row">
                <input v-model="fig.caption" :placeholder="t('figCaption')" class="input" style="flex:2" />
                <input v-model="fig.label" :placeholder="t('figLabel')" class="input" style="flex:1" />
              </div>
              <div class="form-row" style="margin-top:0.3rem">
                <input v-model="fig.image_path" :placeholder="t('figPath')" class="input" style="flex:2" />
                <label class="checkbox-label"><input type="checkbox" v-model="fig.is_wide"/> {{ t('figWide') }}</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右：预览 -->
    <div class="editor-right">
      <div class="preview-header card">
        <h3>{{ t('previewLabel') }}</h3>
        <div class="preview-actions">
          <span class="tag sm" v-if="previewLines && previewMode==='tex'">{{ previewLines }} 行</span>
          <button @click="copyPreview" class="btn btn-sm" :disabled="!previewTex">{{ t('copySource') }}</button>
          <button @click="downloadTex" class="btn btn-sm" :disabled="!previewTex">{{ t('exportTEX') }}</button>
          <button @click="downloadPdf" class="btn btn-sm btn-primary" :disabled="loading">{{ t('exportPDF') }}</button>
        </div>
      </div>
      <!-- PDF 预览 -->
      <div class="preview-body card" v-if="previewMode==='pdf'&&previewPdf" style="padding:0">
        <iframe :src="'data:application/pdf;base64,'+previewPdf" style="width:100%;height:100%;border:none;min-height:600px"></iframe>
      </div>
      <!-- 源码预览 -->
      <div class="preview-body card" v-else-if="previewTex">
        <pre><code>{{ previewTex }}</code></pre>
      </div>
      <!-- 空 -->
      <div class="preview-body card empty-preview" v-else>
        <div class="empty-icon">👁</div>
        <p class="muted">在左侧填写内容，这里会实时显示编译结果</p>
      </div>
    </div>
  </main>

  <!-- ====== 设置 ====== -->
  <main v-else-if="activeTab==='settings'" class="panel">
    <section class="card" v-if="!userConfig"><h2>{{ t('createProfile') }}</h2><p class="muted" style="margin-bottom:0.75rem">{{ t('profileHint') }}</p><div class="form-row"><input v-model="userForm.user_identifier" :placeholder="t('nickname')" class="input" /><select v-model="userForm.default_provider" class="input select"><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="gemini">Gemini</option><option value="ollama">Ollama</option></select><button @click="createUser" class="btn btn-primary" :disabled="loading">{{ t('save') }}</button></div></section>
    <section v-else>
      <div class="card"><h2>{{ t('profile') }}: {{ userConfig.user_identifier }}</h2><p class="muted">{{ t('defaultProvider') }}: {{ userConfig.default_provider }}</p></div>
      <div class="card"><h3>{{ t('downloadPathLabel') }}</h3><p class="muted" style="margin-bottom:0.5rem">{{ t('downloadPathHint') }}</p><div class="form-row"><input v-model="dlPath" class="input" style="flex:1" /><input type="file" ref="dirInputRef" @change="onDirPicked" webkitdirectory directory style="display:none" /><button @click="pickDirectory" class="btn">{{ t('dirChoose') }}</button></div></div>
      <div class="card"><h3>{{ t('llmProviders') }}</h3><div v-if="!llmConfigs.length" class="empty">{{ t('noProviders') }}</div><div v-for="cfg in llmConfigs" :key="cfg.id" class="list-row"><div class="list-info"><strong>{{ cfg.provider }}</strong><span v-if="cfg.model_name" class="tag">{{ cfg.model_name }}</span><span class="tag" :class="cfg.is_active?'green':''">{{ cfg.is_active?t('active'):t('inactive') }}</span></div><div class="list-actions"><button @click="deleteLLMConfig(cfg.id)" class="btn btn-sm btn-danger">{{ t('delete') }}</button></div></div>
      <h3 style="margin-top:1.5rem">{{ t('addProvider') }}</h3><div class="form-row"><select v-model="newLLM.provider" class="input select" style="flex:0.6"><option value="openai">OpenAI</option><option value="anthropic">Anthropic</option><option value="gemini">Gemini</option><option value="ollama">Ollama</option></select><input v-if="newLLM.provider!=='ollama'" v-model="newLLM.api_key" type="password" :placeholder="t('apiKey')" class="input" style="flex:1" /><input v-if="newLLM.provider==='ollama'" v-model="newLLM.base_url" :placeholder="t('baseUrl')" class="input" style="flex:1" /><input v-model="newLLM.model_name" :placeholder="t('modelPlaceholder')" class="input" style="flex:1" /><button @click="addLLMConfig" class="btn btn-primary" :disabled="loading">{{ t('add') }}</button></div></div>
    </section>
  </main>
</div>
</template>

<style>
:root{--bg-primary:#fafaf7;--bg-secondary:#fff;--bg-card:#fff;--bg-hover:#f0ece4;--border:#d9d4c9;--border-light:#e8e4db;--text-primary:#2c2416;--text-secondary:#6b5e4a;--text-muted:#9b8e7a;--accent:#1a5276;--accent-light:#2980b9;--accent-bg:#eaf0f6;--success:#1e7e34;--success-bg:#e8f5e9;--danger:#c0392b;--danger-bg:#fdecea;--radius:6px;--radius-sm:4px;--shadow-sm:0 1px 3px rgba(44,36,22,.06);--shadow-md:0 2px 8px rgba(44,36,22,.08)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Crimson Text','Source Serif 4','Georgia',serif;background:var(--bg-primary);color:var(--text-primary);line-height:1.7;min-height:100vh;-webkit-font-smoothing:antialiased}
.app-shell{display:flex;flex-direction:column;min-height:100vh}
.app-header{display:flex;align-items:center;gap:2rem;padding:0 2.5rem;height:64px;background:var(--bg-secondary);border-bottom:2px solid var(--border);position:sticky;top:0;z-index:100;box-shadow:var(--shadow-sm)}
.logo{display:flex;align-items:baseline;gap:.5rem}.logo-icon{font-size:1.5rem}.logo-text{font-size:1.2rem;font-weight:700;letter-spacing:-.01em;font-family:'Crimson Text','Georgia',serif}.logo-accent{color:var(--accent)}
.nav-tabs{display:flex;gap:.25rem;margin-left:1rem}.nav-tab{background:none;border:none;color:var(--text-secondary);padding:.5rem 1.1rem;border-radius:var(--radius-sm);cursor:pointer;font-size:.9rem;font-weight:500;transition:all .2s;font-family:system-ui,sans-serif;white-space:nowrap}.nav-tab:hover{background:var(--bg-hover);color:var(--text-primary)}.nav-tab.active{background:var(--accent);color:#fff}
.header-actions{margin-left:auto;display:flex;align-items:center;gap:.8rem}
.agent-status{font-size:.75rem;font-family:system-ui,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;color:var(--accent)}.agent-status.warning{color:#b8860b}.agent-status.error{color:var(--danger)}.agent-status.success{color:var(--success)}

.suggestions-dropdown{position:absolute;top:100%;left:0;right:0;background:var(--bg-card);border:1px solid var(--accent-light);border-top:none;border-radius:0 0 var(--radius) var(--radius);box-shadow:var(--shadow-md);z-index:200;max-height:280px;overflow-y:auto}
.suggestion-item{display:flex;align-items:center;justify-content:space-between;padding:.55rem .75rem;cursor:pointer;transition:background .1s;font-family:system-ui,sans-serif;font-size:.85rem}.suggestion-item:hover{background:var(--accent-bg)}.suggestion-item strong{color:var(--text-primary)}

.panel{flex:1;padding:2rem 2.5rem;max-width:100%;width:100%;margin:0 auto}
.card{background:var(--bg-card);border:1px solid var(--border-light);border-radius:var(--radius);padding:1.5rem;margin-bottom:1rem;box-shadow:var(--shadow-sm)}.card h2{font-size:1.1rem;margin-bottom:.75rem;font-weight:600;border-bottom:1px solid var(--border-light);padding-bottom:.5rem}.card h3{font-size:.95rem;margin-bottom:.5rem;font-weight:600}
.highlight-card{border:1px solid var(--accent-light);background:linear-gradient(135deg,#f8fafc 0%,var(--accent-bg) 100%)}
.form-row{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}.input{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:.55rem .75rem;border-radius:var(--radius-sm);font-size:.88rem;flex:1;min-width:80px;outline:none;transition:all .2s;font-family:system-ui,sans-serif}.input:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,.08)}.select{cursor:pointer}
.textarea{width:100%;background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:.85rem;border-radius:var(--radius-sm);font-size:.9rem;line-height:1.7;font-family:'Crimson Text','Georgia',serif;resize:vertical;outline:none;transition:all .2s}.textarea:focus{border-color:var(--accent-light);box-shadow:0 0 0 3px rgba(26,82,118,.08)}
.checkbox-label{display:flex;align-items:center;gap:.3rem;font-size:.82rem;color:var(--text-secondary);cursor:pointer;font-family:system-ui,sans-serif;white-space:nowrap}
.btn{background:#fff;border:1px solid var(--border);color:var(--text-primary);padding:.5rem 1rem;border-radius:var(--radius-sm);font-size:.84rem;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap;font-family:system-ui,sans-serif;display:inline-flex;align-items:center;gap:.3rem}.btn:hover{background:var(--bg-hover)}.btn:disabled{opacity:.5;cursor:not-allowed}.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff}.btn-primary:hover{background:var(--accent-light)}.btn-danger{color:var(--danger)}.btn-danger:hover{background:var(--danger-bg)}.btn-sm{padding:.25rem .55rem;font-size:.78rem}
.tag{display:inline-block;padding:.12rem .5rem;background:var(--bg-primary);border:1px solid var(--border-light);border-radius:3px;font-size:.68rem;font-weight:500;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.05em;font-family:system-ui,sans-serif}.tag.green{border-color:var(--success);color:var(--success);background:var(--success-bg)}.tag.sm{font-size:.62rem;padding:.06rem .3rem}
.badge{padding:.25rem .75rem;border-radius:var(--radius-sm);font-size:.78rem;font-weight:500;font-family:system-ui,sans-serif}.badge.success{background:var(--success-bg);color:var(--success)}.badge.error{background:var(--danger-bg);color:var(--danger)}
.muted{color:var(--text-muted);font-size:.85rem;font-family:system-ui,sans-serif}
.list-row{display:flex;align-items:center;justify-content:space-between;padding:.75rem 0;border-bottom:1px solid var(--border-light);gap:1rem}.list-row:hover{background:var(--accent-bg);margin:0 -.5rem;padding-left:.5rem;padding-right:.5rem;border-radius:var(--radius-sm)}.list-row:last-child{border-bottom:none}.list-info{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}.list-actions{display:flex;gap:.3rem}
.empty{color:var(--text-muted);font-style:italic;padding:1rem 0}.empty-hint{text-align:center;padding:2rem 1rem;color:var(--text-muted)}.empty-hint p{font-size:.95rem;margin-bottom:.5rem}.empty-state{text-align:center;padding:3rem 2rem}.empty-icon{font-size:3rem;margin-bottom:.75rem;opacity:.5}
.editor-split{display:flex;gap:0;padding:0;max-width:100%;height:calc(100vh - 64px);overflow:hidden}.editor-left{flex:1;overflow-y:auto;padding:1.5rem;border-right:1px solid var(--border-light);background:var(--bg-primary)}.editor-right{flex:1;display:flex;flex-direction:column;overflow:hidden;background:var(--bg-secondary)}.editor-right .preview-header{display:flex;align-items:center;justify-content:space-between;margin:0;border-radius:0;border-bottom:1px solid var(--border-light)}.editor-right .preview-header h3{font-size:.95rem;margin:0}.preview-actions{display:flex;align-items:center;gap:.4rem}.preview-body{flex:1;margin:0;border-radius:0;border:none;overflow-y:auto;font-family:'Courier New','Consolas',monospace;font-size:.78rem;line-height:1.45;padding:1.25rem}.preview-body pre{white-space:pre-wrap;word-break:break-all;margin:0}.preview-body code{background:none;color:var(--text-primary)}.empty-preview{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.5rem}
.content-area{display:flex;flex-direction:column;gap:.75rem}.form-card{padding:1.25rem}.form-card-header{display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem}.module-icon{font-size:.85rem;flex-shrink:0}.figure-card{border:1px dashed var(--border);padding:.75rem;margin-bottom:.4rem;border-radius:var(--radius-sm);background:#fdfdfb}
.editor-toolbar{display:flex;align-items:center;justify-content:space-between}
.panel>.card{max-width:900px}.spinner{width:16px;height:16px;border:2px solid var(--border-light);border-top-color:var(--accent);border-radius:50%;animation:spin .6s linear infinite;display:inline-block}@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
