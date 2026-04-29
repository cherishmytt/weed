package com.lwr.controller.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;

/**
 * 机器人状态WebSocket处理器
 * 向前端推送实时状态更新
 */
@Component
public class RobotStatusWebSocketHandler extends TextWebSocketHandler {

    /**
     * 存储所有连接的session
     */
    private final Set<WebSocketSession> sessions = new CopyOnWriteArraySet<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        sessions.add(session);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        sessions.remove(session);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        // 前端不需要发送消息，这里忽略
    }

    /**
     * 广播状态更新给所有连接的前端
     */
    public void broadcastStatusUpdate(Object data) {
        Map<String, Object> message = Map.of(
                "type", "STATUS_UPDATE",
                "data", data
        );
        sendToAll(message);
    }

    /**
     * 广播指令执行结果给所有连接的前端
     * 树莓派上报执行结果后调用此方法
     */
    public void broadcastCommandFeedback(String commandId, String action, String result, String message, String timestamp) {
        Map<String, Object> feedbackData = Map.of(
                "commandId", commandId,
                "action", action,
                "result", result,
                "message", message,
                "timestamp", timestamp
        );
        Map<String, Object> messageWrapper = Map.of(
                "type", "COMMAND_FEEDBACK",
                "data", feedbackData
        );
        sendToAll(messageWrapper);
    }

    /**
     * 广播检测结果给所有连接的前端
     * 树莓派上报检测结果后调用此方法
     */
    public void broadcastDetectionResult(Object data) {
        Map<String, Object> message = Map.of(
                "type", "DETECTION_RESULT",
                "data", data
        );
        sendToAll(message);
    }

    /**
     * 广播激光反馈给所有连接的前端
     * 树莓派上报激光反馈后调用此方法
     */
    public void broadcastLaserFeedback(String commandId, String message) {
        Map<String, Object> feedbackData = Map.of(
                "commandId", commandId,
                "message", message
        );
        Map<String, Object> messageWrapper = Map.of(
                "type", "LASER_FEEDBACK",
                "data", feedbackData
        );
        sendToAll(messageWrapper);
    }

    /**
     * 发送消息到所有连接的前端
     */
    private void sendToAll(Map<String, Object> message) {
        try {
            String json = objectMapper.writeValueAsString(message);
            TextMessage textMessage = new TextMessage(json);

            for (WebSocketSession session : sessions) {
                if (session.isOpen()) {
                    try {
                        session.sendMessage(textMessage);
                    } catch (IOException e) {
                        sessions.remove(session);
                    }
                }
            }
        } catch (Exception e) {
            // 序列化失败，忽略
        }
    }
}
