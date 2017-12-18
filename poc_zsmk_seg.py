# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import os as os
import numpy as np
import robolib as rl
from pylab import *
import mpt as mpt
import pandas as pd
import iolib as il
import funds_selection as fs
import time as time
import zsmk_util as zsmk
import datetime as datetime


def get_ZScom_by_var(return_df, riskfree, typenum, minpercent):
    type_weight_list = []
    log_return_df = np.log(return_df / return_df.shift(1))
    nod = len(log_return_df)
    type_list = log_return_df.columns.tolist()
    nof = len(type_list)
    optsharp_free = mpt.MK_MaxSharp(nof, log_return_df, nod, riskfree)
    optvar_free = mpt.MK_MinVariance(nof, log_return_df, nod, riskfree)
    target_var = np.linspace(mpt.statistics(log_return_df, optvar_free['x'], nod, riskfree)[1],
                             mpt.statistics(log_return_df, optsharp_free['x'], nod, riskfree)[1], typenum-1)
    target_ret = []
    index = 0
    for var in target_var:
        index += 1
        res = mpt.MK_MaxSharp_with_Var(nof, log_return_df, nod, riskfree, var, minpercent)
        type_weight_list.append(res['x'])
        target_ret.append(mpt.statistics(log_return_df, res['x'], nod, riskfree)[0])
        # print(res['x'])
        # print(mpt.statistics(return_df, res['x'], nod, riskfree))
    return type_weight_list, target_ret, target_var


def get_ZScom_for_users(user_detail_df, datelist_out, days_before, funds_profit_df, funds_net_df, riskfree,
                        minpercent, change_return, symbolstr):
    '''
        定期计算某一个用户在某一段时间内的最优组合，并根据计算情况输出产生组合配置的文件
    '''
    zs_combination_df = pd.DataFrame()
    moneyfund_ticker_for_net = zsmk.get_best_moneyfundticker(datelist_out[0], days_before, funds_profit_df,
                                                             method="maxmeanreturn")
    time_cost = 0
    usercount = 0
    funds_type_df, fund_type_list = il.get_funds_type()
    funds_net_df_fill = funds_net_df.copy()
    funds_net_df_fill = funds_net_df_fill.fillna(method="pad")
    funds_net_df_fill = funds_net_df_fill.fillna(method="bfill")
    type_return_avg_df = fs.type_return_avg(funds_net_df_fill, fund_type_list, funds_type_df)
    type_num = len(set(user_detail_df["risk_type"].values.tolist()))
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
            change_dic["name"] = \
                funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["name"].values.tolist()[0]
            change_dic["percent"] = 1.0
            change_dic["type"] = \
                funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["fund_type"].values.tolist()[0]
            change_dic["risk_type"] = userrisktype
            change_dic["risk_score"] = userriskscore
            zs_combination_df = zs_combination_df.append(change_dic, ignore_index=True)
        else:
            count = 0
            current_return = 0.0
            combination_df_inside = pd.DataFrame(columns=["userid", "date", "ticker", "name", "percent", "type"])
            for endday_str in datelist_out:
                count += 1
                # 回测的时候每天都检测太慢了，每20天检测一次
                if count % 30 == 0:
                    datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
                    startday_str = datelist_inside[0]
                    print(endday_str)
                    type_return_avg_pass_df = type_return_avg_df.ix[
                                              startday_str.replace("-", ""):endday_str.replace("-", "")]
                    log_return_df = np.log(type_return_avg_pass_df / type_return_avg_pass_df.shift(1))
                    type_weight_list, target_ret, target_var = get_ZScom_by_var(type_return_avg_pass_df, riskfree,
                                                                                type_num, minpercent)
                    type_fundticker_dic, selected_fund_list = fs.funds_select_for_type(funds_net_df, fund_type_list,
                                                                                       funds_type_df,
                                                                                       type_return_avg_pass_df,
                                                                                       funds_each_type=2,
                                                                                       selectby="corr")
                    total_net_percent = 1.0
                    com_index = 0
                    if float(userriskscore) > 80:
                        com_index = -1
                    elif float(userriskscore) > 60:
                        com_index = -2
                    elif float(userriskscore) > 40:
                        com_index = -3
                    elif float(userriskscore) > 20:
                        com_index = -4
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
                    new_return = zsmk.get_return_by_combination(funds_weight_dic, datelist_out[0], endday_str,
                                                                funds_net_df)
                    if combination_df_inside.empty:
                        for fund, percent in funds_weight_dic.items():
                            change_dic = {}
                            change_dic["userid"] = userid
                            change_dic["date"] = "2017-07-01"
                            change_dic["ticker"] = fund
                            change_dic["name"] = funds_type_df[funds_type_df["ticker"] == fund]["name"].values.tolist()[
                                0]
                            change_dic["percent"] = float(percent) * total_net_percent
                            change_dic["type"] = \
                                funds_type_df[funds_type_df["ticker"] == fund]["fund_type"].values.tolist()[0]
                            change_dic["risk_type"] = userrisktype
                            change_dic["risk_score"] = userriskscore
                            combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                        change_dic = {}
                        change_dic["userid"] = userid
                        change_dic["date"] = "2017-07-01"
                        change_dic["ticker"] = moneyfund_ticker_for_net
                        change_dic["name"] = \
                            funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["name"].values.tolist()[
                                0]
                        change_dic["percent"] = 1 - total_net_percent
                        change_dic["type"] = \
                            funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net][
                                "fund_type"].values.tolist()[
                                0]
                        change_dic["risk_type"] = userrisktype
                        change_dic["risk_score"] = userriskscore
                        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                        current_return = new_return
                    elif (np.exp(new_return) - np.exp(current_return)) > change_return:
                        for fund, percent in funds_weight_dic.items():
                            change_dic = {}
                            change_dic["userid"] = userid
                            change_dic["date"] = endday_str
                            change_dic["ticker"] = fund
                            change_dic["name"] = funds_type_df[funds_type_df["ticker"] == fund]["name"].values.tolist()[
                                0]
                            change_dic["type"] = \
                                funds_type_df[funds_type_df["ticker"] == fund]["fund_type"].values.tolist()[0]
                            change_dic["percent"] = float(percent) * total_net_percent
                            change_dic["risk_type"] = userrisktype
                            change_dic["risk_score"] = userriskscore
                            combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                        current_return = new_return
                        change_dic = {}
                        change_dic["userid"] = userid
                        change_dic["date"] = endday_str
                        change_dic["ticker"] = moneyfund_ticker_for_net
                        change_dic["name"] = \
                            funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["name"].values.tolist()[
                                0]
                        change_dic["type"] = \
                            funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net][
                                "fund_type"].values.tolist()[
                                0]
                        change_dic["percent"] = 1 - total_net_percent
                        change_dic["risk_type"] = userrisktype
                        change_dic["risk_score"] = userriskscore
                        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
            zs_combination_df = zs_combination_df.append(combination_df_inside, ignore_index=True)
        elapsed = (time.clock() - start)
        time_cost += elapsed
        print("Time used:", elapsed)
        print("Time Left Estimated:", (time_cost / (int(usercount))) * len(user_detail_df) - time_cost)
    zs_combination_df.to_excel(il.cwd + r"\result\\zs_combine_type_users_seg_" + symbolstr + ".xls")
    print("File saved:", il.cwd + r"\result\\zs_combine_type_users_seg_" + symbolstr + ".xls")


if __name__ == '__main__':
    format = "%Y-%m-%d"
    days_before = 30
    userid = 1
    riskfree = 0.03
    combination_startdate = "2017-08-01"
    combination_enddate = "2017-10-29"
    datelist_out = rl.dateRange(combination_startdate, combination_enddate)
    funds_net_df_out = il.getZS_funds_net(fill=False)
    funds_profit_df = il.getZS_funds_Profit()
    user_detail_df = il.getZS_users_complete(os.getcwd() + r"\history_data\zs_user_test.csv")
    # user_detail_df = il.getZS_users_complete()
    minpercent = 0.1
    poctype = "zs"
    company_file = "zsmk"
    time_cost = 0
    usercount = 0
    change_return_differ_out = 0.01
    date_count = 0
    symbolstr = "test"
    get_ZScom_for_users(user_detail_df, datelist_out, days_before, funds_profit_df, funds_net_df_out, riskfree,
                        minpercent, change_return_differ_out, symbolstr)
