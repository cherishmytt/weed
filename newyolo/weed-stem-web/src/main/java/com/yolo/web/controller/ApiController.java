package com.yolo.web.controller;

import com.yolo.web.model.PredictionView;
import com.yolo.web.service.YoloInferenceService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api")
public class ApiController {

    private final YoloInferenceService inferenceService;

    public ApiController(YoloInferenceService inferenceService) {
        this.inferenceService = inferenceService;
    }

    @PostMapping("/predict")
    public ResponseEntity<?> predictApi(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "conf", defaultValue = "0.25") double conf,
            @RequestParam(value = "classes", defaultValue = "1") String classes
    ) {
        try {
            PredictionView view = inferenceService.predict(file, conf, classes);
            return ResponseEntity.ok(view);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
