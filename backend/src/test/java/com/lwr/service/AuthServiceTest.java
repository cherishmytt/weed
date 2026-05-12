package com.lwr.service;

import com.lwr.common.result.Result;
import com.lwr.entity.User;
import com.lwr.mapper.UserMapper;
import com.lwr.common.util.JwtUtil;
import com.lwr.service.impl.AuthServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserMapper userMapper;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtUtil jwtUtil;

    @InjectMocks
    private AuthServiceImpl authService;

    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setUsername("admin");
        testUser.setPassword("encoded_password");
        testUser.setRole("admin");
        testUser.setStatus("active");
        testUser.setCreatedAt(LocalDateTime.now());
    }

    @Test
    void testLogin_Success() {
        when(userMapper.findByUsername("admin")).thenReturn(testUser);
        when(passwordEncoder.matches("password", "encoded_password")).thenReturn(true);
        when(jwtUtil.generateToken("admin")).thenReturn("test_jwt_token");

        Result<?> result = authService.login("admin", "password");

        assertNotNull(result);
        assertEquals(200, result.getCode());
        assertNotNull(result.getData());
    }

    @Test
    void testLogin_UserNotFound() {
        when(userMapper.findByUsername("nonexistent")).thenReturn(null);

        Result<?> result = authService.login("nonexistent", "password");

        assertNotNull(result);
        assertEquals(401, result.getCode());
    }

    @Test
    void testLogin_WrongPassword() {
        when(userMapper.findByUsername("admin")).thenReturn(testUser);
        when(passwordEncoder.matches("wrong_password", "encoded_password")).thenReturn(false);

        Result<?> result = authService.login("admin", "wrong_password");

        assertNotNull(result);
        assertEquals(401, result.getCode());
    }
}
