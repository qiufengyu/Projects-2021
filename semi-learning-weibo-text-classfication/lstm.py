import numpy as np
import tensorflow as tf


class SemiLSTM():
    def __init__(self, lr, epochs, batch_size):
        self.model = tf.keras.Sequential()
        self.learning_rate = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.saved_model = None

    def build_lstm(self, lstm_dims=None, dense_dim=32):
        """根据输入的配置，构建 LSTM 网络，
            Args:
              lstm_dims: 每一层的 LSTM units 数量
              dense_dim: 最后决策层的权重矩阵 units
        """
        if lstm_dims is None:
            lstm_dims = [64]
        if len(lstm_dims) == 1:
            self.model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(lstm_dims[0])))
        else:
            for dim in lstm_dims[:-1]:
                self.model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(dim, return_sequences=True)))
            self.model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(lstm_dims[-1])))
        self.model.add(tf.keras.layers.Dense(dense_dim, activation='relu'))
        self.model.add(tf.keras.layers.Dense(1))
        loss_object = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
        self.model.compile(optimizer=optimizer, loss=loss_object,
                           metrics=[tf.keras.metrics.BinaryAccuracy(threshold=0)])

    def train(self, train_data, train_label, test_data, test_label, saved_model='my_lstm'):
        """
        有监督学习的方法，由标注数据训练模型，并评估
        :param train_data:
        :param train_label:
        :param test_data:
        :param test_label:
        :param saved_model:
        :return:
        """
        self.model.fit(train_data, train_label, epochs=self.epochs, batch_size=self.batch_size, shuffle=True,
                       validation_data=(test_data, test_label))
        self.model.save(saved_model)

    def train_semi(self, train_data, train_label, test_data, test_label, unlabeled_data, round, saved_model='my_lstm'):
        _train_data = train_data
        _train_label = train_label
        _unlabeled_data = unlabeled_data
        pick = len(unlabeled_data) // round // 2
        if pick < 1:
            raise ValueError('Invalid combination of unlabeled data size and training rounds')
        else:
            print('Will pick {} positive & negative samples from unlabeled data in every round'.format(pick))
        for i in range(round):
            # 先训练
            print('\nRound {}, # of training data: {}, # of unlabeled data: {}'.format(i + 1, len(_train_data),
                                                                                       len(_unlabeled_data)))
            self.model.fit(_train_data, _train_label, batch_size=self.batch_size, epochs=20, verbose=2, shuffle=True,
                           validation_data=(test_data, test_label))
            # 在 unlabeled 数据集上，评估当前模型的效果
            predictions = self.model(_unlabeled_data)
            predictions_argsort = tf.argsort(predictions, axis=0, direction='ASCENDING', stable=False, name=None)
            # 选择置信度最高的几个正、反样本，加到训练集中去
            rank_scores = np.squeeze(predictions_argsort.numpy(), axis=1)
            total = rank_scores.shape[0]
            _train_data_append = []
            _train_label_append = []
            _unlabeled_data_append = []
            for idx in range(total):
                if rank_scores[idx] < pick:
                    _train_data_append.append(_unlabeled_data[idx])
                    _train_label_append.append(0)
                elif rank_scores[idx] >= total - pick:
                    _train_data_append.append(_unlabeled_data[idx])
                    _train_label_append.append(1)
                else:
                    _unlabeled_data_append.append(_unlabeled_data[idx])
            # update train data & unlabeled data
            _unlabeled_data = np.array(_unlabeled_data_append)
            _train_data = np.concatenate((_train_data, _train_data_append), axis=0)
            _train_label = np.concatenate((_train_label, np.expand_dims(_train_label_append, axis=1)), axis=0)
        self.saved_model = self.model
        print('Training finished, saving model')
        self.model.save(saved_model)

    def test(self, test_data, test_label):
        loss, acc = self.saved_model.evaluate(test_data, test_label, verbose=1)
        print('Accuracy: {:5.2f}%'.format(100 * acc))

    def test_text(self, feature, saved_model):
        if not self.saved_model:
            print('Loading saved model')
            if not saved_model:
                raise ValueError('Do not have a trained model, please train the model first')
            else:
                try:
                    self.saved_model = tf.keras.models.load_model(saved_model)
                except IOError as e:
                    print('Saved model file does not exist at: ' + saved_model)
                    raise e
        prediction = self.saved_model(feature)
        score = np.squeeze(prediction.numpy())
        if score > 0:
            return 1
        else:
            return 0
