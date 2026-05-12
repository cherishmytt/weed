package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.LaserControlService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
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

@Tag(name = "激光控制", description = "激光除草设备控制与状态监控")
@RestController
@RequestMapping("/api/v1/robot/laser")
public class LaserController {

    private final LaserControlService laserControlService;

    public LaserController(LaserControlService laserControlService) {
        this.laserControlService = laserControlService;
    }

    @Operation(summary = "下发激光控制指令", description = "向激光设备发送控制指令，如开关、照射等")
    @ApiResponse(responseCode = "200", description = "指令下发成功")
    @PostMapping("/command")
    public Result<?> sendCommand(@RequestBody Map<String, Object> params) {
        String action = (String) params.get("action");
        Object actionParams = params.get("params");
        return laserControlService.sendCommand(action, actionParams);
    }

    @Operation(summary = "查询激光设备状态", description = "获取激光设备的当前连接和运行状态")
    @ApiResponse(responseCode = "200", description = "获取成功")
    @GetMapping("/status")
    public Result<?> getStatus() {
        return laserControlService.getLaserStatus();
    }

    @Operation(summary = "查询激光设备能力", description = "获取激光设备支持的操作类型和参数范围")
    @ApiResponse(responseCode = "200", description = "获取成功")
    @GetMapping("/capabilities")
    public Result<?> getCapabilities() {
        return laserControlService.getCapabilities();
    }

    @Operation(summary = "查询激光操作日志", description = "分页查询激光设备的操作历史记录")
    @ApiResponse(responseCode = "200", description = "查询成功")
    @GetMapping("/logs")
    public Result<?> getLogs(
            @Parameter(description = "开始时间") @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @Parameter(description = "操作类型筛选") @RequestParam(value = "action", required = false) List<String> action,
            @Parameter(description = "结果筛选") @RequestParam(value = "result", required = false) List<String> result,
            @Parameter(description = "关键词搜索") @RequestParam(value = "keyword", required = false) String keyword,
            @Parameter(description = "目标X最小值") @RequestParam(value = "targetXMin", required = false) Float targetXMin,
            @Parameter(description = "目标X最大值") @RequestParam(value = "targetXMax", required = false) Float targetXMax,
            @Parameter(description = "目标Y最小值") @RequestParam(value = "targetYMin", required = false) Float targetYMin,
            @Parameter(description = "目标Y最大值") @RequestParam(value = "targetYMax", required = false) Float targetYMax,
            @Parameter(description = "深度最小值") @RequestParam(value = "depthMin", required = false) Float depthMin,
            @Parameter(description = "深度最大值") @RequestParam(value = "depthMax", required = false) Float depthMax,
            @Parameter(description = "持续时间最小值(ms)") @RequestParam(value = "durationMin", required = false) Integer durationMin,
            @Parameter(description = "持续时间最大值(ms)") @RequestParam(value = "durationMax", required = false) Integer durationMax,
            @Parameter(description = "排序字段") @RequestParam(value = "sortBy", defaultValue = "createdAt") String sortBy,
            @Parameter(description = "排序方式") @RequestParam(value = "sortOrder", defaultValue = "descending") String sortOrder,
            @Parameter(description = "页码") @RequestParam(value = "page", defaultValue = "1") int page,
            @Parameter(description = "每页数量") @RequestParam(value = "size", defaultValue = "10") int size) {
        return laserControlService.getOperationLogs(startTime, endTime, action, result, keyword,
                targetXMin, targetXMax, targetYMin, targetYMax, depthMin, depthMax,
                durationMin, durationMax, sortBy, sortOrder, page, size);
    }

    @Operation(summary = "导出激光操作日志", description = "根据ID列表导出指定的激光操作日志")
    @ApiResponse(responseCode = "200", description = "导出成功")
    @PostMapping("/logs/export")
    public Result<List<Map<String, Object>>> exportLogs(@RequestBody Map<String, Object> params) {
        List<Long> ids = (List<Long>) params.get("ids");
        return (Result<List<Map<String, Object>>>) laserControlService.exportLogs(ids);
    }

    @Operation(summary = "批量删除激光操作日志", description = "根据ID列表批量删除激光操作日志")
    @ApiResponse(responseCode = "200", description = "删除成功")
    @PostMapping("/logs/batch-delete")
    public Result<Void> batchDeleteLogs(@RequestBody Map<String, Object> params) {
        List<Long> ids = (List<Long>) params.get("ids");
        return laserControlService.batchDeleteLogs(ids);
    }

    @Operation(summary = "上报激光执行反馈", description = "树莓派设备上报激光指令的执行结果")
    @ApiResponse(responseCode = "200", description = "反馈接收成功")
    @PostMapping("/feedback")
    public Result<Void> feedback(@RequestBody Map<String, Object> params) {
        String commandId = (String) params.get("commandId");
        String action = (String) params.get("action");
        String result = (String) params.get("result");
        String message = (String) params.get("message");
        String timestamp = (String) params.get("timestamp");
        return laserControlService.receiveFeedback(commandId, action, result, message, timestamp);
    }

    @Operation(summary = "更新激光设备状态", description = "树莓派设备更新激光设备的运行状态")
    @ApiResponse(responseCode = "200", description = "状态更新成功")
    @PostMapping("/status-update")
    public Result<Void> updateStatus(@RequestBody Map<String, Object> params) {
        String status = (String) params.get("status");
        String statusText = (String) params.get("statusText");
        return laserControlService.updateLaserStatus(status, statusText);
    }
}