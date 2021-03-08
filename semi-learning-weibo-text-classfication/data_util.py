import random
import numpy as np

import tensorflow_hub as hub


class DataUtil:
    def __init__(self, lm_path='nnlm-zh-dim50', max_length=140):
        self.embed = hub.load(lm_path)
        self.max_length = max_length

    def load_data(self, file: str, with_label=True, sep='###'):
        feature = []
        label = []
        samples = 0
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    samples += 1
                    parts = line.split(sep)
                    label.append(int(parts[0]) if with_label else 0)
                    feature.append(self.get_embed(parts[1].strip()))
        label_array = np.expand_dims(label, axis=1)
        return np.array(feature), label_array

    def get_embed(self, text: str):
        char_array = [c for c in text[:self.max_length]]
        _embed = self.embed(char_array).numpy()
        # padding 到 140 长度
        diff = self.max_length - len(char_array)
        if diff > 0:
            _embed = np.pad(_embed, ((0, diff), (0, 0)))
        return _embed

    def extract_feature(self, text: str):
        feature = [self.get_embed(text)]
        return np.array(feature)


def extract_data(file: str, output_path: str, train_ratio=0.4, test_ratio=0.1, unlabeled_ratio=0.5):
    train_count, test_count, unlabeled_count = 0, 0, 0
    postive_count, negative_count = 0, 0
    with open(output_path + '/train.txt', 'w', encoding='utf-8') as f_train:
        with open(output_path + '/test.txt', 'w', encoding='utf-8') as f_test:
            with open(output_path + '/unlabeled.txt', 'w', encoding='utf-8') as f_unlabel:
                with open(file, 'r', encoding='utf-8') as fr:
                    for line in fr:
                        choice = random.choices([0, 1, 2], weights=[train_ratio, test_ratio, unlabeled_ratio], k=1)[0]
                        line = line.strip()
                        parts = line.split('\t')
                        label = '0' if parts[2] == '0' else '1'
                        if label == '0':
                            postive_count += 1
                        else:
                            negative_count += 1
                        formatted_line = label + '###' + parts[1] + '\n'
                        if choice == 0:
                            train_count += 1
                            f_train.write(formatted_line)
                        elif choice == 1:
                            test_count += 1
                            f_test.write(formatted_line)
                        else:
                            unlabeled_count += 1
                            f_unlabel.write(formatted_line)
    print('In all {} positive samples, {} negative samples'.format(postive_count, negative_count))
    print('Generated {} train samples, {} test samples, {} unlabeled samples'.format(train_count, test_count,
                                                                                     unlabeled_count))


if __name__ == '__main__':
    # 1. 数据重新格式化：从原始数据转换成 “标签###文本” 的形式
    # 这是一次性的方法，根据所给原数据格式的不同不一样，就不写成一个类里的通用方法了
    extract_data('raw_data/data.txt', 'data')
    # 2. 从格式化后的数据中，提取特征，得到训练集、测试集或用于半监督学习的未标记集
    data_util = DataUtil()
    feature, label = data_util.load_data('data/train.txt', True)
