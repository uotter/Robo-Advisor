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


def getMW_MaxReturn(funds_input):
    """
        根据马科维茨理论获得最大收益情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MaxReturn(nof, returns, nod)
    return optr['x']


def getMW_MaxSharp(funds_input):
    """
        根据马科维茨理论获得最大夏普情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MaxSharp(nof, returns, nod)
    return optr['x']


def getMW_MinVariance(funds_input):
    """
        根据马科维茨理论获得最小方差（风险）情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MinVariance(nof, returns, nod)
    return optr['x']


def get_zscombination_by_date(startdate, enddate, funds_net_df):
    datelist = rl.dateRange(startdate, enddate)
    funds_net_df = funds_net_df.ix[startdate.replace("-", ""):enddate.replace("-", "")]
    eplison = 0.000000001
    modelname = "test"
    centroids, funds_with_labels, cluster_list = fs.load_model_return(funds_net_df, eplison, modelname)
    funds_list = fs.funds_select(funds_with_labels, cluster_list, method="max_mean_sharp")
    funds_ticker_list = list(funds_list.values())
    funds_ticker_list.sort()
    funds_input = funds_net_df[funds_ticker_list]
    funds_percent = getMW_MaxSharp(funds_input)
    funds_log_return = np.log(funds_input / funds_input.shift(1))
    funds_weight_dic = {funds_ticker_list[w]: funds_percent[w] for w in range(len(funds_ticker_list))}
    opt_sta_list = mpt.statistics(funds_log_return, funds_percent, len(datelist))
    return funds_weight_dic, opt_sta_list


if __name__ == '__main__':
    format = "%Y-%m-%d"
    days = 30
    combination_startdate = "2017-08-05"
    combination_enddate = "2017-10-29"
    funds_net_df = il.getZS_funds_net()
    datelist_out = rl.dateRange(combination_startdate, combination_enddate)
    current_return = 0.0
    combination_df = pd.DataFrame(columns=["userid", "date", "ticker","name", "percent"])
    time_cost = 0.0
    count = 0
    for endday_str in datelist_out:
        count += 1
        datelist_inside = rl.dateRange_daysbefore(endday_str, days)
        startday_str = datelist_inside[0]
        funds_weight_dic, opt_sta_list = get_zscombination_by_date(startday_str, endday_str, funds_net_df)
        new_return = opt_sta_list[0]
        start = time.clock()
        print("计算第" + str(count) + "/" + str(len(datelist_out)) + "个日期.")
        if combination_df.empty:
            for fund, percent in funds_weight_dic.items():
                change_dic = {}
                change_dic["userid"] = 1
                change_dic["date"] = endday_str
                change_dic["ticker"] = fund
                change_dic["name"] = fund
                change_dic["percent"] = percent
                combination_df = combination_df.append(change_dic, ignore_index=True)
            current_return = new_return
        elif (np.exp(new_return) - np.exp(current_return)) > 0.015:
            for fund, percent in funds_weight_dic.items():
                change_dic = {}
                change_dic["userid"] = 1
                change_dic["date"] = endday_str
                change_dic["ticker"] = fund
                change_dic["name"] = fund
                change_dic["percent"] = percent
                combination_df = combination_df.append(change_dic, ignore_index=True)
            current_return = new_return
        elapsed = (time.clock() - start)
        time_cost += elapsed
        print("Time used:", elapsed)
        print("Time Left Estimated:", (time_cost / (int(count))) * len(datelist_out) - time_cost)
    combination_df.to_excel(il.cwd + r"\result\\zs_combine.xls")
    print("File saved:", il.cwd + r"\result\\zs_combine.xls")
