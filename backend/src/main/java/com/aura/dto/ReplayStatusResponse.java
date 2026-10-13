package com.aura.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

public class ReplayStatusResponse {

    @JsonProperty("status")
    private String status;

    @JsonProperty("current_timestamp")
    private String currentTimestamp;

    @JsonProperty("current_index")
    private int currentIndex;

    @JsonProperty("total_records")
    private int totalRecords;

    @JsonProperty("speed_ms")
    private int speedMs;

    @JsonProperty("zone_id")
    private String zoneId;

    @JsonProperty("current_energy_kwh")
    private BigDecimal currentEnergyKwh;

    @JsonProperty("is_anomaly_current")
    private boolean isAnomalyCurrent;

    public ReplayStatusResponse() {
    }

    public ReplayStatusResponse(String status, String currentTimestamp, int currentIndex,
                                int totalRecords, int speedMs, String zoneId,
                                BigDecimal currentEnergyKwh, boolean isAnomalyCurrent) {
        this.status = status;
        this.currentTimestamp = currentTimestamp;
        this.currentIndex = currentIndex;
        this.totalRecords = totalRecords;
        this.speedMs = speedMs;
        this.zoneId = zoneId;
        this.currentEnergyKwh = currentEnergyKwh;
        this.isAnomalyCurrent = isAnomalyCurrent;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getCurrentTimestamp() {
        return currentTimestamp;
    }

    public void setCurrentTimestamp(String currentTimestamp) {
        this.currentTimestamp = currentTimestamp;
    }

    public int getCurrentIndex() {
        return currentIndex;
    }

    public void setCurrentIndex(int currentIndex) {
        this.currentIndex = currentIndex;
    }

    public int getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(int totalRecords) {
        this.totalRecords = totalRecords;
    }

    public int getSpeedMs() {
        return speedMs;
    }

    public void setSpeedMs(int speedMs) {
        this.speedMs = speedMs;
    }

    public String getZoneId() {
        return zoneId;
    }

    public void setZoneId(String zoneId) {
        this.zoneId = zoneId;
    }

    public BigDecimal getCurrentEnergyKwh() {
        return currentEnergyKwh;
    }

    public void setCurrentEnergyKwh(BigDecimal currentEnergyKwh) {
        this.currentEnergyKwh = currentEnergyKwh;
    }

    public boolean isAnomalyCurrent() {
        return isAnomalyCurrent;
    }

    public void setAnomalyCurrent(boolean anomalyCurrent) {
        isAnomalyCurrent = anomalyCurrent;
    }
}
