package com.lwr.service.impl;

import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lwr.common.result.Result;
import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import com.lwr.entity.LaserCommand;
import com.lwr.entity.LaserOperationLog;
import com.lwr.entity.LaserStatus;
import com.lwr.mapper.RobotCommandMapper;
import com.lwr.mapper.LaserOperationLogMapper;
import com.lwr.mapper.LaserStatusMapper;
import com.lwr.service.LaserControlService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 激光控制服务实现
 */
@Slf4j
@Service
public class LaserControlServiceImpl implements LaserControlService {

    private final RobotCommandMapper robotCommandMapper;
    private final LaserOperationLogMapper laserOperationLogMapper;
    private final LaserStatusMapper laserStatusMapper;
    private final RobotStatusWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final DateTimeFormatter isoFormatter = DateTimeFormatter.ISO_DATE_TIME;

    public LaserControlServiceImpl(RobotCommandMapper robotCommandMapper,
                                   LaserOperationLogMapper laserOperationLogMapper,
                                   LaserStatusMapper laserStatusMapper,
                                   RobotStatusWebSocketHandler webSocketHandler) {
        this.robotCommandMapper = robotCommandMapper;
        this.laserOperationLogMapper = laserOperationLogMapper;
        this.laserStatusMapper = laserStatusMapper;
        this.webSocketHandler = webSocketHandler;
    }

    @Override
    @Transactional
    public Result<?> sendCommand(String action, Object params) {
        // FIRE 指令验证：必须先设置瞄准坐标
        if ("FIRE".equals(action)) {
            LaserStatus currentStatus = laserStatusMapper.getCurrent();
            if (currentStatus == null || currentStatus.getAimTargetX() == null || currentStatus.getAimTargetY() == null) {
                return Result.error(400, "请先执行瞄准指令设置目标位置，再进行照射");
            }
        }

        // ========== STOP 指令：立即设置停止标志，实现快速中断 ==========
        if ("STOP".equals(action)) {
            LaserStatus currentStatus = laserStatusMapper.getCurrent();
            if (currentStatus != null) {
                // 设置停止标志状态，树莓派在照射过程中会检测此状态
                currentStatus.setStatus(LaserStatusEnum.STANDBY.getValue());
                currentStatus.setStatusText("停止指令已下发，正在中断...");
                currentStatus.setUpdatedAt(LocalDateTime.now());
                laserStatusMapper.updateById(currentStatus);
                // 立即广播状态更新
                Result<?> statusResult = getLaserStatus();
                if (statusResult.getData() != null) {
                    webSocketHandler.broadcastStatusUpdate(statusResult.getData());
                }
                log.info("STOP指令已下发，立即设置停止标志");
            }
        }

        // 生成指令ID，格式为 cmd-YYYYMMDD-NNN
        LocalDateTime now = LocalDateTime.now();
        int todayCount = robotCommandMapper.countTodayCommands(now);
        String commandId = "cmd-" + now.format(DateTimeFormatter.ofPattern("yyyyMMdd")) +
                "-" + String.format("%03d", todayCount + 1);

        // 保存到待执行队列
        LaserCommand command = new LaserCommand();
        command.setCommandId(commandId);
        command.setAction(action);
        command.setStatus("PENDING");
        command.setCreatedAt(now);
        if (params != null) {
            try {
                command.setParamsJson(objectMapper.writeValueAsString(params));
            } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
                log.warn("序列化指令参数失败", e);
            }
        }
        robotCommandMapper.insert(command);

        // 下发指令时立即创建操作日志，参数提前填入
        Float targetX = null;
        Float targetY = null;
        Float depth = null;
        Integer duration = null;
        if (params != null) {
            if (params instanceof Map) {
                Map<?, ?> paramMap = (Map<?, ?>) params;
                targetX = getFloatValue(paramMap.get("targetX"));
                targetY = getFloatValue(paramMap.get("targetY"));
                depth = getFloatValue(paramMap.get("depth"));
                duration = getIntValue(paramMap.get("duration"));
            }
        }

        LaserOperationLog logEntry = new LaserOperationLog();
        logEntry.setCommandId(commandId);
        logEntry.setAction(action);
        logEntry.setTargetX(targetX);
        logEntry.setTargetY(targetY);
        logEntry.setDepth(depth);
        logEntry.setDuration(duration);
        logEntry.setResult("PENDING");
        logEntry.setMessage("指令已下发，等待设备执行");
        logEntry.setCreatedAt(LocalDateTime.now());
        logEntry.setExecutedAt(LocalDateTime.now());
        laserOperationLogMapper.insert(logEntry);

        log.info("下发激光控制指令: commandId={}, action={}", commandId, action);

        Map<String, Object> data = new HashMap<>();
        data.put("commandId", commandId);
        data.put("status", "SENT");
        return Result.success("指令已下发", data);
    }

    // 激光状态枚举
    private enum LaserStatusEnum {
        DISCONNECTED("disconnected", "设备未连接"),
        STANDBY("standby", "待机"),
        AIMING("aiming", "瞄准中"),
        FIRING("firing", "照射中"),
        COOLING("cooling", "冷却中"),
        ERROR("error", "设备故障");

        private final String value;
        private final String description;

        LaserStatusEnum(String value, String description) {
            this.value = value;
            this.description = description;
        }

        public String getValue() {
            return value;
        }

        public String getDescription() {
            return description;
        }

        public static LaserStatusEnum fromValue(String value) {
            if (value == null || value.isEmpty()) {
                return DISCONNECTED;
            }
            for (LaserStatusEnum status : values()) {
                if (status.value.equals(value)) {
                    return status;
                }
            }
            return DISCONNECTED; // 默认返回未连接状态
        }
    }

    @Override
    public Result<?> getLaserStatus() {
        LaserStatus status = laserStatusMapper.getCurrent();
        if (status == null) {
            status = new LaserStatus();
            status.setConnected(false);
            status.setStatus(LaserStatusEnum.DISCONNECTED.getValue());
            status.setStatusText(LaserStatusEnum.DISCONNECTED.getDescription());
        } else {
            // 确保状态值是有效的枚举值
            LaserStatusEnum validStatus = LaserStatusEnum.fromValue(status.getStatus());
            status.setStatus(validStatus.getValue());
            status.setStatusText(validStatus.getDescription());
        }

        Map<String, Object> data = new HashMap<>();
        data.put("connected", status.getConnected());
        data.put("status", status.getStatus());
        data.put("statusText", status.getStatusText());
        data.put("lastFireAt", status.getLastFireAt() != null
                ? status.getLastFireAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
                : null);
        data.put("totalFireCount", status.getTotalFireCount());
        data.put("totalFireDuration", status.getTotalFireDuration());
        data.put("temperature", status.getTemperature());
        data.put("power", status.getPower());
        data.put("errorCode", status.getErrorCode());
        data.put("aimTargetX", status.getAimTargetX());
        data.put("aimTargetY", status.getAimTargetY());

        return Result.success(data);
    }

    @Override
    public Result<?> getCapabilities() {
        // 硬件未接入阶段返回默认值
        Map<String, Object> data = new HashMap<>();
        data.put("connected", false);
        data.put("model", "unknown");

        Map<String, Object> capabilities = new HashMap<>();
        capabilities.put("powerAdjustable", false);
        capabilities.put("aimAdjustable", false);
        capabilities.put("maxPowerWatt", null);
        capabilities.put("supportedModes", java.util.Arrays.asList("ON_OFF"));

        data.put("capabilities", capabilities);

        return Result.success(data);
    }

    @Override
    public Result<?> getOperationLogs(LocalDateTime startTime, LocalDateTime endTime, List<String> action, List<String> result, String keyword,
                                      Float targetXMin, Float targetXMax, Float targetYMin, Float targetYMax,
                                      Float depthMin, Float depthMax, Integer durationMin, Integer durationMax,
                                      String sortBy, String sortOrder, int page, int size) {
        LambdaQueryWrapper<LaserOperationLog> wrapper = new LambdaQueryWrapper<>();

        // 时间范围筛选
        if (startTime != null) {
            wrapper.ge(LaserOperationLog::getCreatedAt, startTime);
        }
        if (endTime != null) {
            wrapper.le(LaserOperationLog::getCreatedAt, endTime);
        }

        // 指令类型多选筛选
        if (action != null && !action.isEmpty()) {
            wrapper.in(LaserOperationLog::getAction, action);
        }

        // 执行结果多选筛选
        if (result != null && !result.isEmpty()) {
            wrapper.in(LaserOperationLog::getResult, result);
        }

        // 关键词模糊搜索（说明字段）
        if (keyword != null && !keyword.trim().isEmpty()) {
            wrapper.like(LaserOperationLog::getMessage, keyword.trim());
        }

        // Target X 范围筛选
        if (targetXMin != null) {
            wrapper.ge(LaserOperationLog::getTargetX, targetXMin);
        }
        if (targetXMax != null) {
            wrapper.le(LaserOperationLog::getTargetX, targetXMax);
        }

        // Target Y 范围筛选
        if (targetYMin != null) {
            wrapper.ge(LaserOperationLog::getTargetY, targetYMin);
        }
        if (targetYMax != null) {
            wrapper.le(LaserOperationLog::getTargetY, targetYMax);
        }

        // 深度范围筛选
        if (depthMin != null) {
            wrapper.ge(LaserOperationLog::getDepth, depthMin);
        }
        if (depthMax != null) {
            wrapper.le(LaserOperationLog::getDepth, depthMax);
        }

        // 时长范围筛选
        if (durationMin != null) {
            wrapper.ge(LaserOperationLog::getDuration, durationMin);
        }
        if (durationMax != null) {
            wrapper.le(LaserOperationLog::getDuration, durationMax);
        }

        // 排序处理 - 基于全部数据排序
        boolean isAsc = sortOrder != null && sortOrder.toLowerCase().startsWith("asc");
        switch (sortBy) {
            case "id":
                if (isAsc) {
                    wrapper.orderByAsc(LaserOperationLog::getId);
                } else {
                    wrapper.orderByDesc(LaserOperationLog::getId);
                }
                break;
            case "depth":
                if (isAsc) {
                    wrapper.orderByAsc(LaserOperationLog::getDepth);
                } else {
                    wrapper.orderByDesc(LaserOperationLog::getDepth);
                }
                break;
            case "duration":
                if (isAsc) {
                    wrapper.orderByAsc(LaserOperationLog::getDuration);
                } else {
                    wrapper.orderByDesc(LaserOperationLog::getDuration);
                }
                break;
            case "createdAt":
            default:
                if (isAsc) {
                    wrapper.orderByAsc(LaserOperationLog::getCreatedAt);
                } else {
                    wrapper.orderByDesc(LaserOperationLog::getCreatedAt);
                }
                break;
        }

        // 手动 count 获取总数
        long total = laserOperationLogMapper.selectCount(wrapper);

        // 手动分页（不依赖分页插件，避免配置问题）
        int offset = (page - 1) * size;
        wrapper.last("LIMIT " + offset + ", " + size);
        var allRecords = laserOperationLogMapper.selectList(wrapper);

        // 转换为返回数据
        var list = allRecords.stream().map(log -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", log.getId());
            item.put("commandId", log.getCommandId());
            item.put("action", log.getAction());
            item.put("targetX", log.getTargetX());
            item.put("targetY", log.getTargetY());
            item.put("depth", log.getDepth());
            item.put("duration", log.getDuration());
            item.put("result", log.getResult());
            item.put("message", log.getMessage());
            item.put("createdAt", log.getCreatedAt() != null ? log.getCreatedAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) : null);
            return item;
        }).toList();

        Map<String, Object> data = new HashMap<>();
        data.put("total", total);
        data.put("list", list);
        return Result.success(data);
    }

    @Override
    public Result<?> exportLogs(List<Long> ids) {
        // 根据ID列表查询日志
        LambdaQueryWrapper<LaserOperationLog> wrapper = new LambdaQueryWrapper<>();
        wrapper.in(LaserOperationLog::getId, ids);
        wrapper.orderByDesc(LaserOperationLog::getCreatedAt);
        var logs = laserOperationLogMapper.selectList(wrapper);

        // 转换为导出格式
        List<Map<String, Object>> result = logs.stream().map(log -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", log.getId());
            item.put("commandId", log.getCommandId());
            item.put("action", log.getAction());
            item.put("targetX", log.getTargetX());
            item.put("targetY", log.getTargetY());
            item.put("depth", log.getDepth());
            item.put("duration", log.getDuration());
            item.put("result", log.getResult());
            item.put("message", log.getMessage());
            item.put("createdAt", log.getCreatedAt() != null ? log.getCreatedAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) : null);
            return item;
        }).toList();

        return Result.success(result);
    }

    @Override
    public Result<Void> batchDeleteLogs(List<Long> ids) {
        // 批量删除
        LambdaQueryWrapper<LaserOperationLog> wrapper = new LambdaQueryWrapper<>();
        wrapper.in(LaserOperationLog::getId, ids);
        laserOperationLogMapper.delete(wrapper);
        log.info("批量删除激光操作日志: {} 条", ids.size());
        return Result.success(null);
    }

    @Override
    @Transactional
    public Result<Void> receiveFeedback(String commandId, String action, String result, String message, String timestamp) {
        // 解析 ISO 时间（可能带时区）并转换为本地时区
        LocalDateTime executedAt;
        try {
            // 先用 Instant 解析，正确处理时区信息（Z = UTC）
            Instant instant = Instant.parse(timestamp);
            executedAt = LocalDateTime.ofInstant(instant, ZoneId.systemDefault());
        } catch (Exception e) {
            // 如果解析失败，尝试直接解析为 LocalDateTime（无时区信息）
            executedAt = LocalDateTime.parse(timestamp, isoFormatter);
        }

        // 更新指令状态
        LambdaUpdateWrapper<LaserCommand> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(LaserCommand::getCommandId, commandId)
                .set(LaserCommand::getStatus, "ACKED")
                .set(LaserCommand::getAcknowledgedAt, executedAt);
        robotCommandMapper.update(null, updateWrapper);

        // 查询已存在的操作日志（下发时已创建）
        LambdaQueryWrapper<LaserOperationLog> logQueryWrapper = new LambdaQueryWrapper<>();
        logQueryWrapper.eq(LaserOperationLog::getCommandId, commandId);
        LaserOperationLog existingLog = laserOperationLogMapper.selectOne(logQueryWrapper);

        // 解析参数
        Float targetX = null;
        Float targetY = null;
        Float depth = null;
        Integer duration = null;

        // 查询指令获取参数（备用，如果日志里没有就从这里取）
        LambdaQueryWrapper<LaserCommand> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(LaserCommand::getCommandId, commandId);
        LaserCommand command = robotCommandMapper.selectOne(queryWrapper);

        if (command != null && command.getParamsJson() != null) {
            try {
                Map<String, Object> params = objectMapper.readValue(command.getParamsJson(), Map.class);
                targetX = getFloatValue(params.get("targetX"));
                targetY = getFloatValue(params.get("targetY"));
                depth = getFloatValue(params.get("depth"));
                duration = getIntValue(params.get("duration"));
            } catch (Exception e) {
                log.warn("解析指令参数失败: {}", commandId);
            }
        }

        if (existingLog != null) {
            // 更新已有日志
            existingLog.setResult(result);
            existingLog.setMessage(message);
            existingLog.setExecutedAt(executedAt);
            // 如果参数为空，补上（虽然下发时已经填了）
            if (existingLog.getTargetX() == null) existingLog.setTargetX(targetX);
            if (existingLog.getTargetY() == null) existingLog.setTargetY(targetY);
            if (existingLog.getDepth() == null) existingLog.setDepth(depth);
            if (existingLog.getDuration() == null) existingLog.setDuration(duration);
            laserOperationLogMapper.updateById(existingLog);
        } else {
            // 兼容：如果日志不存在（旧数据），创建新的
            LaserOperationLog logEntry = new LaserOperationLog();
            logEntry.setCommandId(commandId);
            logEntry.setAction(action);
            logEntry.setTargetX(targetX);
            logEntry.setTargetY(targetY);
            logEntry.setDepth(depth);
            logEntry.setDuration(duration);
            logEntry.setResult(result);
            logEntry.setMessage(message);
            logEntry.setExecutedAt(executedAt);
            logEntry.setCreatedAt(LocalDateTime.now());
            laserOperationLogMapper.insert(logEntry);
        }

        // 先广播指令执行结果（STATUS_UPDATE 会在后面触发，避免顺序问题）
        webSocketHandler.broadcastCommandFeedback(commandId, action, result, message, timestamp);
        
        // 广播激光反馈事件
        webSocketHandler.broadcastLaserFeedback(commandId, message);

        // 只有执行成功时才更新设备状态数据
        if ("SUCCESS".equalsIgnoreCase(result)) {
            updateLaserStatsAfterExecution(action, result, executedAt, duration, command);
        }

        log.info("激光指令反馈已接收: commandId={}, result={}", commandId, result);
        return Result.success("反馈已记录", null);
    }

    @Override
    public Result<Void> updateLaserStatus(String status, String statusText) {
        LaserStatus currentStatus = laserStatusMapper.getCurrent();
        if (currentStatus == null) {
            currentStatus = new LaserStatus();
            currentStatus.setConnected(true);
            currentStatus.setStatus(status);
            currentStatus.setStatusText(statusText);
            currentStatus.setUpdatedAt(LocalDateTime.now());
            laserStatusMapper.insert(currentStatus);
        } else {
            currentStatus.setStatus(status);
            currentStatus.setStatusText(statusText);
            currentStatus.setUpdatedAt(LocalDateTime.now());
            laserStatusMapper.updateById(currentStatus);
        }

        // 通过 WebSocket 广播最新状态给前端
        Result<?> statusResult = getLaserStatus();
        if (statusResult.getData() != null) {
            webSocketHandler.broadcastStatusUpdate(statusResult.getData());
        }

        return Result.success("状态已更新", null);
    }

    /**
     * 更新激光设备统计数据
     */
    private void updateLaserStatsAfterExecution(String action, String result, LocalDateTime executedAt, Integer duration, LaserCommand command) {
        LaserStatus currentStatus = laserStatusMapper.getCurrent();
        if (currentStatus == null) {
            return;
        }

        // 根据指令更新连接状态
        if ("SUCCESS".equals(result)) {
            switch (action) {
                case "ENABLE":
                    currentStatus.setConnected(true);
                    currentStatus.setStatus(LaserStatusEnum.STANDBY.getValue());
                    currentStatus.setStatusText("设备已连接，待机中");
                    break;
                case "DISABLE":
                    currentStatus.setConnected(false);
                    currentStatus.setStatus(LaserStatusEnum.DISCONNECTED.getValue());
                    currentStatus.setStatusText(LaserStatusEnum.DISCONNECTED.getDescription());
                    break;
                case "FIRE":
                    // FIRE 成功，更新发射计数
                    int newCount = (currentStatus.getTotalFireCount() != null ? currentStatus.getTotalFireCount() : 0) + 1;
                    currentStatus.setTotalFireCount(newCount);
                    currentStatus.setLastFireAt(executedAt);
                    // 累加照射时长
                    if (currentStatus.getTotalFireDuration() == null) {
                        currentStatus.setTotalFireDuration(0);
                    }
                    if (duration != null) {
                        currentStatus.setTotalFireDuration(currentStatus.getTotalFireDuration() + duration);
                    }
                    break;
                case "AIM":
                    currentStatus.setStatus(LaserStatusEnum.AIMING.getValue());
                    currentStatus.setStatusText(LaserStatusEnum.AIMING.getDescription());
                    // 保存瞄准坐标
                    if (command != null && command.getParamsJson() != null) {
                        try {
                            Map<String, Object> params = objectMapper.readValue(command.getParamsJson(), Map.class);
                            currentStatus.setAimTargetX(getFloatValue(params.get("targetX")));
                            currentStatus.setAimTargetY(getFloatValue(params.get("targetY")));
                        } catch (Exception e) {
                            log.warn("解析瞄准坐标失败", e);
                        }
                    }
                    break;
                case "STOP":
                    currentStatus.setStatus(LaserStatusEnum.STANDBY.getValue());
                    currentStatus.setStatusText("照射已停止，待机中");
                    break;
                case "SELF_TEST":
                    currentStatus.setStatusText("自检完成");
                    break;
                case "RESET":
                    currentStatus.setConnected(false);
                    currentStatus.setStatus(LaserStatusEnum.DISCONNECTED.getValue());
                    currentStatus.setStatusText("设备已复位，等待连接");
                    break;
                case "SET_POWER":
                    // 保存设置的功率值
                    if (command != null && command.getParamsJson() != null) {
                        try {
                            Map<String, Object> params = objectMapper.readValue(command.getParamsJson(), Map.class);
                            currentStatus.setPower(getFloatValue(params.get("power")));
                        } catch (Exception e) {
                            log.warn("解析功率参数失败", e);
                        }
                    }
                    break;
            }
        }

        currentStatus.setUpdatedAt(LocalDateTime.now());
        laserStatusMapper.updateById(currentStatus);

        // 通过 WebSocket 广播最新状态给前端
        Result<?> statusResult = getLaserStatus();
        if (statusResult.getData() != null) {
            webSocketHandler.broadcastStatusUpdate(statusResult.getData());
        }
    }

    private Float getFloatValue(Object value) {
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).floatValue();
        }
        return null;
    }

    private Integer getIntValue(Object value) {
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return null;
    }
}
