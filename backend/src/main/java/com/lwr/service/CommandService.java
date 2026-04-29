package com.lwr.service;

import com.lwr.common.result.Result;

/**
 * 指令轮询服务接口（供树莓派调用）
 */
public interface CommandService {

    /**
     * 获取待执行指令列表
     */
    Result<?> getPendingCommands();

    /**
     * 确认指令已执行
     */
    Result<Void> ackCommand(Long id, String result, String message);
}
