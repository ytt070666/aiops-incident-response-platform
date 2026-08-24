package com.yang.aiops.alert;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

/** 向 Python 工作台回调告警状态；回调异常不会影响 Java 告警落库。 */
@Component
public class PythonAlertSyncClient {
    private static final Logger log = LoggerFactory.getLogger(PythonAlertSyncClient.class);
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;
    private final String pythonBaseUrl;
    private final boolean enabled;

    public PythonAlertSyncClient(
            ObjectMapper objectMapper,
            @Value("${aiops.python-base-url:http://localhost:8000}") String pythonBaseUrl,
            @Value("${aiops.python-sync-enabled:true}") boolean enabled
    ) {
        this.objectMapper = objectMapper;
        // Uvicorn 使用 HTTP/1.1；显式固定协议以避免 JDK 尝试 h2c 升级。
        this.httpClient = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
        this.pythonBaseUrl = pythonBaseUrl.replaceAll("/$", "");
        this.enabled = enabled;
    }

    public void sync(Alert alert) {
        if (!enabled) {
            return;
        }
        try {
            String payload = objectMapper.writeValueAsString(Map.of(
                    "id", alert.getId(),
                    "category", alert.getCategory(),
                    "severity", alert.getSeverity(),
                    "title", alert.getTitle(),
                    "detail", alert.getDetail(),
                    "status", alert.getStatus()
            ));
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(pythonBaseUrl + "/api/v1/integrations/java-alerts"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(payload))
                    .build();
            HttpResponse<Void> response = httpClient.send(request, HttpResponse.BodyHandlers.discarding());
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                log.info("alert {} synchronized to Python workbench", alert.getId());
            } else {
                log.warn("Python workbench callback returned {} for alert {}", response.statusCode(), alert.getId());
            }
        } catch (JsonProcessingException exception) {
            log.warn("Could not serialize callback for alert {}: {}", alert.getId(), exception.getMessage());
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            log.warn("Python workbench callback interrupted for alert {}", alert.getId());
        } catch (IOException exception) {
            log.warn("Python workbench callback failed for alert {}: {}", alert.getId(), exception.getMessage());
        }
    }
}
