package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 视觉检测记录实体
 */
@Data
@TableName("detection_record")
public class DetectionRecord {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String rawImagePath;
    private String resultImagePath;
    private Integer weedCount;
    private Integer cropCount;
    private Integer inferenceTime;
    private String detectionsJson; // JSON格式存储检测结果
    private LocalDateTime detectedAt;
    private LocalDateTime createdAt;
}
