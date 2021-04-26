package com.example.spam.service;

import com.example.spam.offline.Bayes;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
public class ClassifyService {
    // 日志记录
    private Logger logger = LoggerFactory.getLogger(this.getClass());

    @Autowired
    private Bayes bayes;


    public int test(String emailText) throws IOException {
        return bayes.testBayes(emailText);
    }
}
