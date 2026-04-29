package com.yolo.web.controller;

import com.yolo.web.service.YoloInferenceService;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class StaticFileConfig implements WebMvcConfigurer {

    private final YoloInferenceService inferenceService;

    public StaticFileConfig(YoloInferenceService inferenceService) {
        this.inferenceService = inferenceService;
    }

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        String location = inferenceService.getOutputRoot().toUri().toString();
        registry.addResourceHandler("/files/**").addResourceLocations(location);
    }
}
