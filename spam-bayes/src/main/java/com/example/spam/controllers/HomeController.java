package com.example.spam.controllers;

import com.example.spam.offline.Bayes;
import com.example.spam.service.HomeService;
import com.google.common.base.Throwables;
import org.checkerframework.checker.units.qual.A;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.ModelAndView;

import java.io.File;
import java.io.IOException;


@Controller
public class HomeController {

    // 日志记录
    private Logger logger = LoggerFactory.getLogger(this.getClass());

    @Autowired
    private HomeService homeService;

    // 访问首页，显示 index.html 内容
    @RequestMapping(value = {"/", "/index"}, method = RequestMethod.GET)
    public ModelAndView index() {
        return new ModelAndView("index");
    }

    // 首页上点击提交，此处接受请求，返回数据
    @RequestMapping(value = {"/", "/index"}, method = RequestMethod.POST)
    public ModelAndView home(@RequestParam(name = "numInput") Integer numInput) {
        ModelAndView homeModelAndView = new ModelAndView("index");
        homeModelAndView.addObject("oldNumInput", numInput);
        homeModelAndView.addObject("title", "朴素贝叶斯分类结果");
        try {
            homeService.setFeatures(numInput);
            homeService.trainModel();
            double[] results = homeService.testTraining();
            homeModelAndView.addObject("averageAcc", String.format("平均准确率：%.4f%%", results[0]));
            homeModelAndView.addObject("spamAcc", String.format("识别出垃圾邮件的准确率：%.4f%%", results[1]));
            homeModelAndView.addObject("hamAcc", String.format("识别出正常邮件的准确率：%.4f%%", results[2]));
        }
        catch (IOException e) {
            logger.error(Throwables.getStackTraceAsString(e));
            homeModelAndView.addObject("errorMessage", e.getMessage());
        }
        return homeModelAndView;
    }
}
