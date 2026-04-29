package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.StatisticsService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 统计数据控制器 - 仪表盘
 */
@RestController
@RequestMapping("/api/v1/statistics")
public class StatisticsController {

    private final StatisticsService statisticsService;

    public StatisticsController(StatisticsService statisticsService) {
        this.statisticsService = statisticsService;
    }

    /**
     * 获取仪表盘概览数据
     */
    @GetMapping("/dashboard")
    public Result<?> getDashboard() {
        return statisticsService.getDashboardData();
    }
}
