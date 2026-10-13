package com.aura.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
public class AiClientConfig {

    @Value("${ai.service.base-url:http://localhost:8000}")
    private String aiServiceBaseUrl;

    @Value("${ai.service.connect-timeout-ms:3000}")
    private int connectTimeoutMs;

    @Value("${ai.service.read-timeout-ms:5000}")
    private int readTimeoutMs;

    @Bean
    public RestClient aiRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofMillis(connectTimeoutMs));
        requestFactory.setReadTimeout(Duration.ofMillis(readTimeoutMs));

        return RestClient.builder()
                .baseUrl(aiServiceBaseUrl)
                .requestFactory(requestFactory)
                .build();
    }
}
