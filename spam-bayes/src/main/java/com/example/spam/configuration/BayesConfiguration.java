package com.example.spam.configuration;

import com.example.spam.offline.Bayes;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;

@Configuration
public class BayesConfiguration {

    @Value("${bayes.features:256}")
    Integer features;

    @Value("${bayes.modelFile:bayes_model.txt}")
    String modelFile;

    @Bean
    public Bayes bayes() throws IOException {
        return new Bayes(features, modelFile);
    }
}
