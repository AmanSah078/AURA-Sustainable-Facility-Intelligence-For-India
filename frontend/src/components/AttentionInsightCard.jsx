import React, { useState } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  Zap,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  Info,
  ChevronDown,
  ChevronUp,
  Cpu,
  Leaf,
  RotateCcw,
  Sparkles
} from 'lucide-react';

export default function AttentionInsightCard({ intelligence, zoneName, activeRole = 'admin' }) {
  const [isExplainOpen, setIsExplainOpen] = useState(false);
  const [isSimulated, setIsSimulated] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  if (!intelligence) return null;

  const isAnomaly = Boolean(intelligence.anomaly_detected);
  const displayZone = zoneName || (intelligence.zone_id ? intelligence.zone_id.replace('_', ' ') : 'Hospital Facility');
  const recommendation = intelligence.recommendation || 'Normal energy usage. No immediate action required.';
  const rootCause = intelligence.root_cause || (isAnomaly 
    ? `Unusual energy usage detected in ${displayZone}. Telemetry indicates significant departure from the expected baseline.`
    : `Energy draw in ${displayZone} is consistent with the historical 7-day seasonal baseline within normal tolerance.`);
  const actionPlan = Array.isArray(intelligence.action_plan) && intelligence.action_plan.length > 0
    ? intelligence.action_plan
    : [recommendation];
  const impactMetric = intelligence.impact_metric || (isAnomaly 
    ? 'Estimated scenario impact: excess load above seasonal baseline. Operational review recommended.' 
    : 'Operating within normal baseline. Zero excess grid draw detected.');
  const score = intelligence.anomaly_score != null ? Number(intelligence.anomaly_score).toFixed(2) : null;
  const excessKwh = intelligence.excess_kwh != null && intelligence.excess_kwh > 0 ? Number(intelligence.excess_kwh).toFixed(1) : null;
  const severity = intelligence.severity_level || (isAnomaly ? 'CRITICAL_SPIKE' : 'OPTIMAL');

  // Evidence-based Calculations from configured parameters
  const excessVal = excessKwh ? parseFloat(excessKwh) : 0;
  const carbonImpactKg = (excessVal * 0.82).toFixed(1); // Configured CEA India Grid Factor: 0.82 kg CO2e / kWh
  const estCostInr = (excessVal * 8.0).toFixed(0);      // Configured Reference Tariff: ₹8.00 / kWh
  const simulatedSavedInr = (excessVal * 8.0 * 0.65).toFixed(0); // Scenario model assuming 65% normalization

  const handleSimulateAction = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
      setIsSimulated(true);
    }, 500);
  };

  const handleResetSimulation = () => {
    setIsSimulated(false);
  };

  return (
    <section className={`attention-card ${!isAnomaly ? 'normal' : ''}`} aria-live="polite">
      <div className="attention-badge-icon">
        {isAnomaly ? <AlertTriangle size={24} /> : <ShieldCheck size={24} />}
      </div>

      <div className="attention-body">
        {/* Header Strip */}
        <div className="attention-heading-wrap">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            <h3 className="attention-title">
              {isAnomaly ? `Decision Support Alert: ${displayZone}` : `Optimal Operation: ${displayZone}`}
            </h3>
            <span className={`attention-tag ${isAnomaly ? 'attention' : 'normal'}`}>
              {isAnomaly ? (severity === 'CRITICAL_SPIKE' ? 'P1 • ELEVATED SURGE' : 'ELEVATED ANOMALY') : 'NORMAL BASELINE'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: 'auto', flexWrap: 'wrap' }}>
            {score !== null && (
              <span className="anomaly-score-badge">
                Z-Score: <strong style={{ color: isAnomaly ? '#ef4444' : '#10b981' }}>{score}</strong>
              </span>
            )}
            {excessKwh && (
              <span className="excess-kwh-badge">
                <Zap size={12} />
                <span>+{excessKwh} kWh Overload</span>
              </span>
            )}
          </div>
        </div>

        {/* 1. Evidence & Context (Truthful, non-invented data context) */}
        <div className="root-cause-box">
          <div className="intelligence-section-label">
            <span className="dot-pulse" style={{ background: isAnomaly ? '#ef4444' : '#10b981' }} />
            <span>EVIDENCE & CONTEXT</span>
          </div>
          <p className="root-cause-text">{rootCause}</p>
        </div>

        {/* 2. Recommended Operational Interventions */}
        {isAnomaly && (
          <div className="action-plan-box">
            <div className="intelligence-section-label">
              <CheckCircle2 size={13} style={{ color: 'var(--status-normal)' }} />
              <span>Recommended Operational Interventions (Decision-Support Checklist)</span>
            </div>
            <ul className="action-plan-list">
              {actionPlan.map((step, idx) => (
                <li key={idx} className="action-plan-item">
                  <ChevronRight size={14} className="action-step-icon" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>

            {/* Honest What-If Scenario Simulation */}
            <div className="mitigation-action-bar">
              {!isSimulated ? (
                <button
                  type="button"
                  className="btn-mitigate"
                  onClick={handleSimulateAction}
                  disabled={isSimulating}
                  title="Run what-if scenario simulation on configured assumptions"
                >
                  <Sparkles size={14} />
                  <span>{isSimulating ? 'Calculating Scenario Impact...' : '⚡ Simulate Recommended Action'}</span>
                </button>
              ) : (
                <div className="mitigation-success-badge">
                  <CheckCircle2 size={16} style={{ color: '#10b981', flexShrink: 0 }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                    <span>
                      <strong>✓ Recommended action simulated:</strong> Estimated scenario impact projects potential return towards baseline (~65% normalization), recovering an estimated <strong>₹{simulatedSavedInr}/hr</strong>.
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      (What-if scenario simulation based on configured reference parameters — no physical hardware commands dispatched)
                    </span>
                  </div>
                  <button type="button" className="btn-undo" onClick={handleResetSimulation} title="Reset Simulation State">
                    <RotateCcw size={12} />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. Quantified Impact & Financial Metric Footer */}
        <div className="impact-metric-bar">
          <div className="impact-metric-content">
            <TrendingUp size={14} style={{ color: isAnomaly ? '#f59e0b' : '#10b981' }} />
            <span className="impact-metric-text">{impactMetric}</span>
          </div>

          {isAnomaly && (
            <div className="impact-pills-wrap">
              <span className="impact-pill cost" title="Calculated based on configured commercial tariff assumption of ₹8.00/kWh">
                Estimated Tariff Impact: <strong>~₹{estCostInr}/hr</strong>
              </span>
              <span className="impact-pill carbon" title="Calculated based on configured CEA National Grid emission factor of 0.82 kg CO₂e/kWh">
                <Leaf size={11} />
                <span>Estimated CO₂e: <strong>+{carbonImpactKg} kg</strong>/hr</span>
              </span>
            </div>
          )}
        </div>

        {/* 4. Explainability & Model Assumptions Drawer */}
        <div className="explainability-section">
          <button
            type="button"
            className="explainability-toggle-btn"
            onClick={() => setIsExplainOpen(!isExplainOpen)}
            aria-expanded={isExplainOpen}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Info size={13} style={{ color: 'var(--color-accent-cyan)' }} />
              <span>Model Assumptions & Explainability Metadata</span>
            </div>
            {isExplainOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {isExplainOpen && (
            <div className="explainability-content">
              <div className="explainability-grid">
                <div className="explain-item">
                  <span className="explain-label">Anomaly Model</span>
                  <span className="explain-val">Multi-Variate 3-Sigma (Z-Score &gt; 3.0) + Seasonal Diurnal Baseline</span>
                </div>
                <div className="explain-item">
                  <span className="explain-label">Baseline Horizon</span>
                  <span className="explain-val">15-Min Diurnal Seasonal Moving Average</span>
                </div>
                <div className="explain-item">
                  <span className="explain-label">Configured Tariff</span>
                  <span className="explain-val">₹8.00 / kWh (Reference commercial tariff assumption)</span>
                </div>
                <div className="explain-item">
                  <span className="explain-label">Configured Carbon Factor</span>
                  <span className="explain-val">0.82 kg CO₂e / kWh (CEA National Grid Reference Baseline)</span>
                </div>
              </div>
              <p className="explain-disclaimer">
                <strong>Decision-Support Notice:</strong> Recommendations are decision-support suggestions based on available facility data and configured assumptions. They are not confirmed root-cause diagnoses or automated hardware control actions.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
