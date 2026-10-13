import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="error-card">
      <div className="error-icon-wrap">
        <AlertCircle size={26} />
      </div>

      <div>
        <h3 className="error-title">Unable to Load Energy Intelligence</h3>
        <p className="error-desc" style={{ marginTop: '0.4rem' }}>
          {error || 'The backend service is currently unreachable. Please ensure Spring Boot and FastAPI services are running.'}
        </p>
      </div>

      <button type="button" className="btn-primary" onClick={onRetry}>
        <RefreshCw size={15} />
        <span>Retry Connection</span>
      </button>
    </div>
  );
}
