const REFRESH_MS = 30_000;

const headlineStatusEl = document.getElementById('headline-status');
const headlineSubtextEl = document.getElementById('headline-subtext');
  const vehicleCountsEl = document.getElementById('vehicle-counts');
  const vehicleRefreshEl = document.getElementById('vehicle-refresh');

  // Update labels to reflect departure events, not vehicles
  const vehicleLabel = document.querySelector('.vehicle-count-label');
  if (vehicleLabel) {
    vehicleLabel.textContent = 'Active Departures';
  }
const disruptionCountEl = document.getElementById('disruption-count');
const disruptionSummaryEl = document.getElementById('disruption-summary');
const heartbeatStatusEl = document.getElementById('heartbeat-status');
const heartbeatUpdatedEl = document.getElementById('heartbeat-updated');
const lineGridEl = document.getElementById('line-grid');
const delayTableBodyEl = document.querySelector('#delay-table tbody');
const disruptionTickerEl = document.getElementById('disruption-ticker');
const gtfsRefreshEl = document.getElementById('status-gtfs-refresh');

const TYPE_LABELS = {
  metro: 'Metro',
  tram: 'Tram',
  bus: 'Bus',
  nightbus: 'Night Bus',
  unknown: 'Other',
};

async function fetchJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function renderHeadline(summary) {
  const disruptionCount = summary?.disruptions?.active ?? 0;
  const departuresTotal = summary?.vehicles?.vehicles_total ?? 0;
  const delayed = summary?.vehicles?.delayed?.length ?? 0;

  let statusText = 'Good Service';
  let statusClass = 'pill--ok';

  if (disruptionCount >= 3 || delayed > 10) {
    statusText = 'Major Disruptions';
    statusClass = 'pill--warning';
  } else if (disruptionCount > 0 || delayed > 0) {
    statusText = 'Minor Delays';
    statusClass = 'pill--minor';
  }

  headlineStatusEl.textContent = statusText;
  headlineStatusEl.className = `pill ${statusClass}`;
  headlineSubtextEl.textContent = `${departuresTotal} active departures, ${delayed} reported delays.`;
}

function renderVehicleCounts(summary) {
  vehicleCountsEl.innerHTML = '';
  const perType = summary?.vehicles?.vehicles_per_type ?? {};
  Object.entries(perType)
    .sort(([, a], [, b]) => b - a)
    .forEach(([type, count]) => {
      const label = TYPE_LABELS[type.toLowerCase()] ?? type.toUpperCase();
      const li = document.createElement('li');
      li.textContent = `${label}: ${count}`;
      vehicleCountsEl.appendChild(li);
    });
  if (!vehicleCountsEl.children.length) {
    const li = document.createElement('li');
    li.textContent = 'No live vehicles published.';
    vehicleCountsEl.appendChild(li);
  }
  const generatedAt = summary?.vehicles?.generated_at;
  vehicleRefreshEl.textContent = generatedAt ? `Updated ${new Date(generatedAt).toLocaleTimeString()}` : '';
}

function renderHeartbeat(summary) {
  const heartbeat = summary?.heartbeat;
  if (!heartbeat) {
    heartbeatStatusEl.textContent = 'No heartbeat detected';
    heartbeatStatusEl.className = 'pill pill--warning';
    heartbeatUpdatedEl.textContent = '';
    return;
  }
  const updatedAt = new Date(heartbeat.updated_at || Date.now());
  const ageSeconds = (Date.now() - updatedAt.getTime()) / 1000;
  const healthy = ageSeconds < 900;
  heartbeatStatusEl.textContent = healthy ? 'Loader healthy' : 'Loader stale';
  heartbeatStatusEl.className = `pill ${healthy ? 'pill--ok' : 'pill--warning'}`;
  heartbeatUpdatedEl.textContent = `Updated ${updatedAt.toLocaleTimeString()}`;
}

function renderDisruptionSummary(summary, disruptions) {
  const activeCount = summary?.disruptions?.active ?? 0;
  disruptionCountEl.textContent = `${activeCount} active`;
  const severe = summary?.disruptions?.severe ?? 0;
  disruptionSummaryEl.textContent = severe ? `${severe} major` : 'No major disruptions';

  disruptionTickerEl.innerHTML = '';
  (disruptions?.disruptions ?? []).forEach((item) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${item.line ?? 'Network'}</strong>: ${item.title ?? item.description ?? 'Update'}`;
    disruptionTickerEl.appendChild(li);
  });
  if (!disruptionTickerEl.children.length) {
    const li = document.createElement('li');
    li.textContent = 'Network running smoothly.';
    disruptionTickerEl.appendChild(li);
  }
}

function renderLineGrid(summary) {
  lineGridEl.innerHTML = '';
  const lineDetails = summary?.vehicles?.line_details ?? [];
  lineDetails.slice(0, 24).forEach((line) => {
    const tile = document.createElement('div');
    tile.className = 'line-tile';
    tile.style.background = line.color ?? '#1f2933';
    tile.innerHTML = `
      <span class="line-tile__name">${line.name}</span>
      <span class="line-tile__count">${line.count}</span>
      <span class="line-tile__type">${TYPE_LABELS[line.type?.toLowerCase()] ?? line.type}</span>
    `;
    lineGridEl.appendChild(tile);
  });
  if (!lineGridEl.children.length) {
    const placeholder = document.createElement('p');
    placeholder.className = 'status-placeholder';
    placeholder.textContent = 'No live data available yet.';
    lineGridEl.appendChild(placeholder);
  }
}

function renderDelays(summary) {
  delayTableBodyEl.innerHTML = '';
  const delayed = summary?.vehicles?.delayed ?? [];
  delayed.forEach((entry) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${entry.line ?? 'Unknown'}</td>
      <td>${entry.next_station ?? '—'}</td>
      <td>${entry.delay ?? 0}</td>
      <td>${Number.isFinite(entry.countdown) ? `${entry.countdown} min` : '—'}</td>
    `;
    delayTableBodyEl.appendChild(tr);
  });
  if (!delayTableBodyEl.children.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="4">No reported delays.</td>';
    delayTableBodyEl.appendChild(tr);
  }
}

function renderGtfsRefresh(summary) {
  if (!gtfsRefreshEl) return;
  const ts = summary?.last_gtfs_refresh;
  gtfsRefreshEl.textContent = ts ? new Date(ts).toLocaleString() : 'N/A';
}

async function refreshDashboard() {
  try {
    const [summary, disruptions] = await Promise.all([
      fetchJson('/api/status/summary'),
      fetchJson('/api/disruptions'),
    ]);
    renderHeadline(summary);
    renderVehicleCounts(summary);
    renderHeartbeat(summary);
    renderDisruptionSummary(summary, disruptions);
    renderLineGrid(summary);
    renderDelays(summary);
    renderGtfsRefresh(summary);
  } catch (error) {
    console.error('Failed to refresh status dashboard', error);
    headlineStatusEl.textContent = 'Data unavailable';
    headlineStatusEl.className = 'pill pill--warning';
    vehicleCountsEl.innerHTML = '<li>No data available</li>';
    lineGridEl.innerHTML = '<p>No live data available yet.</p>';
  }
}

refreshDashboard();
setInterval(refreshDashboard, REFRESH_MS);
