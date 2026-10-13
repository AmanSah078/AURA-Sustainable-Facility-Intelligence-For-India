// =============================================================================
// AURA — AI-Powered Sustainable Facility Intelligence Platform
// Spring Boot API Client Service
//
// React strictly connects to Spring Boot (http://localhost:8080).
// React does NOT call FastAPI directly.
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

/**
 * Helper to perform fetch requests and handle errors cleanly
 */
async function fetchJson(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.message) errorDetail = errJson.message;
      else if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // Non-JSON error body
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Fetch all facilities configured in Spring Boot / MySQL
 */
export async function fetchFacilities() {
  return fetchJson('/api/v1/facilities');
}

/**
 * Fetch specific facility metadata
 */
export async function fetchFacilityById(facilityId) {
  return fetchJson(`/api/v1/facilities/${encodeURIComponent(facilityId)}`);
}

/**
 * Fetch live energy intelligence for a specific zone from Spring Boot (delegated to FastAPI)
 */
export async function fetchEnergyIntelligence(facilityId = 'H001', zoneId = 'Emergency') {
  return fetchJson(`/api/v1/energy/intelligence?facilityId=${encodeURIComponent(facilityId)}&zoneId=${encodeURIComponent(zoneId)}`);
}

/**
 * Fetch live energy intelligence across all zones for a facility
 */
export async function fetchAllZonesIntelligence(facilityId = 'H001') {
  return fetchJson(`/api/v1/energy/intelligence?facilityId=${encodeURIComponent(facilityId)}`);
}

/**
 * Fetch recent energy readings from MySQL for trend charting
 */
export async function fetchRecentReadings(facilityId = 'H001', zoneId = 'Emergency', limit = 24) {
  return fetchJson(`/api/v1/energy/readings?facilityId=${encodeURIComponent(facilityId)}&zoneId=${encodeURIComponent(zoneId)}&limit=${limit}`);
}

/**
 * Fetch recent active anomaly alerts from Spring Boot / MySQL
 */
export async function fetchActiveAnomalies(facilityId = 'H001', limit = 20) {
  return fetchJson(`/api/v1/energy/anomalies?facilityId=${encodeURIComponent(facilityId)}&limit=${limit}`);
}

/**
 * Ingest a sensor reading through Spring Boot HTTP Ingestion API
 */
export async function ingestEnergyReading(readingData) {
  return fetchJson('/api/v1/energy/ingest', {
    method: 'POST',
    body: JSON.stringify(readingData),
  });
}

/**
 * Start synthetic sensor replay simulation in Spring Boot
 */
export async function startReplaySimulation(speedMs = 3000) {
  return fetchJson(`/api/v1/energy/replay/start?speedMs=${speedMs}`, {
    method: 'POST',
  });
}

/**
 * Stop synthetic sensor replay simulation in Spring Boot
 */
export async function stopReplaySimulation() {
  return fetchJson('/api/v1/energy/replay/stop', {
    method: 'POST',
  });
}

/**
 * Reset synthetic sensor replay simulation in Spring Boot
 */
export async function resetReplaySimulation() {
  return fetchJson('/api/v1/energy/replay/reset', {
    method: 'POST',
  });
}

/**
 * Get current status of synthetic sensor replay simulation
 */
export async function fetchReplayStatus() {
  return fetchJson('/api/v1/energy/replay/status');
}
