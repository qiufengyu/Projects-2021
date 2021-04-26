#!/usr/bin/python
# coding=utf-8
import datetime
import json
from flask import Flask, render_template, jsonify, request
import requests
import numpy as np
import pandas as pd
import tushare as ts
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.metrics import mean_absolute_error

app = Flask(__name__)
app.config.from_object('config')

# 去 https://waditu.com 申请一个账号，随便填点个人资料，把自己的 token 放在这里
ts.set_token('your token here')

# 这个函数表示，访问路径为 / 的，即默认的主页，就直接渲染 predict html，显示在浏览器中
@app.route('/')
def predict():
    return render_template('predict.html')

# 注册的一个 post 请求的处理函数，当 URL 是 /stock_predict，且请求方法是 HTTP POST，就由这个函数处理，并返回数据
# 对应 predict html 的
# let request_url = 'http://127.0.0.1:5000/stock_predict';
# $.post(request_url)
@app.route('/stock_predict', methods=['POST'])
def stock_predict():
    # 从请求中获取请求数据，stock code 对应 redict html 里面的 stock_code: stock_code
    code = request.form.get('stock_code')
    # 如果没有获取到，即用户没有输入，就使用默认值，000001.SZ
    if not code:
        code = '000001.SZ'
    # 从请求中获取请求数据，test_ratio 对应 predict html 里面的 test_ratio: test_ratio
    test_ratio = request.form.get('test_ratio')
    # 如果用户没有输入，就使用默认值 0.1
    # 下面的 look_back, train_epochs 也是一样的
    if not test_ratio:
        test_ratio = '0.1'
    look_back = request.form.get('look_back')
    if not look_back:
        look_back = '3'
    train_epochs = request.form.get('train_epochs')
    if not train_epochs:
        train_epochs = '10'
    """股票价格预测"""
    # 从tushare API 接口服务，获取 2016-01-01 开始的股票价格数据，ts_code是股票代码，start_date 可以自定义开始日期
    prices_df = ts.pro_bar(ts_code=code, start_date='2016-01-01')
    # 万一数据为空，或者股票代码实际上不存在，代表有错误，就直接返回数据，里面的 invalid 设置为1
    if prices_df.empty:
        return jsonify({'all_time': prices_df['trade_date'].values.tolist(),
                 'all_data': prices_df['close'].values.tolist(),
                 'add_predict': 0,
                 'test_count': 0,
                 'error': 0,
                 'invalid': 1}) # 这里 invalid = 1，对应 predict html 里面的 if (data.invalid === 1) 条件成立，会显示错误信息，直接返回就结束了
    # 如果获取到了数据，就可以基于历史数据进行股价预测
    # 重排序，因为原始数据是最近的股价在前面，我们需要的是最远的股价在前面
    prices_df = prices_df[::-1]
    # 在控制台打印股价数据
    print(prices_df.head())
    # 计算出测试数据的比例
    test_count = int(float(test_ratio) * prices_df.shape[0])
    # 划分训练数据与测试数据
    train = prices_df['close'].values.tolist()[:-test_count]
    test = prices_df['close'].values.tolist()[-test_count:]
    # 生成训练和测试数据集，会根据设定的 look_back 的数值生成，即今天的股票和前面几天的股票相关，具有某种函数关系
    def create_dataset(prehistory, dataset, look_back):
        dataX = []
        dataY = []

        history = prehistory
        for i in range(len(dataset)):
            x = history[i:(i + look_back)]
            y = dataset[i]
            dataX.append(x)
            dataY.append(y)
            history.append(y)
        dataX.append(history[-look_back:])
        dataY.append(0)
        return np.array(dataX), np.array(dataY)

    # 调用create_dataset 函数，构造数据集，look_back 是用户的输入，原本是 string 类型，需要转换成数字才能进行数学乘法运算
    look_back = int(look_back)
    trainX, trainY = create_dataset([train[0]] * look_back, train, look_back)
    testX, testY = create_dataset(train[-look_back:], test, look_back)

    # 根据参数构建lstm模型
    def create_lstm_model():
        model = Sequential()
        model.add(Dense(6, input_dim=look_back, activation='relu'))
        model.add(Dropout(0.01))
        model.add(Dense(4, input_dim=look_back, activation='relu'))
        model.add(Dense(1))
        model.compile(loss='mean_absolute_error', optimizer='adam')
        return model

    # 模型构建
    model = create_lstm_model()
    # 根据模型的设定，进行模型训练
    train_epochs = int(train_epochs)
    model.fit(trainX, trainY, epochs=train_epochs, batch_size=4, verbose=1)
    # 命令行会有一些训练过程的输出，一直到训练结束
    # predict，调用训练好的模型进行预测
    lstm_predictions = model.predict(testX)
    lstm_predictions = [float(r[0]) for r in lstm_predictions]
    # 计算一下迷行的平均绝对值误差
    lstm_error = mean_absolute_error(testY, lstm_predictions)
    print('Test MSE: %.3f' % lstm_error)
    # 对于预测数据，把前面的真实股价也加上去，使得数据可以对齐
    lstm_predictions = train + lstm_predictions
    # 对于横轴 x，加了一个下一个交易日的坐标点
    all_time_label = prices_df['trade_date'].values.tolist()
    all_time_label.append('Next Day')
    # 把历史数据和预测数据返回给前端，predict html 中的 js 代码获取到数据后，可以渲染出对应的图片
    return jsonify({'all_time': all_time_label, 
                    'all_data': prices_df['close'].values.tolist(),
                    'add_predict': lstm_predictions,
                    'test_count': test_count,
                    'error': lstm_error,
                    'invalid': 0})

# main 函数，启动网页后台服务应用
if __name__ == "__main__":
    app.run(host='127.0.0.1')
