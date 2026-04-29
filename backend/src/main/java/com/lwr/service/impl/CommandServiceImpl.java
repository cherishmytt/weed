package com.lwr.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.lwr.common.result.Result;
import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import com.lwr.entity.LaserCommand;
import com.lwr.mapper.RobotCommandMapper;
import com.lwr.service.CommandService;
import com.lwr.service.LaserControlService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 指令轮询服务实现
 */
@Slf4j
@Service
public class CommandServiceImpl implements CommandService {

    private final RobotCommandMapper robotCommandMapper;
    private final LaserControlService laserControlService;
    private final RobotStatusWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public CommandServiceImpl(RobotCommandMapper robotCommandMapper,
                              LaserControlService laserControlService,
                              RobotStatusWebSocketHandler webSocketHandler) {
        this.robotCommandMapper = robotCommandMapper;
        this.laserControlService = laserControlService;
        this.webSocketHandler = webSocketHandler;
    }

    @Override
    public Result<?> getPendingCommands() {
        List<LaserCommand> commands = robotCommandMapper.findPendingCommands();

        List<Map<String, Object>> result = new ArrayList<>();
        for (LaserCommand cmd : commands) {
            Object params = null;
            if (cmd.getParamsJson() != null) {
                try {
                    params = objectMapper.readValue(cmd.getParamsJson(), Map.class);
                } catch (Exception e) {
                    log.warn("解析指令参数JSON失败: {}", cmd.getCommandId(), e);
                }
            }
            Map<String, Object> item = new HashMap<>();
            item.put("id", cmd.getId());
            item.put("commandId", cmd.getCommandId());
            item.put("action", cmd.getAction());
            item.put("params", params);
            item.put("createdAt", cmd.getCreatedAt() != null ? cmd.getCreatedAt().format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) : null);
            result.add(item);
        }

        // 只把 PENDING 更新为 SENT，已经是 SENT 的保持不变（仍然会返回直到被确认）
        for (LaserCommand cmd : commands) {
            if ("PENDING".equals(cmd.getStatus())) {
                cmd.setStatus("SENT");
                robotCommandMapper.updateById(cmd);
            }
        }

        log.info("返回待执行指令: {} 条", result.size());
        if (result.isEmpty()) {
            log.debug("当前没有待执行指令");
        }
        return Result.success(result);
    }

    @Override
    public Result<Void> ackCommand(Long id, String result, String message) {
        LaserCommand command = robotCommandMapper.selectById(id);
        if (command == null) {
            return Result.error(com.lwr.common.result.ResultCode.NOT_FOUND);
        }

        // 标记为已确认
        command.setStatus("ACKED");
        command.setAcknowledgedAt(LocalDateTime.now());
        robotCommandMapper.updateById(command);

        log.info("指令已确认: id={}, result={}", id, result);

        // 通过 WebSocket 广播最新状态给前端
        Result<?> statusResult = laserControlService.getLaserStatus();
        if (statusResult.getData() != null) {
            webSocketHandler.broadcastStatusUpdate(statusResult.getData());
        }

        return Result.success("指令已确认", null);
    }
}
