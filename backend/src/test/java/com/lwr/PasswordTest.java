package com.lwr;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordTest {
    public static void main(String[] args) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        
        // 测试密码加密
        String rawPassword = "123456";
        String encodedPassword = encoder.encode(rawPassword);
        System.out.println("明文密码: " + rawPassword);
        System.out.println("加密后的密码: " + encodedPassword);
        
        // 测试密码验证
        boolean matches = encoder.matches(rawPassword, encodedPassword);
        System.out.println("密码验证结果: " + matches);
        
        // 测试数据库中的密码
        String dbPassword = "$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6z2Xy";
        boolean dbMatches = encoder.matches(rawPassword, dbPassword);
        System.out.println("数据库密码验证结果: " + dbMatches);
    }
}