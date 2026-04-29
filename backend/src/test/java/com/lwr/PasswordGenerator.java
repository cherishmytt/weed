package com.lwr;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordGenerator {
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        
        // 生成密码
        String rawPassword = "123456";
        String encodedPassword = encoder.encode(rawPassword);
        
        System.out.println("明文密码: " + rawPassword);
        System.out.println("BCrypt 加密后的密码: " + encodedPassword);
        
        // 验证密码
        boolean matches = encoder.matches(rawPassword, encodedPassword);
        System.out.println("密码验证结果: " + matches);
    }
}