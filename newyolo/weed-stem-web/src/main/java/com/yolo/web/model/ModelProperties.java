package com.yolo.web.model;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.model")
public class ModelProperties {

    private String pythonExecutable;
    private String scriptPath;
    private String weightPath;
    private String outputRoot;
    private String classes = "1";
    private int imgsz = 640;

    public String getPythonExecutable() {
        return pythonExecutable;
    }

    public void setPythonExecutable(String pythonExecutable) {
        this.pythonExecutable = pythonExecutable;
    }

    public String getScriptPath() {
        return scriptPath;
    }

    public void setScriptPath(String scriptPath) {
        this.scriptPath = scriptPath;
    }

    public String getWeightPath() {
        return weightPath;
    }

    public void setWeightPath(String weightPath) {
        this.weightPath = weightPath;
    }

    public String getOutputRoot() {
        return outputRoot;
    }

    public void setOutputRoot(String outputRoot) {
        this.outputRoot = outputRoot;
    }

    public String getClasses() {
        return classes;
    }

    public void setClasses(String classes) {
        this.classes = classes;
    }

    public int getImgsz() {
        return imgsz;
    }

    public void setImgsz(int imgsz) {
        this.imgsz = imgsz;
    }
}
