package com.lwr.common.config;

import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

/**
 * WebSocket配置
 */
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final RobotStatusWebSocketHandler robotStatusWebSocketHandler;

    public WebSocketConfig(RobotStatusWebSocketHandler robotStatusWebSocketHandler) {
        this.robotStatusWebSocketHandler = robotStatusWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(robotStatusWebSocketHandler, "/ws/robot-status")
                .setAllowedOrigins("*");
    }
}
