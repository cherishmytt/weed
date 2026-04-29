package com.lwr;

import com.lwr.model.ModelProperties;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@MapperScan("com.lwr.mapper")
@EnableConfigurationProperties(ModelProperties.class)
public class LaserWeedingRobotApplication {

    public static void main(String[] args) {
        SpringApplication.run(LaserWeedingRobotApplication.class, args);
    }
}
