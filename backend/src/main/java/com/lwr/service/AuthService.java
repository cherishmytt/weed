package com.lwr.service;

import com.lwr.common.result.Result;
import com.lwr.entity.User;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户登录
     * @param username 用户名
     * @param password 密码
     * @return 登录结果，包含token和用户信息
     */
    Result<?> login(String username, String password);

    /**
     * 用户注册
     * @param username 用户名
     * @param email 邮箱
     * @param password 密码
     * @return 注册结果
     */
    Result<?> register(String username, String email, String password);

    /**
     * 用户登出
     * @param token 当前token
     * @return 登出结果
     */
    Result<Void> logout(String token);

    /**
     * 获取当前用户信息
     * @param token 当前token
     * @return 用户信息
     */
    Result<?> getCurrentUserInfo(String token);
}
