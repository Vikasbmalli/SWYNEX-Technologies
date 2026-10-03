const dashboard = document.getElementById('dashboard');
const sensitivitySlider = document.getElementById('sensitivity');
const sensitivityValue = document.getElementById('sensitivityValue');
const fileInput = document.getElementById('fileInput');
const sampleBtn = document.getElementById('sampleBtn');
const fileNameLabel = document.getElementById('fileNameLabel');

const errorModal = document.getElementById('errorModal');
const errorMessage = document.getElementById('errorMessage');
const historyModal = document.getElementById('historyModal');

let chart = null;
let currentFile = null; // File object or null (=> sample)

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => (t.hidden = true), 2600);
}

function openModal(el) { el.hidden = false; el.style.display = 'flex'; }
function closeModal(el) { el.hidden = true; el.style.display = 'none'; }

document.getElementById('errorClose').addEventListener('click', () => closeModal(errorModal));
document.getElementById('historyClose').addEventListener('click', () => closeModal(historyModal));
document.getElementById('errorCloseBottom').addEventListener('click', () => closeModal(errorModal));
document.getElementById('historyCloseBottom').addEventListener('click', () => closeModal(historyModal));
[errorModal, historyModal].forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m); }));

sensitivitySlider.addEventListener('input', () => {
  sensitivityValue.textContent = parseFloat(sensitivitySlider.value).toFixed(2);
});

sensitivitySlider.addEventListener('change', () => runAnalysis());

sampleBtn.addEventListener('click', () => {
  currentFile = null;
  fileNameLabel.textContent = 'sample_bills.csv';
  runAnalysis();
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) {
    currentFile = fileInput.files[0];
    fileNameLabel.textContent = currentFile.name;
    runAnalysis();
  }
});

function animateCount(el, target, suffix = '') {
  const isFloat = target % 1 !== 0;
  const start = 0;
  const duration = 700;
  const t0 = performance.now();
  function frame(now) {
    const p = Math.min(1, (now - t0) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = start + (target - start) * eased;
    el.firstChild.textContent = isFloat ? val.toFixed(1) : Math.round(val).toLocaleString();
    if (p < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function setDial(monthsAnalyzed, anomalies) {
  const clean = Math.max(0, monthsAnalyzed - anomalies);
  const dialValue = document.getElementById('dialValue');
  const dialFill = document.getElementById('dialFill');
  const ratio = monthsAnalyzed ? clean / monthsAnalyzed : 0;
  const circumference = 616;
  dialFill.style.strokeDashoffset = circumference - circumference * ratio;
  dialFill.style.stroke = ratio > 0.85 ? 'var(--cyan)' : ratio > 0.6 ? 'var(--amber)' : 'var(--red)';
  dialValue.textContent = `${clean}/${monthsAnalyzed}`;
}

function renderChart(series) {
  const ctx = document.getElementById('usageChart').getContext('2d');
  const pointColors = series.is_anomaly.map(a => a ? '#FF6B6B' : 'rgba(52,224,216,0.9)');
  const pointRadii = series.is_anomaly.map(a => a ? 6 : 2.5);

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: series.months,
      datasets: [{
        label: 'Usage (kWh)',
        data: series.usage,
        borderColor: '#34E0D8',
        borderWidth: 2,
        pointBackgroundColor: pointColors,
        pointBorderColor: '#0A0E1A',
        pointBorderWidth: 1.5,
        pointRadius: pointRadii,
        pointHoverRadius: 7,
        tension: 0.3,
        fill: {
          target: 'origin',
          above: 'rgba(52,224,216,0.06)',
        },
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8B96B8', font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#8B96B8', font: { family: 'JetBrains Mono', size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      },
    },
  });
}

function renderFlagged(flagged) {
  const list = document.getElementById('flaggedList');
  const empty = document.getElementById('noAnomalies');
  list.innerHTML = '';
  if (!flagged.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  flagged.forEach((f, i) => {
    const row = document.createElement('div');
    row.className = 'flagged-row';
    row.style.animationDelay = `${i * 45}ms`;
    row.innerHTML = `
      <span class="flagged-month">${f.month}</span>
      <span class="flagged-usage">${f.usage_kwh} kWh</span>
      <span class="flagged-bill">$${f.bill_amount.toFixed(2)}</span>
      <span class="severity-chip severity-${f.severity}">${f.severity}</span>
      <span class="flagged-reason">${f.reason}</span>`;
    list.appendChild(row);
  });
}

async function runAnalysis() {
  const sensitivity = sensitivitySlider.value;
  const formData = new FormData();
  formData.append('sensitivity', sensitivity);
  if (currentFile) formData.append('file', currentFile);

  sampleBtn.disabled = true;
  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (!data.ok) {
      errorMessage.textContent = data.error;
      openModal(errorModal);
      return;
    }

    dashboard.hidden = false;
    dashboard.style.animation = 'none';
    void dashboard.offsetWidth;
    dashboard.style.animation = '';

    animateCount(document.getElementById('statMonths'), data.months_analyzed);
    animateCount(document.getElementById('statAnomalies'), data.anomalies_found);
    document.getElementById('statAvg').innerHTML = `${Math.round(data.avg_usage)} <span class="unit">kWh</span>`;
    document.getElementById('statMax').textContent = `$${data.max_bill.toFixed(2)}`;
    setDial(data.months_analyzed, data.anomalies_found);
    renderChart(data.series);
    renderFlagged(data.flagged);

    if (data.warnings.length) showToast(data.warnings[0]);
    dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    errorMessage.textContent = 'Could not reach the server. Is app.py running?';
    openModal(errorModal);
  } finally {
    sampleBtn.disabled = false;
  }
}

document.getElementById('historyBtn').addEventListener('click', async () => {
  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    document.getElementById('historySummary').textContent =
      `${data.summary.total_runs} run(s) so far, ${data.summary.total_anomalies} anomalies found in total.`;
    const list = document.getElementById('historyList');
    list.innerHTML = '';
    if (!data.runs.length) {
      list.innerHTML = '<p class="empty-state">No runs yet — analyze some data first.</p>';
    } else {
      data.runs.forEach(r => {
        const row = document.createElement('div');
        row.className = 'history-row';
        const date = new Date(r.created_at * 1000).toLocaleString();
        row.innerHTML = `
          <span class="h-file">${r.filename}</span>
          <span class="h-meta">${r.anomalies_found}/${r.months_analyzed} flagged · sens ${r.sensitivity.toFixed(2)} · ${date}</span>`;
        list.appendChild(row);
      });
    }
    openModal(historyModal);
  } catch (err) {
    showToast('Could not load history.');
  }
});

// Run once on load with the sample data so the page never opens empty-handed.
window.addEventListener('DOMContentLoaded', () => {
  runAnalysis();
});
