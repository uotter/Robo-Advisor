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


def get_ZScom_by_var(return_df, riskfree, typenum, minpercent):
    """
        计算给定的资产库被分成typenum-1份时各个份的资产权重，实际是计算不同风险下的最优投资组合
        :param return_df：资产库净值序列，dataframe
        :param riskfree: 无风险收益，float
        :param typenum: 总的用户风险类别，int
        :param minpercent:基金最小比重，float
        :return type_weight_list: 各个类别对应的权重列表，dic
        :return target_ret: 各个类别对应的对数收益率，list
        :return target_var: 各个类别对应的对数波动率，list
    """
    type_weight_list = []
    log_return_df = np.log(return_df / return_df.shift(1))
    nod = len(log_return_df)
    type_list = log_return_df.columns.tolist()
    nof = len(type_list)
    optsharp_free = mpt.MK_MaxSharp(nof, log_return_df, nod, riskfree, minpercent)
    optvar_free = mpt.MK_MinVariance(nof, log_return_df, nod, riskfree, minpercent)
    target_var = np.linspace(mpt.statistics(log_return_df, optvar_free['x'], nod, riskfree)[1],
                             mpt.statistics(log_return_df, optsharp_free['x'], nod, riskfree)[1], typenum - 1)
    target_ret = []
    target_var_new = []
    index = 0
    for var in target_var:
        index += 1
        res = mpt.MK_MaxSharp_with_Var(nof, log_return_df, nod, riskfree, var, minpercent)
        type_weight_list.append(res['x'])
        target_ret.append(mpt.statistics(log_return_df, res['x'], nod, riskfree)[0])
        target_var_new.append(mpt.statistics(log_return_df, res['x'], nod, riskfree)[1])
        # print(res['x'])
        # print(mpt.statistics(return_df, res['x'], nod, riskfree))
    # type_weight_list[index-1] = optsharp_free['x']
    return type_weight_list, target_ret, target_var_new


def get_user_fund_weight_by_risk(type_weight_list, fund_type_list, type_fundticker_dic, userriskscore):
    total_net_percent = 1.0
    com_index = 0
    if float(userriskscore) > 80:
        com_index = -1
    elif float(userriskscore) > 60:
        com_index = -2
        # total_net_percent = float(userriskscore) * 1.2 / 100.0
    elif float(userriskscore) > 40:
        com_index = -3
        # total_net_percent = float(userriskscore) * 1.2 / 100.0
    elif float(userriskscore) > 20:
        com_index = -4
        # total_net_percent = float(userriskscore) * 1.2 / 100.0
    type_weight = type_weight_list[com_index]
    funds_weight_dic = {}
    for i in range(len(fund_type_list)):
        type = fund_type_list[i]
        fund_weight_detail = type_weight[i]
        funds_list = type_fundticker_dic[type]
        funds_num = len(funds_list)
        fund_weight = fund_weight_detail / funds_num
        for fund in funds_list:
            funds_weight_dic[fund] = fund_weight
    return funds_weight_dic, total_net_percent


def get_user_fund_weight_by_bunds(bunds, return_df, riskfree, type_fundticker_dic, fund_type_list):
    total_net_percent = 1.0
    log_return_df = np.log(return_df / return_df.shift(1))
    nod = len(log_return_df)
    type_list = log_return_df.columns.tolist()
    nof = len(type_list)
    opts = mpt.MK_MaxSharp_with_bnds(nof, log_return_df, nod, riskfree, bunds)
    type_list = log_return_df.columns.tolist()
    funds_weight_dic = {}
    for i in range(len(fund_type_list)):
        type = fund_type_list[i]
        fund_weight_detail = opts['x'][i]
        funds_list = type_fundticker_dic[type]
        funds_num = len(funds_list)
        fund_weight = fund_weight_detail / funds_num
        for fund in funds_list:
            funds_weight_dic[fund] = fund_weight
    return funds_weight_dic, total_net_percent


def get_user_bnds(return_df, user_row, minpercent=0.1):
    log_return_df = np.log(return_df / return_df.shift(1))
    nod = len(log_return_df)
    type_list = log_return_df.columns.tolist()
    nof = len(type_list)
    userriskscore = user_row["risk_score"]
    userrisktype = user_row["risk_type"]
    riskscore_start = 20
    riskscore_end = 100
    log_return_df_des = log_return_df.describe()
    log_return_df_std = log_return_df_des.T.sort_values(by=["std"])["std"]
    type_sorted_std_index_dic = {}
    type_std_ratio = log_return_df_std / log_return_df_std.max()
    type_std_score = riskscore_start + type_std_ratio * (riskscore_end - riskscore_start)
    type_sorted_std_index_df = np.abs(float(userriskscore) - type_std_score)
    # for type in type_list:
    #     # type_std_index = (log_return_df_std.index.tolist()).index(type)
    #
    #     # type_std_score = riskscore_start + (float(type_std_index) / (len(type_list))) * (
    #     #         riskscore_end - riskscore_start)
    #     type_std_score = riskscore_start + type_std_ratio[type] * (riskscore_end - riskscore_start)
    #     std_risk_ratio = np.abs(float(userriskscore) - type_std_score)
    #     type_sorted_std_index_dic[type] = std_risk_ratio
    # type_sorted_std_index_df = pd.Series(type_sorted_std_index_dic)
    type_sorted_std_index_df = type_sorted_std_index_df.sort_values()
    divide_num = len(log_return_df_std)
    maxpercent = 1 - minpercent * (divide_num - 1)
    up_bound_array = np.linspace(minpercent, (1 - minpercent * (divide_num - 1)), divide_num)
    up_bound_list = up_bound_array.tolist()
    up_bound_list.reverse()
    bnds_list = []
    for type in type_list:
        # std_score_ratio_index = type_sorted_std_index_df.index.tolist().index(type)
        # type_maxpercent = up_bound_list[std_score_ratio_index]
        if type_sorted_std_index_df[type] == 0:
            type_maxpercent = maxpercent
        else:
            type_maxpercent = 1 - (
                    (1 - maxpercent) + (type_sorted_std_index_df[type] / (riskscore_end - riskscore_start)) * (
                    maxpercent - minpercent))
        bnds_list.append((minpercent, type_maxpercent))

    return tuple(bnds_list)


if __name__ == '__main__':
    format = "%Y-%m-%d"
    days_before = 30
    userid = 1
    riskfree = 0.03
    combination_startdate = "2017-08-01"
    combination_enddate = "2017-12-10"
    datelist_out = rl.dateRange(combination_startdate, combination_enddate)
    funds_net_df_out = il.getZS_funds_net(fill=False)
    funds_profit_df = il.getZS_funds_Profit()
    # user_detail_df = il.getZS_users_complete(os.getcwd() + r"\history_data\zs_user_test.csv")
    user_detail_df = il.getZS_users_complete()
    minpercent = 0.1
    poctype = "zs"
    company_file = "zsmk"
    time_cost = 0
    usercount = 0
    change_return_differ_out = 0.01
    date_count = 0
    symbolstr = "zsmk_var_diff"
    funds_type_df, fund_type_list = il.get_funds_type()
    funds_net_df_fill = funds_net_df_out.copy()
    funds_net_df_fill = funds_net_df_fill.fillna(method="pad")
    funds_net_df_fill = funds_net_df_fill.fillna(method="bfill")
    type_return_avg_df = fs.type_return_avg(funds_net_df_fill, fund_type_list, funds_type_df)
    for index, row in user_detail_df[23:24].iterrows():
        user_bunds = get_user_bnds(type_return_avg_df, row)
