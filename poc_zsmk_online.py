# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import os as os
import numpy as np
import robolib as rl
from pylab import *
import pandas as pd
import iolib as il
import time as time
import zsmk_util as zsmk
import funds_selection as fs
import mpt as mpt


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


def get_ZScom_online(user_detail_df, company_combination, current_date, daysbefore, funds_net_inside,
                     funds_profit_inside, riskfree, minpercent, change_return_differ):
    """
        增量在线的方式生成组合策略
        :param user_detail_df：给定的用户列表，dataframe
        :param company_combination:当前的基金组合列表，dataframe
        :param current_date:当前日期，格式为2017-01-01，str
        :param daysbefore:以当前日期之前多少天的历史数据作为计算依据
        :param funds_net_inside:基金净值数据，*****此处的fund_net需要是原始未进行缺失值处理的dataframe*****，dataframe
        :param funds_profit_inside:货币型基金日万份收益数据，dataframe
        :param riskfree:无风险利率，float
        :param minpercent: 某一个基金大类的所占比例的下限约束，float
        :param var_goal:预期波动率，预期波动率为0时，表示没有约束，float
        :return: None 但是会输出生成的文件
    """
    datelist = rl.dateRange_daysbefore(current_date, daysbefore, 1)
    end_date = current_date
    start_date = datelist[0]
    zs_combination_df = pd.DataFrame()
    moneyfund_ticker_for_net = zsmk.get_best_moneyfundticker(start_date, daysbefore, funds_profit_inside,
                                                             method="maxmeanreturn")

    funds_type_df, fund_type_list = il.get_funds_type()
    funds_net_df_fill = funds_net_inside.copy()
    funds_net_df_fill = funds_net_df_fill.fillna(method="pad")
    funds_net_df_fill = funds_net_df_fill.fillna(method="bfill")
    type_return_avg_df = fs.type_return_avg(funds_net_df_fill, fund_type_list, funds_type_df)
    combination_change_flag = False
    type_num = len(set(user_detail_df["risk_type"].values.tolist()))
    for index, row in user_detail_df.iterrows():
        userid = row["userid"]
        usermoneyamount = row["moneyamount"]
        userriskscore = row["risk_score"]
        userrisktype = row["risk_type"]
        user_combination = company_combination[company_combination["userid"] == userid]
        if user_combination.empty:
            continue
        else:
            user_combination_cp = user_combination.copy()
            if "type" in user_combination.columns.tolist():
                pass
            else:
                user_combination_cp.insert(len(user_combination.columns), "type", 1)
                for index, row in user_combination.iterrows():
                    fund_type = funds_type_df[funds_type_df["ticker"] == row["ticker"]]["fund_type"].values.tolist()[0]
                    fund_name = funds_type_df[funds_type_df["ticker"] == row["ticker"]]["name"].values.tolist()[0]
                    user_combination_cp.loc[index, "name"] = fund_name
                    user_combination_cp.loc[index, "type"] = fund_type
            zs_combination_df = zs_combination_df.append(user_combination_cp)

            if userrisktype == "保守型":
                pass
            else:
                # 找到用户当前的组合配置
                user_combination_sorted = user_combination.sort_values(by="date")
                last_date_in_user_combination_sorted = user_combination_sorted.iloc[-1]["date"]
                user_combination_last_date = user_combination[
                    user_combination["date"] == last_date_in_user_combination_sorted]
                funds_weight_dic_old = {}
                for index, row in user_combination_last_date.iterrows():
                    fund_ticker = row["ticker"]
                    fund_percent = float(row["percent"])
                    if fund_ticker in funds_net_df_fill.columns.tolist():
                        funds_weight_dic_old[fund_ticker] = fund_percent
                original_return = get_return_by_combination(funds_weight_dic_old, start_date, end_date,
                                                            funds_net_inside)
                type_return_avg_pass_df = type_return_avg_df.ix[
                                          start_date.replace("-", ""):end_date.replace("-", "")]
                log_return_df = np.log(type_return_avg_pass_df / type_return_avg_pass_df.shift(1))
                type_weight_list, target_ret, target_var = zsmk.get_ZScom_by_var(type_return_avg_pass_df, riskfree,
                                                                                 type_num, minpercent)
                type_fundticker_dic, selected_fund_list = fs.funds_select_for_type(funds_net_inside, fund_type_list,
                                                                                   funds_type_df,
                                                                                   type_return_avg_pass_df,
                                                                                   funds_each_type=2,
                                                                                   selectby="corr")
                funds_weight_dic, total_net_percent = zsmk.get_user_fund_weight_by_risk(type_weight_list,
                                                                                        fund_type_list,
                                                                                        type_fundticker_dic,
                                                                                        userriskscore)

                current_return = get_return_by_combination(funds_weight_dic, start_date, end_date,
                                                           funds_net_inside)
                if current_return - original_return > change_return_differ:
                    combination_change_flag = True
                    combination_df_inside = pd.DataFrame(
                        columns=["userid", "date", "ticker", "name", "percent", "type"])
                    for fund, percent in funds_weight_dic.items():
                        change_dic = {}
                        change_dic["userid"] = userid
                        change_dic["date"] = end_date
                        change_dic["ticker"] = fund
                        change_dic["name"] = funds_type_df[funds_type_df["ticker"] == fund]["name"].values.tolist()[0]
                        change_dic["percent"] = float(percent) * total_net_percent
                        change_dic["type"] = \
                        funds_type_df[funds_type_df["ticker"] == fund]["fund_type"].values.tolist()[0]
                        combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                    change_dic = {}
                    change_dic["userid"] = userid
                    change_dic["date"] = end_date
                    change_dic["ticker"] = moneyfund_ticker_for_net
                    change_dic["name"] = \
                        funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["name"].values.tolist()[0]
                    change_dic["percent"] = 1 - total_net_percent
                    change_dic["type"] = \
                        funds_type_df[funds_type_df["ticker"] == moneyfund_ticker_for_net]["fund_type"].values.tolist()[
                            0]
                    combination_df_inside = combination_df_inside.append(change_dic, ignore_index=True)
                    zs_combination_df = zs_combination_df.append(combination_df_inside, ignore_index=True)
                else:
                    pass
    save_old_file_str = il.cwd + r"\result\\zs_combine_type_users__seg_before" + current_date + ".xls"
    save_new_file_str = il.cwd + r"\result\\zs_combine_type_users_seg.xls"
    if combination_change_flag:
        company_combination.to_excel(save_old_file_str)
        zs_combination_df.to_excel(save_new_file_str)
        print("File saved:", save_new_file_str + ", change date: " + current_date)
    else:
        print("No combination changes,no new file outputs: " + current_date)


if __name__ == '__main__':
    format = "%Y-%m-%d"
    days_before = 30
    userid = 1
    riskfree = 0.03
    combination_startdate = "2017-10-29"
    combination_enddate = "2017-12-07"
    datelist_out = rl.dateRange(combination_startdate, combination_enddate)
    funds_net_df_out = il.getZS_funds_net(fill=False)
    funds_profit_df = il.getZS_funds_Profit()
    # user_detail_df = il.getZS_users_complete()
    user_detail_df = il.getZS_users_complete(os.getcwd() + r"\history_data\zs_user_test.csv")
    minpercent = 0.1
    poctype = "zs"
    company_file = "zsmk"
    time_cost = 0
    usercount = 0
    change_return_differ_out = 0.01
    date_count = 0
    for current_date in datelist_out:
        date_count += 1
        company_df = il.getZS_Company_combination_by_excel(il.cwd + r"\result\\zs_combine_type_users_seg.xls")
        usercount += 1
        if date_count % 10 == 0:
            start = time.clock()
            print("计算第" + str(usercount) + "/" + str(len(datelist_out)) + "天.")
            get_ZScom_online(user_detail_df, company_df, current_date, days_before, funds_net_df_out,
                             funds_profit_df, riskfree, minpercent, change_return_differ_out)

            elapsed = (time.clock() - start)
            time_cost += elapsed
            print("Time used:", elapsed)
            print("Time Left Estimated (min):", ((time_cost / (int(usercount))) * len(datelist_out) - time_cost) / 60)
