// ── State ─────────────────────────────────────────────────
let sessionId      = null;
let templateId     = null;
let pollTimers     = {};
let reportSetupMode = false;   // true when going through Steps 2/3 for the Report

// ── Helpers ───────────────────────────────────────────────
const api = async (path, method = 'GET', body = null) => {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail || `Server error: ${res.status}`);
  return data;
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

// ── Step 0: New Session ─────────────────────────────────
function newSession() {
  sessionId       = null;
  templateId      = null;
  reportSetupMode = false;
  Object.values(pollTimers).forEach(clearInterval);
  pollTimers = {};
  document.getElementById('context-input').value = '';
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
  document.getElementById('job-status').innerHTML = '';
  document.getElementById('btn-report').disabled  = true;
  document.getElementById('btn-report').textContent = '📊 Generate Report';
  showStep(1);
}

// ── Step 1: Select Template → Extract Notice ───────────
async function selectTemplate(tpl) {
  const context = document.getElementById('context-input').value.trim();
  if (!context) return showError('step1-error', 'Please paste some context text first.');
  hideError('step1-error');

  document.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
  document.querySelector(`.pill.${tpl}`).classList.add('selected');
  templateId      = tpl;
  reportSetupMode = false;

  // Update step titles for Notice
  document.getElementById('step2-title').textContent = `Fill in Missing ${tpl === 'notice' ? 'Notice' : 'Report'} Fields`;
  document.getElementById('step3-title').textContent = `Review ${tpl === 'notice' ? 'Notice' : 'Report'} Fields`;

  try {
    if (!sessionId) {
      const session = await api('/api/sessions', 'POST', { context });
      sessionId = session.id;
    }

    const result = await api(
      `/api/sessions/${sessionId}/extract?template_id=${templateId}`, 'POST'
    );

    const missingRequired = (result.missing || []).filter(m => m.required);
    if (missingRequired.length > 0) {
      renderMissingForm(result.missing);
      showStep(2);
    } else if ((result.missing || []).length > 0) {
      // Optional fields missing only — show them but allow skipping
      renderMissingForm(result.missing);
      showStep(2);
    } else {
      await loadPreview();
      showStep(3);
    }
    loadHistory();
  } catch (err) {
    showError('step1-error', err.message);
  }
}

// ── Report Setup: Extract Report → Steps 2 / 3 → Generate
async function setupReport() {
  templateId      = 'report';
  reportSetupMode = true;

  document.getElementById('step2-title').textContent = 'Fill in Missing Report Fields';
  document.getElementById('step3-title').textContent = 'Review Report Fields';
  hideError('step4-error');

  try {
    const result = await api(
      `/api/sessions/${sessionId}/extract?template_id=report`, 'POST'
    );

    const missingRequired = (result.missing || []).filter(m => m.required);
    if (missingRequired.length > 0) {
      renderMissingForm(result.missing);
      showStep(2);
    } else if ((result.missing || []).length > 0) {
      renderMissingForm(result.missing);
      showStep(2);
    } else {
      await loadPreview();
      showStep(3);
    }
  } catch (err) {
    showError('step4-error', err.message);
  }
}

// ── Step 2: Missing Fields Form ────────────────────────
function renderMissingForm(missing) {
  const form = document.getElementById('missing-form');
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
      `Please fill required fields: ${emptyRequired.map(a => a.key).join(', ')}`
    );
  }

  try {
    const result = await api(
      `/api/fields/${sessionId}/answers?template_id=${templateId}`,
      'POST',
      { answers: answers.map(a => ({ key: a.key, value: a.value })) }
    );

    if (result.still_missing && result.still_missing.length) {
      return showError('step2-error', `Still required: ${result.still_missing.join(', ')}`);
    }

    await loadPreview();
    showStep(3);
  } catch (err) {
    showError('step2-error', err.message);
  }
}

// ── Step 3: Preview ────────────────────────────────────
async function loadPreview() {
  const fields = await api(`/api/sessions/${sessionId}/preview?template_id=${templateId}`);
  const tbody  = document.getElementById('preview-body');
  tbody.innerHTML = fields.map(f => {
    const display = Array.isArray(f.value)
      ? f.value.join(', ')
      : (f.value ?? '');
    const reqMark = f.required ? '<span style="color:#dc2626">*</span> ' : '';
    return `
      <tr>
        <td>${reqMark}<strong>${f.label}</strong></td>
        <td contenteditable="true" data-key="${f.key}">${display}</td>
        <td><span class="badge-${f.source}">${f.source.toUpperCase()}</span></td>
      </tr>
    `;
  }).join('');
}

// ── Step 3: Confirm — handles both Notice and Report paths
async function confirmAndProceed() {
  hideError('step3-error');
  try {
    // Push inline edits
    const editedCells = document.querySelectorAll('#preview-body td[contenteditable]');
    const edits = Array.from(editedCells)
      .map(td => ({ key: td.dataset.key, value: td.textContent.trim() }))
      .filter(e => e.value !== '');

    if (edits.length) {
      await api(
        `/api/fields/${sessionId}/answers?template_id=${templateId}`,
        'POST', { answers: edits }
      );
    }

    if (reportSetupMode) {
      // Report path: session is already confirmed from notice step.
      // Just go back to Step 4 and kick off report generation.
      reportSetupMode = false;
      showStep(4);
      generate('report');
    } else {
      // Notice path: confirm session, then go to Step 4
      await api(`/api/fields/${sessionId}/confirm`, 'POST');
      showStep(4);
    }
  } catch (err) {
    showError('step3-error', err.message);
  }
}

// ── Step 4: Generate & Download ────────────────────────
async function generate(tpl) {
  const btnId = tpl === 'notice' ? 'btn-notice' : 'btn-report';
  const btn   = document.getElementById(btnId);
  btn.disabled    = true;
  btn.textContent = `⏳ Generating ${tpl}...`;
  hideError('step4-error');

  try {
    const job = await api(`/api/generate/${sessionId}/${tpl}`, 'POST');
    if (!job || !job.id) throw new Error('Server did not return a valid job. Try again.');
    pollTimers[tpl] = setInterval(() => pollJob(job.id, tpl, btn), 1500);
  } catch (err) {
    btn.disabled    = false;
    btn.textContent = tpl === 'notice' ? '📄 Generate Notice' : '📊 Generate Report';
    showError('step4-error', err.message);
  }
}

async function pollJob(jobId, tpl, btn) {
  try {
    const job = await api(`/api/generate/status/${jobId}`);
    updateJobStatus(tpl, job);

    if (job.status === 'done') {
      clearInterval(pollTimers[tpl]);
      btn.textContent = `✅ ${tpl.charAt(0).toUpperCase() + tpl.slice(1)} Done`;
      addDownloadLink(jobId, tpl);

      // After Notice is done, unlock the Report setup button
      if (tpl === 'notice') {
        const reportBtn = document.getElementById('btn-report');
        reportBtn.disabled    = false;
        reportBtn.textContent = '📊 Setup & Generate Report';
      }
      loadHistory();
    } else if (job.status === 'failed') {
      clearInterval(pollTimers[tpl]);
      btn.disabled    = false;
      btn.textContent = `❌ ${tpl} Failed — Retry`;
      showError('step4-error', `Generation failed: ${job.error || 'Unknown error'}`);
    }
  } catch (err) {
    clearInterval(pollTimers[tpl]);
    btn.disabled    = false;
    btn.textContent = `❌ Error — Retry`;
    showError('step4-error', err.message);
  }
}

function updateJobStatus(tpl, job) {
  const container   = document.getElementById('job-status');
  const existingRow = document.getElementById(`status-${tpl}`);
  const badge = `<span class="status-badge ${job.status}">${job.status.toUpperCase()}</span>`;
  const html  = `<div class="status-row" id="status-${tpl}">
    <span>${tpl.charAt(0).toUpperCase() + tpl.slice(1)} Template</span>${badge}
  </div>`;
  if (existingRow) existingRow.outerHTML = html;
  else container.insertAdjacentHTML('beforeend', html);
}

function addDownloadLink(jobId, tpl) {
  const container = document.getElementById('job-status');
  container.insertAdjacentHTML('beforeend', `
    <a href="/api/download/${jobId}" download
       style="display:inline-block;margin-top:6px;padding:10px 20px;
              background:#111827;color:#fff;border-radius:8px;
              text-decoration:none;font-size:14px;">
      ⬇ Download ${tpl.charAt(0).toUpperCase() + tpl.slice(1)}.docx
    </a>
  `);
}

// ── Sidebar History ────────────────────────────────────
async function loadHistory() {
  try {
    const sessions = await api('/api/sessions');
    const list = document.getElementById('history-list');
    list.innerHTML = sessions.map(s => {
      const date  = new Date(s.created_at).toLocaleDateString('en-IN', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
      });
      const title = (s.event_title && s.event_title !== 'Untitled')
        ? s.event_title.slice(0, 28)
        : 'New Session';
      return `<li onclick="restoreSession('${s.id}')" title="${s.event_title}">
        <span class="hist-title">${title}</span>
        <span class="hist-date">${date}</span>
      </li>`;
    }).join('');
  } catch (_) { /* Silently skip */ }
}

function restoreSession(id) {
  sessionId = id;
  showStep(4);
}

// ── Init ──────────────────────────────────────────────
loadHistory();
