package com.yolo.web.controller;

import com.yolo.web.model.PredictionRequest;
import com.yolo.web.model.PredictionView;
import com.yolo.web.service.YoloInferenceService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

@Controller
@RequestMapping("/")
public class HomeController {

    private final YoloInferenceService inferenceService;

    public HomeController(YoloInferenceService inferenceService) {
        this.inferenceService = inferenceService;
    }

    @GetMapping
    public String index(Model model) {
        PredictionRequest request = new PredictionRequest();
        request.setClasses("1");
        model.addAttribute("request", request);
        return "index";
    }

    @PostMapping("predict")
    public String predict(
            @RequestParam("file") MultipartFile file,
            @Valid @ModelAttribute("request") PredictionRequest request,
            BindingResult bindingResult,
            Model model
    ) {
        if (bindingResult.hasErrors()) {
            model.addAttribute("error", "置信度范围应在 0.01 ~ 1.0。");
            return "index";
        }

        try {
            PredictionView result = inferenceService.predict(file, request.getConf(), request.getClasses());
            model.addAttribute("prediction", result);
            return "index";
        } catch (Exception e) {
            model.addAttribute("error", e.getMessage());
            return "index";
        }
    }
}
