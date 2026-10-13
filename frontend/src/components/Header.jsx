import React from 'react';
import { Activity, RefreshCw, Zap, UserCheck, ShieldAlert, Leaf } from 'lucide-react';
import FacilitySelector from './FacilitySelector';

export const ROLES = [
  { id: 'admin', label: 'Facility Admin', icon: UserCheck, desc: 'Cost & Operational Overview' },
  { id: 'operations', label: 'BMS Operations', icon: Activity, desc: 'Real-Time Load & Telemetry' },
  { id: 'sustainability', label: 'Sustainability Officer', icon: Leaf, desc: 'Carbon & ESG Compliance' },
];

export default function Header({
  selectedFacility,
  onSelectFacility,
  onRefresh,
  isRefreshing,
  lastUpdated,
  activeRole = 'admin',
  onSelectRole,
}) {
  return (
    <header className="aura-header">
      <div className="aura-container">
        <div className="header-content">
          {/* Brand Logo & Name */}
          <div className="brand-section">
            <div className="brand-logo-badge" title="AURA Facility Intelligence">
              <Zap size={22} />
            </div>
            <div className="brand-title-wrap">
              <span className="brand-name">AURA</span>
              <span className="brand-subtitle">Sustainable Facility Intelligence</span>
            </div>
          </div>

          {/* Role Persona Switcher (Directly Addressing Hackathon Guideline) */}
          <div className="role-switcher-bar">
            {ROLES.map((r) => {
              const Icon = r.icon;
              const isActive = activeRole === r.id;
              return (
                <button
                  key={r.id}
                  type="button"
                  className={`role-pill ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectRole && onSelectRole(r.id)}
                  title={r.desc}
                >
                  <Icon size={12} />
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>

          {/* Facility Selector & Refresh Controls */}
          <div className="header-controls">
            <FacilitySelector
              selectedFacility={selectedFacility}
              onSelectFacility={onSelectFacility}
            />

            {selectedFacility.id === 'H001' && (
              <button
                type="button"
                className={`refresh-btn ${isRefreshing ? 'spinning' : ''}`}
                onClick={onRefresh}
                title="Refresh Intelligence Telemetry"
                disabled={isRefreshing}
              >
                <RefreshCw size={14} />
                <span className="desktop-only" style={{ fontSize: '0.75rem' }}>
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
