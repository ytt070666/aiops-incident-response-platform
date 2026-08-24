package com.yang.aiops.alert;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/alerts")
public class AlertController {
    private final AlertService service;
    public AlertController(AlertService service) { this.service = service; }
    @GetMapping public List<Alert> list() { return service.list(); }
    @PostMapping @ResponseStatus(HttpStatus.CREATED) public Alert create(@Valid @RequestBody AlertRequest request) { return service.create(request); }
    @PostMapping("/{id}/resolve") public Alert resolve(@PathVariable Long id) { return service.resolve(id); }
}
