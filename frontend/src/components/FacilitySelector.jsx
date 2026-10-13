import React, { useState, useRef, useEffect } from 'react';
import { Building2, ChevronDown, Check, Building, GraduationCap, Factory, Landmark, Cpu } from 'lucide-react';

// Multi-facility platform directory definition
export const FACILITIES = [
  {
    id: 'H001',
    name: 'Government Hospital',
    type: 'Hospital',
    location: 'Bhubaneswar',
    status: 'ACTIVE',
    icon: Building2,
    description: 'Tertiary healthcare center with critical care units and 24/7 emergency services.',
  },
  {
    id: 'C001',
    name: 'Government Engineering College',
    type: 'Higher Education',
    location: 'Cuttack',
    status: 'PENDING',
    icon: GraduationCap,
    description: 'Academic campus comprising lecture halls, hostels, research labs, and libraries.',
  },
  {
    id: 'TECH01',
    name: 'Enterprise IT Campus',
    type: 'Company Campus',
    location: 'Infocity, Bhubaneswar',
    status: 'PENDING',
    icon: Building,
    description: 'Multi-tenant corporate park with data centers and office facilities.',
  },
  {
    id: 'BMC01',
    name: 'Municipal Civic Center',
    type: 'Municipal Facility',
    location: 'Bhubaneswar',
    status: 'PENDING',
    icon: Landmark,
    description: 'Urban municipal headquarters and public administrative complex.',
  },
  {
    id: 'IND01',
    name: 'Industrial Estate Hub',
    type: 'Industrial Estate',
    location: 'Paradeep',
    status: 'PENDING',
    icon: Factory,
    description: 'Manufacturing and heavy fabrication industrial zone with grid substation.',
  },
  {
    id: 'PSU01',
    name: 'PSU Energy & Smelter Complex',
    type: 'PSU Facility',
    location: 'Angul',
    status: 'PENDING',
    icon: Cpu,
    description: 'Public sector metallurgical processing and captive power unit.',
  },
];

export default function FacilitySelector({ selectedFacility, onSelectFacility }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const current = FACILITIES.find(f => f.id === selectedFacility.id) || FACILITIES[0];
  const IconComponent = current.icon;

  return (
    <div className="facility-selector-wrap" ref={dropdownRef}>
      <button
        type="button"
        className={`facility-btn ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title="Switch Facility"
      >
        <span className="facility-icon">
          <IconComponent size={18} />
        </span>
        <div className="facility-text">
          <span className="facility-name">{current.name}</span>
          <span className="facility-meta">{current.type} • {current.location}</span>
        </div>
        <ChevronDown size={14} style={{ color: 'var(--text-muted)', marginLeft: '0.2rem' }} />
      </button>

      {isOpen && (
        <div className="facility-dropdown" role="listbox">
          <div className="dropdown-header">Select Facility</div>
          {FACILITIES.map((facility) => {
            const FacilityIcon = facility.icon;
            const isSelected = facility.id === current.id;
            return (
              <button
                key={facility.id}
                type="button"
                className={`facility-option ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  onSelectFacility(facility);
                  setIsOpen(false);
                }}
                role="option"
                aria-selected={isSelected}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <FacilityIcon size={16} style={{ color: facility.status === 'ACTIVE' ? 'var(--status-normal)' : 'var(--text-muted)' }} />
                  <div className="facility-option-info">
                    <span className="facility-option-title">{facility.name}</span>
                    <span className="facility-option-desc">{facility.type} • {facility.location}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span className={`facility-status-tag ${facility.status === 'ACTIVE' ? 'active' : 'pending'}`}>
                    {facility.status === 'ACTIVE' ? 'LIVE' : 'TELEMETRY PENDING'}
                  </span>
                  {isSelected && <Check size={14} style={{ color: 'var(--status-normal)' }} />}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
