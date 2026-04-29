package com.lwr.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Date;

/**
 * JWT黑名单实体
 */
@Data
@TableName("jwt_blacklist")
public class JwtBlacklist {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String token;
    private Date expiresAt;
    private LocalDateTime createdAt;
}
