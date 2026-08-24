package com.yang.aiops.alert;

import jakarta.persistence.*;
import java.io.Serializable;
import java.time.Instant;

@Entity
@Table(name = "alerts")
public class Alert implements Serializable {
    private static final long serialVersionUID = 1L;
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, length = 30) private String category;
    @Column(nullable = false, length = 10) private String severity;
    @Column(nullable = false, length = 120) private String title;
    @Column(nullable = false, length = 2000) private String detail;
    @Column(nullable = false, length = 20) private String status = "OPEN";
    @Column(nullable = false, updatable = false) private Instant createdAt = Instant.now();

    protected Alert() {}
    public Alert(String category, String severity, String title, String detail) { this.category = category; this.severity = severity; this.title = title; this.detail = detail; }
    public Long getId() { return id; } public String getCategory() { return category; } public String getSeverity() { return severity; }
    public String getTitle() { return title; } public String getDetail() { return detail; } public String getStatus() { return status; } public Instant getCreatedAt() { return createdAt; }
    public void resolve() { this.status = "RESOLVED"; }
}
