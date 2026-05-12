package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.RobotService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
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

@Tag(name = "机器人管理", description = "机器人状态监控与轨迹管理")
@RestController
@RequestMapping("/api/v1/robot")
public class RobotController {

    private final RobotService robotService;

    public RobotController(RobotService robotService) {
        this.robotService = robotService;
    }

    @Operation(summary = "获取机器人基本信息", description = "获取当前机器人的基本信息的接口")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "获取成功",
                    content = @Content(schema = @Schema(implementation = Result.class)))
    })
    @GetMapping("/info")
    public Result<?> getRobotInfo() {
        return robotService.getRobotInfo();
    }

    @Operation(summary = "上报机器人运行状态", description = "由树莓派设备调用，上报机器人实时运行状态")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "上报成功"),
            @ApiResponse(responseCode = "401", description = "未授权")
    })
    @PostMapping("/status")
    public Result<Void> reportStatus(@RequestBody RobotService.RobotStatusReportRequest request) {
        return robotService.reportStatus(request);
    }

    @Operation(summary = "获取最新运行状态", description = "获取机器人最近一次上报的运行状态")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "获取成功")
    })
    @GetMapping("/status/latest")
    public Result<?> getLatestStatus() {
        return robotService.getLatestStatus();
    }

    @Operation(summary = "查询状态历史记录", description = "支持多条件筛选和分页查询机器人状态历史")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "查询成功")
    })
    @GetMapping("/status/history")
    public Result<?> getStatusHistory(
            @Parameter(description = "开始时间") @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @Parameter(description = "关键词搜索(经纬度)") @RequestParam(value = "keyword", required = false) String keyword,
            @Parameter(description = "激光是否开启") @RequestParam(value = "laserOn", required = false) Boolean laserOn,
            @Parameter(description = "最大电量阈值") @RequestParam(value = "maxBattery", required = false) Float maxBattery,
            @Parameter(description = "最低温度阈值") @RequestParam(value = "minTemperature", required = false) Float minTemperature,
            @Parameter(description = "最低CPU使用率阈值") @RequestParam(value = "minCpu", required = false) Float minCpu,
            @Parameter(description = "排序字段") @RequestParam(value = "sortBy", defaultValue = "reportedAt") String sortBy,
            @Parameter(description = "排序方式") @RequestParam(value = "sortOrder", defaultValue = "descending") String sortOrder,
            @Parameter(description = "页码") @RequestParam(value = "page", defaultValue = "1") int page,
            @Parameter(description = "每页数量") @RequestParam(value = "size", defaultValue = "20") int size) {
        return robotService.getStatusHistory(startTime, endTime, keyword, laserOn,
                maxBattery, minTemperature, minCpu, sortBy, sortOrder, page, size);
    }

    @Operation(summary = "导出状态历史记录", description = "导出符合条件的机器人状态历史记录，支持按ID列表导出选中记录")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "导出成功")
    })
    @GetMapping("/status/history/export")
    public Result<List<Map<String, Object>>> exportStatusHistory(
            @Parameter(description = "开始时间") @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @Parameter(description = "关键词搜索") @RequestParam(value = "keyword", required = false) String keyword,
            @Parameter(description = "激光状态") @RequestParam(value = "laserOn", required = false) Boolean laserOn,
            @Parameter(description = "最大电量") @RequestParam(value = "maxBattery", required = false) Float maxBattery,
            @Parameter(description = "最低温度") @RequestParam(value = "minTemperature", required = false) Float minTemperature,
            @Parameter(description = "最低CPU") @RequestParam(value = "minCpu", required = false) Float minCpu,
            @Parameter(description = "选中记录ID列表（逗号分隔）") @RequestParam(value = "ids", required = false) List<Long> ids,
            @Parameter(description = "页码") @RequestParam(value = "page", defaultValue = "1") int page,
            @Parameter(description = "每页数量") @RequestParam(value = "size", defaultValue = "10000") int size) {
        return robotService.exportStatusHistory(startTime, endTime, keyword, laserOn,
                maxBattery, minTemperature, minCpu, ids, page, size);
    }

    @Operation(summary = "查询推行轨迹", description = "查询机器人在指定时间范围内的推行轨迹")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "查询成功")
    })
    @GetMapping("/trajectory")
    public Result<?> getTrajectory(
            @Parameter(description = "开始时间", required = true) @RequestParam("startTime") @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间", required = true) @RequestParam("endTime") @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        return robotService.getTrajectory(startTime, endTime);
    }
}
