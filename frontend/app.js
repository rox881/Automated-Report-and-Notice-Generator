// ── State ─────────────────────────────────────────────────
let sessionId      = null;
let templateId     = null;
let pollTimer      = null;
let hadMissingStep = false;   // tracks whether Step 2 was shown (for ← Back logic)
let previewTimer   = null;    // debounce for live preview updates

// ── API Helper ────────────────────────────────────────────
const api = async (path, method = 'GET', body = null) => {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || `Server error: ${res.status}`);
  return data;
};

// ── Navigation ────────────────────────────────────────────
const showStep = (n) => {
  document.querySelectorAll('.step').forEach(s => s.classList.add('hidden'));
  const target = document.getElementById(`step-${n}`);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

function goBackFromStep3() {
  // If missing-fields step was shown, go back there; otherwise back to Step 1
  if (hadMissingStep) {
    showStep(2);
  } else {
    showStep(1);
  }
}

// ── Error Helpers ─────────────────────────────────────────
const showError = (id, msg) => {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.remove('hidden'); }
};
const hideError = (id) => {
  const el = document.getElementById(id);
  if (el) el.classList.add('hidden');
};

// ── Markdown ↔ HTML Helpers ───────────────────────────────
function mdToHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
    .replace(/\*(.*?)\*/g, '<i>$1</i>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

function htmlToMd(html) {
  if (!html) return '';
  let s = html;
  s = s.replace(/<\s*br\s*\/?>/gi, '\n');
  s = s.replace(/<\/\s*p\s*>/gi, '\n\n');
  s = s.replace(/<\s*p\s*>/gi, '');
  s = s.replace(/<\/\s*div\s*>/gi, '\n');
  s = s.replace(/<\s*div\s*>/gi, '');
  s = s.replace(/<\s*b\s*>/gi, '**');
  s = s.replace(/<\/\s*b\s*>/gi, '**');
  s = s.replace(/<\s*strong\s*>/gi, '**');
  s = s.replace(/<\/\s*strong\s*>/gi, '**');
  s = s.replace(/<\s*i\s*>/gi, '*');
  s = s.replace(/<\/\s*i\s*>/gi, '*');
  s = s.replace(/<\s*em\s*>/gi, '*');
  s = s.replace(/<\/\s*em\s*>/gi, '*');
  const temp = document.createElement('textarea');
  temp.innerHTML = s;
  return temp.value.trim();
}

// Strip all HTML tags to plain text for preview
function htmlToPlain(html) {
  const d = document.createElement('div');
  d.innerHTML = html;
  return d.innerText || d.textContent || '';
}

// ── New Session ───────────────────────────────────────────
function newSession() {
  sessionId      = null;
  templateId     = null;
  hadMissingStep = false;
  if (pollTimer) clearInterval(pollTimer);
  document.getElementById('context-input').value = '';
  document.getElementById('job-status').innerHTML = '';
  ['step1-error','step2-error','step3-error','step4-error'].forEach(hideError);
  showStep(1);
}

// ── Step 1: Start Workflow ────────────────────────────────
async function startWorkflow(tpl) {
  const context = document.getElementById('context-input').value.trim();
  if (!context) return showError('step1-error', 'Please paste some event context or source text first.');
  hideError('step1-error');

  templateId     = tpl;
  hadMissingStep = false;

  const btn = document.querySelector(`.pill.${tpl}`);
  const originalText = btn.innerHTML;
  btn.innerHTML = `⏳ Analyzing &amp; Extracting...`;
  btn.disabled = true;

  try {
    const session = await api('/api/sessions', 'POST', { context });
    sessionId = session.id;

    const result = await api(`/api/sessions/${sessionId}/extract?template_id=${templateId}`, 'POST');

    const missingRequired = (result.missing || []).filter(m => m.required);
    if (missingRequired.length > 0) {
      hadMissingStep = true;
      renderMissingForm(result.missing);
      showStep(2);
    } else {
      await loadReviewStep();
      showStep(3);
    }
    loadHistory();
  } catch (err) {
    showError('step1-error', err.message);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// ── Step 2: Missing Fields ────────────────────────────────
function renderMissingForm(missing) {
  const form = document.getElementById('missing-form');
  document.getElementById('step2-title').textContent =
    `Missing ${templateId === 'notice' ? 'Notice' : 'Report'} Details`;

  form.innerHTML = missing.map(f => {
    const badge = f.required
      ? `<span class="required-badge">* Required</span>`
      : `<span class="optional-badge">(Optional)</span>`;
    return `
      <div class="field-row">
        <label for="field-${f.key}">${f.label} ${badge}</label>
        <input
          id="field-${f.key}"
          data-key="${f.key}"
          data-required="${f.required}"
          type="text"
          placeholder="Enter ${f.label.toLowerCase()}..."
        />
      </div>
    `;
  }).join('');
}

async function submitAnswers() {
  hideError('step2-error');
  const inputs  = document.querySelectorAll('#missing-form input');
  const answers = Array.from(inputs).map(i => ({
    key:      i.dataset.key,
    value:    i.value.trim(),
    required: i.dataset.required === 'true',
  }));

  const emptyRequired = answers.filter(a => a.required && !a.value);
  if (emptyRequired.length) {
    return showError('step2-error',
      `Please fill in: ${emptyRequired.map(a => a.key).join(', ')}`);
  }

  try {
    await api(`/api/fields/${sessionId}/answers?template_id=${templateId}`, 'POST', {
      answers: answers.map(a => ({ key: a.key, value: a.value }))
    });
    await loadReviewStep();
    showStep(3);
  } catch (err) {
    showError('step2-error', err.message);
  }
}

// ── Step 3: Load Review Step ──────────────────────────────
// Stores field data globally for live preview rendering
let _previewFields = [];

async function loadReviewStep() {
  const fields = await api(`/api/sessions/${sessionId}/preview?template_id=${templateId}`);
  _previewFields = fields;

  const tbody = document.getElementById('preview-body');
  const narrativeContainer = document.getElementById('narrative-section');

  document.getElementById('step3-title').textContent = templateId === 'notice'
    ? 'Review & Refine Notice'
    : 'Review & Refine Report';

  const narrativeKeys = ['introduction', 'discussion', 'conclusion'];
  const metadataFields = fields.filter(f => !narrativeKeys.includes(f.key));
  const narrativeFields = fields.filter(f => narrativeKeys.includes(f.key));

  // Render metadata table (editable cells)
  tbody.innerHTML = metadataFields.map(f => {
    let display = Array.isArray(f.value) ? f.value.join(', ') : (f.value ?? f.default ?? '');
    const reqMark = f.required ? '<span style="color:#dc2626">*</span> ' : '';
    return `
      <tr>
        <td><strong>${reqMark}${f.label}</strong></td>
        <td contenteditable="true" data-key="${f.key}" oninput="schedulePreviewUpdate()">${display}</td>
      </tr>
    `;
  }).join('');

  // Narrative section
  if (templateId === 'report') {
    narrativeContainer.classList.remove('hidden');
    narrativeFields.forEach(f => {
      const editor = document.getElementById(`editor-${f.key}`);
      if (editor) editor.innerHTML = mdToHtml(f.value || f.default || '');
    });
  } else {
    narrativeContainer.classList.add('hidden');
  }

  // Initial live preview render
  renderA4Preview();
}

// ── Live A4 Preview Renderer ──────────────────────────────
function schedulePreviewUpdate() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(renderA4Preview, 350);
}

function collectCurrentValues() {
  // Build a values map from the current editable state in the UI
  const vals = {};

  // Metadata from table
  document.querySelectorAll('#preview-body td[contenteditable]').forEach(td => {
    vals[td.dataset.key] = td.textContent.trim();
  });

  // Narratives from editors (plain text for preview)
  ['introduction', 'discussion', 'conclusion'].forEach(key => {
    const ed = document.getElementById(`editor-${key}`);
    if (ed) vals[key] = ed.innerHTML; // keep HTML for rich preview
  });

  return vals;
}

function renderA4Preview() {
  const container = document.getElementById('live-preview-content');
  if (!container) return;

  const vals = collectCurrentValues();
  const tpl  = templateId;

  if (tpl === 'report') {
    renderReportPreview(vals, container);
  } else if (tpl === 'notice') {
    renderNoticePreview(vals, container);
  }
}

function renderReportPreview(v, container) {
  const speakers = v['speakers'] || '';
  const speakerLines = speakers.split(',').map(s => `<div class="a4-speaker">${s.trim()}</div>`).join('');

  const intro      = v['introduction'] || '';
  const discussion = v['discussion']  || '';
  const conclusion = v['conclusion']  || '';

  container.innerHTML = `
    <div class="a4-header">
      <div class="a4-college-name">A P SHAH INSTITUTE OF TECHNOLOGY</div>
      <div class="a4-dept">AIML CLUB</div>
      <div class="a4-doc-type">EVENT REPORT</div>
    </div>

    <div class="a4-title-block">
      <div class="a4-event-title">${v['event_title'] || '{{ Event Title }}'}</div>
    </div>

    <table class="a4-meta-table">
      <tr><td class="a4-meta-label">Date</td><td>${v['event_date'] || ''}</td></tr>
      <tr><td class="a4-meta-label">No. of Participants</td><td>${v['participant_count'] || ''}</td></tr>
      <tr><td class="a4-meta-label">Department</td><td>${v['department'] || 'All'}</td></tr>
      <tr><td class="a4-meta-label">Targeted Audience</td><td>${v['target_audience'] || 'AIML Club learners'}</td></tr>
      <tr><td class="a4-meta-label">Speakers</td><td>${speakerLines}</td></tr>
    </table>

    <div class="a4-section">
      <div class="a4-section-heading">Introduction</div>
      <div class="a4-narrative" contenteditable="true" data-preview-key="introduction"
           oninput="syncPreviewToEditor('introduction', this)">${intro}</div>
    </div>

    <div class="a4-section">
      <div class="a4-section-heading">Discussion</div>
      <div class="a4-narrative" contenteditable="true" data-preview-key="discussion"
           oninput="syncPreviewToEditor('discussion', this)">${discussion}</div>
    </div>

    <div class="a4-section">
      <div class="a4-section-heading">Conclusion</div>
      <div class="a4-narrative" contenteditable="true" data-preview-key="conclusion"
           oninput="syncPreviewToEditor('conclusion', this)">${conclusion}</div>
    </div>

    <div class="a4-photo-section">
      <div class="a4-section-heading">Photo Gallery</div>
      <div class="a4-photo-grid">
        <div class="a4-photo-slot">
          <div class="a4-photo-placeholder">Photo 1</div>
          <div class="a4-photo-caption">${v['photo_1_caption'] || 'Speakers introducing the concepts of AI&amp;ML to the learners'}</div>
        </div>
        <div class="a4-photo-slot">
          <div class="a4-photo-placeholder">Photo 2</div>
          <div class="a4-photo-caption">${v['photo_2_caption'] || 'Students engaging in the session'}</div>
        </div>
        <div class="a4-photo-slot">
          <div class="a4-photo-placeholder">Photo 3</div>
          <div class="a4-photo-caption">${v['photo_3_caption'] || 'Speaker solving doubts of students'}</div>
        </div>
        <div class="a4-photo-slot">
          <div class="a4-photo-placeholder">Photo 4</div>
          <div class="a4-photo-caption">${v['photo_4_caption'] || 'Winner of Mentimeter quiz competition'}</div>
        </div>
      </div>
    </div>

    <div class="a4-sign-row">
      <div class="a4-sign-col">Club Coordinator<br/><span class="a4-sign-line"></span></div>
      <div class="a4-sign-col">Faculty In-charge<br/><span class="a4-sign-line"></span></div>
      <div class="a4-sign-col">HOD<br/><span class="a4-sign-line"></span></div>
    </div>
  `;
}

function renderNoticePreview(v, container) {
  const speakers = v['speakers'] || '';
  const speakerLines = speakers.split(',').map(s => `<li>${s.trim()}</li>`).join('');

  container.innerHTML = `
    <div class="a4-header">
      <div class="a4-college-name">A P SHAH INSTITUTE OF TECHNOLOGY</div>
      <div class="a4-dept">AIML CLUB</div>
      <div class="a4-doc-type">NOTICE</div>
    </div>

    <div class="a4-notice-meta">
      <span>Academic Year: ${v['academic_year'] || ''}</span>
      <span>Date: ${v['notice_date'] || ''}</span>
    </div>

    <div class="a4-notice-body">
      <p>All AIML Club Learners are hereby informed that a session on
      <strong>${v['session_title'] || '{{ Session Title }}'}</strong>
      will be conducted on <strong>${v['event_date'] || ''}</strong>
      from <strong>${v['event_time'] || ''}</strong> in
      <strong>${v['venue'] || ''}</strong> by:</p>
      <ul class="a4-speaker-list">${speakerLines}</ul>
      <p>All interested students are encouraged to attend.</p>
    </div>

    <div class="a4-sign-row" style="margin-top:48px">
      <div class="a4-sign-col">Club Coordinator<br/><span class="a4-sign-line"></span></div>
      <div class="a4-sign-col">Faculty In-charge<br/><span class="a4-sign-line"></span></div>
      <div class="a4-sign-col">HOD<br/><span class="a4-sign-line"></span></div>
    </div>
  `;
}

// Sync edits made directly on the A4 preview back to the left editor
function syncPreviewToEditor(key, previewEl) {
  const leftEditor = document.getElementById(`editor-${key}`);
  if (leftEditor) leftEditor.innerHTML = previewEl.innerHTML;
}

// ── Rich-Text Toolbar ─────────────────────────────────────
function formatDoc(cmd) {
  document.execCommand(cmd, false, null);
}

// ── AI Reframing ──────────────────────────────────────────
async function reframeSection(sectionKey, instruction) {
  const editor = document.getElementById(`editor-${sectionKey}`);
  if (!editor) return;

  const currentText = htmlToMd(editor.innerHTML);
  const chips = document.querySelector(`.preset-chips[data-target="${sectionKey}"]`);
  if (chips) chips.classList.add('loading');

  const oldHtml = editor.innerHTML;
  editor.innerHTML = `<em>⚡ Reframing with: "${instruction}"...</em>`;

  try {
    const result = await api(`/api/sessions/${sessionId}/reframe`, 'POST', {
      section: sectionKey,
      instruction,
      current_text: currentText,
    });
    editor.innerHTML = mdToHtml(result.reframed_text || currentText);
    renderA4Preview();
  } catch (err) {
    editor.innerHTML = oldHtml;
    showError('step3-error', `Reframing failed: ${err.message}`);
  } finally {
    if (chips) chips.classList.remove('loading');
  }
}

function applyCustomReframe(sectionKey) {
  const input = document.getElementById(`prompt-${sectionKey}`);
  if (!input || !input.value.trim()) return;
  reframeSection(sectionKey, input.value.trim());
  input.value = '';
}

// ── Confirm & Generate ────────────────────────────────────
async function confirmAndGenerate() {
  hideError('step3-error');

  try {
    const answers = [];

    // Collect metadata edits
    document.querySelectorAll('#preview-body td[contenteditable]').forEach(td => {
      answers.push({ key: td.dataset.key, value: td.textContent.trim() });
    });

    // Collect narrative edits
    if (templateId === 'report') {
      ['introduction', 'discussion', 'conclusion'].forEach(key => {
        const ed = document.getElementById(`editor-${key}`);
        if (ed) answers.push({ key, value: htmlToMd(ed.innerHTML) });
      });
    }

    await api(`/api/fields/${sessionId}/answers?template_id=${templateId}`, 'POST', { answers });
    await api(`/api/fields/${sessionId}/confirm`, 'POST');

    showStep(4);
    await startGeneration();
  } catch (err) {
    showError('step3-error', err.message);
  }
}

// ── Step 4: Generation & Polling ─────────────────────────
async function startGeneration() {
  hideError('step4-error');
  const container = document.getElementById('job-status');
  container.innerHTML = `
    <div class="status-row">
      <span>Compiling ${templateId.toUpperCase()} document with native formatting...</span>
      <span class="status-badge running">RUNNING</span>
    </div>
  `;

  try {
    const job = await api(`/api/generate/${sessionId}/${templateId}`, 'POST');
    if (!job || !job.id) throw new Error('Could not start document compilation job.');
    pollTimer = setInterval(() => pollJobStatus(job.id), 1200);
  } catch (err) {
    showError('step4-error', err.message);
  }
}

async function pollJobStatus(jobId) {
  try {
    const job = await api(`/api/generate/status/${jobId}`);
    const container = document.getElementById('job-status');

    if (job.status === 'done') {
      clearInterval(pollTimer);
      container.innerHTML = `
        <div class="status-row">
          <span>${templateId.charAt(0).toUpperCase() + templateId.slice(1)} Document Ready</span>
          <span class="status-badge done">DONE</span>
        </div>
        <div style="margin-top:20px;text-align:center">
          <a href="/api/download/${jobId}" download
             style="display:inline-block;padding:14px 32px;background:#16a34a;color:#fff;
                    border-radius:10px;text-decoration:none;font-size:15px;font-weight:600;
                    box-shadow:0 2px 6px rgba(22,163,74,0.3)">
            ⬇ Download ${templateId.charAt(0).toUpperCase() + templateId.slice(1)}.docx
          </a>
        </div>
      `;
      loadHistory();
    } else if (job.status === 'failed') {
      clearInterval(pollTimer);
      container.innerHTML = `
        <div class="status-row">
          <span>Generation Failed</span>
          <span class="status-badge failed">FAILED</span>
        </div>
      `;
      showError('step4-error', `Error: ${job.error || 'Unknown error'}`);
    }
  } catch (err) {
    clearInterval(pollTimer);
    showError('step4-error', err.message);
  }
}

// ── Sidebar History ───────────────────────────────────────
async function loadHistory() {
  try {
    const sessions = await api('/api/sessions');
    const list = document.getElementById('history-list');
    list.innerHTML = sessions.map(s => {
      const date = new Date(s.created_at).toLocaleDateString('en-IN', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
      });
      const title = (s.event_title && s.event_title !== 'Untitled')
        ? s.event_title.slice(0, 26)
        : 'Session';
      return `<li onclick="restoreSession('${s.id}')" title="${s.event_title || ''}">
        <span class="hist-title">${title}</span>
        <span class="hist-date">${date}</span>
      </li>`;
    }).join('');
  } catch (_) {}
}

function restoreSession(id) {
  sessionId      = id;
  hadMissingStep = false;
  loadReviewStep().then(() => showStep(3));
}

// ── Init ──────────────────────────────────────────────────
loadHistory();
