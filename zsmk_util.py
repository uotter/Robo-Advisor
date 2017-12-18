# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import robolib as rl
from pylab import *
import mpt as mpt
import pandas as pd
import iolib as il
import funds_selection as fs
import time as time
import poc_zs as zsmk
import datetime as datetime

def get_return_by_combination(funds_weight_dic_inside, start_date, end_date, funds_net_compute_return):
    """
        计算给定的组合从start_date到end_date时间内的收益率
        :param funds_weight_dic_inside：组合相对应的基金编号和对应比例的字典，dic
        :param start_date: 初始日期，格式为2017-01-01，str
        :param end_date: 结束日期，格式为2017-01-01，str
        :param funds_net_compute_return:基金净值数据，dataframe
        :return: 在该段时间内的收益率，float
    """
    start_value = 0
    end_value = 0
    daterange = rl.dateRange(start_date, end_date, step=1, format="%Y-%m-%d")
    for fund_ticker, fund_percent in funds_weight_dic_inside.items():
        fund_net_start = rl.getFundsNetBefore_byTickerDate_MartrixFundsDf(fund_ticker, start_date.replace("-", ""),
                                                                          funds_net_compute_return, "%Y%m%d")
        if fund_net_start == 0:
            fund_net_start = rl.getFundsNetNext_byTickerDate_MartrixFundsDf(fund_ticker, start_date.replace("-", ""),
                                                                            funds_net_compute_return,
                                                                            "%Y%m%d")
        fund_net_end = rl.getFundsNetBefore_byTickerDate_MartrixFundsDf(fund_ticker, end_date.replace("-", ""),
                                                                        funds_net_compute_return, "%Y%m%d")
        if fund_net_end == 0:
            fund_net_end = rl.getFundsNetNext_byTickerDate_MartrixFundsDf(fund_ticker, end_date.replace("-", ""),
                                                                          funds_net_compute_return,
                                                                          "%Y%m%d")
        start_value += fund_net_start * fund_percent
        end_value += fund_net_end * fund_percent
    return ((end_value - start_value) / start_value) / (len(daterange) / 365)


def get_best_moneyfundticker(endday_str, days_before, funds_profit_df, method="maxmeanreturn"):
    '''
        根据选择标准（如最大收益），给出最优的货币基金
    '''
    datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
    startday_str = datelist_inside[0]
    funds_profit_df = funds_profit_df.ix[startday_str.replace("-", ""):startday_str.replace("-", "")]
    if method == "maxmeanreturn":
        funds_profit_mean_df = funds_profit_df.mean().T
        fund_ticker = funds_profit_mean_df.idxmax()
    return fund_ticker