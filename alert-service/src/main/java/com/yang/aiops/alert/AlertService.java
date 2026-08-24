package com.yang.aiops.alert;

import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class AlertService {
    private final AlertRepository repository;
    private final PythonAlertSyncClient pythonSyncClient;
    public AlertService(AlertRepository repository, PythonAlertSyncClient pythonSyncClient) {
        this.repository = repository;
        this.pythonSyncClient = pythonSyncClient;
    }
    @Cacheable("alerts") public List<Alert> list() { return repository.findAllByOrderByCreatedAtDesc(); }
    @CacheEvict(value = "alerts", allEntries = true)
    public Alert create(AlertRequest request) {
        Alert alert = repository.save(new Alert(request.category(), request.severity(), request.title(), request.detail()));
        pythonSyncClient.sync(alert);
        return alert;
    }
    @Transactional @CacheEvict(value = "alerts", allEntries = true)
    public Alert resolve(Long id) {
        Alert alert = repository.findById(id).orElseThrow(() -> new AlertNotFoundException(id));
        alert.resolve();
        pythonSyncClient.sync(alert);
        return alert;
    }
}
