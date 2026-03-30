package com.upchr.mytool;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * ToolsPlus 应用启动类
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
@MapperScan("com.upchr.mytool.modules.*.mapper")
public class MytoolApplication {

    public static void main(String[] args) {
        SpringApplication.run(MytoolApplication.class, args);
    }
}
