from pathlib import Path

import jieba
import numpy as np

from NewsSummaryClassification.settings import BASE_DIR


def load_vocabulary(vocabulary_file: Path):
    """
    :param vocabulary_file:
    :return: 返回 词-下标 和 下标-词 的两组对应关系
    """
    word2index = {}
    index2word = []
    count = 0
    with open(vocabulary_file, 'r', encoding='utf-8') as f:
        for word in f:
            word = word.strip()
            word2index[word] = count
            index2word.append(word)
            count += 1
    return word2index, index2word


def load_embeddings(embedding_file: Path, index2word):
    """
    :param embedding_file:
    :param index2word:
    :return: 返回 词-embedding 的对应关系
    """
    word2embedding = {}
    count = 0
    dim = -1
    with open(embedding_file, 'r') as f:
        for _v in f:
            word = index2word[count]
            v = [float(x) for x in _v.strip().split()]
            word2embedding[word] = v
            dim = len(v)
            count += 1
    return word2embedding, dim


def make_feature(word2embedding, dim, sentence):
    valid_count = 0
    sum_embedding = np.zeros(dim, dtype=np.float32)
    for w in jieba.lcut(sentence=sentence):
        if w in word2embedding:
            sum_embedding = sum_embedding + np.array(word2embedding[w])
            valid_count += 1
    if valid_count > 0:
        return sum_embedding / float(valid_count)
    else:
        return sum_embedding


if __name__ == '__main__':
    word2index, index2word = load_vocabulary(BASE_DIR + '/vocabulary.txt')
    word2embedding, dim = load_embeddings(BASE_DIR + '/embeddings.txt', index2word)
    feature = make_feature(word2embedding, dim, '风里夹着温柔 将浪漫的光影涂满人间 穿过四月的原野 跳动的绿色火焰与姗姗来迟的芬芳撞了个满怀 共赴一场春日的盛宴')
    print(feature)