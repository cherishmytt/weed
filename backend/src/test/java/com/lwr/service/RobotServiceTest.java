package com.lwr.service;

import com.lwr.common.result.Result;
import com.lwr.entity.RobotInfo;
import com.lwr.mapper.RobotInfoMapper;
import com.lwr.mapper.RobotStatusMapper;
import com.lwr.mapper.LaserStatusMapper;
import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import com.lwr.service.impl.RobotServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RobotServiceTest {

    @Mock
    private RobotInfoMapper robotInfoMapper;

    @Mock
    private RobotStatusMapper robotStatusMapper;

    @Mock
    private LaserStatusMapper laserStatusMapper;

    @Mock
    private RobotStatusWebSocketHandler webSocketHandler;

    @InjectMocks
    private RobotServiceImpl robotService;

    private RobotInfo testRobotInfo;

    @BeforeEach
    void setUp() {
        testRobotInfo = new RobotInfo();
        testRobotInfo.setId(1L);
        testRobotInfo.setRobotCode("ROBOT001");
        testRobotInfo.setName("测试机器人");
        testRobotInfo.setModel("LWR-1000");
        testRobotInfo.setCurrentStatus(1);
    }

    @Test
    void testGetRobotInfo_Success() {
        when(robotInfoMapper.getCurrent()).thenReturn(testRobotInfo);

        Result<?> result = robotService.getRobotInfo();

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
    }

    @Test
    void testGetRobotInfo_NoRobot() {
        when(robotInfoMapper.getCurrent()).thenReturn(null);

        Result<?> result = robotService.getRobotInfo();

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNull(result.getData());
    }

    @Test
    void testGetLatestStatus_NoData() {
        when(robotStatusMapper.findLatest()).thenReturn(null);

        Result<?> result = robotService.getLatestStatus();

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNull(result.getData());
    }

    @Test
    void testBroadcastStatusUpdate() {
        com.lwr.entity.RobotStatus status = new com.lwr.entity.RobotStatus();
        status.setBattery(85.0f);
        status.setSpeed(1.5f);

        doNothing().when(webSocketHandler).broadcastStatusUpdate(any());

        robotService.broadcastStatusUpdate(status);

        verify(webSocketHandler, times(1)).broadcastStatusUpdate(any());
    }
}
