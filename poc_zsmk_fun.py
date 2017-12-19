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


def get_ZScom_online(user_detail_df, company_combination, datelist, daysbefore, funds_net_inside,
                     funds_profit_inside, riskfree, minpercent, change_return_differ,symbolstr):
    """
        增量在线的方式生成组合策略
        :param user_detail_df：给定的用户列表，dataframe
        :param company_combination:当前的基金组合列表，dataframe
        :param datelist:时间段的list，list
        :param daysbefore:以当前日期之前多少天的历史数据作为计算依据
        :param funds_net_inside:基金净值数据，*****此处的fund_net需要是原始未进行缺失值处理的dataframe*****，dataframe
        :param funds_profit_inside:货币型基金日万份收益数据，dataframe
        :param riskfree:无风险利率，float
        :param minpercent: 某一个基金大类的所占比例的下限约束，float
        :param var_goal:预期波动率，预期波动率为0时，表示没有约束，float
        :param symbolstr:一个人工确定的数值，用于标识生成文件的文件名，实验时方便区分不同的实验，str
        :return: None 但是会输出生成的文件
    """
    zs_combination_df = pd.DataFrame()
    funds_type_df, fund_type_list = il.get_funds_type()
    funds_net_df_fill = funds_net_inside.copy()
    funds_net_df_fill = funds_net_df_fill.fillna(method="pad")
    funds_net_df_fill = funds_net_df_fill.fillna(method="bfill")
    type_return_avg_df = fs.type_return_avg(funds_net_df_fill, fund_type_list, funds_type_df)
    user_type_num = len(set(user_detail_df["risk_type"].values.tolist()))
    for current_date in datelist:
        moneyfund_ticker_for_net = zsmk.get_best_moneyfundticker(current_date, days_before, funds_profit_df,
                                                                 method="maxmeanreturn")
        usercount = 0
        for index, row in user_detail_df.iterrows():
            usercount += 1
            userid = row["userid"]
            usermoneyamount = row["moneyamount"]
            userriskscore = row["risk_score"]
            userrisktype = row["risk_type"]
            start = time.clock()
            print("计算第" + str(usercount) + "/" + str(len(user_detail_df)) + "个用户.")
            # 如果company_combination不是空的，则说明是增量式的生成用户后续配置
            try:
                user_combination = company_combination[company_combination["userid"] == userid]
            # 如果company_combination是空的，则说明是全新生成用户的配置情况
            except:
                user_combination = pd.DataFrame()

        # 如果company_combination是空的，则说明是全新生成用户的配置情况
        if company_combination.empty:
            pass
        # 如果company_combination不是空的，则说明是增量式的生成用户后续配置
        else:
            pass






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
