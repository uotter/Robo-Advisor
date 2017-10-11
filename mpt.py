# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
from pylab import *
import iolib as il
import robolib as rl
import numpy as np
import pandas as pd


# 计算收益率,波动率(方差),sharp率


def statistics(returnpd_daily, weights, days):
    """
        returnpd_daily 各个组成产品的对数日收益率dataframe
        weights 各个产品的权重
        days 统计的总时间段天数
    """
    weights = np.array(weights)
    port_returns = np.sum(returnpd_daily.mean() * weights) * days
    port_variance = np.sqrt(np.dot(weights.T, np.dot(returnpd_daily.cov() * days, weights)))
    return np.array([port_returns, port_variance, port_returns / port_variance])


# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

funds_daily = il.getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
nod = len(funds_daily)
nof = 4
funds = rl.getNetWorthFromDailyProfit(funds_daily)
funds = funds.apply(lambda x: pd.to_numeric(x, errors='ignore'))
print(funds.ix[0].dtype)
print((funds / funds.shift(1)).ix[0].dtype)
returns = np.log(funds / funds.shift(1))

returns_year = returns.mean()*nod
print(returns_year)
print(returns)



