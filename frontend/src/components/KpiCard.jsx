import React from 'react';

export default function KpiCard({ label, value, unit, icon: Icon, subtext, variant = 'emerald' }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card-header">
        <span className="kpi-label">{label}</span>
        {Icon && (
          <div className={`kpi-icon-wrap ${variant}`}>
            <Icon size={16} />
          </div>
        )}
      </div>

      <div>
        <div className="kpi-value-wrap">
          <span className="kpi-value">{value}</span>
          {unit && <span className="kpi-unit">{unit}</span>}
        </div>
        {subtext && <div className="kpi-subtext">{subtext}</div>}
      </div>
    </div>
  );
}
