package com.aura;

import com.aura.dto.EnergyIngestRequest;
import com.aura.entity.EnergyIntelligence;
import com.aura.entity.EnergyReading;
import com.aura.entity.Facility;
import com.aura.service.EnergyService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class AuraApplicationTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private EnergyService energyService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("Test 1: Spring Boot context and MySQL connection succeed")
    void contextLoads() {
        assertThat(energyService).isNotNull();
    }

    @Test
    @DisplayName("Test 2: Facility H001 can be retrieved from MySQL")
    void testGetFacilityH001() throws Exception {
        Optional<Facility> facilityOpt = energyService.getFacility("H001");
        assertThat(facilityOpt).isPresent();
        Facility f = facilityOpt.get();
        assertThat(f.getFacilityId()).isEqualTo("H001");
        assertThat(f.getName()).isEqualTo("Government Hospital");
        assertThat(f.getFacilityType()).isEqualTo("HOSPITAL");

        // Verify REST endpoint
        mockMvc.perform(get("/api/v1/facilities/H001"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.facilityId").value("H001"))
                .andExpect(jsonPath("$.name").value("Government Hospital"))
                .andExpect(jsonPath("$.facilityType").value("HOSPITAL"));
    }

    @Test
    @DisplayName("Test 3: Recent energy readings can be retrieved from MySQL")
    void testGetEnergyReadings() throws Exception {
        List<EnergyReading> readings = energyService.getRecentReadings("H001", "Emergency", 10);
        assertThat(readings).isNotEmpty();
        EnergyReading r = readings.get(0);
        assertThat(r.getFacilityId()).isEqualTo("H001");
        assertThat(r.getZoneId()).isEqualTo("Emergency");
        assertThat(r.getSource()).isNotEmpty();

        // Verify REST endpoint
        mockMvc.perform(get("/api/v1/energy/readings?facilityId=H001&zoneId=EMERGENCY&limit=5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$[0].facilityId").value("H001"))
                .andExpect(jsonPath("$[0].zoneId").value("Emergency"));
    }

    @Test
    @DisplayName("Test 4: Latest energy reading can be retrieved for a zone")
    void testGetLatestReading() throws Exception {
        Optional<EnergyReading> latestOpt = energyService.getLatestReading("H001", "Emergency");
        assertThat(latestOpt).isPresent();
        EnergyReading r = latestOpt.get();
        assertThat(r.getFacilityId()).isEqualTo("H001");
        assertThat(r.getZoneId()).isEqualTo("Emergency");
        assertThat(r.getEnergyKwh()).isNotNull();

        // Verify REST endpoint
        mockMvc.perform(get("/api/v1/energy/readings/latest?facilityId=H001&zoneId=EMERGENCY"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.facilityId").value("H001"))
                .andExpect(jsonPath("$.zoneId").value("Emergency"))
                .andExpect(jsonPath("$.energyKwh").isNumber());
    }

    @Test
    @DisplayName("Test 5: Historical energy intelligence record can be retrieved from DB")
    void testGetHistoricalEnergyIntelligenceFromDb() {
        Optional<EnergyIntelligence> intelOpt = energyService.getLatestHistoricalIntelligence("H001", "Emergency");
        assertThat(intelOpt).isPresent();
        EnergyIntelligence intel = intelOpt.get();
        assertThat(intel.getFacilityId()).isEqualTo("H001");
        assertThat(intel.getZoneId()).isEqualTo("Emergency");
        assertThat(intel.getAnomalyScore()).isNotNull();
        assertThat(intel.getRecommendation()).isNotBlank();
    }

    @Test
    @DisplayName("Test 6: Live FastAPI HTTP Integration - EMERGENCY Zone")
    void testLiveFastApiEnergyIntelligenceEmergency() throws Exception {
        mockMvc.perform(get("/api/v1/energy/intelligence?facilityId=H001&zoneId=EMERGENCY"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.facility_id").value("H001"))
                .andExpect(jsonPath("$.zone_id").value("Emergency"))
                .andExpect(jsonPath("$.current_energy_kwh").isNumber())
                .andExpect(jsonPath("$.anomaly_detected").isBoolean())
                .andExpect(jsonPath("$.anomaly_score").isNumber())
                .andExpect(jsonPath("$.forecast_energy_kwh").isNumber())
                .andExpect(jsonPath("$.forecast_horizon").value("next_1_hour"))
                .andExpect(jsonPath("$.recommendation").isString())
                .andExpect(jsonPath("$.source").isNotEmpty())
                // Ensure internal ML features and anomaly_flag are NOT exposed
                .andExpect(jsonPath("$.anomaly_flag").doesNotExist())
                .andExpect(jsonPath("$.residual").doesNotExist())
                .andExpect(jsonPath("$.rolling_res_mean").doesNotExist())
                .andExpect(jsonPath("$.rolling_res_std").doesNotExist())
                .andExpect(jsonPath("$.energy_lag_96").doesNotExist())
                .andExpect(jsonPath("$.hour_sin").doesNotExist());
    }

    @Test
    @DisplayName("Test 7: Live FastAPI HTTP Integration - ICU Zone")
    void testLiveFastApiEnergyIntelligenceIcu() throws Exception {
        mockMvc.perform(get("/api/v1/energy/intelligence?facilityId=H001&zoneId=ICU"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.facility_id").value("H001"))
                .andExpect(jsonPath("$.zone_id").value("ICU"))
                .andExpect(jsonPath("$.current_energy_kwh").isNumber())
                .andExpect(jsonPath("$.anomaly_detected").isBoolean())
                .andExpect(jsonPath("$.anomaly_score").isNumber())
                .andExpect(jsonPath("$.forecast_energy_kwh").isNumber())
                .andExpect(jsonPath("$.forecast_horizon").value("next_1_hour"))
                .andExpect(jsonPath("$.recommendation").isString())
                .andExpect(jsonPath("$.anomaly_flag").doesNotExist());
    }

    @Test
    @DisplayName("Test 8: Invalid Zone Error Handling")
    void testInvalidZoneErrorHandling() throws Exception {
        mockMvc.perform(get("/api/v1/energy/intelligence?facilityId=H001&zoneId=INVALID_ZONE"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.error").value("Bad Request"))
                .andExpect(jsonPath("$.message").isNotEmpty());
    }

    @Test
    @DisplayName("Test 9: Invalid Facility Error Handling")
    void testInvalidFacilityErrorHandling() throws Exception {
        mockMvc.perform(get("/api/v1/energy/intelligence?facilityId=INVALID_FACILITY&zoneId=EMERGENCY"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.status").value(404))
                .andExpect(jsonPath("$.error").value("Not Found"))
                .andExpect(jsonPath("$.message").value("Facility not found: INVALID_FACILITY"));
    }

    @Test
    @DisplayName("Test 10: Ingest Telemetry Reading via POST /api/v1/energy/ingest")
    void testIngestEnergyReading() throws Exception {
        EnergyIngestRequest request = new EnergyIngestRequest();
        request.setFacilityId("H001");
        request.setZoneId("Emergency");
        request.setTimestamp("06-01-2026 15:30");
        request.setEnergyKwh(new BigDecimal("364.61"));
        request.setOccupancyPercent(new BigDecimal("88.0"));
        request.setTemperatureC(new BigDecimal("26.4"));
        request.setSource("replay_sensor");

        mockMvc.perform(post("/api/v1/energy/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").isNumber())
                .andExpect(jsonPath("$.facilityId").value("H001"))
                .andExpect(jsonPath("$.zoneId").value("Emergency"))
                .andExpect(jsonPath("$.energyKwh").value(364.61));
    }

    @Test
    @DisplayName("Test 11: Replay Status Endpoint")
    void testReplayStatus() throws Exception {
        mockMvc.perform(get("/api/v1/energy/replay/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").isNotEmpty())
                .andExpect(jsonPath("$.zone_id").value("Emergency"));
    }
}
