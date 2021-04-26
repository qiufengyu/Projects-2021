package com.example.spam.offline;

import com.example.spam.jaba.Jaba;
import com.example.spam.jaba.enumeration.CutModeEnum;
import com.google.common.base.Throwables;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

public class Bayes {
    // 日志记录
    private Logger logger = LoggerFactory.getLogger(this.getClass());

    // 分隔符
    final String SEP = "#@#";

    // 分词器
    Jaba jaba;

    // 数据集信息
    int numInputs;
    int examples;

    // 模型的参数
    double spamProbability;
    double hamProbability;

    boolean modelValid;

    String hamFile = "data/ham.txt";
    String spamFile = "data/spam.txt";
    String stopwordsFile = "data/stopwords.txt";
    String vocabularyFile = "data/vocabulary.txt";

    Set<String> stopwords;
    Set<String> vocabulary;
    Map<String, Integer> wordCountMap;
    Map<String, Double> hamLogProbMap;
    Map<String, Double> spamLogProbMap;

    String modelFile;

    public Bayes(Integer numInputs, String modelFile) throws IOException {
        // 特征词数，取最频繁的 256 词
        // 太少太多效果都不好
        this.numInputs = numInputs;
        this.modelFile = modelFile;
        // 训练和测试的样本
        examples = 1793 + 2942;
        // 两种邮件的先验概率
        spamProbability = 0.0;
        hamProbability = 0.0;
        modelValid = false;
        // 停用词
        stopwords = new HashSet<>();
        loadStopwords();
        // 词语计数
        wordCountMap = new HashMap<>();
        // 词表
        vocabulary = new HashSet<>();
        // 概率统计，贝叶斯模型的重要参数
        hamLogProbMap = new HashMap<>();
        spamLogProbMap = new HashMap<>();
        jaba = Jaba.getInstance();
    }

    public void setNumInputs(int numInputs) throws IOException {
        this.numInputs = numInputs;
        generateVocabulary();
    }

    public void generateVocabulary() throws IOException {
        logger.info("读取数据...");
        loadStopwords();
        readRawFile(hamFile);
        readRawFile(spamFile);
        List<Map.Entry<String, Integer>> counter = wordCountMap.entrySet().stream()
                .sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
                .limit(numInputs)
                .collect(Collectors.toList());
        BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(vocabularyFile), StandardCharsets.UTF_8));
        for (Map.Entry<String, Integer> e: counter) {
            bw.write(e.getKey() + SEP + e.getValue() + "\n");
        }
        bw.flush();
        bw.close();
        logger.info("读取数据完毕！");
    }

    private void readRawFile(String file) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8));
        String line;
        while (true) {
            line = br.readLine();
            if (StringUtils.isNotBlank(line)) {
                String[] words = line.split("\\s");
                Arrays.stream(words).forEach(w -> {
                    if (!stopwords.contains(w) && StringUtils.isNotBlank(w) && !StringUtils.isNumeric(w)) {
                        wordCountMap.merge(w, 1, Integer::sum);
                    }
                });
            } else {
                break;
            }
        }
        br.close();
    }

    private void loadVocabulary() throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(vocabularyFile), StandardCharsets.UTF_8));
        String line;
        while (true) {
            line = br.readLine();
            if (StringUtils.isNotBlank(line)) {
                String[] tokens = line.split(SEP);
                vocabulary.add(StringUtils.strip(tokens[0]));
            }
            else {
                break;
            }
        }
    }

    // Bayes 模型训练
    public void train() throws IOException {
        // 先读取支持文件
        logger.info("读取特征文件 vocabulary.txt...");
        loadVocabulary();
        logger.info("读取文件，训练模型...");
        // 统计两类邮件中的词语特征
        int spamCount = countProb(spamFile, spamLogProbMap);
        int hamCount = countProb(hamFile, hamLogProbMap);
        spamProbability = (double) spamCount / (spamCount + hamCount);
        hamProbability = 1.0 - spamProbability;
        writeLogProb(modelFile);
        logger.info("模型训练完毕！");

    }

    private int countProb(String file, Map<String, Double> wordProbMap) {
        BufferedReader br = null;
        Map<String, Integer> m = new HashMap<>();
        int count = 0 ;
        try {
            br = new BufferedReader(new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8));
            String line;
            while (true) {
                line = br.readLine();
                if (StringUtils.isNotBlank(line)) {
                    ++count;
                    String[] tokens = line.split("\\s");
                    Arrays.stream(tokens).forEach(w -> {
                        if (StringUtils.isNotBlank(w) && !stopwords.contains(w)) {
                            m.merge(w, 1, Integer::sum);
                        }
                    });
                }
                else {
                    break;
                }
            }
            br.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        // 计算概率，保存在 wordProbMap 中
        // 为了防止溢出，+1 平滑，且直接保存为对数形式，防止后面概率相乘精度不够
        int totalCount = m.values().stream().reduce(0, Integer::sum) + vocabulary.size();
        vocabulary.forEach(w -> wordProbMap.put(w, Math.log(((double)(1 + m.getOrDefault(w, 0))) / totalCount)));
        return count;
    }

    private void writeLogProb(String bayesModelFile) {
        try {
            BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(bayesModelFile)));
            // 第一行写两种类型的概率
            bw.write("COUNT" + SEP + spamProbability + SEP + hamProbability + "\n");
            // 后面写的是
            for (String w: vocabulary) {
                bw.write(w + SEP + spamLogProbMap.get(w) + SEP + hamLogProbMap.get(w) + "\n");
            }
            bw.flush();
            bw.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // 从训练好的模型文件（bayes_model.txt）加载
    public void loadModel() throws IOException {
        logger.info("加载模型...");
        BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(modelFile), StandardCharsets.UTF_8));
        String line = br.readLine();
        String[] probs = line.split(SEP);
        spamProbability = Double.parseDouble(probs[1]);
        hamProbability = Double.parseDouble(probs[2]);
        while(true) {
            line = br.readLine();
            if (StringUtils.isBlank(line))
                break;
            String[] values = line.split(SEP);
            spamLogProbMap.put(values[0], Double.parseDouble(values[1]));
            hamLogProbMap.put(values[0], Double.parseDouble(values[2]));
        }
        modelValid = true;
        br.close();
        logger.info("模型加载完毕！");
    }

    public double[] testTrainingData() throws IOException {
        loadStopwords(); // stopwords set
        loadVocabulary(); // vocabulary set
        if (!modelValid) {
            loadModel();
        }
        logger.info("开始测试...");
        int correctSpam = 0;
        int correctHam = 0;
        int totalSpam = 0;
        int totalHam = 0;
        // 读取文件
        String line;
        BufferedReader br1 = new BufferedReader(new InputStreamReader(new FileInputStream("data/spam.txt"), StandardCharsets.UTF_8));
        while (true) {
            line = br1.readLine();
            if (StringUtils.isBlank(line)) {
                break;
            }
            ++totalSpam;
            double logProbSpam = Math.log(spamProbability);
            double logProbHam = Math.log(hamProbability);
            String[] parts = line.split("\\s");
            for (String w: parts) {
                if (StringUtils.isNotBlank(w) && vocabulary.contains(w)) {
                    logProbHam += hamLogProbMap.get(w);
                    logProbSpam += spamLogProbMap.get(w);
                }
            }
            if (logProbHam <= logProbSpam) {
                ++correctSpam;
            }
        }
        br1.close();
        BufferedReader br2 = new BufferedReader(new InputStreamReader(new FileInputStream("data/ham.txt"), StandardCharsets.UTF_8));
        while (true) {
            line = br2.readLine();
            if (StringUtils.isBlank(line)) {
                break;
            }
            ++totalHam;
            double logProbSpam = Math.log(spamProbability);
            double logProbHam = Math.log(hamProbability);
            String[] parts = line.split("\\s");
            for (String w: parts) {
                if (StringUtils.isNotBlank(w) && vocabulary.contains(w)) {
                    logProbHam += hamLogProbMap.get(w);
                    logProbSpam += spamLogProbMap.get(w);
                }
            }
            if (logProbHam >= logProbSpam) {
                ++correctHam;
            }
        }
        br2.close();
        int correct = correctSpam + correctHam;
        int totalExample = totalSpam + totalHam;
        double acc = (double) correct / totalExample * 100;
        logger.info(String.format("平均准确率：%.4f%%", acc));
        double accSpam = (double) correctSpam / totalSpam * 100;
        double accHam = (double) correctHam / totalHam * 100;
        logger.info(String.format("识别出垃圾邮件的准确率：%.4f%%", accSpam));
        logger.info(String.format("识别出正确邮件的准确率：%.4f%%", accHam));
        double[] values = new double[3];
        values[0] = acc;
        values[1] = accSpam;
        values[2] = accHam;
        return values;
    }


    public int testBayes(String text) throws IOException {
        // 如果没有训练过，就加载已经训练好的模型
        if (!modelValid) {
            loadModel();
        }
        List<String> l = jaba.cut(text, CutModeEnum.CUT);
        logger.info("分词结果： " + l.toString());
        double spamLogProb = Math.log(spamProbability), hamLogProb = Math.log(hamProbability);
        for (String s: l) {
            if (StringUtils.isNotBlank(s) && vocabulary.contains(s)) {
                spamLogProb += spamLogProbMap.get(s);
                hamLogProb += hamLogProbMap.get(s);
            }
        }
        return spamLogProb > hamLogProb ? 1 : 0;
    }

    public boolean isModelValid() {
        return modelValid;
    }

    private void loadStopwords() {
        try {
            BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(stopwordsFile), StandardCharsets.UTF_8));
            String line;
            while (true) {
                line = br.readLine();
                if (StringUtils.isNotBlank(line)) {
                    stopwords.add(StringUtils.strip(line));
                } else {
                    break;
                }
            }
        } catch (FileNotFoundException e) {
            logger.error(Throwables.getStackTraceAsString(e));
        } catch (IOException e) {
            logger.error(Throwables.getStackTraceAsString(e));
        }
    }
}
