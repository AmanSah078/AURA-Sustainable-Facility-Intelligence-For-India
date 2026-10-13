package com.aura.service;

import com.aura.dto.EnergyIngestRequest;
import com.aura.dto.ReplayStatusResponse;
import com.aura.entity.EnergyReading;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Service managing dataset replay / sensor simulation.
 * Replays sequential 15-minute readings from data/energy.csv through Spring Boot's ingestion API.
 * Never writes directly to MySQL; strictly uses energyService.ingestEnergyReading.
 */
@Service
public class ReplayService {

    private static final Logger log = LoggerFactory.getLogger(ReplayService.class);

    // Deterministic demo window: 06-01-2026 14:00 to 17:00 (Emergency ward)
    // Normal (168-171 kWh) -> Anomaly Spike at 15:30 (364.61 kWh) -> Normal recovery (174-177 kWh)
    private static final String DEFAULT_ZONE = "Emergency";
    private static final String DEMO_START_TIME = "06-01-2026 14:00";
    private static final String DEMO_END_TIME = "06-01-2026 17:00";

    private final EnergyService energyService;
    private final List<EnergyIngestRequest> replayQueue = new ArrayList<>();
    private final AtomicInteger currentIndex = new AtomicInteger(0);
    private final AtomicBoolean isRunning = new AtomicBoolean(false);

    private ScheduledExecutorService executorService;
    private ScheduledFuture<?> replayFuture;
    private int speedMs = 3000;

    public ReplayService(EnergyService energyService) {
        this.energyService = energyService;
        loadReplayData();
    }

    /**
     * Load demo sequence from data/energy.csv
     */
    public synchronized void loadReplayData() {
        replayQueue.clear();
        File csvFile = findEnergyCsvFile();

        if (csvFile != null && csvFile.exists()) {
            try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
                String headerLine = br.readLine();
                if (headerLine != null) {
                    String[] headers = headerLine.split(",");
                    int tsIdx = -1, facIdx = -1, zoneIdx = -1, kwhIdx = -1, occIdx = -1, tempIdx = -1;

                    for (int i = 0; i < headers.length; i++) {
                        String h = headers[i].trim().toLowerCase();
                        if (h.equals("timestamp")) tsIdx = i;
                        else if (h.equals("facility_id")) facIdx = i;
                        else if (h.equals("zone_id")) zoneIdx = i;
                        else if (h.equals("energy_kwh")) kwhIdx = i;
                        else if (h.equals("occupancy_percent")) occIdx = i;
                        else if (h.equals("temperature_c")) tempIdx = i;
                    }

                    String line;
                    while ((line = br.readLine()) != null) {
                        String[] parts = line.split(",");
                        if (parts.length > Math.max(tsIdx, kwhIdx)) {
                            String zone = zoneIdx >= 0 ? parts[zoneIdx].trim() : "Emergency";
                            String ts = tsIdx >= 0 ? parts[tsIdx].trim() : "";

                            if (zone.equalsIgnoreCase(DEFAULT_ZONE) && ts.startsWith("06-01-2026")) {
                                String timePart = ts.contains(" ") ? ts.split(" ")[1] : "";
                                if (timePart.compareTo("14:00") >= 0 && timePart.compareTo("17:00") <= 0) {
                                    BigDecimal kwh = new BigDecimal(parts[kwhIdx].trim());
                                    EnergyIngestRequest req = new EnergyIngestRequest();
                                    req.setFacilityId(facIdx >= 0 ? parts[facIdx].trim() : "H001");
                                    req.setZoneId(DEFAULT_ZONE);
                                    req.setTimestamp(ts);
                                    req.setEnergyKwh(kwh);
                                    if (occIdx >= 0 && occIdx < parts.length && !parts[occIdx].isBlank()) {
                                        req.setOccupancyPercent(new BigDecimal(parts[occIdx].trim()));
                                    }
                                    if (tempIdx >= 0 && tempIdx < parts.length && !parts[tempIdx].isBlank()) {
                                        req.setTemperatureC(new BigDecimal(parts[tempIdx].trim()));
                                    }
                                    req.setSource("replay_sensor");
                                    replayQueue.add(req);
                                }
                            }
                        }
                    }
                }
            } catch (Exception e) {
                log.error("Failed to read data/energy.csv: {}", e.getMessage(), e);
            }
        }

        // Fallback to embedded validated demo sequence if file couldn't be loaded
        if (replayQueue.isEmpty()) {
            loadFallbackQueue();
        }

        log.info("Loaded {} telemetry records into Replay Queue for zone '{}'", replayQueue.size(), DEFAULT_ZONE);
    }

    private void loadFallbackQueue() {
        replayQueue.clear();
        String[][] raw = {
                {"06-01-2026 14:00", "166.50", "42.0", "22.5"},
                {"06-01-2026 14:15", "167.80", "45.0", "22.6"},
                {"06-01-2026 14:30", "169.76", "48.0", "22.7"},
                {"06-01-2026 14:45", "168.48", "50.0", "22.8"},
                {"06-01-2026 15:00", "171.58", "52.0", "23.0"},
                {"06-01-2026 15:15", "170.38", "55.0", "23.1"},
                {"06-01-2026 15:30", "364.61", "88.0", "26.4"}, // ANOMALY SPIKE
                {"06-01-2026 15:45", "175.89", "56.0", "23.5"},
                {"06-01-2026 16:00", "177.88", "54.0", "23.4"},
                {"06-01-2026 16:15", "174.95", "51.0", "23.2"},
                {"06-01-2026 16:30", "172.10", "49.0", "23.0"},
                {"06-01-2026 16:45", "169.40", "46.0", "22.8"},
                {"06-01-2026 17:00", "167.30", "44.0", "22.6"}
        };
        for (String[] r : raw) {
            EnergyIngestRequest req = new EnergyIngestRequest();
            req.setFacilityId("H001");
            req.setZoneId("Emergency");
            req.setTimestamp(r[0]);
            req.setEnergyKwh(new BigDecimal(r[1]));
            req.setOccupancyPercent(new BigDecimal(r[2]));
            req.setTemperatureC(new BigDecimal(r[3]));
            req.setSource("replay_sensor");
            replayQueue.add(req);
        }
    }

    private File findEnergyCsvFile() {
        File[] candidates = {
                new File("data/energy.csv"),
                new File("../data/energy.csv"),
                new File("c:/BPUT_HACK_2026/data/energy.csv")
        };
        for (File f : candidates) {
            if (f.exists()) return f;
        }
        return null;
    }

    /**
     * Start or resume the replay simulation.
     */
    public synchronized ReplayStatusResponse startReplay(Integer customSpeedMs) {
        if (customSpeedMs != null && customSpeedMs >= 500) {
            this.speedMs = customSpeedMs;
        }

        if (currentIndex.get() >= replayQueue.size()) {
            currentIndex.set(0); // auto-rewind on restart
        }

        if (isRunning.compareAndSet(false, true)) {
            if (executorService == null || executorService.isShutdown()) {
                executorService = Executors.newSingleThreadScheduledExecutor();
            }

            replayFuture = executorService.scheduleWithFixedDelay(
                    this::stepReplay,
                    0,
                    this.speedMs,
                    TimeUnit.MILLISECONDS
            );
            log.info("Replay started at speed {} ms per interval", this.speedMs);
        }

        return getStatus();
    }

    /**
     * Pause / Stop the replay simulation.
     */
    public synchronized ReplayStatusResponse stopReplay() {
        if (isRunning.compareAndSet(true, false)) {
            if (replayFuture != null) {
                replayFuture.cancel(false);
            }
            log.info("Replay paused at index {} / {}", currentIndex.get(), replayQueue.size());
        }
        return getStatus();
    }

    @PostConstruct
    public void init() {
        resetReplay();
    }

    /**
     * Reset replay index to beginning and restore clean baseline telemetry in MySQL.
     */
    public synchronized ReplayStatusResponse resetReplay() {
        stopReplay();
        currentIndex.set(0);

        // Ingest clean baseline reading (06-01-2026 14:00, 166.50 kWh) so initial dashboard state is 100% Normal
        if (!replayQueue.isEmpty()) {
            EnergyIngestRequest baselineReq = replayQueue.get(0);
            try {
                energyService.ingestEnergyReading(baselineReq);
                log.info("Reset replay to clean baseline at {} ({} kWh)", baselineReq.getTimestamp(), baselineReq.getEnergyKwh());
            } catch (Exception e) {
                log.warn("Could not ingest baseline record on reset: {}", e.getMessage());
            }
        }

        return getStatus();
    }

    /**
     * Single step forward in replay sequence.
     */
    public void stepReplay() {
        int idx = currentIndex.get();
        if (idx >= replayQueue.size()) {
            log.info("Replay sequence completed ({} records ingested).", replayQueue.size());
            stopReplay();
            return;
        }

        EnergyIngestRequest request = replayQueue.get(idx);
        try {
            EnergyReading saved = energyService.ingestEnergyReading(request);
            log.info("[REPLAY SENSOR] [{}/{}] Ingested {} | Load: {} kWh | ID: {}",
                    idx + 1, replayQueue.size(), saved.getTimestamp(), saved.getEnergyKwh(), saved.getId());
            currentIndex.incrementAndGet();
        } catch (Exception e) {
            log.error("[REPLAY SENSOR] Failed to ingest record at index {}: {}", idx, e.getMessage());
        }
    }

    /**
     * Get current replay simulation status.
     */
    public ReplayStatusResponse getStatus() {
        int idx = Math.min(currentIndex.get(), replayQueue.size());
        String statusStr = isRunning.get() ? "RUNNING" : (idx >= replayQueue.size() && idx > 0 ? "COMPLETED" : (idx > 0 ? "PAUSED" : "IDLE"));

        String currentTs = "";
        BigDecimal currentKwh = BigDecimal.ZERO;
        boolean isAnomaly = false;

        if (!replayQueue.isEmpty()) {
            int displayIdx = Math.max(0, Math.min(idx > 0 ? idx - 1 : 0, replayQueue.size() - 1));
            EnergyIngestRequest lastReq = replayQueue.get(displayIdx);
            currentTs = lastReq.getTimestamp();
            currentKwh = lastReq.getEnergyKwh();
            isAnomaly = currentKwh.compareTo(new BigDecimal("250.0")) > 0;
        }

        return new ReplayStatusResponse(
                statusStr,
                currentTs,
                idx,
                replayQueue.size(),
                this.speedMs,
                DEFAULT_ZONE,
                currentKwh,
                isAnomaly
        );
    }

    @PreDestroy
    public void cleanup() {
        stopReplay();
        if (executorService != null) {
            executorService.shutdownNow();
        }
    }
}
