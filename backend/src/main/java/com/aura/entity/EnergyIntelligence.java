package com.aura.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "energy_intelligence")
public class EnergyIntelligence {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "facility_id", length = 32, nullable = false)
    private String facilityId;

    @Column(name = "zone_id", length = 32, nullable = false)
    private String zoneId;

    @Column(name = "timestamp", nullable = false)
    private LocalDateTime timestamp;

    @Column(name = "current_energy_kwh", precision = 10, scale = 2, nullable = false)
    private BigDecimal currentEnergyKwh;

    @Column(name = "anomaly_detected", nullable = false)
    private Boolean anomalyDetected;

    @Column(name = "anomaly_score", precision = 6, scale = 3, nullable = false)
    private BigDecimal anomalyScore;

    @Column(name = "forecast_energy_kwh", precision = 10, scale = 2, nullable = false)
    private BigDecimal forecastEnergyKwh;

    @Column(name = "forecast_horizon", length = 32)
    private String forecastHorizon;

    @Column(name = "recommendation", nullable = false, columnDefinition = "TEXT")
    private String recommendation;

    @Column(name = "source", length = 32)
    private String source;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;

    public EnergyIntelligence() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
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

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    public BigDecimal getCurrentEnergyKwh() {
        return currentEnergyKwh;
    }

    public void setCurrentEnergyKwh(BigDecimal currentEnergyKwh) {
        this.currentEnergyKwh = currentEnergyKwh;
    }

    public Boolean getAnomalyDetected() {
        return anomalyDetected;
    }

    public void setAnomalyDetected(Boolean anomalyDetected) {
        this.anomalyDetected = anomalyDetected;
    }

    public BigDecimal getAnomalyScore() {
        return anomalyScore;
    }

    public void setAnomalyScore(BigDecimal anomalyScore) {
        this.anomalyScore = anomalyScore;
    }

    public BigDecimal getForecastEnergyKwh() {
        return forecastEnergyKwh;
    }

    public void setForecastEnergyKwh(BigDecimal forecastEnergyKwh) {
        this.forecastEnergyKwh = forecastEnergyKwh;
    }

    public String getForecastHorizon() {
        return forecastHorizon;
    }

    public void setForecastHorizon(String forecastHorizon) {
        this.forecastHorizon = forecastHorizon;
    }

    public String getRecommendation() {
        return recommendation;
    }

    public void setRecommendation(String recommendation) {
        this.recommendation = recommendation;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
