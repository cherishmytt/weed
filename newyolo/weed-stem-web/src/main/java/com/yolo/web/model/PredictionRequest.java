package com.yolo.web.model;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;

public class PredictionRequest {

    @NotNull
    @DecimalMin("0.01")
    @DecimalMax("1.0")
    private Double conf = 0.25;
    private String classes = "1";

    public Double getConf() {
        return conf;
    }

    public void setConf(Double conf) {
        this.conf = conf;
    }

    public String getClasses() {
        return classes;
    }

    public void setClasses(String classes) {
        this.classes = classes;
    }
}
