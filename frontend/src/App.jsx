import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Zap, Clock, ShieldAlert, TrendingUp, Layers, CheckCircle2, AlertTriangle, Building2 } from 'lucide-react';
import Header from './components/Header';
import ModuleNavigation from './components/ModuleNavigation';
import { FACILITIES } from './components/FacilitySelector';
import KpiCard from './components/KpiCard';
import AttentionInsightCard from './components/AttentionInsightCard';
import EnergyTrendChart from './components/EnergyTrendChart';
import ZoneStatusGrid from './components/ZoneStatusGrid';
import ReplayControlBar from './components/ReplayControlBar';
import UnconfiguredState from './components/UnconfiguredState';
import LoadingSkeleton from './components/LoadingSkeleton';
import ErrorState from './components/ErrorState';
import {
  fetchAllZonesIntelligence,
  fetchEnergyIntelligence,
  fetchRecentReadings,
  startReplaySimulation,
  stopReplaySimulation,
  resetReplaySimulation,
  fetchReplayStatus,
} from './services/api';

const ZONES = [
  { id: 'ALL', name: 'All Hospital Wards' },
  { id: 'Emergency', name: 'Emergency' },
  { id: 'ICU', name: 'ICU' },
  { id: 'General_Ward', name: 'General Ward' },
  { id: 'OPD', name: 'OPD' },
  { id: 'Admin', name: 'Admin Wing' },
];

export default function App() {
  const [selectedFacility, setSelectedFacility] = useState(FACILITIES[0]);
  const [activeModule, setActiveModule] = useState('energy');
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [activeRole, setActiveRole] = useState('admin');

  const [allZonesData, setAllZonesData] = useState([]);
  const [currentZoneData, setCurrentZoneData] = useState(null);
  const [recentReadings, setRecentReadings] = useState([]);

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState('');

  // Replay simulation state
  const [replayStatus, setReplayStatus] = useState(null);
  const [replaySpeedMs, setReplaySpeedMs] = useState(3000);
  const pollingTimerRef = useRef(null);

  // Load telemetry from Spring Boot backend
  const loadDashboardData = useCallback(async (isSilentRefresh = false) => {
    if (selectedFacility.id !== 'H001') {
      setLoading(false);
      return;
    }

    if (!isSilentRefresh) {
      setLoading(true);
    } else {
      setIsRefreshing(true);
    }
    setError(null);

    try {
      // 1. Fetch live intelligence across all hospital zones from Spring Boot -> FastAPI
      const allZonesIntel = await fetchAllZonesIntelligence('H001');
      setAllZonesData(allZonesIntel);

      // Extract latest timestamp from telemetry
      if (allZonesIntel.length > 0 && allZonesIntel[0].timestamp) {
        setLastUpdated(allZonesIntel[0].timestamp);
      }

      // 2. Fetch specific zone intelligence or default to Emergency for focused readings
      const targetZone = selectedZone === 'ALL' ? 'Emergency' : selectedZone;
      const zoneIntel = await fetchEnergyIntelligence('H001', targetZone);
      setCurrentZoneData(zoneIntel);

      // 3. Fetch recent readings from Spring Boot -> MySQL for the trend chart
      const readings = await fetchRecentReadings('H001', targetZone, 24);
      setRecentReadings(readings);

      // 4. Also check replay status if available
      try {
        const repStatus = await fetchReplayStatus();
        setReplayStatus(repStatus);
      } catch {
        // Non-critical if replay status is not ready
      }

    } catch (err) {
      console.error('Failed to load energy intelligence:', err);
      setError(err.message || 'Unable to communicate with Spring Boot backend.');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [selectedFacility.id, selectedZone]);

  // Initial load: ensure replay is reset to clean baseline on first visit
  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      resetReplaySimulation()
        .catch(() => {})
        .finally(() => {
          loadDashboardData();
        });
    } else {
      loadDashboardData();
    }
  }, [loadDashboardData]);

  // Periodic polling effect when replay simulation is RUNNING
  useEffect(() => {
    const isRunning = replayStatus?.status === 'RUNNING';

    if (isRunning) {
      // Poll backend every 1.5 - 2 seconds for fresh replayed telemetry
      pollingTimerRef.current = setInterval(() => {
        loadDashboardData(true);
      }, 1800);
    } else {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    }

    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }
    };
  }, [replayStatus?.status, loadDashboardData]);

  // Replay Action Handlers
  const handleStartReplay = async () => {
    try {
      const res = await startReplaySimulation(replaySpeedMs);
      setReplayStatus(res);
      // Auto-switch to Emergency ward to clearly observe the anomaly spike & recovery
      if (selectedZone === 'ALL') {
        setSelectedZone('Emergency');
      }
      loadDashboardData(true);
    } catch (err) {
      console.error('Failed to start replay:', err);
    }
  };

  const handleStopReplay = async () => {
    try {
      const res = await stopReplaySimulation();
      setReplayStatus(res);
      loadDashboardData(true);
    } catch (err) {
      console.error('Failed to stop replay:', err);
    }
  };

  const handleResetReplay = async () => {
    try {
      const res = await resetReplaySimulation();
      setReplayStatus(res);
      loadDashboardData(true);
    } catch (err) {
      console.error('Failed to reset replay:', err);
    }
  };

  const handleChangeSpeed = (newSpeedMs) => {
    setReplaySpeedMs(newSpeedMs);
  };

  // Compute aggregate or zone-specific metrics
  const isAllZones = selectedZone === 'ALL';

  const totalCurrentKwh = isAllZones
    ? allZonesData.reduce((sum, z) => sum + (Number(z.current_energy_kwh) || 0), 0)
    : Number(currentZoneData?.current_energy_kwh || 0);

  const totalForecastKwh = isAllZones
    ? allZonesData.reduce((sum, z) => sum + (Number(z.forecast_energy_kwh) || 0), 0)
    : Number(currentZoneData?.forecast_energy_kwh || 0);

  const activeAlertsCount = allZonesData.filter(z => Boolean(z.anomaly_detected)).length;

  const activeAnomalyZone = allZonesData.find(z => Boolean(z.anomaly_detected));
  const activeDisplayIntelligence = isAllZones
    ? (activeAnomalyZone || allZonesData[0] || currentZoneData)
    : currentZoneData;

  const currentZoneLabel = ZONES.find(z => z.id === selectedZone)?.name || selectedZone;

  return (
    <div className="aura-app">
      {/* Top Navigation & Facility Switcher */}
      <Header
        selectedFacility={selectedFacility}
        onSelectFacility={(fac) => {
          setSelectedFacility(fac);
          setSelectedZone('ALL');
        }}
        onRefresh={() => loadDashboardData(true)}
        isRefreshing={isRefreshing}
        lastUpdated={lastUpdated}
        activeRole={activeRole}
        onSelectRole={setActiveRole}
      />

      <main className="main-content">
        <div className="aura-container">
          {/* Module Navigation Tabs */}
          <ModuleNavigation
            activeModule={activeModule}
            onSelectModule={(mod) => setActiveModule(mod)}
          />

          {/* Case 1: Unconfigured Facility Selected */}
          {selectedFacility.id !== 'H001' ? (
            <UnconfiguredState
              type="facility"
              targetName={selectedFacility.name}
              onResetToDemo={() => setSelectedFacility(FACILITIES[0])}
            />
          ) : activeModule !== 'energy' ? (
            /* Case 2: Non-Energy Module Selected */
            <UnconfiguredState
              type="module"
              targetName={activeModule.toUpperCase()}
              onResetToDemo={() => setActiveModule('energy')}
            />
          ) : error ? (
            /* Case 3: Backend Error State */
            <ErrorState
              error={error}
              onRetry={() => loadDashboardData(false)}
            />
          ) : loading && !isRefreshing ? (
            /* Case 4: Loading Skeleton */
            <LoadingSkeleton />
          ) : (
            /* Case 5: Main Energy Dashboard (Government Hospital H001) */
            <>
              {/* Synthetic Sensor Replay Simulation Control Bar */}
              <ReplayControlBar
                replayStatus={replayStatus}
                onStart={handleStartReplay}
                onStop={handleStopReplay}
                onReset={handleResetReplay}
                speedMs={replaySpeedMs}
                onChangeSpeed={handleChangeSpeed}
              />

              {/* Facility Header & Zone Filters */}
              <section className="facility-intro-bar">
                <div className="facility-hero-info">
                  <h1 className="facility-hero-title">
                    <span>{selectedFacility.name}</span>
                    <span className="facility-live-dot" title="Live Telemetry Stream Active" />
                  </h1>
                  <div className="facility-hero-meta">
                    <span>{selectedFacility.type}</span>
                    <span>•</span>
                    <span>{selectedFacility.location}</span>
                    {lastUpdated && (
                      <>
                        <span>•</span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Clock size={12} />
                          Telemetry Event: {lastUpdated}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Zone Quick-Filter Pills */}
                <div className="zone-selector-bar" role="tablist" aria-label="Hospital Wards">
                  {ZONES.map((zone) => {
                    const isActive = selectedZone === zone.id;
                    const zoneIntel = allZonesData.find(z => z.zone_id === zone.id);
                    const hasAnomaly = zone.id === 'ALL'
                      ? activeAlertsCount > 0
                      : Boolean(zoneIntel?.anomaly_detected);

                    return (
                      <button
                        key={zone.id}
                        type="button"
                        className={`zone-pill ${isActive ? 'active' : ''}`}
                        onClick={() => setSelectedZone(zone.id)}
                        role="tab"
                        aria-selected={isActive}
                      >
                        <span className={`zone-status-dot ${hasAnomaly ? 'attention' : ''}`} />
                        <span>{zone.name}</span>
                      </button>
                    );
                  })}
                </div>
              </section>

              {/* KPI Metrics Section */}
              <section className="kpi-grid" aria-label="Energy Key Performance Indicators">
                <KpiCard
                  label={isAllZones ? "Total Facility Load" : `${currentZoneLabel} Load`}
                  value={totalCurrentKwh.toFixed(1)}
                  unit="kWh"
                  icon={Zap}
                  variant={currentZoneData?.anomaly_detected ? "amber" : "emerald"}
                  subtext="15-minute telemetry interval"
                />

                <KpiCard
                  label="Short-Term Forecast"
                  value={totalForecastKwh.toFixed(1)}
                  unit="kWh"
                  icon={TrendingUp}
                  variant="cyan"
                  subtext="Next 1-hour diurnal horizon"
                />

                <KpiCard
                  label="Operational Status"
                  value={
                    isAllZones
                      ? (activeAlertsCount > 0 ? "Attention" : "Optimal")
                      : (currentZoneData?.anomaly_detected ? "Attention" : "Optimal")
                  }
                  icon={
                    isAllZones
                      ? (activeAlertsCount > 0 ? AlertTriangle : CheckCircle2)
                      : (currentZoneData?.anomaly_detected ? AlertTriangle : CheckCircle2)
                  }
                  variant={
                    isAllZones
                      ? (activeAlertsCount > 0 ? "amber" : "emerald")
                      : (currentZoneData?.anomaly_detected ? "amber" : "emerald")
                  }
                  subtext={
                    isAllZones
                      ? (activeAlertsCount > 0 ? `${activeAlertsCount} ward requiring review` : "All 5 wards operating normally")
                      : `Score: ${Number(currentZoneData?.anomaly_score || 0).toFixed(2)}`
                  }
                />

                <KpiCard
                  label="Active Alerts"
                  value={activeAlertsCount}
                  unit={activeAlertsCount === 1 ? "alert" : "alerts"}
                  icon={ShieldAlert}
                  variant={activeAlertsCount > 0 ? "amber" : "emerald"}
                  subtext={activeAlertsCount > 0 ? "Unusual load pattern detected" : "Zero active anomaly alerts"}
                />
              </section>

              {/* Attention & Decision Support Recommendation Card */}
              <AttentionInsightCard
                intelligence={activeDisplayIntelligence}
                zoneName={isAllZones ? (activeAnomalyZone ? `${activeAnomalyZone.zone_id} Ward` : 'Hospital Overview') : currentZoneLabel}
                activeRole={activeRole}
              />

              {/* 2-Column Analytics: Energy Trend Chart + Zone Status List */}
              <div className="dashboard-grid-2col">
                <EnergyTrendChart
                  readings={recentReadings}
                  zoneTitle={isAllZones ? "Emergency Ward" : currentZoneLabel}
                  forecastBaseline={activeDisplayIntelligence?.forecast_energy_kwh}
                  isLiveAnomaly={Boolean(activeDisplayIntelligence?.anomaly_detected)}
                />

                <ZoneStatusGrid
                  zonesIntelligence={allZonesData}
                  selectedZone={selectedZone}
                  onSelectZone={(zoneId) => setSelectedZone(zoneId)}
                />
              </div>
            </>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="aura-footer">
        <div className="aura-container">
          <div className="footer-content">
            <div className="footer-tag">
              <Building2 size={14} style={{ color: 'var(--status-normal)' }} />
              <span>AURA — Sustainable Facility Intelligence Platform</span>
            </div>
            <span>Government Hospital (H001) Deep Demo • Bhubaneswar, Odisha</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
