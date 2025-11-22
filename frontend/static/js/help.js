const openBtn = document.getElementById('help-button');
let modal = document.getElementById('help-modal');

function ensureModal() {
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'help-modal';
    modal.className = 'modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'help-title');
    modal.innerHTML = `
      <div class="modal__dialog">
        <header class="modal__header">
          <h2 id="help-title">About Wiener Linien & This App</h2>
          <button id="help-close" class="modal__close" aria-label="Close">×</button>
        </header>
        <div class="modal__content">
          <section>
            <h3>Overview</h3>
            <p>Wiener Linien operates Vienna’s public transport network—metro, tram, and bus—with very high ridership. Real‑time operations compare the GTFS timetable with live telemetry to power countdowns and disruption info.</p>
          </section>
          <section>
            <h3>History (brief)</h3>
            <ul>
              <li>1865–1900s: Trams established; electrification</li>
              <li>1970s–present: U‑Bahn expansions, integrated ticketing</li>
              <li>2010s–2020s: Modernization, open data APIs, accessibility</li>
            </ul>
          </section>
          <section>
            <h3>Economics & Impact</h3>
            <ul>
              <li>Strong farebox recovery supported by high utilization</li>
              <li>Benefits: lower congestion, cleaner air, better access</li>
              <li>Reliability investments reduce lifetime operating costs</li>
            </ul>
          </section>
          <section>
            <h3>Statistics (illustrative)</h3>
            <ul>
              <li>Daily trips: hundreds of thousands across all modes</li>
              <li>On‑time performance: among the best in EU urban systems</li>
              <li>Coverage: most residents within minutes of a stop</li>
            </ul>
          </section>
          <section>
            <h3>How This App Works</h3>
            <ul>
              <li>GTFS provides planned routes/stops; WL monitor provides live positions</li>
              <li>Map shows vehicles and polylines; status board summarizes health</li>
              <li>Privacy‑friendly: no personal data collected; geolocation is opt‑in</li>
            </ul>
          </section>
        </div>
        <footer class="modal__footer">
          <button id="help-ok" class="button">Got it</button>
        </footer>
      </div>`;
    document.body.appendChild(modal);
  }
}

function openModal() {
  ensureModal();
  modal.style.display = 'block';
}

function closeModal() {
  if (modal) modal.style.display = 'none';
}

if (openBtn) {
  openBtn.addEventListener('click', openModal);
}

document.addEventListener('click', (e) => {
  if (!modal) return;
  const target = e.target;
  if (target.id === 'help-close' || target.id === 'help-ok') {
    closeModal();
  }
  if (target === modal) {
    closeModal();
  }
});
