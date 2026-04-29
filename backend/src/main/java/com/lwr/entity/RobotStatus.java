package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 机器人运行状态历史实体
 */
@Data
@TableName("robot_status")
public class RobotStatus {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Float battery;
    private Float speed;
    private Float temperature;
    private Boolean laserOn;
    private Float cpuUsage;
    private Double longitude;
    private Double latitude;
    private String imuData; // JSON格式存储
    private LocalDateTime reportedAt;
    private LocalDateTime createdAt;
}
