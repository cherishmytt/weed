package com.lwr.mapper;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.lwr.entity.JwtBlacklist;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Date;

/**
 * JWT黑名单Mapper
 */
@Mapper
public interface JwtBlacklistMapper extends BaseMapper<JwtBlacklist> {

    /**
     * 检查token是否在黑名单中且未过期
     */
    default boolean existsByTokenAndExpiresAtAfter(@Param("token") String token, @Param("now") Date now) {
        LambdaQueryWrapper<JwtBlacklist> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(JwtBlacklist::getToken, token).gt(JwtBlacklist::getExpiresAt, now);
        return this.exists(wrapper);
    }
}
