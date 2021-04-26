import paddle
from paddle.nn import Linear
import paddle.nn.functional as F
import os
import random
import numpy as np
from NewsSummaryClassification.settings import BASE_DIR

BASE_DIR_STRING = str(BASE_DIR)

# 从其他模块中调用
from paddlemodel.feature import load_vocabulary, load_embeddings, make_feature

word2index, index2word = load_vocabulary(BASE_DIR_STRING + '/vocabulary.txt')
# 词向量特征、输入特征维数
word2embedding, DIM = load_embeddings(BASE_DIR_STRING + '/embeddings.txt', index2word)

# 一些常量、设定等
NUM_CATEGORIES = 6
category_map = {
    'SOCIAL': 0,
    'SPORTS': 1,
    'ENT': 2,
    'MIL': 3,
    'TECH': 4,
    'FIN': 5
}

category_map_inv = ['社会',
                    '体育',
                    '娱乐',
                    '军事',
                    '科技',
                    '财经']
# 每一批的数据大小
BATCH_SIZE = 100
# 网络结构、参数定义
LAYER1 = 100
LAYER2 = 50
# 训练迭代轮次
EPOCH_NUM = 30


class Network(paddle.nn.Layer):
    def __init__(self, ):
        super(Network, self).__init__()
        self.fc1 = paddle.nn.Linear(in_features=DIM, out_features=LAYER2)
        self.relu1 = paddle.nn.ReLU()
        self.fc2 = paddle.nn.Linear(in_features=LAYER2, out_features=NUM_CATEGORIES)
        self.softmax = paddle.nn.Softmax()

    def forward(self, inputs):
        outputs1 = self.fc1(inputs)
        outputs1 = self.relu1(outputs1)
        outputs2 = self.fc2(outputs1)
        output = self.softmax(outputs2)
        return output


def load_data(mode='train'):
    print('loading data...')
    features = []
    labels = []
    if mode == 'train':
        # 训练数据集
        for category in category_map:
            file_name = BASE_DIR_STRING + '/data/' + category + '.txt'
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        features.append(make_feature(word2embedding, DIM, line))
                        labels.append(category_map[category])
    elif mode == 'test':
        # 测试数据集
        for category in category_map:
            file_name = BASE_DIR_STRING + '/data_test/' + category + '.txt'
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        features.append(make_feature(word2embedding, DIM, line))
                        labels.append(category_map[category])
    else:
        raise NotImplementedError
    # 样本数
    num_of_samples = len(features)
    print(mode, '#Samples:', num_of_samples)
    assert num_of_samples == len(labels), 'length of features should be the same with labels'
    # 样本序号，后面根据序号读取
    index_list = list(range(num_of_samples))

    # 数据生成器
    def data_generator():
        if mode == 'train':
            # 训练模式下打乱顺序
            random.shuffle(index_list)
        feature_list = []
        label_list = []
        for i in index_list:
            feature = np.array(features[i]).astype(np.float32)
            label = np.array(labels[i]).astype('int64')
            feature_list.append(feature)
            label_list.append(label)
            if len(feature_list) == BATCH_SIZE:
                yield np.array(feature_list), np.array(label_list)
                feature_list = []
                label_list = []
        # 还有一些其他数据剩余的
        if len(feature_list) > 0:
            yield np.array(feature_list), np.array(label_list)

    return data_generator


def train(model):
    model = Network()
    model.train()
    train_loader = load_data()
    test_loader = load_data('test')
    optimizer = paddle.optimizer.Adam(learning_rate=5e-3, parameters=model.parameters())
    for epoch in range(EPOCH_NUM):
        for batch_id, data in enumerate(train_loader()):
            # 准备数据
            features, labels = data
            features = paddle.to_tensor(features)
            labels = paddle.to_tensor(labels, stop_gradient=True)
            predicts = model(features)
            ce_loss = F.cross_entropy(predicts, labels)
            avg_loss = paddle.mean(ce_loss)
            # 每 20 批次输出一次损失
            if batch_id % 20 == 0:
                loss_val = avg_loss.numpy()[0]
                print('epoch: {}, batch: {}, loss: {}'.format(epoch, batch_id, loss_val))
            # 后向传播，更新参数的过程
            avg_loss.backward()
            optimizer.step()
            optimizer.clear_grad()
        # 在测试集上验证模型的效果
        test_samples = 0
        correct = 0
        for batch_id, data in enumerate(test_loader()):
            features, labels = data
            features = paddle.to_tensor(features)
            labels = paddle.to_tensor(labels, stop_gradient=True)
            predicts = model(features)
            test_samples += len(labels)
            arg_max_predicts = paddle.argmax(predicts, axis=-1)
            correct_tensor = paddle.sum(paddle.cast(paddle.equal(labels, arg_max_predicts), dtype=np.int64))
            correct_array = correct_tensor.numpy()
            correct += correct_array[0]
        acc = correct / test_samples
        print('epoch: {}, test cases: {}, correct: {}, accuracy: {}'.format(epoch, test_samples, correct, acc))

    # 保存模型参数和优化器的参数
    paddle.save(model.state_dict(), BASE_DIR_STRING + '/model.pdparams')
    paddle.save(optimizer.state_dict(), BASE_DIR_STRING + '/model.pdopt')
    print(optimizer.state_dict().keys())


def predict(model, param_path, sentence):
    model.train()
    params_dict = paddle.load(param_path + '.pdparams')
    model.set_state_dict(params_dict)
    # 构建一个 1 x DIM 的特征输入
    feature = np.array([make_feature(word2embedding, DIM, sentence)]).astype(np.float32)
    feature_tensor = paddle.to_tensor(feature)
    predict = model(feature_tensor)
    arg_max_predict = paddle.argmax(predict, axis=-1)
    predict_category = arg_max_predict.numpy()[0]
    return category_map_inv[predict_category]


if __name__ == '__main__':
    model = Network()
    train(model)
    res = predict(model, BASE_DIR_STRING + '/model', '每一个5年我军定型的装备、研制的装备、铺开的装备 是人民空军压力最大的那一年——在经过5年的战备准备后 美国人自己也不知道')
    print(res)