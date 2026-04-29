package com.lwr.service;

import com.lwr.common.result.Result;

/**
 * 统计服务接口 - 仪表盘数据
 */
public interface StatisticsService {

    /**
     * 获取仪表盘概览数据
     */
    Result<?> getDashboardData();
}
