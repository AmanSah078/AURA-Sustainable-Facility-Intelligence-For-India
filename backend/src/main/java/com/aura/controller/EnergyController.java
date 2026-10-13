package com.aura.controller;

import com.aura.dto.EnergyIngestRequest;
import com.aura.dto.EnergyIntelligenceResponse;
import com.aura.dto.ReplayStatusResponse;
import com.aura.entity.EnergyIntelligence;
import com.aura.entity.EnergyReading;
import com.aura.service.EnergyService;
import com.aura.service.ReplayService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST Controller exposing Facility, Energy Intelligence, Ingestion, and Replay endpoints.
 * Calls Spring Boot EnergyService and ReplayService.
 */
@RestController
@RequestMapping("/api/v1/energy")
@CrossOrigin(origins = "*")
public class EnergyController {

    private final EnergyService energyService;
    private final ReplayService replayService;

    // Normalization map for user-friendly case-insensitive zone queries
    private static final Map<String, String> ZONE_MAP = Map.of(
            "admin", "Admin",
            "emergency", "Emergency",
            "general_ward", "General_Ward",
            "generalward", "General_Ward",
            "general ward", "General_Ward",
            "icu", "ICU",
            "opd", "OPD"
    );

    public EnergyController(EnergyService energyService, ReplayService replayService) {
        this.energyService = energyService;
        this.replayService = replayService;
    }

    private String normalizeZone(String zoneId) {
        if (zoneId == null) {
            return null;
        }
        return ZONE_MAP.getOrDefault(zoneId.trim().toLowerCase(), zoneId);
    }

    /**
     * Ingest a single energy reading from IoT sensor or Replay Engine into MySQL.
     * POST /api/v1/energy/ingest
     */
    @PostMapping("/ingest")
    public ResponseEntity<EnergyReading> ingestReading(@Valid @RequestBody EnergyIngestRequest request) {
        String canonicalZone = normalizeZone(request.getZoneId());
        request.setZoneId(canonicalZone);
        EnergyReading saved = energyService.ingestEnergyReading(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    /**
     * Retrieve recent energy readings for a facility and zone.
     * GET /api/v1/energy/readings?facilityId=H001&zoneId=EMERGENCY&limit=20
     */
    @GetMapping("/readings")
    public ResponseEntity<List<EnergyReading>> getRecentReadings(
            @RequestParam(defaultValue = "H001") String facilityId,
            @RequestParam String zoneId,
            @RequestParam(defaultValue = "20") int limit) {

        String canonicalZone = normalizeZone(zoneId);
        List<EnergyReading> readings = energyService.getRecentReadings(facilityId, canonicalZone, limit);
        return ResponseEntity.ok(readings);
    }

    /**
     * Retrieve the most recent energy reading for a facility and zone.
     * GET /api/v1/energy/readings/latest?facilityId=H001&zoneId=EMERGENCY
     */
    @GetMapping("/readings/latest")
    public ResponseEntity<EnergyReading> getLatestReading(
            @RequestParam(defaultValue = "H001") String facilityId,
            @RequestParam String zoneId) {

        String canonicalZone = normalizeZone(zoneId);
        return energyService.getLatestReading(facilityId, canonicalZone)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Retrieve live Energy Intelligence for a facility and zone from FastAPI Python AI Engine.
     * GET /api/v1/energy/intelligence?facilityId=H001&zoneId=EMERGENCY
     * GET /api/v1/energy/intelligence?zone_id=EMERGENCY
     */
    @GetMapping("/intelligence")
    public ResponseEntity<?> getEnergyIntelligence(
            @RequestParam(defaultValue = "H001") String facilityId,
            @RequestParam(required = false) String zoneId,
            @RequestParam(name = "zone_id", required = false) String zoneIdSnake) {

        String rawZone = (zoneId != null && !zoneId.isBlank()) ? zoneId : zoneIdSnake;
        if (rawZone != null && !rawZone.isBlank()) {
            String canonicalZone = normalizeZone(rawZone);
            EnergyIntelligenceResponse response = energyService.getEnergyIntelligenceFromAi(facilityId, canonicalZone);
            return ResponseEntity.ok(response);
        } else {
            List<EnergyIntelligenceResponse> responses = energyService.getAllZonesEnergyIntelligenceFromAi(facilityId);
            return ResponseEntity.ok(responses);
        }
    }

    /**
     * Retrieve recent active anomalies for alert notifications from persistent database.
     * GET /api/v1/energy/anomalies?facilityId=H001&limit=20
     */
    @GetMapping("/anomalies")
    public ResponseEntity<List<EnergyIntelligence>> getActiveAnomalies(
            @RequestParam(defaultValue = "H001") String facilityId,
            @RequestParam(defaultValue = "20") int limit) {

        return ResponseEntity.ok(energyService.getActiveAnomalies(facilityId, limit));
    }

    // =========================================================================
    // Dataset Replay / Synthetic Sensor Simulation Endpoints
    // =========================================================================

    /**
     * Start or resume synthetic sensor replay.
     * POST /api/v1/energy/replay/start?speedMs=3000
     */
    @PostMapping("/replay/start")
    public ResponseEntity<ReplayStatusResponse> startReplay(
            @RequestParam(defaultValue = "3000") int speedMs) {
        return ResponseEntity.ok(replayService.startReplay(speedMs));
    }

    /**
     * Pause / Stop synthetic sensor replay.
     * POST /api/v1/energy/replay/stop
     */
    @PostMapping("/replay/stop")
    public ResponseEntity<ReplayStatusResponse> stopReplay() {
        return ResponseEntity.ok(replayService.stopReplay());
    }

    /**
     * Reset synthetic sensor replay to the start of the demo window.
     * POST /api/v1/energy/replay/reset
     */
    @PostMapping("/replay/reset")
    public ResponseEntity<ReplayStatusResponse> resetReplay() {
        return ResponseEntity.ok(replayService.resetReplay());
    }

    /**
     * Get status of synthetic sensor replay.
     * GET /api/v1/energy/replay/status
     */
    @GetMapping("/replay/status")
    public ResponseEntity<ReplayStatusResponse> getReplayStatus() {
        return ResponseEntity.ok(replayService.getStatus());
    }
}
