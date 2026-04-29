package com.lwr.service;

import com.lwr.common.result.Result;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

/**
 * 视觉检测服务接口
 */
public interface DetectionService {

    /**
     * 上报检测结果（由树莓派调用）
     */
    Result<?> reportDetection(MultipartFile rawImage, MultipartFile resultImage, String resultJson);

    /**
     * 查询检测记录列表
     */
    Result<?> getDetectionRecords(LocalDateTime startTime, LocalDateTime endTime, int page, int size);

    /**
     * 获取单条检测详情
     */
    Result<?> getDetectionDetail(Long id);
}
