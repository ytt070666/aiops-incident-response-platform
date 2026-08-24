package com.yang.aiops.alert;
public class AlertNotFoundException extends RuntimeException { public AlertNotFoundException(Long id) { super("告警不存在: " + id); } }
