package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 机器人基本信息实体
 */
@Data
@TableName("robot_info")
public class RobotInfo {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String robotCode;
    private String name;
    private String model;
    private Integer currentStatus;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
