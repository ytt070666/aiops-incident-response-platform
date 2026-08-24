package com.yang.aiops.alert;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = {"spring.datasource.url=jdbc:h2:mem:alerts;MODE=MySQL", "spring.jpa.hibernate.ddl-auto=create-drop", "spring.cache.type=none", "aiops.python-sync-enabled=false"})
@AutoConfigureMockMvc
class AlertControllerTest {
    @Autowired MockMvc mvc;
    @Test void createsAndListsAlerts() throws Exception {
        mvc.perform(post("/api/v1/alerts").contentType(MediaType.APPLICATION_JSON).content("{\"category\":\"WAF\",\"severity\":\"高\",\"title\":\"测试告警\",\"detail\":\"用于验证 Java 微服务接口\"}"))
           .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("OPEN"));
        mvc.perform(get("/api/v1/alerts")).andExpect(status().isOk()).andExpect(jsonPath("$[0].title").value("测试告警"));
    }
}
