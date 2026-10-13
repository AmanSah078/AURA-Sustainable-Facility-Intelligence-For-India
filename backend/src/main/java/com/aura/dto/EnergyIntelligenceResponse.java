package com.aura.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Energy Intelligence response contract.
 * Strictly exposes user-facing intelligence fields only.
 * Does NOT expose internal ML features or raw anomaly_flag.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EnergyIntelligenceResponse {

    @JsonProperty("facility_id")
    private String facilityId;

    @JsonProperty("zone_id")
    private String zoneId;

    @JsonProperty("timestamp")
    private String timestamp;

    @JsonProperty("current_energy_kwh")
    private Double currentEnergyKwh;

    @JsonProperty("anomaly_detected")
    private Boolean anomalyDetected;

    @JsonProperty("anomaly_score")
    private Double anomalyScore;

    @JsonProperty("forecast_energy_kwh")
    private Double forecastEnergyKwh;

    @JsonProperty("forecast_horizon")
    private String forecastHorizon;

    @JsonProperty("recommendation")
    private String recommendation;

    @JsonProperty("root_cause")
    private String rootCause;

    @JsonProperty("action_plan")
    private java.util.List<String> actionPlan;

    @JsonProperty("impact_metric")
    private String impactMetric;

    @JsonProperty("severity_level")
    private String severityLevel;

    @JsonProperty("excess_kwh")
    private Double excessKwh;

    @JsonProperty("source")
    private String source;

    public EnergyIntelligenceResponse() {
    }

    public EnergyIntelligenceResponse(String facilityId, String zoneId, String timestamp,
                                      Double currentEnergyKwh, Boolean anomalyDetected,
                                      Double anomalyScore, Double forecastEnergyKwh,
                                      String forecastHorizon, String recommendation,
                                      String source) {
        this.facilityId = facilityId;
        this.zoneId = zoneId;
        this.timestamp = timestamp;
        this.currentEnergyKwh = currentEnergyKwh;
        this.anomalyDetected = anomalyDetected;
        this.anomalyScore = anomalyScore;
        this.forecastEnergyKwh = forecastEnergyKwh;
        this.forecastHorizon = forecastHorizon;
        this.recommendation = recommendation;
        this.source = source;
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

    public Double getCurrentEnergyKwh() {
        return currentEnergyKwh;
    }

    public void setCurrentEnergyKwh(Double currentEnergyKwh) {
        this.currentEnergyKwh = currentEnergyKwh;
    }

    public Boolean getAnomalyDetected() {
        return anomalyDetected;
    }

    public void setAnomalyDetected(Boolean anomalyDetected) {
        this.anomalyDetected = anomalyDetected;
    }

    public Double getAnomalyScore() {
        return anomalyScore;
    }

    public void setAnomalyScore(Double anomalyScore) {
        this.anomalyScore = anomalyScore;
    }

    public Double getForecastEnergyKwh() {
        return forecastEnergyKwh;
    }

    public void setForecastEnergyKwh(Double forecastEnergyKwh) {
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

    public String getRootCause() {
        return rootCause;
    }

    public void setRootCause(String rootCause) {
        this.rootCause = rootCause;
    }

    public java.util.List<String> getActionPlan() {
        return actionPlan;
    }

    public void setActionPlan(java.util.List<String> actionPlan) {
        this.actionPlan = actionPlan;
    }

    public String getImpactMetric() {
        return impactMetric;
    }

    public void setImpactMetric(String impactMetric) {
        this.impactMetric = impactMetric;
    }

    public String getSeverityLevel() {
        return severityLevel;
    }

    public void setSeverityLevel(String severityLevel) {
        this.severityLevel = severityLevel;
    }

    public Double getExcessKwh() {
        return excessKwh;
    }

    public void setExcessKwh(Double excessKwh) {
        this.excessKwh = excessKwh;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    @Override
    public String toString() {
        return "EnergyIntelligenceResponse{" +
                "facilityId='" + facilityId + '\'' +
                ", zoneId='" + zoneId + '\'' +
                ", timestamp='" + timestamp + '\'' +
                ", currentEnergyKwh=" + currentEnergyKwh +
                ", anomalyDetected=" + anomalyDetected +
                ", anomalyScore=" + anomalyScore +
                ", forecastEnergyKwh=" + forecastEnergyKwh +
                ", forecastHorizon='" + forecastHorizon + '\'' +
                ", recommendation='" + recommendation + '\'' +
                ", source='" + source + '\'' +
                '}';
    }
}
