# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
from pylab import *
import iolib as il
import numpy as np
import scipy.optimize as sco
import pandas as pd
import funds_selection as fs


# 计算收益率,波动率(方差),sharp率
def statistics(returnpd_daily, weights, nod):
    """
        returnpd_daily 各个组成产品的对数日收益率dataframe
        weights 各个产品的权重
        days 统计的总时间段天数
    """
    weights = np.array(weights)
    port_returns = np.sum(returnpd_daily.mean() * weights) * nod
    port_variance = np.sqrt(np.dot(weights.T, np.dot(returnpd_daily.cov() * nod, weights)))
    return np.array([port_returns, port_variance, port_returns / port_variance])


# 计算收益率,波动率(方差),sharp率
def opt_statistics(weights):
    """
        returnpd_daily 各个组成产品的对数日收益率dataframe
        weights 各个产品的权重
        days 统计的总时间段天数
    """
    weights = np.array(weights)
    port_returns = np.sum(returns.mean() * weights) * nod
    port_variance = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * nod, weights)))
    return np.array([port_returns, port_variance, port_returns / port_variance])


# 最小化夏普指数的负值
def min_sharpe(weights, *args):
    return_df, days = args[0], args[1]
    return -statistics(return_df, weights, days)[2]


# 最小化收益的负值
def min_return(weights, *args):
    # return -opt_statistics(weights)[0] * 10000
    return_df, days = args[0], args[1]
    return -statistics(return_df, weights, days)[0]


# 定义一个函数对方差进行最小化
def min_variance(weights, *args):
    # return opt_statistics(weights)[1] * 100000
    return_df, days = args[0], args[1]
    return statistics(return_df, weights, days)[1]


def MKOptimization(goalfunc, nof, return_df, days):
    """
        根据最优化目标函数求解马科维茨最优解
        goalfunc 优化目标函数 min_sharpe：最大夏普率  min_variance：最小方差（波动率）
        nof 组合所使用的产品数量
    """
    additional_args = (return_df, days)
    # 约束是所有参数(权重)的总和为1。这可以用minimize函数的约定表达如下
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # 将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
    bnds = tuple((0, 1) for x in range(nof))
    opts = sco.minimize(goalfunc, nof * [1. / nof, ], args=additional_args, method='SLSQP', bounds=bnds,
                        constraints=cons)
    return opts


def MK_MaxReturn(nof, return_df, days):
    """
        暴露给外部调用
        goalfunc 优化目标函数 min_sharpe：最大夏普率  min_variance：最小方差（波动率）
        nof 组合所使用的产品数量
    """
    additional_args = (return_df, days)
    # 约束是所有参数(权重)的总和为1。这可以用minimize函数的约定表达如下
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # 将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
    bnds = tuple((0, 1) for x in range(nof))
    opts = sco.minimize(min_return, nof * [1. / nof, ], args=additional_args, method='SLSQP', bounds=bnds,
                        constraints=cons)
    return opts


def MK_MaxSharp(nof, return_df, days):
    """
        暴露给外部调用
        goalfunc 优化目标函数 min_sharpe：最大夏普率  min_variance：最小方差（波动率）
        nof 组合所使用的产品数量
    """
    additional_args = (return_df, days)
    # 约束是所有参数(权重)的总和为1。这可以用minimize函数的约定表达如下
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # 将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
    bnds = tuple((0, 1) for x in range(nof))
    opts = sco.minimize(min_sharpe, nof * [1. / nof, ], args=additional_args, method='SLSQP', bounds=bnds,
                        constraints=cons)
    return opts


def MK_MinVariance(nof, return_df, days):
    """
        暴露给外部调用
        goalfunc 优化目标函数 min_sharpe：最大夏普率  min_variance：最小方差（波动率）
        nof 组合所使用的产品数量
    """
    additional_args = (return_df, days)
    # 约束是所有参数(权重)的总和为1。这可以用minimize函数的约定表达如下
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # 将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
    bnds = tuple((0, 1) for x in range(nof))
    opts = sco.minimize(min_variance, nof * [1. / nof, ], args=additional_args, method='SLSQP', bounds=bnds,
                        constraints=cons)
    return opts


def MCPlot(nof, returns):
    """
        传入收益率矩阵和组合数量，使用蒙特卡洛模拟来绘制投资组合散点图
        nof 组合所使用的产品数量
        returns 日对数收益率dataframe
    """
    port_returns = []
    port_variance = []
    for p in range(4000):
        weights = np.random.random(nof)
        weights /= np.sum(weights)
        port_returns.append(np.sum(returns.mean() * 252 * weights))
        port_variance.append(np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights))))

    port_returns = np.array(port_returns)
    port_variance = np.array(port_variance)

    # 无风险利率设定为0.35%(活期利率）
    risk_free = 0.0035
    plt.figure(figsize=(8, 4))
    plt.scatter(port_variance, port_returns, c=(port_returns - risk_free) / port_variance, marker='o')
    plt.grid(True)
    plt.xlabel('excepted volatility', fontproperties="simhei")
    plt.ylabel('expected return')
    plt.colorbar(label='Sharpe ratio')
    plt.show()


def EFPlot(goalfunc, nod, nof, opts, optv, return_df, days):
    # 在不同目标收益率水平（target_returns）循环时，最小化的一个约束条件会变化。
    target_returns = np.linspace(opt_statistics(optv['x'])[0], opt_statistics(optv['x'])[0] + 0.1, 30)
    # target_returns = np.linspace(0, 0.2, 30)
    target_variance = []
    target_returns_compute = []

    # 将参数值(权重)限制在0和1之间。这些值以多个元组组成的一个元组形式提供给最小化函数
    bnds = tuple((0, 1) for x in range(nof))
    index = 0
    additional_args = (return_df, days)
    for tar in target_returns:
        index += 1
        print("计算第" + str(index) + "个有效前沿取样，共" + str(len(target_returns)) + "个有效前沿取样。")
        cons = (
            {'type': 'eq', 'fun': lambda x: opt_statistics(x)[0] - tar}, {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        res = sco.minimize(goalfunc, nof * [1. / nof, ], args=additional_args, method='SLSQP', bounds=bnds,
                           constraints=cons)
        target_variance.append(opt_statistics(res['x'])[1])
        target_returns_compute.append(opt_statistics(res['x'])[0])
        print(res['x'])
        print(opt_statistics(res['x']))

    target_variance = np.array(target_variance)
    port_returns = []
    port_variance = []
    minv_weights = []
    minv = 100
    # 蒙特卡洛采样
    for p in range(4000):
        weights = np.random.random(nof)
        weights /= np.sum(weights)
        port_returns.append(np.sum(returns.mean() * nod * weights))
        port_variance.append(np.sqrt(np.dot(weights.T, np.dot(returns.cov() * nod, weights))))
        variance = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * nod, weights)))
        if variance < minv:
            minv = variance
            minv_weights = weights
    port_returns = np.array(port_returns)
    port_variance = np.array(port_variance)
    plt.figure(figsize=(8, 4))
    # 圆圈：蒙特卡洛随机产生的组合分布
    plt.scatter(port_variance, port_returns, c=port_returns / port_variance, marker='o')
    # 叉号：有效前沿
    plt.scatter(target_variance, target_returns, c=target_returns / target_variance, marker='x')
    # 红星：标记最高sharpe组合
    plt.plot(opt_statistics(opts['x'])[1], opt_statistics(opts['x'])[0], 'r*', markersize=15.0)
    # 黄星：标记最小方差组合
    plt.plot(opt_statistics(optv['x'])[1], opt_statistics(optv['x'])[0], 'y*', markersize=15.0)
    plt.grid(True)
    plt.xlabel('expected volatility')
    plt.ylabel('expected return')
    plt.colorbar(label='Sharpe ratio')
    plt.show()


def getNetWorthFromDailyProfit(funds):
    '''
        从基金数据的日万份收益计算器净值，以方便后续计算对数收益率,由于使用了万份净值，初始净值按照一万分计算
        按复利计算
    '''
    returnpd = funds.copy(deep=True)
    returnpd.ix[0] = returnpd.ix[0] + 10000
    nod = len(funds)
    for i in range(1, nod):
        returnpd.ix[i] = returnpd.ix[i - 1] + funds.ix[i] * (returnpd.ix[i - 1] / 10000)
    return returnpd


# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

if __name__ == '__main__':
    funds_daily = il.getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
    # funds_daily = funds_daily[['depsoit', 'fund1', 'fund3']]
    # funds = getNetWorthFromDailyProfit(funds_daily)
    funds_net_df = il.getZS_funds_net()
    k = 5
    iteration = 100
    eplison = 0.000000001
    modelname = "test"
    centroids, funds_with_labels, cluster_list = fs.load_model_return(funds_net_df, eplison, modelname)
    funds_list = fs.funds_select(funds_with_labels, cluster_list, method="max_mean_sharp")
    funds = funds_net_df[list(funds_list.values())]
    # funds = pd.DataFrame(centroids, index=cluster_list)
    # funds = funds.T
    nod = len(funds)
    nof = len(funds.columns)
    print("Read and Preprocess Data Complete")
    returns = np.log(funds / funds.shift(1))
    # returns = funds
    # return_np = np.random.randn(nof,nod)
    # returns = pd.DataFrame(return_np.T)
    # # returns.to_csv(il.cwd+r"\result\temp.csv", sep=',', header=True, index=True)
    # # MCPlot(nof, returns)
    # # returns_year = returns.mean() * nod
    return_corr = returns.corr()
    print(return_corr)
    # # return_covs = returns.cov() * nod
    optvs = MKOptimization(min_variance, nof, returns, nod)
    optss = MKOptimization(min_sharpe, nof, returns, nod)
    print("Optimization Complete")
    print(optvs)
    print(optss)
    print('maxsharp' + str(opt_statistics(optss['x'])))
    print('minvariance' + str(opt_statistics(optvs['x'])))
    EFPlot(min_variance, nod, nof, optss, optvs, returns, nod)
