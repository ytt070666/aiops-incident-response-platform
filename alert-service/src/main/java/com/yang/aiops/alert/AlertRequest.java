package com.yang.aiops.alert;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record AlertRequest(
    @NotBlank @Pattern(regexp = "WAF|Linux|网络") String category,
    @NotBlank @Pattern(regexp = "高|中|低") String severity,
    @NotBlank String title,
    @NotBlank String detail
) {}
