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

@app.route('/')
def predict():
    return render_template('predict.html')

@app.route('/stock_predict', methods=['POST'])
def stock_predict():
    code = request.form.get('stock_code')
    if not code:
        code = '000001.SZ'
    test_ratio = request.form.get('test_ratio')
    if not test_ratio:
        test_ratio = '0.1'
    look_back = request.form.get('look_back')
    if not look_back:
        look_back = '3'
    train_epochs = request.form.get('train_epochs')
    if not train_epochs:
        train_epochs = '10'
    """股票价格预测"""
    prices_df = ts.pro_bar(ts_code=code, start_date='2016-01-01')
    if prices_df.empty:
        return jsonify({'all_time': prices_df['trade_date'].values.tolist(),
                 'all_data': prices_df['close'].values.tolist(),
                 'add_predict': 0,
                 'test_count': 0,
                 'error': 0,
                 'invalid': 1})
    # 重排序
    prices_df = prices_df[::-1]
    print(prices_df.head())

    test_count = int(float(test_ratio) * prices_df.shape[0])

    train = prices_df['close'].values.tolist()[:-test_count]
    test = prices_df['close'].values.tolist()[-test_count:]

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
        return np.array(dataX), np.array(dataY)

    # 数据集构造
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

    model = create_lstm_model()

    train_epochs = int(train_epochs)
    model.fit(trainX, trainY, epochs=train_epochs, batch_size=4, verbose=1)

    # predict
    lstm_predictions = model.predict(testX)
    lstm_predictions = [float(r[0]) for r in lstm_predictions]
    lstm_error = mean_absolute_error(testY, lstm_predictions)
    print('Test MSE: %.3f' % lstm_error)
    lstm_predictions = train + lstm_predictions

    return jsonify({'all_time': prices_df['trade_date'].values.tolist(),
                    'all_data': prices_df['close'].values.tolist(),
                    'add_predict': lstm_predictions,
                    'test_count': test_count,
                    'error': lstm_error,
                    'invalid': 0})


if __name__ == "__main__":
    app.run(host='127.0.0.1')
