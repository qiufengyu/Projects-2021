from data_util import DataUtil
from lstm import SemiLSTM

if __name__ == '__main__':
    # 根据微博设定，截取文本最长长度为 140
    data_util = DataUtil()
    # 1. 建立 LSTM 网络
    lstm = SemiLSTM(lr=1e-4, epochs=20, batch_size=50)
    feature, label = data_util.load_data('data/train.txt', True)
    unlabeled_data, _ = data_util.load_data('data/unlabeled.txt', False)
    test_data, test_label = data_util.load_data('data/test.txt', True)
    lstm.build_lstm([32])
    lstm.train_semi(feature, label, test_data, test_label, unlabeled_data, round=5, saved_model='my-lstm')
    lstm.test(test_data, test_label)
    # 2. 根据训练好的模型，预测是否为不良言论
    saved_lstm = SemiLSTM(lr=1e-4, epochs=20, batch_size=50)
    text = '如何真正为自己的利益发声，而不被境外势力利用？那些势力并不关心你想要的民主，它们只想要中国弱下去'
    feature = data_util.extract_feature(text)
    result = saved_lstm.test_text(feature, saved_model='my-lstm')
    print(result)
    text = '菅义伟在开记者会，两次鞠躬、向国民道歉，“没能解除紧急事态，我非常抱歉”。记者问，“没能解除紧急事态的原因是什么？您自己觉得充分向国民说明了吗？”v光计划 。'
    feature = data_util.extract_feature(text)
    result = saved_lstm.test_text(feature, saved_model='my-lstm')
    print(result)

    # Round 1, # of training data: 7476, # of unlabeled data: 9295
    # 150/150 - 4s - loss: 0.4739 - binary_accuracy: 0.7825 - val_loss: 0.4815 - val_binary_accuracy: 0.7682
    # Round 2,  # of training data: 9334, # of unlabeled data: 7437
    # 187/187 - 5s - loss: 0.5096 - binary_accuracy: 0.7629 - val_loss: 0.4501 - val_binary_accuracy: 0.7944
    # Round 3, # of training data: 11192, # of unlabeled data: 5579
    # 224/224 - 6s - loss: 0.5247 - binary_accuracy: 0.7561 - val_loss: 0.4677 - val_binary_accuracy: 0.7913
    # Round 4, # of training data: 13050, # of unlabeled data: 3721
    # 261/261 - 6s - loss: 0.5357 - binary_accuracy: 0.7522 - val_loss: 0.4417 - val_binary_accuracy: 0.8156
    # Round 5, # of training data: 14908, # of unlabeled data: 1863
    # 299/299 - 9s - loss: 0.5418 - binary_accuracy: 0.7456 - val_loss: 0.4340 - val_binary_accuracy: 0.8284

    # 测试集准确率：61/61 [==============================] - 0s 7ms/step - loss: 0.4340 - binary_accuracy: 0.8284
    # Accuracy: 82.84%







