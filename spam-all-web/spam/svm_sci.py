import os

import joblib
from sklearn import metrics
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC, NuSVC, LinearSVC
from time import time

import pickle

from SpamWeb.settings import BASE_DIR
from spam.svm_data import text_process


class SVMSCI():
    def load_data(self):
        with open(BASE_DIR + "/spam/svmdata/ham.txt", "r", encoding="utf-8") as f:
            ham_list = f.readlines()
        with open(BASE_DIR + "/spam/svmdata/spam.txt", "r", encoding="utf-8") as f:
            spam_list = f.readlines()
        X = ham_list + spam_list
        y_ham = [-1] * len(ham_list)
        y_spam = [1] * len(spam_list)
        y = y_ham + y_spam
        return X, y


    def train(self):
        """
        通过 scikit-learn 库的 svm 工具进行分析
        :return:
        """
        corpus, y = self.load_data()
        # 只选择最常见的标志性 200 词（max_features）
        # 提取 tf-idf 特征
        vectorizer = TfidfVectorizer(corpus, max_features=200)
        X = vectorizer.fit_transform(corpus).toarray()
        # 数据切分为训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        svm = SVC(gamma="scale")
        svm.fit(X_test, y_test)
        joblib.dump(svm, os.path.join(BASE_DIR, "spam", "scisvm.pkl"))
        y_pred = svm.predict(X_test)
        acc = metrics.accuracy_score(y_test, y_pred) * 100.0
        print("Accuracy :{}".format(acc))
        cm = metrics.confusion_matrix(y_test, y_pred)
        ham_ham = cm[0][0]
        ham_spam = cm[0][1]
        spam_ham = cm[1][0]
        spam_spam = cm[1][1]
        precision = spam_spam / (ham_spam + spam_spam) * 100.0
        recall = spam_spam / (spam_spam + spam_ham) * 100.0
        f1 = 2.0 * precision * recall / (precision+recall)
        # 把这个基于 tf-idf 的 vectorizer （特征化工具）保存下来，方便后续使用
        # 先是二进制文件，提高存储效率
        pickle.dump(vectorizer, open(BASE_DIR + "/spam/vectorizer.pkl", "wb"))
        # 这个文件可以看到，在邮件分类中起到关键作用的词
        with open(BASE_DIR + "/spam/vectorizer.words", "w", encoding="utf-8") as f_vec:
            for w in vectorizer.vocabulary_:
                f_vec.write(w + "\n")
        return acc, precision, recall, f1


    def svm_test_one(self, mail):
        with open(BASE_DIR + "/spam/vectorizer.pkl", "rb") as f:
            vectorizer = pickle.load(f)
        model = joblib.load(BASE_DIR + "/spam/scisvm.pkl")
        mail_vector = vectorizer.transform([mail]).toarray()
        pred = model.predict(mail_vector)
        return pred == 1


if __name__ == '__main__':
    start = time()
    svm = SVMSCI()
    # 会生成 vectorizer.pkl
    # 帮助生成样本的特征
    print(svm.train())
    end = time()
    print("运行时间：", end - start, "秒，即", (end - start) / 60.0, "分")
    # 其他的内容是调用 Scikit-learn 的 svm 实现，但是效果不好
    # 所以只借助了它用来特征处理、数据分割的部分
    # 下面是进行单个测试的代码

    raw_mail = """
  贵公司负责人(经理/财务）您好： 
      我是深圳市华隆源实业有限公司的（广州、东莞等市有分公司）。
  我司实力雄厚，有着良好的社会关系。因进项较多现完成不了每月销
  售额度。每月有一部分增值税电脑发票、海关缴款书等（6%左右）和
  普通商品销售税发票电脑运输发票，广告发票，服务业发票等 (国税
  地税2%左右）优惠代开或合作，点数较低。还可以根据所做数量额度
  的大小来商讨优惠的点数,公司成立多年一直坚持以“诚信”为中心作
  为公司的核心思想、树立公司形象, 真正做到“彼此合作一次、必成
  永久朋友，本公司郑重承诺所用绝对是真票！
  　　
      如贵司在发票的真伪方面有任何疑虑或担心，可上网查证或我司
  直接与贵司去税务局抵扣核对。 

      此信息长期有效，如须进一步洽商: 
      详情请电：13926517268
      邮  箱：szhly1688@tom.com
      联系人：林振国


  顺祝商祺！ 

    """
    mail_list = text_process(raw_mail.split("\n"))
    mail = " ".join(mail_list)
    res = svm.svm_test_one(mail)
    if res > 0:
        print("垃圾邮件！")
    else:
        print("正常邮件！")


