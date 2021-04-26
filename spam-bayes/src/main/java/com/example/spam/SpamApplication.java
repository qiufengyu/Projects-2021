package com.example.spam;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.io.IOException;

@SpringBootApplication
public class SpamApplication {

	public static void main(String[] args) {
		// 启动网页应用
		SpringApplication.run(SpamApplication.class, args);
	}
}
