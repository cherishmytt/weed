package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.RobotService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RobotControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private RobotService robotService;

    @Test
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void testGetRobotInfo_Success() throws Exception {
        Map<String, Object> robotData = new HashMap<>();
        robotData.put("robotCode", "ROBOT001");
        robotData.put("name", "测试机器人");
        robotData.put("status", 1);

        when(robotService.getRobotInfo()).thenReturn(Result.success(robotData));

        mockMvc.perform(get("/api/v1/robot/info")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.robotCode").value("ROBOT001"));
    }

    @Test
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void testGetLatestStatus_Success() throws Exception {
        Map<String, Object> statusData = new HashMap<>();
        statusData.put("battery", 85.0f);
        statusData.put("speed", 1.5f);
        statusData.put("temperature", 35.0f);

        when(robotService.getLatestStatus()).thenReturn(Result.success(statusData));

        mockMvc.perform(get("/api/v1/robot/status/latest")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200))
                .andExpect(jsonPath("$.data.battery").value(85.0));
    }

    @Test
    void testGetRobotInfo_Unauthorized() throws Exception {
        mockMvc.perform(get("/api/v1/robot/info")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @WithMockUser(username = "admin", roles = {"ADMIN"})
    void testGetStatusHistory_WithParams() throws Exception {
        Map<String, Object> historyData = new HashMap<>();
        historyData.put("total", 100);
        historyData.put("list", java.util.Collections.emptyList());

        when(robotService.getStatusHistory(any(), any(), any(), any(), any(), any(), any(), any(), any(), any(), any()))
                .thenReturn(Result.success(historyData));

        mockMvc.perform(get("/api/v1/robot/status/history")
                        .param("page", "1")
                        .param("size", "20")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));
    }
}
