# Extension Roadmap TODOs

## Phase 1 – Immediate UX
- [ ] Backend: add `/api/arrivals?rbl=` endpoint (wrap `collect_vehicle_data(station=...)`).
- [ ] Frontend: arrivals panel component (trigger from map click or stop search).
- [ ] UI: highlight selected stop and show countdown/delay per departure.
- [ ] Add quick filters for day vs. night routes in the panel.

## Phase 2 – Location Awareness
- [ ] Backend: `/api/stops/nearby?lat=&lon=` returning top stops with distance + RBL.
- [ ] Frontend: “Near Me” button using browser geolocation.
- [ ] Graceful fallback when geolocation is denied/unavailable.

## Phase 3 – Personalization
- [ ] Implement client-side favorites (store stop/line combos).
- [ ] Provide “Home” and “Work” quick actions linked to favorites.
- [ ] Dedicated night-bus view with countdown emphasis.

## Phase 4 – Alerts & Enhancements
- [ ] Integrate Wiener Linien `/trafficInfo` into arrival cards.
- [ ] Refine mobile layout (arrivals first, map secondary on phones).
- [ ] Introduce per-RBL caching layer (~20s TTL) to limit monitor calls.
- [ ] Explore batching monitor requests for nearby stops.

## Stretch Goals
- [ ] Package as PWA (offline schedules, installable).
- [ ] Push notification prototype for favorite stops (late arrivals).
- [ ] Voice/quick query UI (“Next U1 at Stephansplatz?”).

