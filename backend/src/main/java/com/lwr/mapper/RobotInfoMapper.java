package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.RobotInfo;
import org.apache.ibatis.annotations.Mapper;

/**
 * 机器人基本信息Mapper
 */
@Mapper
public interface RobotInfoMapper extends BaseMapper<RobotInfo> {

    /**
     * 获取当前机器人信息（系统只有一台）
     */
    default RobotInfo getCurrent() {
        LambdaQueryWrapper<RobotInfo> wrapper = new LambdaQueryWrapper<>();
        wrapper.last("LIMIT 1");
        return this.selectOne(wrapper);
    }

    /**
     * 更新机器人当前状态
     */
    default int updateCurrentStatus(Integer status) {
        LambdaQueryWrapper<RobotInfo> wrapper = new LambdaQueryWrapper<>();
        wrapper.last("LIMIT 1");
        RobotInfo current = this.selectOne(wrapper);
        if (current != null) {
            current.setCurrentStatus(status);
            return this.updateById(current);
        }
        return 0;
    }
}
