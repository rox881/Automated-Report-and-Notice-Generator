// ── State ─────────────────────────────────────────────────
let sessionId    = null;
let templateId   = null;
let noticeJobId  = null;
let reportJobId  = null;

// ── Helpers ───────────────────────────────────────────────
const api = (path, method = 'GET', body = null) => {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  return fetch(path, opts).then(r => r.json());
};

const showStep = (n) => {
  document.querySelectorAll('.step').forEach(s => s.classList.add('hidden'));
  document.getElementById(`step-${n}`).classList.remove('hidden');
};

const showError = (id, msg) => {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.remove('hidden');
};

const hideError = (id) => document.getElementById(id).classList.add('hidden');

// ── Step 0: New Session ────────────────────────────────────
function newSession() {
  sessionId = null; templateId = null;
  noticeJobId = null; reportJobId = null;
  document.getElementById('context-input').value = '';
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
  document.getElementById('job-status').innerHTML = '';
  document.getElementById('btn-report').disabled = true;
  showStep(1);
}

// ── Step 1: Template selection ─────────────────────────────
async function selectTemplate(tpl) {
  const context = document.getElementById('context-input').value.trim();
  if (!context) return showError('step1-error', 'Please paste some context text first.');
  hideError('step1-error');

  document.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
  document.querySelector(`.pill.${tpl}`).classList.add('selected');
  templateId = tpl;

  // Create session
  const session = await api('/api/sessions', 'POST', { context });
  sessionId = session.id;

  // Run extraction
  const result = await api(`/api/sessions/${sessionId}/extract?template_id=${templateId}`, 'POST');

  if (result.status === 'needs_input') {
    renderMissingForm(result.missing);
    showStep(2);
  } else {
    await loadPreview();
    showStep(3);
  }
}

// ── Step 2: Missing fields form ────────────────────────────
function renderMissingForm(missing) {
  const form = document.getElementById('missing-form');
  form.innerHTML = missing.map(f => `
    <div class="field-row">
      <label for="field-${f.key}">${f.label}</label>
      <input id="field-${f.key}" data-key="${f.key}" type="text" placeholder="Enter ${f.label.toLowerCase()}..." />
    </div>
  `).join('');
}

async function submitAnswers() {
  hideError('step2-error');
  const inputs = document.querySelectorAll('#missing-form input');
  const answers = Array.from(inputs).map(i => ({ key: i.dataset.key, value: i.value.trim() }));
  const empty = answers.filter(a => !a.value);
  if (empty.length) return showError('step2-error', `Please fill in: ${empty.map(a => a.key).join(', ')}`);

  const result = await api(`/api/fields/${sessionId}/answers?template_id=${templateId}`, 'POST', { answers });

  if (result.still_missing && result.still_missing.length) {
    return showError('step2-error', `Still missing: ${result.still_missing.join(', ')}`);
  }

  await loadPreview();
  showStep(3);
}

// ── Step 3: Preview & confirm ──────────────────────────────
async function loadPreview() {
  const fields = await api(`/api/sessions/${sessionId}/preview?template_id=${templateId}`);
  const tbody  = document.getElementById('preview-body');
  tbody.innerHTML = fields.map(f => `
    <tr>
      <td><strong>${f.label}</strong></td>
      <td contenteditable="true" data-key="${f.key}">${Array.isArray(f.value) ? f.value.join(', ') : (f.value ?? '')}</td>
      <td><span class="badge-${f.source}">${f.source.toUpperCase()}</span></td>
    </tr>
  `).join('');
}

async function confirmSession() {
  hideError('step3-error');

  // Collect any inline edits
  const editedCells = document.querySelectorAll('#preview-body td[contenteditable]');
  const edits = Array.from(editedCells).map(td => ({
    key: td.dataset.key,
    value: td.textContent.trim()
  }));
  if (edits.length) {
    await api(`/api/fields/${sessionId}/answers?template_id=${templateId}`, 'POST', { answers: edits });
  }

  await api(`/api/fields/${sessionId}/confirm`, 'POST');
  showStep(4);
}

// ── Step 4: Generate & download ────────────────────────────
async function generate(tpl) {
  const btn = tpl === 'notice'
    ? document.getElementById('btn-notice')
    : document.getElementById('btn-report');

  btn.disabled = true;
  btn.textContent = `⏳ Generating ${tpl}...`;

  const job = await api(`/api/generate/${sessionId}/${tpl}`, 'POST');
  const jobId = job.id;

  if (tpl === 'notice') noticeJobId = jobId;
  else reportJobId = jobId;

  pollJob(jobId, tpl, btn);
}

function pollJob(jobId, tpl, btn) {
  const interval = setInterval(async () => {
    const job = await api(`/api/generate/status/${jobId}`);
    updateJobStatus(tpl, job);

    if (job.status === 'done') {
      clearInterval(interval);
      btn.textContent = `✅ ${tpl.charAt(0).toUpperCase() + tpl.slice(1)} Done`;
      addDownloadLink(jobId, tpl);

      // Unlock Report button after Notice is done
      if (tpl === 'notice') {
        document.getElementById('btn-report').disabled = false;
      }
      loadHistory();
    } else if (job.status === 'failed') {
      clearInterval(interval);
      btn.textContent = `❌ ${tpl} Failed`;
      btn.disabled = false;
    }
  }, 1500);
}

function updateJobStatus(tpl, job) {
  const container = document.getElementById('job-status');
  const existingRow = document.getElementById(`status-${tpl}`);
  const badge = `<span class="status-badge ${job.status}">${job.status.toUpperCase()}</span>`;
  const html = `<div class="status-row" id="status-${tpl}"><span>${tpl.charAt(0).toUpperCase() + tpl.slice(1)} Template</span>${badge}</div>`;
  if (existingRow) existingRow.outerHTML = html;
  else container.insertAdjacentHTML('beforeend', html);
}

function addDownloadLink(jobId, tpl) {
  const container = document.getElementById('job-status');
  container.insertAdjacentHTML('beforeend', `
    <a href="/api/download/${jobId}" download
       style="display:inline-block;margin-top:4px;padding:10px 20px;background:#111827;color:#fff;border-radius:8px;text-decoration:none;font-size:14px;">
      ⬇ Download ${tpl.charAt(0).toUpperCase() + tpl.slice(1)}.docx
    </a>
  `);
}

// ── Sidebar History ────────────────────────────────────────
async function loadHistory() {
  const sessions = await api('/api/sessions');
  const list = document.getElementById('history-list');
  list.innerHTML = sessions.map(s => {
    const date = new Date(s.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
    return `<li onclick="restoreSession('${s.id}')" title="${s.id}">Session – ${date}</li>`;
  }).join('');
}

function restoreSession(id) {
  sessionId = id;
  // Reload preview for last used template (or prompt user to select one)
  showStep(4);
}

// ── Init ───────────────────────────────────────────────────
loadHistory();
