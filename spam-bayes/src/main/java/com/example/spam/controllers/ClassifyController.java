package com.example.spam.controllers;

import com.example.spam.offline.Bayes;
import com.example.spam.service.ClassifyService;
import com.google.common.base.Throwables;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.ModelAndView;

import java.io.IOException;


@Controller
public class ClassifyController {

    // 日志记录
    private Logger logger = LoggerFactory.getLogger(this.getClass());

    @Autowired
    private ClassifyService classifyService;

    @RequestMapping(value = {"/classify"}, method = RequestMethod.GET)
    public ModelAndView classifyDefault() {
        ModelAndView homeModelAndView = new ModelAndView("classify");
        return homeModelAndView;
    }

    @RequestMapping(value = {"/classify"}, method = RequestMethod.POST)
    public ModelAndView classify(@RequestParam(name = "emailText") String emailText) {
        ModelAndView homeModelAndView = new ModelAndView("classify");
        homeModelAndView.addObject("holder", emailText);
        int bayesResult;
        try {
            bayesResult = classifyService.test(emailText);
            homeModelAndView.addObject("result", bayesResult);
        } catch (IOException e) {
            logger.error(Throwables.getStackTraceAsString(e));
            homeModelAndView.addObject("errorMessage", e.getMessage());
        }
        return homeModelAndView;
    }



}
