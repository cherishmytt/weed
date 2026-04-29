package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.LaserControlService;
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
 * 激光控制控制器
 */
@RestController
@RequestMapping("/api/v1/robot/laser")
public class LaserController {

    private final LaserControlService laserControlService;

    public LaserController(LaserControlService laserControlService) {
        this.laserControlService = laserControlService;
    }

    /**
     * 下发激光控制指令
     */
    @PostMapping("/command")
    public Result<?> sendCommand(@RequestBody Map<String, Object> params) {
        String action = (String) params.get("action");
        Object actionParams = params.get("params");
        return laserControlService.sendCommand(action, actionParams);
    }

    /**
     * 查询激光设备当前状态
     */
    @GetMapping("/status")
    public Result<?> getStatus() {
        return laserControlService.getLaserStatus();
    }

    /**
     * 查询激光设备能力信息
     */
    @GetMapping("/capabilities")
    public Result<?> getCapabilities() {
        return laserControlService.getCapabilities();
    }

    /**
     * 查询激光操作日志（支持多条件筛选）
     */
    @GetMapping("/logs")
    public Result<?> getLogs(
            @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @RequestParam(value = "action", required = false) List<String> action,
            @RequestParam(value = "result", required = false) List<String> result,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "targetXMin", required = false) Float targetXMin,
            @RequestParam(value = "targetXMax", required = false) Float targetXMax,
            @RequestParam(value = "targetYMin", required = false) Float targetYMin,
            @RequestParam(value = "targetYMax", required = false) Float targetYMax,
            @RequestParam(value = "depthMin", required = false) Float depthMin,
            @RequestParam(value = "depthMax", required = false) Float depthMax,
            @RequestParam(value = "durationMin", required = false) Integer durationMin,
            @RequestParam(value = "durationMax", required = false) Integer durationMax,
            @RequestParam(value = "sortBy", defaultValue = "createdAt") String sortBy,
            @RequestParam(value = "sortOrder", defaultValue = "descending") String sortOrder,
            @RequestParam(value = "page", defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "10") int size) {
        return laserControlService.getOperationLogs(startTime, endTime, action, result, keyword,
                targetXMin, targetXMax, targetYMin, targetYMax, depthMin, depthMax,
                durationMin, durationMax, sortBy, sortOrder, page, size);
    }

    /**
     * 导出激光操作日志
     */
    @PostMapping("/logs/export")
    public Result<List<Map<String, Object>>> exportLogs(@RequestBody Map<String, Object> params) {
        List<Long> ids = (List<Long>) params.get("ids");
        // 修复：添加强制类型转换
        return (Result<List<Map<String, Object>>>) laserControlService.exportLogs(ids);
    }

    /**
     * 批量删除激光操作日志
     */
    @PostMapping("/logs/batch-delete")
    public Result<Void> batchDeleteLogs(@RequestBody Map<String, Object> params) {
        List<Long> ids = (List<Long>) params.get("ids");
        return laserControlService.batchDeleteLogs(ids);
    }

    /**
     * 上报激光执行反馈（由树莓派调用）
     */
    @PostMapping("/feedback")
    public Result<Void> feedback(@RequestBody Map<String, Object> params) {
        String commandId = (String) params.get("commandId");
        String action = (String) params.get("action");
        String result = (String) params.get("result");
        String message = (String) params.get("message");
        String timestamp = (String) params.get("timestamp");
        return laserControlService.receiveFeedback(commandId, action, result, message, timestamp);
    }

    /**
     * 更新激光设备状态（由树莓派调用）
     */
    @PostMapping("/status-update")
    public Result<Void> updateStatus(@RequestBody Map<String, Object> params) {
        String status = (String) params.get("status");
        String statusText = (String) params.get("statusText");
        return laserControlService.updateLaserStatus(status, statusText);
    }
}