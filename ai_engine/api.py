"""
AURA — AI-Powered Sustainable Facility Intelligence Platform
Module: Energy Intelligence API Layer (FastAPI)

Architecture:
  Spring Boot / React UI
          ↓  (HTTP Request)
     FastAPI (ai_engine/api.py)
          ↓  (Service Call)
  EnergyIntelligenceService (ai_engine/energy_service.py)
          ↓  (JSON Response conforming to Contract)

This module handles HTTP routing, query parsing, error handling, and CORS.
All machine learning, anomaly detection, and forecasting logic is delegated
strictly to EnergyIntelligenceService.
"""

from typing import Optional, List, Dict, Union, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ai_engine.energy_service import EnergyIntelligenceService

# Initialize FastAPI application
app = FastAPI(
    title="AURA Facility Intelligence API",
    description="Operational Decision Support REST API for Hospital Facility Intelligence",
    version="1.0.0"
)

# CORS Configuration:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instance
energy_service = EnergyIntelligenceService()

# Mapping for user-friendly case-insensitive zone matching
ZONE_ALIAS_MAP = {
    "admin": "Admin",
    "emergency": "Emergency",
    "general_ward": "General_Ward",
    "general ward": "General_Ward",
    "generalward": "General_Ward",
    "icu": "ICU",
    "opd": "OPD",
}

VALID_ZONES_DISPLAY = ["ICU", "EMERGENCY", "GENERAL_WARD", "OPD", "ADMIN"]


@app.on_event("startup")
def startup_event():
    """
    Pre-warm the energy intelligence service on server startup
    so initial requests experience zero initialization latency.
    """
    energy_service.load_and_prepare_data()


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """
    Lightweight health check endpoint for container probes and Spring Boot pinging.
    """
    return {"status": "ok"}


@app.get(
    "/api/v1/energy/intelligence",
    tags=["Energy Intelligence"],
    summary="Get Energy Intelligence"
)
def get_energy_intelligence(
    zone_id: Optional[str] = Query(
        None,
        description="Optional hospital zone identifier (e.g. ICU, EMERGENCY, GENERAL_WARD, OPD, ADMIN). If omitted, returns all zones."
    ),
    timestamp: Optional[str] = Query(
        None,
        description="Optional specific reading timestamp (DD-MM-YYYY HH:MM). If omitted, uses the latest reading."
    )
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns energy intelligence adhering strictly to the Energy Intelligence Contract.
    
    - If `zone_id` is provided: Returns a single zone intelligence object.
    - If `zone_id` is omitted: Returns latest intelligence across all five hospital zones.
    """
    # Case 1: Return latest intelligence across all hospital zones
    if zone_id is None:
        return energy_service.get_latest_intelligence_all_zones()

    # Case 2: Match and validate specific zone_id
    normalized_key = zone_id.strip().lower()
    canonical_zone = ZONE_ALIAS_MAP.get(normalized_key)

    if not canonical_zone:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown zone_id: '{zone_id}'. Valid zones are: {', '.join(VALID_ZONES_DISPLAY)}"
        )

    try:
        return energy_service.get_energy_intelligence(
            zone_id=canonical_zone,
            timestamp=timestamp
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
