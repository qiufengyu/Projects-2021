import numpy as np
import argparse
import random


def read_vectors(path, topn):
    lines_num, dim = 0, 0
    vectors = {}
    iw = []
    wi = {}
    with open(path, encoding='utf-8', errors='ignore') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                dim = int(line.rstrip().split()[1])
                continue
            lines_num += 1
            tokens = line.rstrip().split(' ')
            vectors[tokens[0]] = [float(x) for x in tokens[1:]]
            iw.append(tokens[0])
            if topn != 0 and lines_num >= topn:
                break
    for i, w in enumerate(iw):
        wi[w] = i
    return vectors, iw, wi, dim


def main():
    # 从 https://github.com/Embedding/Chinese-Word-Vectors 下载的中文词向量文件
    # 改成你对应的 sgns.renmin.word 文件路径
    vectors_path = "/Users/godfray/Downloads/sgns.renmin.word"
    # 选择其中的 10000 个高频词
    vectors, iw, wi, dim = read_vectors(vectors_path, 10000)
    with open('../embeddings.txt', 'w', encoding='utf-8') as fwe:
        with open('../vocabulary.txt', 'w', encoding='utf-8') as fwv:
            for w in vectors:
                v_string = [str(x) for x in vectors[w]]
                fwe.write(' '.join(v_string) + '\n')
                fwv.write(w + '\n')


if __name__ == '__main__':
    main()

