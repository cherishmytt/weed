package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 机器人指令队列实体
 */
@Data
@TableName("robot_command")
public class LaserCommand {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String commandId;
    private String action;
    private String paramsJson; // JSON格式存储参数
    private String status; // PENDING / SENT / ACKED
    private LocalDateTime createdAt;
    private LocalDateTime acknowledgedAt;
}
