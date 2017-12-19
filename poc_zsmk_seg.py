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
            old_funds_weight_dic = {}
            for endday_str in datelist_out:
                count += 1
                # 回测的时候每天都检测太慢了，每20天检测一次
                if count % 30 == 0:
                    if not bool(old_funds_weight_dic):
                        pass
                    else:
                        current_return = zsmk.get_return_by_combination(old_funds_weight_dic, datelist_out[0], endday_str,
                                                                funds_net_df)
                    datelist_inside = rl.dateRange_daysbefore(endday_str, days_before)
                    startday_str = datelist_inside[0]
                    print(endday_str)
                    type_return_avg_pass_df = type_return_avg_df.ix[
                                              startday_str.replace("-", ""):endday_str.replace("-", "")]
                    log_return_df = np.log(type_return_avg_pass_df / type_return_avg_pass_df.shift(1))
                    type_weight_list, target_ret, target_var = zsmk.get_ZScom_by_var(type_return_avg_pass_df, riskfree,
                                                                                     type_num, minpercent)
                    type_fundticker_dic, selected_fund_list = fs.funds_select_for_type(funds_net_df, fund_type_list,
                                                                                       funds_type_df,
                                                                                       type_return_avg_pass_df,
                                                                                       funds_each_type=2,
                                                                                       selectby="corr")
                    funds_weight_dic, total_net_percent = zsmk.get_user_fund_weight_by_risk(type_weight_list,
                                                                                            fund_type_list,
                                                                                            type_fundticker_dic,
                                                                                            userriskscore)
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
                        old_funds_weight_dic = funds_weight_dic
                    elif (new_return - current_return) > change_return:
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
                        old_funds_weight_dic = funds_weight_dic
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
    get_ZScom_for_users(user_detail_df, datelist_out, days_before, funds_profit_df, funds_net_df_out, riskfree,
                        minpercent, change_return_differ_out, symbolstr)
