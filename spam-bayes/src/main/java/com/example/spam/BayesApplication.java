package com.example.spam;

import com.example.spam.offline.Bayes;

import java.io.IOException;

public class BayesApplication {
    public static void main(String[] args) {
        //  贝叶斯模型
        Bayes bayes = null;
        try {
            bayes = new Bayes(256, "bayes_model.txt");
            // 生成相关数据文件
            bayes.generateVocabulary();
            // 训练
            bayes.train();
            // 测试
            System.out.println(bayes.testBayes("首先感谢jieba分词原作者fxsjy，没有他的无私贡献，我们也不会结识到结巴 分词. 同时也感谢jieba分词java版本的实现团队huaban，他们的努力使得Java也能直接做出效果很棒的分词。\n" +
                    "不过由于huaban已经没有再对java版进行维护，所以我自己对项目进行了开发。除了结巴分词(java版)所保留的原项目针对搜索引擎分词的功能(cutforindex、cutforsearch)，我加入了tfidf的关键词提取功能，并且实现的效果和python的jieba版本的效果一模一样！"));
            bayes.testTrainingData();
        }
        catch (IOException e) {
            e.printStackTrace();
        }

    }
}
