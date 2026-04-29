package com.yolo.web.model;

public class PredictionView {
    private InferenceResult result;
    private String outputImageUrl;
    private String originalImageUrl;
    private String runtimeLog;

    public InferenceResult getResult() {
        return result;
    }

    public void setResult(InferenceResult result) {
        this.result = result;
    }

    public String getOutputImageUrl() {
        return outputImageUrl;
    }

    public void setOutputImageUrl(String outputImageUrl) {
        this.outputImageUrl = outputImageUrl;
    }

    public String getOriginalImageUrl() {
        return originalImageUrl;
    }

    public void setOriginalImageUrl(String originalImageUrl) {
        this.originalImageUrl = originalImageUrl;
    }

    public String getRuntimeLog() {
        return runtimeLog;
    }

    public void setRuntimeLog(String runtimeLog) {
        this.runtimeLog = runtimeLog;
    }
}
