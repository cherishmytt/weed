package com.lwr.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lwr.common.result.Result;
import com.lwr.common.result.ResultCode;
import com.lwr.controller.websocket.RobotStatusWebSocketHandler;
import com.lwr.entity.DetectionRecord;
import com.lwr.mapper.DetectionRecordMapper;
import com.lwr.service.DetectionService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import jakarta.annotation.PostConstruct;

/**
 * 视觉检测服务实现
 */
@Slf4j
@Service
public class DetectionServiceImpl implements DetectionService {

    private final DetectionRecordMapper detectionRecordMapper;
    private final RobotStatusWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${file.storage.base-path:./uploads}")
    private String basePath;

    public DetectionServiceImpl(DetectionRecordMapper detectionRecordMapper, RobotStatusWebSocketHandler webSocketHandler) {
        this.detectionRecordMapper = detectionRecordMapper;
        this.webSocketHandler = webSocketHandler;
    }

    @PostConstruct
    public void init() {
        // 确保 basePath 有默认值
        if (basePath == null) {
            basePath = "./uploads";
        }
        log.info("初始化前的 basePath: {}", basePath);
        // 确保 basePath 是绝对路径
        File baseDir = new File(basePath);
        log.info("baseDir.isAbsolute(): {}", baseDir.isAbsolute());
        if (!baseDir.isAbsolute()) {
            // 如果是相对路径，使用项目根目录作为基准
            String userDir = System.getProperty("user.dir");
            log.info("用户目录: {}", userDir);
            basePath = new File(userDir, basePath).getAbsolutePath();
            log.info("转换后的 basePath: {}", basePath);
            baseDir = new File(basePath);
        }
        // 确保基础目录存在
        log.info("baseDir.exists(): {}", baseDir.exists());
        if (!baseDir.exists()) {
            boolean mkdirsResult = baseDir.mkdirs();
            log.info("创建目录结果: {}", mkdirsResult);
        }
        log.info("文件存储基础路径: {}", basePath);
    }

    @Override
    public Result<?> reportDetection(MultipartFile rawImage, MultipartFile resultImage, String resultJson) {
        try {
            log.info("开始处理检测结果上报");
            
            // 确保 basePath 是绝对路径
            String actualBasePath = basePath;
            if (actualBasePath == null) {
                actualBasePath = "./uploads";
            }
            File baseDir = new File(actualBasePath);
            if (!baseDir.isAbsolute()) {
                actualBasePath = new File(System.getProperty("user.dir"), actualBasePath).getAbsolutePath();
                baseDir = new File(actualBasePath);
            }
            // 确保基础目录存在
            if (!baseDir.exists()) {
                baseDir.mkdirs();
            }
            log.info("文件存储基础路径: {}", actualBasePath);
            
            // 解析检测结果JSON
            JsonNode resultNode = objectMapper.readTree(resultJson);

            int weedCount = resultNode.has("weedCount") ? resultNode.get("weedCount").asInt() : 0;
            int cropCount = resultNode.has("cropCount") ? resultNode.get("cropCount").asInt() : 0;
            int inferenceTime = resultNode.has("inferenceTime") ? resultNode.get("inferenceTime").asInt() : 0;
            String detectedAtStr = resultNode.has("detectedAt") ? resultNode.get("detectedAt").asText() : LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME);
            // 解析ISO格式时间，转换UTC到系统默认时区
            Instant instant = Instant.parse(detectedAtStr);
            LocalDateTime detectedAt = LocalDateTime.ofInstant(instant, ZoneId.systemDefault());

            // 生成文件名
            String timeStamp = detectedAt.format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
            String uuid = UUID.randomUUID().toString().substring(0, 8);

            // 保存原始图片
            String rawImagePath = "detection/raw/" + timeStamp + "_" + uuid + ".jpg";
            String rawFullPath = actualBasePath + "/" + rawImagePath;
            log.info("保存原始图片到: {}", rawFullPath);
            saveFile(rawImage, rawFullPath);
            String rawImageUrl = "/files/" + rawImagePath;

            // 保存结果图片
            String resultImagePath = "detection/result/" + timeStamp + "_" + uuid + "_det.jpg";
            String resultFullPath = actualBasePath + "/" + resultImagePath;
            log.info("保存结果图片到: {}", resultFullPath);
            saveFile(resultImage, resultFullPath);
            String resultImageUrl = "/files/" + resultImagePath;

            // 保存到数据库
            DetectionRecord record = new DetectionRecord();
            record.setRawImagePath(rawImagePath);
            record.setResultImagePath(resultImagePath);
            record.setWeedCount(weedCount);
            record.setCropCount(cropCount);
            record.setInferenceTime(inferenceTime);
            record.setDetectionsJson(resultJson);
            record.setDetectedAt(detectedAt);

            detectionRecordMapper.insert(record);

            // 构造返回结果
            Map<String, Object> data = new HashMap<>();
            data.put("id", record.getId());
            data.put("imageUrl", rawImageUrl);
            data.put("resultUrl", resultImageUrl);
            data.put("weedCount", weedCount);
            data.put("cropCount", cropCount);
            data.put("inferenceTime", inferenceTime);
            data.put("detectedAt", detectedAt.format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

            // 通过WebSocket广播给前端
            webSocketHandler.broadcastDetectionResult(data);

            log.info("检测结果上报成功: id={}, weeds={}, crops={}", record.getId(), weedCount, cropCount);
            return Result.success(data);

        } catch (IOException e) {
            log.error("保存检测图片失败", e);
            return Result.error(ResultCode.INVALID_IMAGE_FORMAT);
        } catch (Exception e) {
            log.error("解析检测结果失败", e);
            return Result.error(ResultCode.DETECTION_SERVICE_UNAVAILABLE);
        }
    }

    @Override
    public Result<?> getDetectionRecords(LocalDateTime startTime, LocalDateTime endTime, int page, int size) {
        // 手动构建查询条件
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<DetectionRecord> query =
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
        query.orderByDesc(DetectionRecord::getDetectedAt);
        if (startTime != null) {
            query.ge(DetectionRecord::getDetectedAt, startTime);
        }
        if (endTime != null) {
            query.le(DetectionRecord::getDetectedAt, endTime);
        }

        // 查询所有符合条件的记录
        var allRecords = detectionRecordMapper.selectList(query);

        // 手动分页确保生效
        long total = allRecords.size();
        int fromIndex = (page - 1) * size;
        int toIndex = Math.min(fromIndex + size, allRecords.size());

        Map<String, Object> data = new HashMap<>();
        data.put("total", total);

        var list = allRecords.subList(fromIndex, toIndex).stream().map(record -> {
            Map<String, Object> item = new HashMap<>();
            item.put("id", record.getId());
            item.put("imageUrl", "/files/" + record.getRawImagePath());
            item.put("resultUrl", "/files/" + record.getResultImagePath());
            item.put("weedCount", record.getWeedCount());
            item.put("cropCount", record.getCropCount());
            item.put("inferenceTime", record.getInferenceTime());
            item.put("detectedAt", record.getDetectedAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
            return item;
        }).toList();

        data.put("list", list);
        return Result.success(data);
    }

    @Override
    public Result<?> getDetectionDetail(Long id) {
        DetectionRecord record = detectionRecordMapper.selectById(id);
        if (record == null) {
            return Result.error(ResultCode.NOT_FOUND);
        }

        Map<String, Object> data = new HashMap<>();
        data.put("id", record.getId());
        data.put("imageUrl", "/files/" + record.getRawImagePath());
        data.put("resultUrl", "/files/" + record.getResultImagePath());
        data.put("weedCount", record.getWeedCount());
        data.put("cropCount", record.getCropCount());
        data.put("inferenceTime", record.getInferenceTime());
        try {
            // 打印detectionsJson的前500个字符，帮助诊断问题
            log.info("解析检测结果JSON (前500字符): {}", record.getDetectionsJson().substring(0, Math.min(500, record.getDetectionsJson().length())));
            
            JsonNode rootNode = objectMapper.readValue(record.getDetectionsJson(), JsonNode.class);
            
            // 检查rootNode的结构
            log.info("rootNode has detections: {}, isArray: {}", rootNode.has("detections"), rootNode.has("detections") ? rootNode.get("detections").isArray() : false);
            
            // 从JSON中提取detections数组并转换格式
            if (rootNode.has("detections") && rootNode.get("detections").isArray()) {
                JsonNode detectionsNode = rootNode.get("detections");
                log.info("detections数组长度: {}", detectionsNode.size());
                
                java.util.List<Object> detectionsList = new java.util.ArrayList<>();
                for (JsonNode detectionNode : detectionsNode) {
                    Map<String, Object> detection = new HashMap<>();

                    // 兼容两种格式：
                    // - 旧格式: "class" (文本)
                    // - YOLO格式: "classId" (数字) + "className" (文本)
                    if (detectionNode.has("class")) {
                        detection.put("class", detectionNode.get("class").asText());
                    } else if (detectionNode.has("classId")) {
                        detection.put("class", String.valueOf(detectionNode.get("classId").asInt()));
                    } else {
                        detection.put("class", "0");
                    }

                    if (detectionNode.has("className")) {
                        detection.put("className", detectionNode.get("className").asText());
                    }

                    if (detectionNode.has("confidence")) {
                        detection.put("confidence", detectionNode.get("confidence").asDouble());
                    }

                    // 转换bbox格式：兼容多种格式转为数组 [x1, y1, x2, y2]
                    if (detectionNode.has("bbox")) {
                        JsonNode bboxNode = detectionNode.get("bbox");
                        if (bboxNode.isObject()) {
                            // YOLO格式: {x1, y1, x2, y2} 直接使用
                            if (bboxNode.has("x1") && bboxNode.has("y1") && bboxNode.has("x2") && bboxNode.has("y2")) {
                                double x1 = bboxNode.get("x1").asDouble();
                                double y1 = bboxNode.get("y1").asDouble();
                                double x2 = bboxNode.get("x2").asDouble();
                                double y2 = bboxNode.get("y2").asDouble();
                                detection.put("bbox", new double[]{x1, y1, x2, y2});
                            }
                            // 旧格式: {x, y, width, height} 需要转换
                            else if (bboxNode.has("x") && bboxNode.has("y") && bboxNode.has("width") && bboxNode.has("height")) {
                                double x = bboxNode.has("x") ? bboxNode.get("x").asDouble() : 0;
                                double y = bboxNode.has("y") ? bboxNode.get("y").asDouble() : 0;
                                double width = bboxNode.has("width") ? bboxNode.get("width").asDouble() : 0;
                                double height = bboxNode.has("height") ? bboxNode.get("height").asDouble() : 0;
                                detection.put("bbox", new double[]{x, y, x + width, y + height});
                            } else {
                                detection.put("bbox", new double[]{0, 0, 0, 0});
                            }
                        } else if (detectionNode.get("bbox").isArray()) {
                            // 如果已经是数组格式，直接使用
                            java.util.List<Double> bboxList = new java.util.ArrayList<>();
                            for (JsonNode node : detectionNode.get("bbox")) {
                                bboxList.add(node.asDouble());
                            }
                            detection.put("bbox", bboxList.stream().mapToDouble(Double::doubleValue).toArray());
                        } else {
                            detection.put("bbox", new double[]{0, 0, 0, 0});
                        }
                    } else {
                        // 如果没有bbox字段，添加一个默认值
                        detection.put("bbox", new double[]{0, 0, 0, 0});
                    }

                    // 处理keypoints
                    if (detectionNode.has("keypoints") && detectionNode.get("keypoints").isArray()) {
                        detection.put("keypoints", objectMapper.convertValue(detectionNode.get("keypoints"), Object.class));
                    } else if (detectionNode.has("stem") && detectionNode.get("stem").isObject()) {
                        // YOLO格式: 根茎关键点 stem {x, y} 转为keypoints数组
                        JsonNode stemNode = detectionNode.get("stem");
                        double x = stemNode.has("x") ? stemNode.get("x").asDouble() : 0;
                        double y = stemNode.has("y") ? stemNode.get("y").asDouble() : 0;
                        detection.put("keypoints", new double[]{x, y});
                        detection.put("stem", objectMapper.convertValue(stemNode, Object.class));
                    } else {
                        detection.put("keypoints", new java.util.ArrayList<>());
                    }

                    // 处理depth
                    if (detectionNode.has("depth")) {
                        detection.put("depth", detectionNode.get("depth").asDouble());
                    }

                    // 处理position3d
                    if (detectionNode.has("position3d") && detectionNode.get("position3d").isObject()) {
                        JsonNode position3dNode = detectionNode.get("position3d");
                        Map<String, Object> position3d = new HashMap<>();
                        position3d.put("x", position3dNode.get("x").asDouble());
                        position3d.put("y", position3dNode.get("y").asDouble());
                        position3d.put("z", position3dNode.get("z").asDouble());
                        detection.put("position3d", position3d);
                    }

                    detectionsList.add(detection);
                }
                data.put("detections", detectionsList);
                log.info("成功解析detections数组，长度: {}", detectionsList.size());
            } else {
                // 尝试从其他字段中提取检测信息
                java.util.List<Object> detectionsList = new java.util.ArrayList<>();
                
                // 检查是否有直接的检测结果字段
                if (rootNode.has("weedCount") || rootNode.has("cropCount")) {
                    // 根据weedCount和cropCount创建多个检测记录
                    int weedCount = rootNode.has("weedCount") ? rootNode.get("weedCount").asInt() : 0;
                    int cropCount = rootNode.has("cropCount") ? rootNode.get("cropCount").asInt() : 0;
                    
                    log.info("没有detections字段，根据weedCount: {}和cropCount: {}创建检测记录", weedCount, cropCount);
                    
                    // 添加杂草检测记录
                    for (int i = 0; i < weedCount; i++) {
                        Map<String, Object> detection = new HashMap<>();
                        detection.put("class", "0");
                        detection.put("className", "杂草");
                        detection.put("confidence", 0.9);
                        detection.put("bbox", new double[]{0, 0, 0, 0});
                        detection.put("keypoints", new java.util.ArrayList<>());
                        detectionsList.add(detection);
                    }
                    
                    // 添加作物检测记录
                    for (int i = 0; i < cropCount; i++) {
                        Map<String, Object> detection = new HashMap<>();
                        detection.put("class", "1");
                        detection.put("className", "作物");
                        detection.put("confidence", 0.9);
                        detection.put("bbox", new double[]{0, 0, 0, 0});
                        detection.put("keypoints", new java.util.ArrayList<>());
                        detectionsList.add(detection);
                    }
                }
                
                data.put("detections", detectionsList);
                log.info("创建默认检测记录，长度: {}", detectionsList.size());
            }
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            log.warn("解析检测结果JSON失败: {}", id, e);
            data.put("detections", new java.util.ArrayList<>());
        }
        data.put("detectedAt", record.getDetectedAt().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

        return Result.success(data);
    }

    private void saveFile(MultipartFile file, String fullPath) throws IOException {
        File dest = new File(fullPath);
        // 确保目录存在
        if (dest.getParentFile() != null && !dest.getParentFile().exists()) {
            if (!dest.getParentFile().mkdirs()) {
                throw new IOException("无法创建目录: " + dest.getParentFile().getAbsolutePath());
            }
        }
        file.transferTo(dest);
    }
}
