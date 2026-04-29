package com.lwr.service.impl;

import com.lwr.common.result.Result;
import com.lwr.common.result.ResultCode;
import com.lwr.common.util.JwtUtil;
import com.lwr.entity.JwtBlacklist;
import com.lwr.entity.User;
import com.lwr.mapper.JwtBlacklistMapper;
import com.lwr.mapper.UserMapper;
import com.lwr.service.AuthService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * 认证服务实现
 */
@Slf4j
@Service
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final JwtBlacklistMapper jwtBlacklistMapper;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder passwordEncoder;
    
    // 邮箱正则表达式
    private static final String EMAIL_REGEX = "^[a-zA-Z0-9_+&*-]+(?:\\.[a-zA-Z0-9_+&*-]+)*@(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,7}$";
    private static final Pattern EMAIL_PATTERN = Pattern.compile(EMAIL_REGEX);

    public AuthServiceImpl(UserMapper userMapper,
                           JwtBlacklistMapper jwtBlacklistMapper,
                           JwtUtil jwtUtil,
                           PasswordEncoder passwordEncoder) {
        this.userMapper = userMapper;
        this.jwtBlacklistMapper = jwtBlacklistMapper;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public Result<?> login(String username, String password) {
        // 查询用户
        log.info("收到登录请求，用户名: {}", username);
        User user = userMapper.findByUsername(username);
        if (user == null) {
            log.warn("登录失败，用户名不存在: {}", username);
            return Result.error(ResultCode.LOGIN_FAILED);
        }

        // 验证密码
        log.debug("前端传递的密码: {}", password);
        log.debug("数据库存储的密码: {}", user.getPassword());

        boolean passwordMatch;
        String storedPassword = user.getPassword();

        // 检查密码是否是BCrypt格式
        if (storedPassword.startsWith("$2a$") || storedPassword.startsWith("$2b$") || storedPassword.startsWith("$2y$")) {
            // 使用BCrypt验证
            passwordMatch = passwordEncoder.matches(password, storedPassword);
        } else {
            // 直接比较明文密码（兼容旧数据）
            passwordMatch = password.equals(storedPassword);
            log.warn("使用明文密码验证，安全性较低");
        }

        log.debug("密码验证结果: {}", passwordMatch);

        if (!passwordMatch) {
            log.warn("登录失败，密码错误: {}", username);
            return Result.error(ResultCode.LOGIN_FAILED);
        }

        // 生成token
        String token = jwtUtil.generateToken(user.getUserId(), user.getUsername());

        // 构造返回数据
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("userId", user.getUserId());
        data.put("username", user.getUsername());
        data.put("role", user.getRole());

        log.info("用户登录成功: {}", username);
        return Result.success("登录成功", data);
    }

    @Override
    public Result<?> register(String username, String email, String password) {
        log.info("收到注册请求，用户名: {}, 邮箱: {}", username, email);

        // 验证用户名长度
        if (username == null || username.length() < 3 || username.length() > 50) {
            log.warn("注册失败，用户名长度不符合要求: {}", username);
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "用户名长度应为3-50个字符");
        }

        // 验证邮箱格式
        if (email == null || email.trim().isEmpty() || !isValidEmail(email)) {
            log.warn("注册失败，邮箱格式不正确: {}", email);
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "请输入有效的邮箱地址");
        }

        // 验证密码长度
        if (password == null || password.length() < 6) {
            log.warn("注册失败，密码长度不足: {}", username);
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "密码长度至少为6个字符");
        }

        // 检查用户名是否已存在
        User existingUser = userMapper.findByUsername(username);
        if (existingUser != null) {
            log.warn("注册失败，用户名已存在: {}", username);
            return Result.error(ResultCode.USERNAME_EXISTS);
        }

        // 创建新用户
        User newUser = new User();
        newUser.setUsername(username);
        newUser.setEmail(email.trim());
        // 使用BCrypt加密密码
        newUser.setPassword(passwordEncoder.encode(password));
        newUser.setRole("USER"); // 默认角色为普通用户
        newUser.setCreatedAt(LocalDateTime.now());
        newUser.setUpdatedAt(LocalDateTime.now());

        // 保存用户
        userMapper.insert(newUser);
        log.info("用户注册成功: {}", username);

        // 返回成功信息
        Map<String, Object> data = new HashMap<>();
        data.put("userId", newUser.getUserId());
        data.put("username", newUser.getUsername());
        data.put("role", newUser.getRole());

        return Result.success("注册成功", data);
    }

    @Override
    public Result<Void> logout(String token) {
        if (token != null && jwtUtil.validateToken(token)) {
            // 将token加入黑名单
            Date expiration = jwtUtil.getExpirationDateFromToken(token);
            JwtBlacklist blacklist = new JwtBlacklist();
            blacklist.setToken(token);
            blacklist.setExpiresAt(expiration);
            jwtBlacklistMapper.insert(blacklist);
            log.info("用户登出成功，token已加入黑名单");
        }
        return Result.success("登出成功", null);
    }

    @Override
    public Result<?> getCurrentUserInfo(String token) {
        Long userId = jwtUtil.getUserIdFromToken(token);
        User user = userMapper.selectById(userId);
        if (user == null) {
            return Result.error(ResultCode.UNAUTHORIZED);
        }

        Map<String, Object> data = new HashMap<>();
        data.put("userId", user.getUserId());
        data.put("username", user.getUsername());
        data.put("role", user.getRole());

        return Result.success(data);
    }
    
    /**
     * 验证邮箱格式是否有效
     */
    private boolean isValidEmail(String email) {
        if (email == null || email.trim().isEmpty()) {
            return false;
        }
        return EMAIL_PATTERN.matcher(email.trim()).matches();
    }
}
