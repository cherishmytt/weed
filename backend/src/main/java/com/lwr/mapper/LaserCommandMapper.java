package com.lwr.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.LaserCommand;
import org.apache.ibatis.annotations.Mapper;

/**
 * 机器人指令队列Mapper
 */
@Mapper
public interface LaserCommandMapper extends BaseMapper<LaserCommand> {

}
