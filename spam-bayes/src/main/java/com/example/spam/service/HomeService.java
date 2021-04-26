package com.example.spam.service;

import com.example.spam.offline.Bayes;
import com.google.common.base.Throwables;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
public class HomeService {
    // 日志记录
    private Logger logger = LoggerFactory.getLogger(this.getClass());

    @Autowired
    private Bayes bayes;

    public void setFeatures(int features) throws IOException {
        bayes.setNumInputs(features);
        bayes.generateVocabulary();
    }

    public void trainModel() throws IOException {
        bayes.train();
    }

    public double[] testTraining() throws IOException {
        if (!bayes.isModelValid()) {
            bayes.loadModel();
        }
        return bayes.testTrainingData();
    }
}
