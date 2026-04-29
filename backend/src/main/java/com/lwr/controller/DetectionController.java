package com.lwr.controller;

import com.lwr.common.result.Result;
import com.lwr.model.PredictionView;
import com.lwr.service.DetectionService;
import com.lwr.service.YoloInferenceService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

/**
 * 视觉检测控制器
 */
@RestController
@RequestMapping("/api/v1/detection")
public class DetectionController {

    private final DetectionService detectionService;
    private final YoloInferenceService yoloInferenceService;

    public DetectionController(DetectionService detectionService, YoloInferenceService yoloInferenceService) {
        this.detectionService = detectionService;
        this.yoloInferenceService = yoloInferenceService;
    }

    /**
     * 上报检测结果（由树莓派调用）
     */
    @PostMapping("/report")
    public Result<?> report(
            @RequestParam("rawImage") MultipartFile rawImage,
            @RequestParam("resultImage") MultipartFile resultImage,
            @RequestParam("result") String resultJson) {
        return detectionService.reportDetection(rawImage, resultImage, resultJson);
    }

    /**
     * YOLOv8 杂草检测推理（直接在后端调用Python模型）
     */
    @PostMapping("/yolo-predict")
    public Result<?> yoloPredict(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "conf", defaultValue = "0.25") double conf,
            @RequestParam(value = "classes", required = false) String classes) {
        try {
            long start = System.currentTimeMillis();
            PredictionView result = yoloInferenceService.predict(file, conf, classes);
            long elapsed = System.currentTimeMillis() - start;
            // 创建包含elapsedMs的结果Map
            java.util.Map<String, Object> response = new java.util.HashMap<>();
            response.put("result", result);
            response.put("elapsedMs", elapsed);
            return Result.success(response);
        } catch (IllegalArgumentException e) {
            return Result.error(400, e.getMessage());
        } catch (Exception e) {
            return Result.error(500, "推理失败: " + e.getMessage());
        }
    }

    /**
     * 查询检测记录列表
     */
    @GetMapping("/records")
    public Result<?> getRecords(
            @RequestParam(value = "startTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @RequestParam(value = "endTime", required = false) @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime,
            @RequestParam(value = "page", defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "10") int size) {
        return detectionService.getDetectionRecords(startTime, endTime, page, size);
    }

    /**
     * 获取单条检测详情
     */
    @GetMapping("/records/{id}")
    public Result<?> getDetail(@PathVariable Long id) {
        return detectionService.getDetectionDetail(id);
    }
}
