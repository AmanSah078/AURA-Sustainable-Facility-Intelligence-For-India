import React from 'react';
import { Play, Pause, RotateCcw, Radio, FastForward, Activity, AlertTriangle } from 'lucide-react';

export default function ReplayControlBar({
  replayStatus,
  onStart,
  onStop,
  onReset,
  speedMs,
  onChangeSpeed,
}) {
  const isRunning = replayStatus?.status === 'RUNNING';
  const isCompleted = replayStatus?.status === 'COMPLETED';
  const currentTs = replayStatus?.current_timestamp || '--';
  const currentKwh = replayStatus?.current_energy_kwh != null ? Number(replayStatus.current_energy_kwh).toFixed(1) : '--';
  const isAnomaly = Boolean(replayStatus?.is_anomaly_current);
  const currentIdx = replayStatus?.current_index || 0;
  const totalRecs = replayStatus?.total_records || 13;
  const progressPercent = Math.min(100, Math.round((currentIdx / Math.max(totalRecs, 1)) * 100));

  return (
    <div className="replay-bar-card">
      <div className="replay-bar-top">
        <div className="replay-bar-title-wrap">
          <div className="replay-badge">
            <Radio size={12} className={isRunning ? 'pulsing-icon' : ''} />
            <span>Demo: Synthetic Sensor Simulation</span>
          </div>
          <span className="replay-meta-text">
            Emergency Ward Telemetry Window (Normal → <strong>Anomaly Spike @ 15:30</strong> → Recovery)
          </span>
        </div>

        {/* Controls */}
        <div className="replay-controls-group">
          {/* Speed Selector */}
          <div className="speed-selector" title="Replay Packet Speed">
            <FastForward size={13} style={{ color: 'var(--text-muted)' }} />
            <select
              value={speedMs}
              onChange={(e) => onChangeSpeed(Number(e.target.value))}
              className="speed-dropdown"
              disabled={isRunning}
            >
              <option value={5000}>0.5x (5s)</option>
              <option value={3000}>1.0x (3s)</option>
              <option value={1500}>2.0x (1.5s)</option>
              <option value={1000}>3.0x (1.0s)</option>
            </select>
          </div>

          {/* Start / Pause Button */}
          {!isRunning ? (
            <button
              type="button"
              className="replay-btn play"
              onClick={onStart}
              title="Start sequential sensor replay stream"
            >
              <Play size={14} />
              <span>{isCompleted ? 'Restart Replay' : (currentIdx > 0 ? 'Resume' : 'Start Replay')}</span>
            </button>
          ) : (
            <button
              type="button"
              className="replay-btn pause"
              onClick={onStop}
              title="Pause replay stream"
            >
              <Pause size={14} />
              <span>Pause</span>
            </button>
          )}

          {/* Reset Button */}
          <button
            type="button"
            className="replay-btn reset"
            onClick={onReset}
            title="Reset replay to beginning"
            disabled={currentIdx === 0 && !isRunning}
          >
            <RotateCcw size={13} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Progress & Live Telemetry Telemetry Bar */}
      <div className="replay-progress-wrap">
        <div className="replay-progress-info">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span className="replay-status-indicator" style={{ color: isRunning ? 'var(--status-normal)' : (isCompleted ? 'var(--accent-cyan)' : 'var(--text-muted)') }}>
              ● {replayStatus?.status || 'IDLE'}
            </span>
            <span className="replay-ts-badge">
              Timestamp: <strong>{currentTs}</strong>
            </span>
            <span className="replay-load-badge">
              Ingested Load: <strong>{currentKwh} kWh</strong>
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {isAnomaly && (
              <span className="replay-spike-alert">
                <AlertTriangle size={12} />
                <span>ANOMALOUS LOAD SPIKE</span>
              </span>
            )}
            <span className="replay-progress-text">
              Packet {currentIdx} of {totalRecs} ({progressPercent}%)
            </span>
          </div>
        </div>

        <div className="replay-progress-track">
          <div
            className={`replay-progress-fill ${isAnomaly ? 'spike' : ''}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}
