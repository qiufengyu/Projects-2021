import os
from copy import copy
import shutil
import pathlib
import pickle
from time import time
from pylab import *

import numpy as np

from SpamWeb.settings import BASE_DIR
from spam.dt_data_process import get_all_files, vocabulary, load_vocab, get_index, make_feature, make_feature_for_test_email
from spam.dt_my import *
from spam.dt_view import create_plot


class DTMain:
  def __init__(self, train_file='/spam/dtdata/training.txt', vocab_file='/spam/dtdata/vocab.txt'):
    self.tree = {}
    self.train_file = BASE_DIR + train_file
    self.vocab_file = BASE_DIR + vocab_file
    self.tree_file = BASE_DIR + '/spam/tree.pickle'
    self.data, self.features = create_data(self.train_file, self.vocab_file)
    self.predict_labels = copy(self.features)

  def data_preparation(self):
    # 大约使用了 5000 条数据
    # 开始特征抽取等工作
    all_file_list = get_all_files('data')
    print("合计有效文件数：", len(all_file_list))
    spam_set = get_index('index')

    # 如果使用了全部的数据集，也可以指定哪些为训练、哪些为测试的
    # 如 using_file_list = all_file_list[0:5000] 表示使用前 5000 条数据
    using_file_list = all_file_list

    # 生成字典运行一次即可，避免重复劳动
    # 为了加快训练的速度，通常只取最频繁的 200 词
    vocabulary(using_file_list)

    vocab = load_vocab(self.vocab_file, top_n=200)
    # print(len(vocab))
    make_feature(using_file_list, vocab, spam_set, output=self.train_file)


  def train(self):
    np.random.shuffle(self.data)
    data_length = len(self.data)
    # 定义交叉验证比例
    rate = 0.8
    training_length = int(rate * data_length)
    training_set, test_set = self.data[0:training_length].astype(int), self.data[training_length:].astype(int)
    # 可以设置最大深度 max_depth，默认 8
    # 选择基于最大信息熵/最大信息增益/信息增益比等方法选择属性构建决策树
    # split_function 取值如下：
    # 1. choose_best_split_feature_by_ID3 -> 最大信息增益
    # 2. choose_best_split_feature_by_C45 -> 信息增益比
    print("开始构建决策树...")
    my_tree = create_tree(training_set, self.features, depth=0, max_depth=8, split_function=choose_best_split_feature_by_C45)
    print("决策树构建完毕！")
    # 把决策树保存在本地
    with open(self.tree_file, 'wb') as f_tree:
      pickle.dump(my_tree, f_tree, pickle.HIGHEST_PROTOCOL)

    # 加载决策树
    print("加载决策树")
    with open(self.tree_file, 'rb') as f_tree:
      new_tree = pickle.load(f_tree)
    self.tree = new_tree
    # 预测训练集
    predict_result = predict(test_set[:, :-1], new_tree, self.predict_labels)
    # 测试训练集准确率
    acc = accuracy(test_set, predict_result)
    print("决策树分类精确度: {:.4f}%".format(acc))

    p, r, f = prf(test_set, predict_result)
    print(f"准确率：{p:.4f}%，召回率：{r:.4f}%，F值：{f:.4f}%")
    return acc, p, r, f

  def test_one(self, text='专业诚信代开发票，联系QQ: 123456。本公司竭诚为您服务！'):
    print("加载决策树")
    with open(self.tree_file, 'rb') as f_tree:
      new_tree = pickle.load(f_tree)
    print("单个实例测试：")
    vocab = load_vocab(self.vocab_file)
    mail_feature = make_feature_for_test_email(text, word_dict=vocab)
    result = predict_one(mail_feature, new_tree, self.predict_labels)
    print('邮件正文：', text)
    if result > 0:
      print('垃圾邮件')
    else:
      print('正常邮件')
    return result > 0

  def plot_tree(self):
    # 绘制决策树
    # 下面的设置是为了图中能够正确显示中文
    # Windows 10 环境默认好像是 OK 的，macOS 需要设置一下
    # 参考：https://www.zhihu.com/question/25404709
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
    mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题
    create_plot(self.tree)


if __name__ == '__main__':
  # 数据准备，运行一次即可
  mydt = DTMain()
  # mydt.data_preparation()
  # 自己实现的决策树分类算法
  start = time.time()
  mydt.train()
  end = time.time()
  print("运行时间：", end-start, "秒，即", (end-start)/60.0, "分")
  mydt.test_one()
  print('='*80)
  # mydt.plot_tree()



