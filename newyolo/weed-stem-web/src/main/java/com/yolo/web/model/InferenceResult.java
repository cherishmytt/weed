package com.yolo.web.model;

import java.util.ArrayList;
import java.util.List;

public class InferenceResult {

    private String image;
    private int width;
    private int height;
    private List<Detection> detections = new ArrayList<>();

    public String getImage() {
        return image;
    }

    public void setImage(String image) {
        this.image = image;
    }

    public int getWidth() {
        return width;
    }

    public void setWidth(int width) {
        this.width = width;
    }

    public int getHeight() {
        return height;
    }

    public void setHeight(int height) {
        this.height = height;
    }

    public List<Detection> getDetections() {
        return detections;
    }

    public void setDetections(List<Detection> detections) {
        this.detections = detections;
    }

    public static class Detection {
        private int classId;
        private String className;
        private double confidence;
        private BoundingBox bbox;
        private Point stem;

        public int getClassId() {
            return classId;
        }

        public void setClassId(int classId) {
            this.classId = classId;
        }

        public String getClassName() {
            return className;
        }

        public void setClassName(String className) {
            this.className = className;
        }

        public double getConfidence() {
            return confidence;
        }

        public void setConfidence(double confidence) {
            this.confidence = confidence;
        }

        public BoundingBox getBbox() {
            return bbox;
        }

        public void setBbox(BoundingBox bbox) {
            this.bbox = bbox;
        }

        public Point getStem() {
            return stem;
        }

        public void setStem(Point stem) {
            this.stem = stem;
        }
    }

    public static class BoundingBox {
        private double x1;
        private double y1;
        private double x2;
        private double y2;

        public double getX1() {
            return x1;
        }

        public void setX1(double x1) {
            this.x1 = x1;
        }

        public double getY1() {
            return y1;
        }

        public void setY1(double y1) {
            this.y1 = y1;
        }

        public double getX2() {
            return x2;
        }

        public void setX2(double x2) {
            this.x2 = x2;
        }

        public double getY2() {
            return y2;
        }

        public void setY2(double y2) {
            this.y2 = y2;
        }
    }

    public static class Point {
        private double x;
        private double y;

        public double getX() {
            return x;
        }

        public void setX(double x) {
            this.x = x;
        }

        public double getY() {
            return y;
        }

        public void setY(double y) {
            this.y = y;
        }
    }
}
