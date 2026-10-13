package com.aura.client;

import com.aura.dto.EnergyIntelligenceResponse;
import com.aura.exception.AiServiceTimeoutException;
import com.aura.exception.AiServiceUnavailableException;
import com.aura.exception.InvalidZoneException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.net.SocketTimeoutException;
import java.util.List;

/**
 * Synchronous HTTP Client for FastAPI Energy Intelligence service.
 * Handles HTTP requests, timeouts, and error propagation cleanly.
 * Performs ZERO ML logic in Java.
 */
@Component
public class EnergyAiClient {

    private static final Logger log = LoggerFactory.getLogger(EnergyAiClient.class);
    private static final String ENERGY_INTELLIGENCE_PATH = "/api/v1/energy/intelligence";

    private final RestClient aiRestClient;
    private final ObjectMapper objectMapper;

    @Value("${ai.service.base-url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    public EnergyAiClient(RestClient aiRestClient, ObjectMapper objectMapper) {
        this.aiRestClient = aiRestClient;
        this.objectMapper = objectMapper;
    }

    /**
     * Fetch real-time energy intelligence for a specific zone from FastAPI service.
     */
    public EnergyIntelligenceResponse fetchEnergyIntelligence(String zoneId) {
        return fetchEnergyIntelligence(zoneId, null);
    }

    /**
     * Fetch energy intelligence for a specific zone and timestamp from FastAPI service.
     */
    public EnergyIntelligenceResponse fetchEnergyIntelligence(String zoneId, String timestamp) {
        log.info("Calling FastAPI Energy Intelligence endpoint: {}?zone_id={}&timestamp={}", ENERGY_INTELLIGENCE_PATH, zoneId, timestamp);

        try {
            return aiRestClient.get()
                    .uri(uriBuilder -> {
                        var builder = uriBuilder
                                .path(ENERGY_INTELLIGENCE_PATH)
                                .queryParam("zone_id", zoneId);
                        if (timestamp != null && !timestamp.isBlank()) {
                            builder.queryParam("timestamp", timestamp);
                        }
                        return builder.build();
                    })
                    .retrieve()
                    .onStatus(HttpStatusCode::is4xxClientError, (request, response) -> {
                        String body = new String(response.getBody().readAllBytes());
                        String detail = extractDetailMessage(body, "Invalid request for zone: " + zoneId);
                        throw new InvalidZoneException(detail);
                    })
                    .onStatus(HttpStatusCode::is5xxServerError, (request, response) -> {
                        String body = new String(response.getBody().readAllBytes());
                        String detail = extractDetailMessage(body, "FastAPI internal error");
                        throw new AiServiceUnavailableException("AI Service returned server error: " + detail);
                    })
                    .body(EnergyIntelligenceResponse.class);

        } catch (InvalidZoneException e) {
            throw e;
        } catch (ResourceAccessException e) {
            if (e.getCause() instanceof SocketTimeoutException || e.getMessage().contains("timed out") || e.getMessage().contains("timeout")) {
                log.error("Timeout connecting to FastAPI at {}: {}", aiServiceBaseUrl, e.getMessage());
                throw new AiServiceTimeoutException("AI Energy Intelligence service timed out at " + aiServiceBaseUrl);
            }
            log.error("FastAPI unreachable at {}: {}", aiServiceBaseUrl, e.getMessage());
            throw new AiServiceUnavailableException(
                    "AI Energy Intelligence service is unavailable at " + aiServiceBaseUrl +
                    ". Please verify FastAPI service is running."
            );
        } catch (HttpClientErrorException e) {
            String detail = extractDetailMessage(e.getResponseBodyAsString(), e.getMessage());
            throw new InvalidZoneException(detail);
        } catch (HttpServerErrorException e) {
            throw new AiServiceUnavailableException("FastAPI returned server error: " + e.getMessage());
        } catch (Exception e) {
            if (e.getMessage() != null && (e.getMessage().contains("Connection refused") || e.getMessage().contains("ConnectException"))) {
                throw new AiServiceUnavailableException(
                        "AI Energy Intelligence service is unavailable at " + aiServiceBaseUrl +
                        ". Please verify FastAPI service is running."
                );
            }
            log.error("Error communicating with FastAPI: {}", e.getMessage(), e);
            throw new AiServiceUnavailableException("Failed to retrieve energy intelligence: " + e.getMessage(), e);
        }
    }

    /**
     * Fetch latest energy intelligence across all zones from FastAPI service.
     */
    public List<EnergyIntelligenceResponse> fetchAllZonesEnergyIntelligence() {
        log.info("Calling FastAPI Energy Intelligence endpoint for all zones: {}", ENERGY_INTELLIGENCE_PATH);

        try {
            return aiRestClient.get()
                    .uri(ENERGY_INTELLIGENCE_PATH)
                    .retrieve()
                    .onStatus(HttpStatusCode::isError, (request, response) -> {
                        String body = new String(response.getBody().readAllBytes());
                        String detail = extractDetailMessage(body, "Error from AI service");
                        throw new AiServiceUnavailableException("AI Service error: " + detail);
                    })
                    .body(new ParameterizedTypeReference<List<EnergyIntelligenceResponse>>() {});

        } catch (ResourceAccessException e) {
            if (e.getCause() instanceof SocketTimeoutException || e.getMessage().contains("timed out") || e.getMessage().contains("timeout")) {
                throw new AiServiceTimeoutException("AI Energy Intelligence service timed out at " + aiServiceBaseUrl);
            }
            throw new AiServiceUnavailableException(
                    "AI Energy Intelligence service is unavailable at " + aiServiceBaseUrl +
                    ". Please verify FastAPI service is running."
            );
        } catch (Exception e) {
            throw new AiServiceUnavailableException("Failed to retrieve energy intelligence: " + e.getMessage(), e);
        }
    }

    private String extractDetailMessage(String responseBody, String defaultMessage) {
        if (responseBody == null || responseBody.isBlank()) {
            return defaultMessage;
        }
        try {
            JsonNode node = objectMapper.readTree(responseBody);
            if (node.has("detail")) {
                return node.get("detail").asText();
            }
            if (node.has("message")) {
                return node.get("message").asText();
            }
        } catch (Exception ignored) {
        }
        return responseBody;
    }
}
