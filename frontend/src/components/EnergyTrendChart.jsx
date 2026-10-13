import React from 'react';
import { TrendingUp, AlertTriangle } from 'lucide-react';

export default function EnergyTrendChart({
  readings = [],
  zoneTitle = 'Telemetry',
  forecastBaseline = 172.9,
  isLiveAnomaly = false,
}) {
  if (!readings || readings.length === 0) {
    return (
      <div className="card-panel">
        <div className="panel-header">
          <div className="panel-title">
            <TrendingUp size={16} style={{ color: 'var(--status-normal)' }} />
            <span>Energy Consumption Trend</span>
          </div>
          <span className="panel-subtitle">15-Min Telemetry</span>
        </div>
        <div className="chart-empty">
          <span>No historical readings available for this zone.</span>
        </div>
      </div>
    );
  }

  // 1. Deduplicate readings by timestamp (take newest reading if multiple exist)
  const timestampMap = new Map();
  for (const r of readings) {
    const ts = r.timestamp;
    if (ts && !timestampMap.has(ts)) {
      timestampMap.set(ts, r);
    }
  }
  const distinctReadings = Array.from(timestampMap.values());

  // 2. Sort chronologically left-to-right
  const parseTs = (t) => {
    if (!t) return 0;
    if (typeof t === 'string' && t.includes('-') && t.includes(' ')) {
      const [d, time] = t.split(' ');
      const [day, month, year] = d.split('-');
      return new Date(`${year}-${month}-${day}T${time}:00`).getTime();
    }
    return new Date(t).getTime();
  };

  distinctReadings.sort((a, b) => parseTs(a.timestamp) - parseTs(b.timestamp));

  // Limit window to 16 points for clean spacing
  const windowReadings = distinctReadings.slice(-16);

  const dataPoints = windowReadings.map((r, i) => {
    const yVal = Number(r.energyKwh ?? r.energy_kwh ?? 0);
    const isSpikeVal = yVal > 250 || (forecastBaseline && yVal > forecastBaseline * 1.35);
    return {
      x: i,
      y: yVal,
      timestamp: r.timestamp || '',
      isSpikeVal,
    };
  });

  const values = dataPoints.map((d) => d.y);
  if (forecastBaseline) values.push(forecastBaseline);

  const minVal = Math.floor(Math.min(...values) * 0.85);
  const maxVal = Math.ceil(Math.max(...values) * 1.15) || 100;
  const range = maxVal - minVal || 1;

  // Chart coordinate space: viewBox 0 0 500 190
  const width = 500;
  const height = 190;
  const padLeft = 42;
  const padRight = 24;
  const padTop = 32;
  const padBottom = 28;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const points = dataPoints.map((d, i) => {
    const px = padLeft + (i / Math.max(dataPoints.length - 1, 1)) * chartW;
    const py = padTop + chartH - ((d.y - minVal) / range) * chartH;
    return { px, py, ...d };
  });

  const linePath = points.reduce((acc, p, i) => {
    return `${acc} ${i === 0 ? 'M' : 'L'} ${p.px.toFixed(1)} ${p.py.toFixed(1)}`;
  }, '');

  const areaPath =
    points.length > 0
      ? `${linePath} L ${points[points.length - 1].px.toFixed(1)} ${(padTop + chartH).toFixed(1)} L ${points[0].px.toFixed(1)} ${(padTop + chartH).toFixed(1)} Z`
      : '';

  // Baseline Y coordinate
  const baselineY = forecastBaseline
    ? padTop + chartH - ((forecastBaseline - minVal) / range) * chartH
    : null;

  // Generate 4 grid lines
  const gridSteps = [0, 0.33, 0.66, 1];

  const formatTime = (ts) => {
    if (!ts) return '';
    if (ts.includes(' ')) return ts.split(' ')[1];
    if (ts.includes('T')) return ts.split('T')[1].substring(0, 5);
    return ts;
  };

  // Identify peak point ONLY when isLiveAnomaly is true
  const peakSpikeIndex = isLiveAnomaly
    ? points.reduce((maxIdx, p, idx, arr) => (p.y > arr[maxIdx].y ? idx : maxIdx), 0)
    : -1;

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title">
          {isLiveAnomaly ? (
            <AlertTriangle size={16} style={{ color: '#ef4444' }} />
          ) : (
            <TrendingUp size={16} style={{ color: 'var(--status-normal)' }} />
          )}
          <span>Energy Consumption Trend</span>
          {isLiveAnomaly && (
            <span className="chart-spike-live-tag">
              <span className="dot-pulse" style={{ background: '#ef4444' }} />
              <span>LIVE ANOMALY DETECTED</span>
            </span>
          )}
        </div>
        <span className="panel-subtitle">{zoneTitle} • 15-Min Telemetry Intervals</span>
      </div>

      <div className="chart-container">
        <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            {/* Emerald Gradient for normal load */}
            <linearGradient id="energyGradientNormal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>

            {/* Amber/Red Gradient ONLY during live anomaly */}
            <linearGradient id="energyGradientSpike" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.40" />
              <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.12" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>

            {/* Red Glow Filter for Anomaly Radar Core */}
            <filter id="redGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Grid lines & Y-axis labels */}
          {gridSteps.map((step, idx) => {
            const y = padTop + chartH * (1 - step);
            const val = Math.round(minVal + range * step);
            return (
              <g key={idx}>
                <line x1={padLeft} y1={y} x2={width - padRight} y2={y} className="chart-grid-line" />
                <text x={padLeft - 8} y={y + 3} textAnchor="end" className="chart-axis-text">
                  {val}
                </text>
              </g>
            );
          })}

          {/* Dashed Baseline Reference Line */}
          {baselineY && baselineY >= padTop && baselineY <= padTop + chartH && (
            <g className="chart-baseline-group">
              <line
                x1={padLeft}
                y1={baselineY}
                x2={width - padRight}
                y2={baselineY}
                stroke="#06b6d4"
                strokeDasharray="4 4"
                strokeWidth="1.2"
                opacity="0.45"
              />
              <rect
                x={padLeft + 4}
                y={baselineY - 13}
                width="114"
                height="13"
                rx="3"
                fill="rgba(16, 25, 42, 0.85)"
                stroke="rgba(6, 182, 212, 0.3)"
                strokeWidth="0.8"
              />
              <text x={padLeft + 8} y={baselineY - 3} textAnchor="start" fill="#06b6d4" fontSize="8.5" fontWeight="600">
                Baseline: {forecastBaseline} kWh
              </text>
            </g>
          )}

          {/* Area Fill */}
          {areaPath && (
            <path
              d={areaPath}
              fill={isLiveAnomaly ? 'url(#energyGradientSpike)' : 'url(#energyGradientNormal)'}
              className="chart-area"
            />
          )}

          {/* Trend Line (Clean Emerald in normal, Red-Gold in Live Anomaly) */}
          {linePath && (
            <path
              d={linePath}
              className={`chart-line ${isLiveAnomaly ? 'has-spike' : ''}`}
            />
          )}

          {/* Data Points */}
          {points.map((p, idx) => {
            // ONLY the active spike point gets the glowing radar effect, and ONLY when live anomaly is true!
            const isTargetLiveSpike = isLiveAnomaly && idx === peakSpikeIndex && p.isSpikeVal;

            if (isTargetLiveSpike) {
              const excess = (p.y - (forecastBaseline || 172.9)).toFixed(1);
              const tagWidth = 118;
              const tagX = Math.max(padLeft, Math.min(width - padRight - tagWidth, p.px - tagWidth / 2));
              const tagY = Math.max(padTop - 10, p.py - 26);

              return (
                <g key={idx} className="chart-spike-node">
                  {/* Outer Pulsing Radar Wave */}
                  <circle
                    cx={p.px}
                    cy={p.py}
                    r="12"
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="1.5"
                    className="chart-radar-ring"
                  />
                  {/* Glowing Red Core Beacon */}
                  <circle
                    cx={p.px}
                    cy={p.py}
                    r="5.5"
                    fill="#ef4444"
                    stroke="#ffffff"
                    strokeWidth="2"
                    filter="url(#redGlow)"
                    className="chart-dot-spike"
                  >
                    <title>{`🚨 LIVE ANOMALY: ${p.timestamp} — ${p.y} kWh (+${excess} kWh Overload)`}</title>
                  </circle>

                  {/* High-Impact Floating Alert Callout */}
                  <g className="chart-spike-callout">
                    <rect
                      x={tagX}
                      y={tagY}
                      width={tagWidth}
                      height="18"
                      rx="4"
                      fill="#1e1014"
                      stroke="#ef4444"
                      strokeWidth="1"
                    />
                    <text
                      x={tagX + tagWidth / 2}
                      y={tagY + 12}
                      textAnchor="middle"
                      fill="#ef4444"
                      fontSize="9"
                      fontWeight="700"
                    >
                      ⚠ SPIKE: {p.y.toFixed(1)} kW (+{excess})
                    </text>
                  </g>
                </g>
              );
            }

            // Normal Data Point (Clean Emerald Dot)
            return (
              <circle
                key={idx}
                cx={p.px}
                cy={p.py}
                r="3.5"
                className="chart-dot"
              >
                <title>{`${p.timestamp}: ${p.y} kWh`}</title>
              </circle>
            );
          })}

          {/* X-axis time labels */}
          {points.length > 0 && (
            <>
              <text x={points[0].px} y={height - 8} className="chart-axis-text" textAnchor="start">
                {formatTime(points[0].timestamp)}
              </text>
              {points.length > 2 && (
                <text
                  x={points[Math.floor(points.length / 2)].px}
                  y={height - 8}
                  className="chart-axis-text"
                  textAnchor="middle"
                >
                  {formatTime(points[Math.floor(points.length / 2)].timestamp)}
                </text>
              )}
              <text
                x={points[points.length - 1].px}
                y={height - 8}
                className="chart-axis-text"
                textAnchor="end"
              >
                {formatTime(points[points.length - 1].timestamp)}
              </text>
            </>
          )}
        </svg>
      </div>
    </div>
  );
}
