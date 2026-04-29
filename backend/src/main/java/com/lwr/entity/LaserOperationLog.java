package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 激光操作日志实体
 */
@Data
@TableName("laser_operation_log")
public class LaserOperationLog {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String commandId;
    private String action;
    private Float targetX;
    private Float targetY;
    private Float depth;
    private Integer duration;
    private String result;
    private String message;
    private LocalDateTime executedAt;
    private LocalDateTime createdAt;
}
