package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 激光设备当前状态实体
 */
@Data
@TableName("laser_status")
public class LaserStatus {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Boolean connected;
    private String status;
    private String statusText;
    private LocalDateTime lastFireAt;
    private Integer totalFireCount;
    private Integer totalFireDuration;
    private Float temperature;
    private Float power;
    private String errorCode;
    private LocalDateTime updatedAt;
    private Float aimTargetX;
    private Float aimTargetY;
}
