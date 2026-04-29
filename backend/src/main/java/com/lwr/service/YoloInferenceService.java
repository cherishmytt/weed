package com.lwr.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.lwr.model.InferenceResult;
import com.lwr.model.ModelProperties;
import com.lwr.model.PredictionView;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class YoloInferenceService {

    private static final DateTimeFormatter TS_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
    private final ModelProperties properties;
    private final ObjectMapper objectMapper;
    private Path outputRoot;

    public YoloInferenceService(ModelProperties properties, ObjectMapper objectMapper) {
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    public void init() throws IOException {
        outputRoot = Paths.get(properties.getOutputRoot()).toAbsolutePath().normalize();
        Files.createDirectories(outputRoot.resolve("uploads"));
        Files.createDirectories(outputRoot.resolve("results"));
    }

    public Path getOutputRoot() {
        return outputRoot;
    }

    public PredictionView predict(MultipartFile file, double conf, String classes) throws IOException, InterruptedException {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("请先上传图片文件。");
        }
        if (conf <= 0.0 || conf > 1.0) {
            throw new IllegalArgumentException("置信度范围应在 0.01 ~ 1.0。");
        }

        String ext = getExtension(file.getOriginalFilename());
        if (!List.of(".jpg", ".jpeg", ".png", ".bmp").contains(ext.toLowerCase(Locale.ROOT))) {
            throw new IllegalArgumentException("仅支持 jpg/jpeg/png/bmp 图片。");
        }

        String requestId = TS_FORMAT.format(LocalDateTime.now()) + "_" + UUID.randomUUID().toString().substring(0, 8);
        Path uploadPath = outputRoot.resolve("uploads").resolve(requestId + ext);
        Path resultImagePath = outputRoot.resolve("results").resolve(requestId + "_pred.jpg");
        Path resultJsonPath = outputRoot.resolve("results").resolve(requestId + ".json");

        Files.copy(file.getInputStream(), uploadPath);

        List<String> command = new ArrayList<>();
        command.add(properties.getPythonExecutable());
        command.add(properties.getScriptPath());
        command.add("--model");
        command.add(properties.getWeightPath());
        command.add("--input");
        command.add(uploadPath.toString());
        command.add("--output-image");
        command.add(resultImagePath.toString());
        command.add("--output-json");
        command.add(resultJsonPath.toString());
        command.add("--conf");
        command.add(String.format(Locale.US, "%.4f", conf));
        String classFilter = classes == null ? properties.getClasses() : classes.trim();
        if (classFilter != null && !classFilter.isBlank()) {
            if (!classFilter.matches("^\\d+(,\\d+)*$")) {
                throw new IllegalArgumentException("classes 格式错误，请使用如 8 或 0,8。");
            }
            command.add("--classes");
            command.add(classFilter);
        }
        command.add("--imgsz");
        command.add(String.valueOf(properties.getImgsz()));

        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.redirectErrorStream(true);
        Process process = processBuilder.start();

        StringBuilder log = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                log.append(line).append(System.lineSeparator());
            }
        }
        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("模型推理失败，退出码 " + exitCode + "。日志：\n" + log);
        }

        if (!Files.exists(resultJsonPath)) {
            throw new RuntimeException("模型推理完成但未生成结果 JSON。日志：\n" + log);
        }

        InferenceResult inference = objectMapper.readValue(resultJsonPath.toFile(), InferenceResult.class);

        PredictionView view = new PredictionView();
        view.setResult(inference);
        view.setRuntimeLog(log.toString());
        view.setOriginalImageUrl(toFileUrl(uploadPath));
        view.setOutputImageUrl(toFileUrl(resultImagePath));
        return view;
    }

    private String toFileUrl(Path path) {
        Path rel = outputRoot.relativize(path.toAbsolutePath().normalize());
        return "/files/yolo/" + rel.toString().replace("\\", "/");
    }

    private String getExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf('.'));
    }
}
