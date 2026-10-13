package com.aura.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * DTO for ingesting real-time or replayed sensor readings into Spring Boot.
 * Supports both snake_case and camelCase JSON field names.
 */
public class EnergyIngestRequest {

    @JsonProperty("facility_id")
    @JsonAlias({"facilityId"})
    private String facilityId = "H001";

    @NotBlank(message = "zone_id is required")
    @JsonProperty("zone_id")
    @JsonAlias({"zoneId"})
    private String zoneId;

    @NotBlank(message = "timestamp is required")
    @JsonProperty("timestamp")
    private String timestamp;

    @NotNull(message = "energy_kwh is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "energy_kwh must be greater than 0")
    @JsonProperty("energy_kwh")
    @JsonAlias({"energyKwh"})
    private BigDecimal energyKwh;

    @JsonProperty("occupancy_percent")
    @JsonAlias({"occupancyPercent"})
    private BigDecimal occupancyPercent;

    @JsonProperty("temperature_c")
    @JsonAlias({"temperatureC"})
    private BigDecimal temperatureC;

    @JsonProperty("operational_status")
    @JsonAlias({"operationalStatus"})
    private String operationalStatus = "NORMAL";

    @JsonProperty("energy_source")
    @JsonAlias({"energySource"})
    private String energySource = "GRID";

    @JsonProperty("source")
    private String source = "replay_sensor";

    public EnergyIngestRequest() {
    }

    public EnergyIngestRequest(String facilityId, String zoneId, String timestamp, BigDecimal energyKwh) {
        this.facilityId = facilityId;
        this.zoneId = zoneId;
        this.timestamp = timestamp;
        this.energyKwh = energyKwh;
    }

    public String getFacilityId() {
        return facilityId;
    }

    public void setFacilityId(String facilityId) {
        this.facilityId = facilityId;
    }

    public String getZoneId() {
        return zoneId;
    }

    public void setZoneId(String zoneId) {
        this.zoneId = zoneId;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public BigDecimal getEnergyKwh() {
        return energyKwh;
    }

    public void setEnergyKwh(BigDecimal energyKwh) {
        this.energyKwh = energyKwh;
    }

    public BigDecimal getOccupancyPercent() {
        return occupancyPercent;
    }

    public void setOccupancyPercent(BigDecimal occupancyPercent) {
        this.occupancyPercent = occupancyPercent;
    }

    public BigDecimal getTemperatureC() {
        return temperatureC;
    }

    public void setTemperatureC(BigDecimal temperatureC) {
        this.temperatureC = temperatureC;
    }

    public String getOperationalStatus() {
        return operationalStatus;
    }

    public void setOperationalStatus(String operationalStatus) {
        this.operationalStatus = operationalStatus;
    }

    public String getEnergySource() {
        return energySource;
    }

    public void setEnergySource(String energySource) {
        this.energySource = energySource;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }
}
