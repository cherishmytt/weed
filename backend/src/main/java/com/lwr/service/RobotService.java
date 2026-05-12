package com.lwr.service;

import com.lwr.common.result.Result;
import com.lwr.entity.RobotStatus;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 机器人服务接口
 */
public interface RobotService {

    /**
     * 获取机器人基本信息
     */
    Result<?> getRobotInfo();

    /**
     * 上报机器人运行状态
     */
    Result<Void> reportStatus(RobotStatusReportRequest request);

    /**
     * 获取最新运行状态
     */
    Result<?> getLatestStatus();

    /**
     * 查询状态历史（支持多条件筛选）
     */
    Result<?> getStatusHistory(LocalDateTime startTime, LocalDateTime endTime, String keyword, Boolean laserOn,
                               Float maxBattery, Float minTemperature, Float minCpu, String sortBy, String sortOrder, int page, int size);

    /**
     * 导出状态历史（筛选结果）
     * @param ids 选中记录ID列表，若不为空则只导出指定ID的记录
     */
    Result<List<Map<String, Object>>> exportStatusHistory(LocalDateTime startTime, LocalDateTime endTime, String keyword, Boolean laserOn,
                                          Float maxBattery, Float minTemperature, Float minCpu, List<Long> ids, int page, int size);

    /**
     * 查询轨迹
     */
    Result<?> getTrajectory(LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 推送状态更新到WebSocket连接
     */
    void broadcastStatusUpdate(RobotStatus status);

    /**
     * 状态上报请求DTO
     */
    class RobotStatusReportRequest {
        private Float battery;
        private Float speed;
        private Float temperature;
        private Boolean laserOn;
        private Float cpuUsage;
        private Double longitude;
        private Double latitude;
        private Object imu;
        private String reportedAt;

        public Float getBattery() { return battery; }
        public void setBattery(Float battery) { this.battery = battery; }
        public Float getSpeed() { return speed; }
        public void setSpeed(Float speed) { this.speed = speed; }
        public Float getTemperature() { return temperature; }
        public void setTemperature(Float temperature) { this.temperature = temperature; }
        public Boolean getLaserOn() { return laserOn; }
        public void setLaserOn(Boolean laserOn) { this.laserOn = laserOn; }
        public Float getCpuUsage() { return cpuUsage; }
        public void setCpuUsage(Float cpuUsage) { this.cpuUsage = cpuUsage; }
        public Double getLongitude() { return longitude; }
        public void setLongitude(Double longitude) { this.longitude = longitude; }
        public Double getLatitude() { return latitude; }
        public void setLatitude(Double latitude) { this.latitude = latitude; }
        public Object getImu() { return imu; }
        public void setImu(Object imu) { this.imu = imu; }
        public String getReportedAt() { return reportedAt; }
        public void setReportedAt(String reportedAt) { this.reportedAt = reportedAt; }
    }

    class TrajectoryPoint {
        private Double lng;
        private Double lat;
        private String time;

        public TrajectoryPoint(Double lng, Double lat, String time) {
            this.lng = lng;
            this.lat = lat;
            this.time = time;
        }

        public Double getLng() { return lng; }
        public Double getLat() { return lat; }
        public String getTime() { return time; }
    }
}
