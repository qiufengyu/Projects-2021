# 一些杂七杂八的代码，项目中不再使用
# 可能其他地方有需要，可以作为参考

import os
from pathlib import Path


def extract_labeled_data(path, output):
    p = Path(path)
    entertainment_path = p / 'entertainment'
    sports_path = p / 'sports'
    entertainment_raw_files = [f for f in os.listdir(entertainment_path) if f.endswith('.txt')]  # label 0
    sports_raw_files = [f for f in os.listdir(sports_path) if f.endswith('.txt')]  # label 1
    with open(output, 'w', encoding='utf-8') as fw:
        for f in entertainment_raw_files:
            with open(entertainment_path / f, 'r', encoding='utf-8') as lines:
                one_line = ''.join([x.strip() for x in lines])
                fw.write('0###' + one_line + '\n')
        for f in sports_raw_files:
            with open(sports_path / f, 'r', encoding='utf-8') as lines:
                one_line = ''.join([x.strip() for x in lines])
                fw.write('1###' + one_line + '\n')


def extract_unlabeled_data(path, output):
    p = Path(path)
    raw_files = [f for f in os.listdir(path) if f.endswith('.txt')]
    with open(output, 'w', encoding='utf-8') as fw:
        for f in raw_files:
            with open(p / f, 'r', encoding='utf-8') as lines:
                one_line = ''.join([x.strip() for x in lines])
                fw.write('_###' + one_line + '\n')
