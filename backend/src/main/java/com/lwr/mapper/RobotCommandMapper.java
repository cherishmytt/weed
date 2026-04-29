package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.LaserCommand;
import org.apache.ibatis.annotations.Mapper;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 机器人指令队列Mapper
 */
@Mapper
public interface RobotCommandMapper extends BaseMapper<LaserCommand> {

    /**
     * 获取所有待执行指令（包括 PENDING 和 SENT 但未确认的）
     */
    default List<LaserCommand> findPendingCommands() {
        LambdaQueryWrapper<LaserCommand> wrapper = new LambdaQueryWrapper<>();
        wrapper.in(LaserCommand::getStatus, "PENDING", "SENT").orderByAsc(LaserCommand::getCreatedAt);
        return this.selectList(wrapper);
    }

    /**
     * 获取当天最大序号
     */
    default int countTodayCommands(LocalDateTime date) {
        LambdaQueryWrapper<LaserCommand> wrapper = new LambdaQueryWrapper<>();
        wrapper.likeRight(LaserCommand::getCommandId, "cmd-" + date.format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd")));
        return this.selectCount(wrapper).intValue();
    }
}
