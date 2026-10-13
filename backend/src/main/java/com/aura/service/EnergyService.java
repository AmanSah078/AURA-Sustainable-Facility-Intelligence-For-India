package com.aura.service;

import com.aura.client.EnergyAiClient;
import com.aura.dto.EnergyIngestRequest;
import com.aura.dto.EnergyIntelligenceResponse;
import com.aura.entity.EnergyIntelligence;
import com.aura.entity.EnergyReading;
import com.aura.entity.Facility;
import com.aura.exception.FacilityNotFoundException;
import com.aura.repository.EnergyIntelligenceRepository;
import com.aura.repository.EnergyReadingRepository;
import com.aura.repository.FacilityRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Service layer for Facility and Energy data access, ingestion, and AI service orchestration.
 * Strictly acts as the application and persistence orchestrator.
 * Contains ZERO machine learning logic; all AI remains in FastAPI / EnergyIntelligenceService.
 */
@Service
@Transactional(readOnly = true)
public class EnergyService {

    private static final Logger log = LoggerFactory.getLogger(EnergyService.class);
    private static final DateTimeFormatter TS_FORMATTER_DMY = DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm");
    private static final DateTimeFormatter TS_FORMATTER_ISO = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss");
    private static final DateTimeFormatter TS_FORMATTER_SQL = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static final List<String> HOSPITAL_ZONES = List.of("Admin", "Emergency", "General_Ward", "ICU", "OPD");

    private final FacilityRepository facilityRepository;
    private final EnergyReadingRepository energyReadingRepository;
    private final EnergyIntelligenceRepository energyIntelligenceRepository;
    private final EnergyAiClient energyAiClient;

    public EnergyService(FacilityRepository facilityRepository,
                         EnergyReadingRepository energyReadingRepository,
                         EnergyIntelligenceRepository energyIntelligenceRepository,
                         EnergyAiClient energyAiClient) {
        this.facilityRepository = facilityRepository;
        this.energyReadingRepository = energyReadingRepository;
        this.energyIntelligenceRepository = energyIntelligenceRepository;
        this.energyAiClient = energyAiClient;
    }

    /**
     * Ingest a single real-time or replayed sensor energy reading into MySQL.
     * Validates facility, fields, and parses timestamp cleanly.
     */
    @Transactional
    public EnergyReading ingestEnergyReading(EnergyIngestRequest request) {
        String facId = (request.getFacilityId() != null && !request.getFacilityId().isBlank())
                ? request.getFacilityId() : "H001";

        if (!facilityRepository.existsById(facId)) {
            log.warn("Ingest failed: Facility '{}' does not exist", facId);
            throw new FacilityNotFoundException("Facility not found: " + facId);
        }

        if (request.getZoneId() == null || request.getZoneId().isBlank()) {
            throw new IllegalArgumentException("zone_id is required");
        }

        if (request.getEnergyKwh() == null || request.getEnergyKwh().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("energy_kwh must be a positive number");
        }

        LocalDateTime parsedTimestamp = parseTimestamp(request.getTimestamp());

        EnergyReading reading = new EnergyReading();
        reading.setFacilityId(facId);
        reading.setZoneId(request.getZoneId());
        reading.setTimestamp(parsedTimestamp);
        reading.setEnergyKwh(request.getEnergyKwh());
        reading.setOccupancyPercent(request.getOccupancyPercent() != null ? request.getOccupancyPercent() : BigDecimal.ZERO);
        reading.setTemperatureC(request.getTemperatureC());
        reading.setOperationalStatus(request.getOperationalStatus() != null ? request.getOperationalStatus() : "NORMAL");
        reading.setEnergySource(request.getEnergySource() != null ? request.getEnergySource() : "GRID");
        reading.setSource(request.getSource() != null ? request.getSource() : "replay_sensor");

        EnergyReading saved = energyReadingRepository.save(reading);
        log.info("Successfully ingested energy reading [id={}, zone={}, ts={}, load={} kWh]",
                saved.getId(), saved.getZoneId(), saved.getTimestamp(), saved.getEnergyKwh());
        return saved;
    }

    /**
     * Retrieve real-time Energy Intelligence for a facility and zone from the FastAPI AI service.
     * Evaluates against the latest ingested reading timestamp in MySQL if available.
     */
    public EnergyIntelligenceResponse getEnergyIntelligenceFromAi(String facilityId, String zoneId) {
        if (facilityId != null && !facilityId.isBlank()) {
            if (!facilityRepository.existsById(facilityId)) {
                log.warn("Facility validation failed: '{}' does not exist", facilityId);
                throw new FacilityNotFoundException("Facility not found: " + facilityId);
            }
        }

        if (zoneId == null || zoneId.isBlank()) {
            throw new IllegalArgumentException("zoneId is required for energy intelligence lookup");
        }

        // Check if there is a recently ingested reading in MySQL to evaluate against (by ID insertion)
        Optional<EnergyReading> latestReadingOpt = energyReadingRepository
                .findTopByFacilityIdAndZoneIdOrderByIdDesc(facilityId, zoneId);

        String targetTimestamp = null;
        if (latestReadingOpt.isPresent()) {
            targetTimestamp = latestReadingOpt.get().getTimestamp().format(TS_FORMATTER_DMY);
        }

        try {
            return energyAiClient.fetchEnergyIntelligence(zoneId, targetTimestamp);
        } catch (Exception e) {
            if (targetTimestamp != null) {
                log.warn("Timestamp '{}' lookup in zone '{}' failed in AI service, falling back to latest model index: {}",
                        targetTimestamp, zoneId, e.getMessage());
                return energyAiClient.fetchEnergyIntelligence(zoneId, null);
            }
            throw e;
        }
    }

    /**
     * Retrieve real-time Energy Intelligence across all zones from the FastAPI AI service.
     */
    public List<EnergyIntelligenceResponse> getAllZonesEnergyIntelligenceFromAi(String facilityId) {
        if (facilityId != null && !facilityId.isBlank()) {
            if (!facilityRepository.existsById(facilityId)) {
                throw new FacilityNotFoundException("Facility not found: " + facilityId);
            }
        }

        List<EnergyIntelligenceResponse> results = new ArrayList<>();
        for (String zone : HOSPITAL_ZONES) {
            try {
                results.add(getEnergyIntelligenceFromAi(facilityId, zone));
            } catch (Exception e) {
                log.warn("Could not fetch intelligence for zone {}: {}", zone, e.getMessage());
            }
        }

        if (results.isEmpty()) {
            return energyAiClient.fetchAllZonesEnergyIntelligence();
        }
        return results;
    }

    /**
     * Retrieve facility metadata by ID (e.g. H001).
     */
    public Optional<Facility> getFacility(String facilityId) {
        return facilityRepository.findById(facilityId);
    }

    /**
     * Retrieve all configured facilities.
     */
    public List<Facility> getAllFacilities() {
        return facilityRepository.findAll();
    }

    /**
     * Retrieve the most recent energy reading for a facility and zone.
     */
    public Optional<EnergyReading> getLatestReading(String facilityId, String zoneId) {
        return energyReadingRepository.findTopByFacilityIdAndZoneIdOrderByTimestampDesc(facilityId, zoneId);
    }

    /**
     * Retrieve recent energy readings for a facility and zone with pagination limit.
     * Orders by ID descending so newly ingested sensor/replay packets are immediately returned.
     */
    public List<EnergyReading> getRecentReadings(String facilityId, String zoneId, int limit) {
        int safeLimit = Math.min(Math.max(limit, 1), 500);
        return energyReadingRepository.findByFacilityIdAndZoneIdOrderByIdDesc(
                facilityId, zoneId, PageRequest.of(0, safeLimit)
        );
    }

    /**
     * Retrieve the most recent processed energy intelligence record stored in MySQL for a zone.
     */
    public Optional<EnergyIntelligence> getLatestHistoricalIntelligence(String facilityId, String zoneId) {
        return energyIntelligenceRepository.findTopByFacilityIdAndZoneIdOrderByTimestampDesc(facilityId, zoneId);
    }

    /**
     * Retrieve recent intelligence records from MySQL for a facility and zone.
     */
    public List<EnergyIntelligence> getRecentIntelligence(String facilityId, String zoneId, int limit) {
        int safeLimit = Math.min(Math.max(limit, 1), 100);
        return energyIntelligenceRepository.findByFacilityIdAndZoneIdOrderByTimestampDesc(
                facilityId, zoneId, PageRequest.of(0, safeLimit)
        );
    }

    /**
     * Retrieve latest active anomaly alerts from MySQL for a facility.
     */
    public List<EnergyIntelligence> getActiveAnomalies(String facilityId, int limit) {
        int safeLimit = Math.min(Math.max(limit, 1), 50);
        return energyIntelligenceRepository.findByFacilityIdAndAnomalyDetectedTrueOrderByTimestampDesc(
                facilityId, PageRequest.of(0, safeLimit)
        );
    }

    private LocalDateTime parseTimestamp(String tsStr) {
        if (tsStr == null || tsStr.isBlank()) {
            return LocalDateTime.now();
        }
        try {
            return LocalDateTime.parse(tsStr, TS_FORMATTER_DMY);
        } catch (DateTimeParseException ignored) {
        }
        try {
            return LocalDateTime.parse(tsStr, TS_FORMATTER_ISO);
        } catch (DateTimeParseException ignored) {
        }
        try {
            return LocalDateTime.parse(tsStr, TS_FORMATTER_SQL);
        } catch (DateTimeParseException ignored) {
        }
        try {
            return LocalDateTime.parse(tsStr);
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException("Invalid timestamp format: '" + tsStr + "'. Supported: DD-MM-YYYY HH:mm or ISO-8601");
        }
    }
}
