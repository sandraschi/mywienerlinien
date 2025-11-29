# Extension Roadmap TODOs

## Phase 1 – Immediate UX ✅ COMPLETE
- [x] Backend: add `/api/arrivals?rbl=` endpoint (wrap `collect_vehicle_data(station=...)`).
- [x] Frontend: arrivals panel component (trigger from map click or stop search).
- [x] UI: highlight selected stop and show countdown/delay per departure.
- [x] Add quick filters for day vs. night routes in the panel.

## Phase 2 – Location Awareness ✅ COMPLETE
- [x] Backend: `/api/stops/nearby?lat=&lon=` returning top stops with distance + RBL.
- [x] Frontend: "Near Me" button using browser geolocation.
- [x] Graceful fallback when geolocation is denied/unavailable.

## Phase 3 – Personalization ✅ COMPLETE
- [x] Implement client-side favorites (store stop/line combos).
- [x] Provide "Home" and "Work" quick actions linked to favorites.
- [x] Dedicated night-bus view with countdown emphasis (via day/night filters).

## Phase 4 – Alerts & Enhancements ✅ COMPLETE
- [x] Integrate Wiener Linien `/trafficInfo` into arrival cards.
- [x] Refine mobile layout (arrivals first, map secondary on phones).
- [x] Introduce per-RBL caching layer (~30s TTL) to limit monitor calls.
- [ ] Explore batching monitor requests for nearby stops.

## Stretch Goals (Next Phase)
- [ ] Package as PWA (offline schedules, installable).
- [ ] Push notification prototype for favorite stops (late arrivals).
- [ ] Voice/quick query UI ("Next U1 at Stephansplatz?").
- [ ] Auto-refresh arrivals panel every 30 seconds.
- [ ] Add arrival cards to traffic alerts (show affected departures).

