/* ============================================================
   MAIN UTILITIES
   ============================================================ */

// Build fallback data paths so files resolve in GitHub Pages and Render URLs
function getDataPathCandidates(path) {
  const candidates = [];
  const seen = new Set();

  function pushCandidate(candidate) {
    if (!candidate || seen.has(candidate)) return;
    seen.add(candidate);
    candidates.push(candidate);
  }

  pushCandidate(path);

  if (!/^\.?\//.test(path)) {
    pushCandidate('./' + path);
  }

  if (path.startsWith('data/')) {
    const pathname = window.location.pathname || '';
    if (pathname.includes('/dashboard/')) {
      const base = pathname.split('/dashboard/')[0] || '';
      pushCandidate(base + '/dashboard/' + path);
    } else {
      pushCandidate('/dashboard/' + path);
    }
  }

  return candidates;
}

// Generate timestamp
function getLastUpdated() {
  const now = new Date();
  return now.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// Format numbers for display
function formatCurrency(value) {
  if (Math.abs(value) >= 1e9) {
    return '$' + (value / 1e9).toFixed(2) + 'B';
  }
  if (Math.abs(value) >= 1e6) {
    return '$' + (value / 1e6).toFixed(2) + 'M';
  }
  if (Math.abs(value) >= 1e3) {
    return '$' + (value / 1e3).toFixed(1) + 'K';
  }
  return '$' + value.toFixed(2);
}

function formatPercent(value, decimals = 2) {
  return (value * 100).toFixed(decimals) + '%';
}

function formatNumber(value, decimals = 0) {
  return value.toLocaleString('en-US', { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
}

function formatBasisPoints(value) {
  return (value * 10000).toFixed(0) + ' bps';
}

// Fetch JSON data
async function loadJSON(path) {
  const candidates = getDataPathCandidates(path);
  let lastError = null;

  for (const candidate of candidates) {
    try {
      const response = await fetch(candidate);
      if (!response.ok) {
        lastError = new Error(`HTTP ${response.status}: ${candidate}`);
        continue;
      }
      return await response.json();
    } catch (error) {
      lastError = error;
    }
  }

  console.error('Error loading JSON:', path, lastError);
  return null;
}

// Fetch CSV data and parse
async function loadCSV(path) {
  const candidates = getDataPathCandidates(path);
  let lastError = null;

  for (const candidate of candidates) {
    try {
      const response = await fetch(candidate);
      if (!response.ok) {
        lastError = new Error(`HTTP ${response.status}: ${candidate}`);
        continue;
      }
      const text = await response.text();
      return parseCSV(text);
    } catch (error) {
      lastError = error;
    }
  }

  console.error('Error loading CSV:', path, lastError);
  return [];
}

// Simple CSV parser
function parseCSV(text) {
  const lines = text.split('\n').filter(line => line.trim());
  if (lines.length < 1) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  const data = [];

  for (let i = 1; i < lines.length; i++) {
    const obj = {};
    const values = lines[i].split(',').map(v => v.trim());
    headers.forEach((header, idx) => {
      const val = values[idx];
      // Try to parse as number
      obj[header] = isNaN(val) ? val : parseFloat(val);
    });
    data.push(obj);
  }

  return data;
}

// Set up navigation active state
function setActiveNav(pageName) {
  document.querySelectorAll('.navbar-menu a').forEach(link => {
    link.classList.remove('active');
  });

  const active = document.querySelector(`.navbar-menu a[data-page="${pageName}"]`);
  if (active) {
    active.classList.add('active');
  }
}

// Get risk color for value
function getRiskColor(rate) {
  if (rate <= 0.06) return '#f1c40f'; // yellow
  if (rate <= 0.13) return '#f39c12'; // orange
  if (rate <= 0.22) return '#e67e22'; // darker orange
  if (rate <= 0.30) return '#e74c3c'; // red
  if (rate <= 0.38) return '#e63946'; // deep red
  if (rate <= 0.45) return '#d02d26'; // darker red
  return '#8e44ad'; // purple
}

// Get grade letter for rate
function getGradeLetter(rate) {
  if (rate <= 0.06) return 'A';
  if (rate <= 0.13) return 'B';
  if (rate <= 0.22) return 'C';
  if (rate <= 0.30) return 'D';
  if (rate <= 0.38) return 'E';
  if (rate <= 0.45) return 'F';
  return 'G';
}

// Risk level classification
function getRiskLevel(rate) {
  if (rate <= 0.06) return 'low';
  if (rate <= 0.15) return 'moderate';
  if (rate <= 0.30) return 'elevated';
  return 'high';
}

// Apply dark mode defaults to all future Chart.js instances
function applyDarkChartDefaults() {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = '#7c8494';
  Chart.defaults.borderColor = '#30363d';
  if (Chart.defaults.scale) {
    Chart.defaults.scale.grid = Chart.defaults.scale.grid || {};
    Chart.defaults.scale.grid.color = 'rgba(255,255,255,0.06)';
  }
}

// Initialize page (called from each HTML page)
function initPage(pageName) {
  setActiveNav(pageName);
  const timestampEl = document.querySelector('.navbar-timestamp');
  if (timestampEl) {
    timestampEl.textContent = 'Updated: ' + getLastUpdated();
  }
  applyDarkChartDefaults();
}

// Initialize timestamp immediately so pages never remain at placeholder values.
document.addEventListener('DOMContentLoaded', () => {
  const timestampEl = document.querySelector('.navbar-timestamp');
  if (timestampEl) {
    timestampEl.textContent = 'Updated: ' + getLastUpdated();
  }
});

// Console banner
console.log('%cLending Risk Intelligence Dashboard', 'font-size: 16px; font-weight: bold; color: #34495e;');
console.log('%cDesigned for shareholder navigation', 'color: #7f8c8d; font-style: italic;');
