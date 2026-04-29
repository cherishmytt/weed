package com.lwr.test;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class DatabaseTest {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/laser_weeding?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=Asia/Shanghai";
        String username = "root";
        String password = "123456";

        try {
            // 显式加载MySQL驱动
            Class.forName("com.mysql.cj.jdbc.Driver");
            System.out.println("MySQL驱动加载成功！");
        } catch (ClassNotFoundException e) {
            System.out.println("MySQL驱动加载失败: " + e.getMessage());
            return;
        }

        try (Connection conn = DriverManager.getConnection(url, username, password)) {
            System.out.println("数据库连接成功！");

            // 检查user表的结构
            System.out.println("\n--- user表结构 ---");
            try (ResultSet rs = conn.getMetaData().getColumns(null, null, "user", null)) {
                while (rs.next()) {
                    System.out.println(rs.getString("COLUMN_NAME") + " " + rs.getString("TYPE_NAME") + " " + rs.getString("COLUMN_SIZE"));
                }
            }

            // 检查user表的现有数据
            System.out.println("\n--- user表现有数据 ---");
            try (PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM user");
                 ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    System.out.println("user_id: " + rs.getLong("user_id") + ", username: " + rs.getString("username") + ", password: " + rs.getString("password") + ", role: " + rs.getString("role"));
                }
            }

            // 尝试插入新用户
            System.out.println("\n--- 尝试插入新用户 ---");
            try (PreparedStatement pstmt = conn.prepareStatement("INSERT INTO user (username, password, role) VALUES (?, ?, ?)")) {
                pstmt.setString(1, "test_user");
                pstmt.setString(2, "123456");
                pstmt.setString(3, "USER");
                int rows = pstmt.executeUpdate();
                System.out.println("插入成功，影响行数: " + rows);
            } catch (SQLException e) {
                System.out.println("插入失败: " + e.getMessage());
            }

            // 再次检查user表的现有数据
            System.out.println("\n--- user表现有数据（插入后） ---");
            try (PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM user");
                 ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    System.out.println("user_id: " + rs.getLong("user_id") + ", username: " + rs.getString("username") + ", password: " + rs.getString("password") + ", role: " + rs.getString("role"));
                }
            }

        } catch (SQLException e) {
            System.out.println("数据库连接失败: " + e.getMessage());
        }
    }
}