import React from 'react';

export default function LoadingSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* KPI Skeleton Grid */}
      <div className="kpi-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="kpi-card">
            <div className="skeleton skeleton-text" />
            <div className="skeleton skeleton-val" />
            <div className="skeleton skeleton-text" style={{ width: '40%' }} />
          </div>
        ))}
      </div>

      {/* Attention Skeleton */}
      <div className="card-panel" style={{ height: '110px' }}>
        <div className="skeleton skeleton-val" style={{ width: '50%', height: '22px' }} />
        <div className="skeleton skeleton-text" style={{ width: '90%', height: '16px', marginTop: '10px' }} />
      </div>

      {/* 2-Col Grid Skeleton */}
      <div className="dashboard-grid-2col">
        <div className="card-panel" style={{ height: '260px' }}>
          <div className="skeleton skeleton-text" style={{ width: '40%' }} />
          <div className="skeleton" style={{ width: '100%', height: '180px', marginTop: '15px' }} />
        </div>
        <div className="card-panel" style={{ height: '260px' }}>
          <div className="skeleton skeleton-text" style={{ width: '40%' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '15px' }}>
            {[1, 2, 3, 4].map((j) => (
              <div key={j} className="skeleton" style={{ width: '100%', height: '40px' }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
