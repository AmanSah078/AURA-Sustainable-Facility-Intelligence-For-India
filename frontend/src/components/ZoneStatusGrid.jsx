import React from 'react';
import { Layers, ChevronRight } from 'lucide-react';

const ZONE_METADATA = {
  Emergency: { title: 'Emergency Ward', code: 'EMERGENCY' },
  ICU: { title: 'Intensive Care Unit', code: 'ICU' },
  General_Ward: { title: 'General Ward', code: 'GENERAL_WARD' },
  OPD: { title: 'Outpatient Dept', code: 'OPD' },
  Admin: { title: 'Administration Wing', code: 'ADMIN' },
};

export default function ZoneStatusGrid({ zonesIntelligence = [], selectedZone, onSelectZone }) {
  return (
    <div className="card-panel">
      <div className="panel-header">
        <div className="panel-title">
          <Layers size={16} style={{ color: 'var(--status-normal)' }} />
          <span>Zone Telemetry & Status</span>
        </div>
        <span className="panel-subtitle">5 Monitored Wards</span>
      </div>

      <div className="zone-list">
        {zonesIntelligence.map((item) => {
          const rawId = item.zone_id || '';
          const meta = ZONE_METADATA[rawId] || { title: rawId.replace('_', ' '), code: rawId };
          const isAnomaly = Boolean(item.anomaly_detected);
          const isSelected = selectedZone === rawId;
          const currentKwh = Number(item.current_energy_kwh || 0).toFixed(1);
          const forecastKwh = Number(item.forecast_energy_kwh || 0).toFixed(1);

          return (
            <div
              key={rawId}
              className={`zone-item-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectZone(rawId)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectZone(rawId);
                }
              }}
              title={`Click to focus on ${meta.title}`}
            >
              <div className="zone-item-left">
                <div className={`zone-avatar ${isAnomaly ? 'attention' : ''}`}>
                  {rawId.substring(0, 3).toUpperCase()}
                </div>
                <div className="zone-name-info">
                  <span className="zone-item-name">{meta.title}</span>
                  <span className="zone-item-meta">
                    Forecast: <strong>{forecastKwh} kWh</strong>
                  </span>
                </div>
              </div>

              <div className="zone-item-right">
                <span className="zone-item-kwh">{currentKwh} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-muted)' }}>kWh</span></span>
                <span className={`zone-item-badge ${isAnomaly ? 'attention' : 'normal'}`}>
                  {isAnomaly ? 'Attention Required' : 'Normal'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
