# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
from pylab import *
import iolib as il
import robolib as rl
import numpy as np
import scipy.optimize as sco

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

funds_daily = il.getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
nod = len(funds_daily)
noa = 4
funds = rl.getNetWorthFromDailyProfit(funds_daily)
returns = np.log(funds / funds.shift(1))


def statistics(weights):
    weights = np.array(weights)
    port_returns = np.sum(returns.mean() * weights) * nod
    port_variance = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * nod, weights)))
    return np.array([port_returns, port_variance, port_returns / port_variance])


# 最小化夏普指数的负值
def min_sharpe(weights):
    return -statistics(weights)[2]


# 约束是所有参数(权重)的总和为1。这可以用minimize函数的约定表达如下
cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

# 我们还将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
bnds = tuple((0, 1) for x in range(noa))

# 优化函数调用中忽略的唯一输入是起始参数列表(对权重的初始猜测)。我们简单的使用平均分布。
opts = sco.minimize(min_sharpe, noa * [1. / noa, ], method='SLSQP', bounds=bnds, constraints=cons)


# 但是我们定义一个函数对 方差进行最小化
def min_variance(weights):
    return statistics(weights)[1]


optv = sco.minimize(min_variance, noa * [1. / noa, ], method='SLSQP', bounds=bnds, constraints=cons)

# 在不同目标收益率水平（target_returns）循环时，最小化的一个约束条件会变化。
target_returns = np.linspace(statistics(optv['x'])[0], statistics(optv['x'])[0] + 0.01, 10)
target_variance = []
index = 0
for tar in target_returns:
    index += 1
    print("计算第" + str(index) + "个有效前沿取样，共" + str(len(target_returns)) + "个有效前沿取样。")
    cons = ({'type': 'eq', 'fun': lambda x: statistics(x)[0] - tar}, {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    res = sco.minimize(min_variance, noa * [1. / noa, ], method='SLSQP', bounds=bnds, constraints=cons)
    target_variance.append(res['fun'])
    print(res['x'])
    print(statistics(res['x']))

target_variance = np.array(target_variance)
port_returns = []
port_variance = []
for p in range(4000):
    weights = np.random.random(noa)
    weights /=np.sum(weights)
    port_returns.append(np.sum(returns.mean()*252*weights))
    port_variance.append(np.sqrt(np.dot(weights.T, np.dot(returns.cov()*252, weights))))

port_returns = np.array(port_returns)
port_variance = np.array(port_variance)
plt.figure(figsize=(8, 4))
# 圆圈：蒙特卡洛随机产生的组合分布
plt.scatter(port_variance, port_returns, c=port_returns / port_variance, marker='o')
# 叉号：有效前沿
plt.scatter(target_variance, target_returns, c=target_returns / target_variance, marker='x')
# 红星：标记最高sharpe组合
plt.plot(statistics(opts['x'])[1], statistics(opts['x'])[0], 'r*', markersize=15.0)
# 黄星：标记最小方差组合
plt.plot(statistics(optv['x'])[1], statistics(optv['x'])[0], 'y*', markersize=15.0)
plt.grid(True)
plt.xlabel('expected volatility')
plt.ylabel('expected return')
plt.colorbar(label='Sharpe ratio')
plt.show()
