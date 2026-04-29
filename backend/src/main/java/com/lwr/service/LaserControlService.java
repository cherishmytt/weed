package com.lwr.service;

import com.lwr.common.result.Result;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 激光控制服务接口
 */
public interface LaserControlService {

    /**
     * 下发激光控制指令
     */
    Result<?> sendCommand(String action, Object params);

    /**
     * 获取激光设备当前状态
     */
    Result<?> getLaserStatus();

    /**
     * 获取激光设备能力信息
     */
    Result<?> getCapabilities();

    /**
     * 查询激光操作日志（支持多条件筛选）
     */
    Result<?> getOperationLogs(LocalDateTime startTime, LocalDateTime endTime, List<String> action, List<String> result, String keyword,
                               Float targetXMin, Float targetXMax, Float targetYMin, Float targetYMax,
                               Float depthMin, Float depthMax, Integer durationMin, Integer durationMax,
                               String sortBy, String sortOrder, int page, int size);

    /**
     * 导出激光操作日志
     */
    Result<?> exportLogs(List<Long> ids);

    /**
     * 批量删除激光操作日志
     */
    Result<Void> batchDeleteLogs(List<Long> ids);

    /**
     * 接收激光执行反馈（由树莓派调用）
     */
    Result<Void> receiveFeedback(String commandId, String action, String result, String message, String timestamp);

    /**
     * 更新激光设备状态（由树莓派调用）
     */
    Result<Void> updateLaserStatus(String status, String statusText);
}
