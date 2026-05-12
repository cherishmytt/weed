package com.lwr.service.impl;

import com.lwr.common.result.Result;
import com.lwr.common.util.JsonUtil;
import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import com.lwr.entity.RobotInfo;
import com.lwr.entity.RobotStatus;
import com.lwr.entity.LaserStatus;
import com.lwr.mapper.RobotInfoMapper;
import com.lwr.mapper.RobotStatusMapper;
import com.lwr.mapper.LaserStatusMapper;
import com.lwr.service.RobotService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 机器人服务实现
 */
@Slf4j
@Service
public class RobotServiceImpl implements RobotService {

    private final RobotInfoMapper robotInfoMapper;
    private final RobotStatusMapper robotStatusMapper;
    private final LaserStatusMapper laserStatusMapper;
    private final RobotStatusWebSocketHandler webSocketHandler;
    private final DateTimeFormatter isoFormatter = DateTimeFormatter.ISO_DATE_TIME;
    private final DateTimeFormatter outputFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public RobotServiceImpl(RobotInfoMapper robotInfoMapper,
                            RobotStatusMapper robotStatusMapper,
                            LaserStatusMapper laserStatusMapper,
                            RobotStatusWebSocketHandler webSocketHandler) {
        this.robotInfoMapper = robotInfoMapper;
        this.robotStatusMapper = robotStatusMapper;
        this.laserStatusMapper = laserStatusMapper;
        this.webSocketHandler = webSocketHandler;
    }

    @Override
    public Result<?> getRobotInfo() {
        RobotInfo robotInfo = robotInfoMapper.getCurrent();
        if (robotInfo == null) {
            return Result.success(null);
        }

        Map<String, Object> data = new HashMap<>();
        data.put("robotCode", robotInfo.getRobotCode());
        data.put("name", robotInfo.getName());
        data.put("model", robotInfo.getModel());
        data.put("status", robotInfo.getCurrentStatus());

        String statusText = switch (robotInfo.getCurrentStatus() == null ? 0 : robotInfo.getCurrentStatus()) {
            case 0 -> "离线";
            case 1 -> "待机";
            case 2 -> "作业中";
            case 3 -> "故障";
            default -> "未知";
        };
        data.put("statusText", statusText);

        return Result.success(data);
    }

    @Override
    public Result<Void> reportStatus(RobotStatusReportRequest request) {
        RobotStatus status = new RobotStatus();
        status.setBattery(request.getBattery());
        status.setSpeed(request.getSpeed());
        status.setTemperature(request.getTemperature());
        status.setLaserOn(request.getLaserOn());
        status.setCpuUsage(request.getCpuUsage());
        status.setLongitude(request.getLongitude());
        status.setLatitude(request.getLatitude());

        if (request.getImu() != null) {
            status.setImuData(JsonUtil.toJson(request.getImu()));
        }

        // 解析时间 - 树莓派上报的是UTC时间，转换到系统默认时区
        Instant instant = Instant.parse(request.getReportedAt());
        LocalDateTime reportedAt = LocalDateTime.ofInstant(instant, ZoneId.systemDefault());
        status.setReportedAt(reportedAt);

        robotStatusMapper.insert(status);

        // 更新机器人当前在线状态 - 只要有上报就说明机器人在线
        // 根据是否开启激光判断是作业中还是待机
        int newStatus = request.getLaserOn() != null && request.getLaserOn() ? 2 : 1;
        robotInfoMapper.updateCurrentStatus(newStatus);

        // 同步激光连接状态 - 只要机器人在持续上报状态，说明激光已经连接
        LaserStatus laserStatus = laserStatusMapper.getCurrent();
        if (laserStatus != null) {
            // 只要机器人能够上报状态，说明系统已经运行，激光应该标记为已连接
            if (laserStatus.getConnected() == null || !laserStatus.getConnected()) {
                laserStatus.setConnected(true);
            }
            // 根据机器人上报的激光开关更新当前状态（如果上报包含了）
            if (request.getLaserOn() != null) {
                if (request.getLaserOn()) {
                    laserStatus.setStatus("firing");
                    laserStatus.setStatusText("激光正在照射");
                } else {
                    laserStatus.setStatus("standby");
                    laserStatus.setStatusText("设备已连接，待机中");
                }
            }
            laserStatus.setUpdatedAt(LocalDateTime.now());
            laserStatusMapper.updateById(laserStatus);
        }

        // 通过WebSocket广播给前端
        broadcastStatusUpdate(status);

        log.debug("机器人状态上报成功: battery={}, speed={}, currentStatus={}, laserOn={}", request.getBattery(), request.getSpeed(), newStatus, request.getLaserOn());
        return Result.success("上报成功", null);
    }

    @Override
    public Result<?> getLatestStatus() {
        RobotStatus status = robotStatusMapper.findLatest();
        if (status == null) {
            return Result.success(null);
        }

        Map<String, Object> data = formatStatusForResponse(status);
        return Result.success(data);
    }

    @Override
    public Result<?> getStatusHistory(LocalDateTime startTime, LocalDateTime endTime, String keyword, Boolean laserOn,
                                     Float maxBattery, Float minTemperature, Float minCpu, String sortBy, String sortOrder, int page, int size) {
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<RobotStatus> wrapper =
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();

        // 时间范围筛选
        if (startTime != null) {
            wrapper.ge(RobotStatus::getReportedAt, startTime);
        }
        if (endTime != null) {
            wrapper.le(RobotStatus::getReportedAt, endTime);
        }

        // 关键词搜索（时间戳、经纬度模糊匹配）
        if (keyword != null && !keyword.trim().isEmpty()) {
            // 先对经纬度进行模糊搜索
            wrapper.and(w -> w
                    .like(RobotStatus::getLongitude, keyword)
                    .or()
                    .like(RobotStatus::getLatitude, keyword)
            );
        }

        // 激光状态筛选
        if (laserOn != null) {
            wrapper.eq(RobotStatus::getLaserOn, laserOn);
        }

        // 低电量筛选
        if (maxBattery != null) {
            wrapper.le(RobotStatus::getBattery, maxBattery);
        }

        // 高温筛选
        if (minTemperature != null) {
            wrapper.ge(RobotStatus::getTemperature, minTemperature);
        }

        // 高CPU筛选
        if (minCpu != null) {
            wrapper.ge(RobotStatus::getCpuUsage, minCpu);
        }

        // 排序处理 - 基于全部数据排序，而不是只排当前页
        boolean isAsc = sortOrder != null && sortOrder.toLowerCase().startsWith("asc");
        switch (sortBy) {
            case "battery":
                if (isAsc) {
                    wrapper.orderByAsc(RobotStatus::getBattery);
                } else {
                    wrapper.orderByDesc(RobotStatus::getBattery);
                }
                break;
            case "temperature":
                if (isAsc) {
                    wrapper.orderByAsc(RobotStatus::getTemperature);
                } else {
                    wrapper.orderByDesc(RobotStatus::getTemperature);
                }
                break;
            case "cpuUsage":
                if (isAsc) {
                    wrapper.orderByAsc(RobotStatus::getCpuUsage);
                } else {
                    wrapper.orderByDesc(RobotStatus::getCpuUsage);
                }
                break;
            case "speed":
                if (isAsc) {
                    wrapper.orderByAsc(RobotStatus::getSpeed);
                } else {
                    wrapper.orderByDesc(RobotStatus::getSpeed);
                }
                break;
            case "reportedAt":
            default:
                if (isAsc) {
                    wrapper.orderByAsc(RobotStatus::getReportedAt);
                } else {
                    wrapper.orderByDesc(RobotStatus::getReportedAt);
                }
                break;
        }

        // 手动 count 保证 total 正确性
        long total = robotStatusMapper.selectCount(wrapper);

        // 查询所有符合条件的数据用于统计计算（不限制数量）
        List<RobotStatus> allRecordsForStats = robotStatusMapper.selectList(wrapper);

        // 计算基于所有数据的统计信息
        Map<String, Object> stats = calculateStatistics(allRecordsForStats);

        // 手动分页（不依赖分页插件，避免配置问题）
        int offset = (page - 1) * size;
        wrapper.last("LIMIT " + offset + ", " + size);
        List<RobotStatus> pageRecords = robotStatusMapper.selectList(wrapper);

        // 转换为返回格式
        List<Map<String, Object>> list = new ArrayList<>();
        for (RobotStatus status : pageRecords) {
            list.add(formatStatusForResponse(status));
        }

        Map<String, Object> data = new HashMap<>();
        data.put("total", total);
        data.put("list", list);
        data.put("stats", stats);

        return Result.success(data);
    }

    @Override
    public Result<List<Map<String, Object>>> exportStatusHistory(LocalDateTime startTime, LocalDateTime endTime, String keyword, Boolean laserOn,
                                          Float maxBattery, Float minTemperature, Float minCpu, List<Long> ids, int page, int size) {
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<RobotStatus> wrapper =
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();

        if (ids != null && !ids.isEmpty()) {
            wrapper.in(RobotStatus::getId, ids);
        } else {
            if (startTime != null) {
                wrapper.ge(RobotStatus::getReportedAt, startTime);
            }
            if (endTime != null) {
                wrapper.le(RobotStatus::getReportedAt, endTime);
            }
            if (keyword != null && !keyword.trim().isEmpty()) {
                wrapper.and(w -> w
                        .like(RobotStatus::getLongitude, keyword)
                        .or()
                        .like(RobotStatus::getLatitude, keyword)
                );
            }
            if (laserOn != null) {
                wrapper.eq(RobotStatus::getLaserOn, laserOn);
            }
            if (maxBattery != null) {
                wrapper.le(RobotStatus::getBattery, maxBattery);
            }
            if (minTemperature != null) {
                wrapper.ge(RobotStatus::getTemperature, minTemperature);
            }
            if (minCpu != null) {
                wrapper.ge(RobotStatus::getCpuUsage, minCpu);
            }
        }

        wrapper.orderByDesc(RobotStatus::getReportedAt);

        List<RobotStatus> records;
        if (ids != null && !ids.isEmpty()) {
            records = robotStatusMapper.selectList(wrapper);
        } else {
            com.baomidou.mybatisplus.extension.plugins.pagination.Page<RobotStatus> pageRequest =
                    new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>(page, size);
            var pageResult = robotStatusMapper.selectPage(pageRequest, wrapper);
            records = pageResult.getRecords();
        }

        List<Map<String, Object>> result = new ArrayList<>();
        for (RobotStatus status : records) {
            result.add(formatStatusForResponse(status));
        }

        return Result.success(result);
    }

    @Override
    public Result<?> getTrajectory(LocalDateTime startTime, LocalDateTime endTime) {
        List<RobotStatus> points = robotStatusMapper.findTrajectoryBetween(startTime, endTime);

        List<TrajectoryPoint> result = new ArrayList<>();
        for (RobotStatus point : points) {
            if (point.getLongitude() != null && point.getLatitude() != null) {
                String timeStr = outputFormatter.format(point.getReportedAt());
                // 经纬度保留小数点后六位
                Double lng = Math.round(point.getLongitude() * 1000000) / 1000000.0;
                Double lat = Math.round(point.getLatitude() * 1000000) / 1000000.0;
                result.add(new TrajectoryPoint(lng, lat, timeStr));
            }
        }

        Map<String, Object> data = new HashMap<>();
        data.put("points", result);
        return Result.success(data);
    }

    @Override
    public void broadcastStatusUpdate(RobotStatus status) {
        Map<String, Object> data = formatStatusForResponse(status);
        webSocketHandler.broadcastStatusUpdate(data);
    }

    /**
     * 计算基于所有数据的统计信息
     */
    private Map<String, Object> calculateStatistics(List<RobotStatus> allRecords) {
        Map<String, Object> stats = new HashMap<>();

        if (allRecords == null || allRecords.isEmpty()) {
            stats.put("totalRecords", 0);
            stats.put("maxTemp", 0);
            stats.put("avgTemp", 0);
            stats.put("minBattery", null);
            stats.put("avgCpu", 0);
            stats.put("maxCpu", 0);
            stats.put("avgSpeed", 0);
            stats.put("laserOnCount", 0);
            return stats;
        }

        double sumTemp = 0;
        double maxTemp = Double.NEGATIVE_INFINITY;
        double sumCpu = 0;
        double maxCpu = Double.NEGATIVE_INFINITY;
        double minBattery = Double.POSITIVE_INFINITY;
        double sumSpeed = 0;
        int laserOnCount = 0;
        int validSpeedCount = 0;

        for (RobotStatus item : allRecords) {
            // 温度
            if (item.getTemperature() != null) {
                sumTemp += item.getTemperature();
                if (item.getTemperature() > maxTemp) {
                    maxTemp = item.getTemperature();
                }
            }
            // CPU
            if (item.getCpuUsage() != null) {
                sumCpu += item.getCpuUsage();
                if (item.getCpuUsage() > maxCpu) {
                    maxCpu = item.getCpuUsage();
                }
            }
            // 电量
            if (item.getBattery() != null && item.getBattery() < minBattery) {
                minBattery = item.getBattery();
            }
            // 速度
            if (item.getSpeed() != null) {
                sumSpeed += item.getSpeed();
                validSpeedCount++;
            }
            // 激光开启计数
            if (item.getLaserOn() != null && item.getLaserOn()) {
                laserOnCount++;
            }
        }

        stats.put("totalRecords", allRecords.size());
        stats.put("maxTemp", maxTemp != Double.NEGATIVE_INFINITY ? Math.round(maxTemp * 10.0) / 10.0 : 0);
        stats.put("avgTemp", Math.round((sumTemp / allRecords.size()) * 10.0) / 10.0);
        stats.put("minBattery", minBattery != Double.POSITIVE_INFINITY ? Math.round(minBattery * 10.0) / 10.0 : null);
        stats.put("avgCpu", Math.round((sumCpu / allRecords.size()) * 10.0) / 10.0);
        stats.put("maxCpu", maxCpu != Double.NEGATIVE_INFINITY ? Math.round(maxCpu * 10.0) / 10.0 : 0);
        stats.put("avgSpeed", validSpeedCount > 0 ? Math.round((sumSpeed / validSpeedCount) * 100.0) / 100.0 : 0);
        stats.put("laserOnCount", laserOnCount);

        return stats;
    }

    /**
     * 格式化状态为响应格式
     */
    private Map<String, Object> formatStatusForResponse(RobotStatus status) {
        Map<String, Object> data = new HashMap<>();
        data.put("id", status.getId());
        data.put("battery", status.getBattery());
        data.put("speed", status.getSpeed());
        data.put("temperature", status.getTemperature());
        data.put("laserOn", status.getLaserOn());
        data.put("cpuUsage", status.getCpuUsage());
        // 经纬度保留小数点后六位
        if (status.getLongitude() != null) {
            data.put("longitude", Math.round(status.getLongitude() * 1000000) / 1000000.0);
        } else {
            data.put("longitude", null);
        }
        if (status.getLatitude() != null) {
            data.put("latitude", Math.round(status.getLatitude() * 1000000) / 1000000.0);
        } else {
            data.put("latitude", null);
        }

        if (status.getImuData() != null) {
            data.put("imu", JsonUtil.fromJson(status.getImuData(), Object.class));
        }

        if (status.getReportedAt() != null) {
            data.put("reportedAt", outputFormatter.format(status.getReportedAt()));
        }

        return data;
    }
}
