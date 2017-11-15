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
import datetime as datetime


def getMW_MaxReturn(funds_input, riskfree):
    """
        根据马科维茨理论获得最大收益情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MaxReturn(nof, returns, nod, riskfree)
    return optr['x']


def getMW_MaxSharp(funds_input, riskfree):
    """
        根据马科维茨理论获得最大夏普情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MaxSharp(nof, returns, nod, riskfree)
    return optr['x']


def getMW_MinVariance(funds_input, riskfree):
    """
        根据马科维茨理论获得最小方差（风险）情况下的资产组合
    """
    funds = funds_input
    nod = len(funds_input)
    nof = len(funds_input.columns)
    returns = np.log(funds / funds.shift(1))
    optr = mpt.MK_MinVariance(nof, returns, nod, riskfree)
    return optr['x']


def get_zscombination_by_date(startdate, enddate, funds_net_df, riskfree):
    datelist = rl.dateRange(startdate, enddate)
    funds_net_df = funds_net_df.ix[startdate.replace("-", ""):enddate.replace("-", "")]
    eplison = 0.000000001
    modelname = "test"
    centroids, funds_with_labels, cluster_list = fs.load_model_return(funds_net_df, eplison, modelname)
    funds_list = fs.funds_select(funds_with_labels, cluster_list, method="max_mean_sharp")
    funds_ticker_list = list(funds_list.values())
    funds_ticker_list.sort()
    funds_input = funds_net_df[funds_ticker_list]
    funds_percent = getMW_MaxSharp(funds_input, riskfree)
    funds_log_return = np.log(funds_input / funds_input.shift(1))
    funds_weight_dic = {funds_ticker_list[w]: funds_percent[w] for w in range(len(funds_ticker_list))}
    opt_sta_list = mpt.statistics(funds_log_return, funds_percent, len(datelist), riskfree)
    return funds_weight_dic, opt_sta_list


def get_best_moneyfundticker(endday_str, days_before, funds_profit_df, method="maxmeanreturn"):
    datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
    startday_str = datelist_inside[0]
    funds_profit_df = funds_profit_df.ix[startday_str.replace("-", ""):startday_str.replace("-", "")]
    if method == "maxmeanreturn":
        funds_profit_mean_df = funds_profit_df.mean().T
        fund_ticker = funds_profit_mean_df.idxmax()
    return fund_ticker


def get_zscombination_for_users(user_detail_df,datelist_out, days_before, funds_profit_df, funds_net_df, riskfree):
    zs_combination_df = pd.DataFrame()
    moneyfund_ticker_for_net = get_best_moneyfundticker(datelist_out[0], days_before, funds_profit_df,
                                                        method="maxmeanreturn")
    time_cost = 0
    usercount = 0
    for index, row in user_detail_df.iterrows():
        usercount += 1
        userid = row["userid"]
        usermoneyamount = row["moneyamount"]
        userriskscore = row["risk_score"]
        userrisktype = row["risk_type"]
        start = time.clock()
        print("计算第" + str(usercount) + "/" + str(len(user_detail_df)) + "个用户.")
        if userrisktype == "保守型":
            change_dic = {}
            change_dic["userid"] = userid
            change_dic["date"] = "2017-07-01"
            change_dic["ticker"] = moneyfund_ticker_for_net
            change_dic["name"] = moneyfund_ticker_for_net
            change_dic["percent"] = 1.0
            zs_combination_df = zs_combination_df.append(change_dic, ignore_index=True)
        else:
            count = 0
            current_return = 0.0
            total_net_percent = float(userriskscore) / 100
            combination_df_inside = pd.DataFrame(columns=["userid", "date", "ticker", "name", "percent"])
            for endday_str in datelist_out:
                count += 1
                datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
                startday_str = datelist_inside[0]
                funds_weight_dic, opt_sta_list = get_zscombination_by_date(startday_str, endday_str, funds_net_df,
                                                                           riskfree)
                new_return = opt_sta_list[0]
                if combination_df_inside.empty:
                    for fund, percent in funds_weight_dic.items():
                        change_dic = {}
                        change_dic["userid"] = userid
                        change_dic["date"] = "2017-07-01"
                        change_dic["ticker"] = fund
                        change_dic["name"] = fund
                        change_dic["percent"] = float(percent) * total_net_percent
                        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                    change_dic = {}
                    change_dic["userid"] = userid
                    change_dic["date"] = "2017-07-01"
                    change_dic["ticker"] = moneyfund_ticker_for_net
                    change_dic["name"] = moneyfund_ticker_for_net
                    change_dic["percent"] = 1 - total_net_percent
                    combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                    current_return = new_return
                elif (np.exp(new_return) - np.exp(current_return)) > 0.015:
                    for fund, percent in funds_weight_dic.items():
                        change_dic = {}
                        change_dic["userid"] = userid
                        change_dic["date"] = endday_str
                        change_dic["ticker"] = fund
                        change_dic["name"] = fund
                        change_dic["percent"] = float(percent) * total_net_percent
                        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                    current_return = new_return
                    change_dic = {}
                    change_dic["userid"] = userid
                    change_dic["date"] = endday_str
                    change_dic["ticker"] = moneyfund_ticker_for_net
                    change_dic["name"] = moneyfund_ticker_for_net
                    change_dic["percent"] = 1 - total_net_percent
                    combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
            zs_combination_df = zs_combination_df.append(combination_df_inside, ignore_index=True)
        elapsed = (time.clock() - start)
        time_cost += elapsed
        print("Time used:", elapsed)
        print("Time Left Estimated:", (time_cost / (int(usercount))) * len(user_detail_df) - time_cost)
    zs_combination_df.to_excel(il.cwd + r"\result\\zs_combine_users.xls")
    print("File saved:", il.cwd + r"\result\\zs_combine_users.xls")


def get_best_combination_singleuser_singleday(userid, endday_str, days_before, funds_net_df, riskfree):
    datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
    startday_str = datelist_inside[0]
    funds_weight_dic, opt_sta_list = get_zscombination_by_date(startday_str, endday_str, funds_net_df, riskfree)
    new_return = opt_sta_list[0]
    combination_df_inside = pd.DataFrame(columns=["userid", "date", "ticker", "name", "percent"])
    for fund, percent in funds_weight_dic.items():
        change_dic = {}
        change_dic["userid"] = userid
        change_dic["date"] = endday_str
        change_dic["ticker"] = fund
        change_dic["name"] = fund
        change_dic["percent"] = percent
        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
    return combination_df_inside, new_return


def get_best_combination_netfund_singleuser(datelist_out, days_before, funds_net_df, userid):
    current_return = 0.0
    combination_df = pd.DataFrame(columns=["userid", "date", "ticker", "name", "percent"])
    time_cost = 0.0
    count = 0
    for endday_str in datelist_out:
        count += 1
        start = time.clock()
        print("计算第" + str(count) + "/" + str(len(datelist_out)) + "个日期.")
        combination_df_inside, new_return = get_best_combination_singleuser_singleday(userid, endday_str, days_before,
                                                                                      funds_net_df)
        if combination_df.empty:
            combination_df = combination_df_inside
            current_return = new_return
        elif (np.exp(new_return) - np.exp(current_return)) > 0.015:
            combination_df = combination_df.append(combination_df_inside, ignore_index=True)
            current_return = new_return
        elapsed = (time.clock() - start)
        time_cost += elapsed
        print("Time used:", elapsed)
        print("Time Left Estimated:", (time_cost / (int(count))) * len(datelist_out) - time_cost)
    return combination_df


if __name__ == '__main__':
    format = "%Y-%m-%d"
    days_before = 30
    userid = 1
    riskfree = 0.03
    combination_startdate = "2017-08-05"
    combination_enddate = "2017-10-29"
    datelist_out = rl.dateRange(combination_startdate, combination_enddate)
    funds_net_df = il.getZS_funds_net()
    funds_profit_df = il.getZS_funds_Profit()
    user_detail_df = il.getZS_users_complete()
    get_zscombination_for_users(user_detail_df,datelist_out, days_before, funds_profit_df, funds_net_df, riskfree)
