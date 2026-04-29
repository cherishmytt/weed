package com.lwr.common.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.io.File;

/**
 * 文件存储配置 - 静态资源映射
 */
@Configuration
public class FileStorageConfig implements WebMvcConfigurer {

    @Value("${file.storage.base-path:./uploads}")
    private String basePath;

    @Value("${file.storage.url-prefix:/files/**}")
    private String urlPrefix;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 确保目录存在
        File baseDir = new File(basePath);
        if (!baseDir.exists()) {
            baseDir.mkdirs();
        }

        // 映射访问路径到本地目录
        registry.addResourceHandler(urlPrefix)
                .addResourceLocations("file:" + basePath + "/");
    }
}
