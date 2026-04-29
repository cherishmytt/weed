package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.LaserStatus;
import org.apache.ibatis.annotations.Mapper;

/**
 * 激光设备状态Mapper
 */
@Mapper
public interface LaserStatusMapper extends BaseMapper<LaserStatus> {

    /**
     * 获取当前激光状态（系统只有一台机器人，所以只有一条记录）
     */
    default LaserStatus getCurrent() {
        LambdaQueryWrapper<LaserStatus> wrapper = new LambdaQueryWrapper<>();
        wrapper.last("LIMIT 1");
        return this.selectOne(wrapper);
    }
}
