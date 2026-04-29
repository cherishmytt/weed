package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.service.CommandService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 指令轮询控制器（供树莓派调用）
 */
@RestController
@RequestMapping("/api/v1/robot/commands")
public class CommandController {

    private final CommandService commandService;

    public CommandController(CommandService commandService) {
        this.commandService = commandService;
    }

    /**
     * 获取待执行指令（树莓派轮询调用）
     */
    @GetMapping("/pending")
    public Result<?> getPendingCommands() {
        return commandService.getPendingCommands();
    }

    /**
     * 确认指令已执行（树莓派调用）
     */
    @PutMapping("/{id}/ack")
    public Result<Void> ackCommand(@PathVariable Long id, @RequestBody Map<String, Object> params) {
        String result = (String) params.get("result");
        String message = (String) params.get("message");
        return commandService.ackCommand(id, result, message);
    }
}
