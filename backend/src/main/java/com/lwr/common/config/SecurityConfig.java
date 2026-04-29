package com.lwr.common.config;

import com.lwr.common.util.JwtUtil;
import com.lwr.mapper.JwtBlacklistMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Date;

/**
 * Spring Security配置
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private final JwtUtil jwtUtil;
    private final JwtBlacklistMapper jwtBlacklistMapper;

    public SecurityConfig(JwtUtil jwtUtil, JwtBlacklistMapper jwtBlacklistMapper) {
        this.jwtUtil = jwtUtil;
        this.jwtBlacklistMapper = jwtBlacklistMapper;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/api/v1/auth/login",
                                "/api/v1/auth/register",
                                "/api/v1/detection/report",
                                "/api/v1/detection/yolo-predict",
                                "/files/**",
                                "/ws/**",
                                "/error",
                                "/favicon.ico"
                        ).permitAll()
                                .anyRequest().authenticated()
                )
                .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        // 允许multipart在认证filter之前被解析，解决Required part 'rawImage' not present错误
        http.setSharedObject(org.springframework.web.multipart.MultipartResolver.class,
                new org.springframework.web.multipart.support.StandardServletMultipartResolver());

        return http.build();
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter(jwtUtil, jwtBlacklistMapper);
    }

    /**
     * JWT认证过滤器
     */
    public static class JwtAuthenticationFilter extends OncePerRequestFilter {

        private final JwtUtil jwtUtil;
        private final JwtBlacklistMapper jwtBlacklistMapper;

        public JwtAuthenticationFilter(JwtUtil jwtUtil, JwtBlacklistMapper jwtBlacklistMapper) {
            this.jwtUtil = jwtUtil;
            this.jwtBlacklistMapper = jwtBlacklistMapper;
        }

        @Override
        protected void doFilterInternal(HttpServletRequest request,
                                        HttpServletResponse response,
                                        FilterChain filterChain)
                throws ServletException, IOException {

            String token = extractToken(request);

            if (token != null && jwtUtil.validateToken(token)) {
                // 检查是否在黑名单中
                if (!isBlacklisted(token)) {
                    Long userId = jwtUtil.getUserIdFromToken(token);
                    String username = jwtUtil.getUsernameFromToken(token);
                    // 创建认证对象并设置到上下文
                    Authentication authentication = new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(
                            username, null, java.util.Collections.emptyList()
                    );
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                }
            }

            filterChain.doFilter(request, response);
        }

        @Override
        protected boolean shouldNotFilter(HttpServletRequest request) {
            // 不对multipart请求做过滤，避免破坏multipart解析
            String contentType = request.getContentType();
            return contentType != null && contentType.toLowerCase().startsWith("multipart/");
        }

        private String extractToken(HttpServletRequest request) {
            String header = request.getHeader("Authorization");
            if (header != null && header.startsWith("Bearer ")) {
                return header.substring(7);
            }
            return null;
        }

        private boolean isBlacklisted(String token) {
            // 查询数据库中是否存在该token，且未过期
            Date now = new Date();
            return jwtBlacklistMapper.existsByTokenAndExpiresAtAfter(token, now);
        }
    }
}
