import React from 'react';
import { ShieldAlert, ArrowRight, Zap, Building2 } from 'lucide-react';

export default function UnconfiguredState({ type = 'facility', targetName, onResetToDemo }) {
  const isFacility = type === 'facility';

  return (
    <div className="unconfigured-card">
      <div className="unconfigured-icon-wrap">
        {isFacility ? <Building2 size={28} /> : <Zap size={28} />}
      </div>

      <h3 className="unconfigured-title">
        {isFacility ? 'Operational Telemetry Pending' : `${targetName} Module Not Configured`}
      </h3>

      <p className="unconfigured-desc">
        {isFacility ? (
          <>
            Operational data streams and live telemetry are not yet connected for <strong>{targetName}</strong>.
            AURA's verified end-to-end intelligence engine is currently active for <strong>Government Hospital (H001)</strong>.
          </>
        ) : (
          <>
            The <strong>{targetName}</strong> intelligence pipeline is not yet connected for this facility.
            Real-time telemetry, anomaly detection, and forecasting are active on the <strong>Energy</strong> module.
          </>
        )}
      </p>

      <button type="button" className="btn-primary" onClick={onResetToDemo}>
        {isFacility ? 'Switch to Government Hospital' : 'Switch to Energy Module'}
        <ArrowRight size={15} />
      </button>
    </div>
  );
}
