import React from 'react';
import { Zap, Droplets, Trash2, Leaf, Wrench, ShieldAlert, Car } from 'lucide-react';

export const MODULES = [
  { id: 'energy', name: 'Energy', icon: Zap, isLive: true },
  { id: 'water', name: 'Water', icon: Droplets, isLive: false },
  { id: 'waste', name: 'Waste', icon: Trash2, isLive: false },
  { id: 'environment', name: 'Environment', icon: Leaf, isLive: false },
  { id: 'equipment', name: 'Equipment', icon: Wrench, isLive: false },
  { id: 'safety', name: 'Safety', icon: ShieldAlert, isLive: false },
  { id: 'traffic', name: 'Traffic', icon: Car, isLive: false },
];

export default function ModuleNavigation({ activeModule, onSelectModule }) {
  return (
    <div className="module-nav-wrap">
      <nav className="module-nav" aria-label="Facility Intelligence Modules">
        {MODULES.map((module) => {
          const Icon = module.icon;
          const isActive = activeModule === module.id;
          return (
            <button
              key={module.id}
              type="button"
              className={`module-tab ${isActive ? 'active' : ''}`}
              onClick={() => onSelectModule(module.id)}
            >
              <Icon size={15} style={{ color: isActive ? 'var(--status-normal)' : 'inherit' }} />
              <span>{module.name}</span>
              <span className={`module-badge ${module.isLive ? 'live' : 'pending'}`}>
                {module.isLive ? 'Active' : 'Pending'}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
