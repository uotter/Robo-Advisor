# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import robolib as rl
from pylab import *
import pandas as pd
import iolib as il
import time as time

zs_funds_fee = il.getZS_Funds_Fee()
zs_funds_discount = il.getZS_Funds_discount()
zs_funds_tdays = il.getZS_Funds_tdays()
users = il.getZS_users()

funds_net = il.getFunds_Net()
funds_profit = il.getFunds_Profit()

startday_str = "2017-07-01"
endday_str = "2017-10-29"
format = "%Y-%m-%d"
strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
datelist = rl.dateRange(startday_str, endday_str)
datelist_possible = list(set(funds_net["date"].values.tolist()))
datelist_possible.sort(key=funds_net["date"].values.tolist().index)
datelist_possible_moneyfund = list(set(funds_profit["date"].values.tolist()))
datelist_possible_moneyfund.sort(key=funds_profit["date"].values.tolist().index)


def get_supplier_tickers(poctype,company_file):
    company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + poctype + "_" + company_file + ".csv")
    company_ticker_dic = {}
    company_date_set = set(company_df["date"].values.tolist())

    for index2, row2 in company_df.iterrows():
        # 对该公司对该用户组合在当天日期内的每个配置情况循环买入基金
        fund_ticker = row2["ticker"]
        # 基金编号
        fund_percent = float(row2["percent"])
        # 买入日期
        fund_date = row2["date"]