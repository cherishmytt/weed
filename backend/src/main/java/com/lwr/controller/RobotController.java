package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.RobotService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 机器人状态控制器
 */
@RestController
@RequestMapping("/api/v1/robot")
public class RobotController {

    private final RobotService robotService;

    public RobotController(RobotService robotService) {
        this.robotService = robotService;
    }

    /**
     * 获取机器人基本信息
     */
    @GetMapping("/info")
    public Result<?> getRobotInfo() {
        return robotService.getRobotInfo();
    }

    /**
     * 上报机器人运行状态（由树莓派调用）
     */
    @PostMapping("/status")
    public Result<Void> reportStatus(@RequestBody RobotService.RobotStatusReportRequest request) {
        return robotService.reportStatus(request);
    }

    /**
     * 获取最新运行状态
     */
    @GetMapping("/status/latest")
    public Result<?> getLatestStatus() {
        return robotService.getLatestStatus();
    }

    /**
     * 查询状态历史记录（支持多条件筛选）
     */
    @GetMapping("/status/history")
    public Result<?> getStatusHistory(
            @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "laserOn", required = false) Boolean laserOn,
            @RequestParam(value = "maxBattery", required = false) Float maxBattery,
            @RequestParam(value = "minTemperature", required = false) Float minTemperature,
            @RequestParam(value = "minCpu", required = false) Float minCpu,
            @RequestParam(value = "sortBy", defaultValue = "reportedAt") String sortBy,
            @RequestParam(value = "sortOrder", defaultValue = "descending") String sortOrder,
            @RequestParam(value = "page", defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "20") int size) {
        return robotService.getStatusHistory(startTime, endTime, keyword, laserOn,
                maxBattery, minTemperature, minCpu, sortBy, sortOrder, page, size);
    }

    /**
     * 导出状态历史记录（筛选结果）
     */
    @GetMapping("/status/history/export")
    public Result<List<Map<String, Object>>> exportStatusHistory(
            @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "laserOn", required = false) Boolean laserOn,
            @RequestParam(value = "maxBattery", required = false) Float maxBattery,
            @RequestParam(value = "minTemperature", required = false) Float minTemperature,
            @RequestParam(value = "minCpu", required = false) Float minCpu,
            @RequestParam(value = "page", defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "10000") int size) {
        return robotService.exportStatusHistory(startTime, endTime, keyword, laserOn,
                maxBattery, minTemperature, minCpu, page, size);
    }

    /**
     * 查询推行轨迹
     */
    @GetMapping("/trajectory")
    public Result<?> getTrajectory(
            @RequestParam("startTime") @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @RequestParam("endTime") @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        return robotService.getTrajectory(startTime, endTime);
    }
}
