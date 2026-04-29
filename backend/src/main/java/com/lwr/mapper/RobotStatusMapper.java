package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.RobotStatus;
import org.apache.ibatis.annotations.Mapper;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 机器人运行状态Mapper
 */
@Mapper
public interface RobotStatusMapper extends BaseMapper<RobotStatus> {

    /**
     * 获取最新一条状态记录
     */
    default RobotStatus findLatest() {
        LambdaQueryWrapper<RobotStatus> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(RobotStatus::getReportedAt).last("LIMIT 1");
        return this.selectOne(wrapper);
    }

    /**
     * 查询指定时间范围内的轨迹点
     */
    default List<RobotStatus> findTrajectoryBetween(LocalDateTime startTime, LocalDateTime endTime) {
        LambdaQueryWrapper<RobotStatus> wrapper = new LambdaQueryWrapper<>();
        wrapper.select(RobotStatus::getLongitude, RobotStatus::getLatitude, RobotStatus::getReportedAt)
              .between(RobotStatus::getReportedAt, startTime, endTime)
              .orderByAsc(RobotStatus::getReportedAt);
        return this.selectList(wrapper);
    }
}
