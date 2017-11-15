# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import pandas as pd
import time as time
import datetime as datetime
from pylab import *
import robolib as rl
import calendar
import os

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

# read the funds' information from files
cwd = os.getcwd()
fund1_path = cwd + r"\history_data\fund1.txt"
fund2_path = cwd + r"\history_data\fund2.txt"
fund3_path = cwd + r"\history_data\fund3.txt"
user_type_percent_path = cwd + r"\initial_percent\zengjinbao_v3_for_machine.csv"
result_path_csv = cwd + r"\result\zengjinbao_result.csv"
result_path_html = cwd + r"\result\zengjinbao_result.html"
percent_path_csv = cwd + r"\result\percent_result.csv"
compare_path_csv = cwd + r"\result\zengjinbao_result_compare.csv"
holiday_path = cwd + r"\usefuldata\holidays.csv"
shibor_path = cwd + r"\history_data\Shibor.csv"
fundspool_path = cwd + r"\history_data\FundsPool.csv"
funds_fee_path = cwd + r"\history_data\zs_fee.csv"
funds_discount_path = cwd + r"\history_data\zs_discount.csv"
funds_tdays_path = cwd + r"\history_data\zs_tdays.csv"
users_path = cwd + r"\history_data\zs_user.csv"
funds_net_path = cwd + r"\history_data\funds_net.csv"
funds_profit_path = cwd + r"\history_data\funds_profit.csv"


def getFunds_Everyday(startday_str, endday_str):
    fund1 = pd.read_csv(fund1_path).set_index("endDate")
    fund2 = pd.read_csv(fund2_path).set_index("endDate")
    fund3 = pd.read_csv(fund3_path).set_index("endDate")
    shibor = pd.read_csv(shibor_path).set_index("date")
    holidays = pd.read_csv(holiday_path)
    fund1 = rl.smoothfund(holidays, fund1)
    fund2 = rl.smoothfund(holidays, fund2)
    fund3 = rl.smoothfund(holidays, fund3)
    # 活期存款利率
    depsoit_current_rate = 0.0035
    # shibor作为活期存款
    sort_date_shibor = (rl.fillDepsoit(startday_str, endday_str, shibor, "depsoit_rate")).sort_index()
    sort_date_shibor.loc["2017-01-01", "depsoit_rate"] = 2.589
    sort_date_shibor.loc["2017-01-02", "depsoit_rate"] = 2.589
    base_yearrate = sort_date_shibor
    base_dayprofit = rl.yearrate_to_dayprofit(base_yearrate, "depsoit_rate", "percent")
    returnpd = pd.DataFrame(base_dayprofit["depsoit_rate"])
    returnpd.rename(columns={"depsoit_rate": "depsoit"}, inplace=True)
    returnpd = returnpd.join(fund1["dailyProfit"])
    returnpd.rename(columns={"dailyProfit": "fund1"}, inplace=True)
    returnpd = returnpd.join(fund2["dailyProfit"])
    returnpd.rename(columns={"dailyProfit": "fund2"}, inplace=True)
    returnpd = returnpd.join(fund3["dailyProfit"])
    returnpd.rename(columns={"dailyProfit": "fund3"}, inplace=True)
    cols = returnpd.columns
    for col in cols:
        returnpd[col] = returnpd[col].astype(float)
    return returnpd


def getZS_Funds_Fee():
    '''
        读取我行代销的基金列表，相应的申购费率和赎回费率
    '''
    funds_fee_raw = pd.read_csv(funds_fee_path, dtype=str)
    zs_funds_pd_columns = ["ticker", "name", "type", "risk", "buyratio", "sellratio"]
    zs_funds_pd = pd.DataFrame(columns=zs_funds_pd_columns)
    for index, row in funds_fee_raw.iterrows():
        ticker = funds_fee_raw.loc[index, "产品代码"]
        if len(str(ticker).strip()) == 6:
            fundsname = funds_fee_raw.loc[index, "产品简称"]
            fundstype = funds_fee_raw.loc[index, "产品类型"]
            fundsrisk = funds_fee_raw.loc[index, "风险等级"]
            fundsbuy = str(
                funds_fee_raw.loc[index, "买费率"] if funds_fee_raw.loc[index, "买费率"] not in ["不收费", "无"] else 0)
            fundssell = str(
                funds_fee_raw.loc[index, "卖费率"] if funds_fee_raw.loc[index, "卖费率"] not in ["不收费", "无"] else 0)
            funds_fee_dic = {"ticker": ticker, "name": fundsname, "type": fundstype, "risk": fundsrisk,
                             "buyratio": float(fundsbuy.replace("%", "")) / 100.0,
                             "sellratio": float(fundssell.replace("%", "")) / 100.0}
            zs_funds_pd = zs_funds_pd.append(funds_fee_dic, ignore_index=True)
    return zs_funds_pd


def getZS_Funds_discount():
    '''
        读取我行代销的基金的申购折扣
    '''
    funds_discount_raw = pd.read_csv(funds_discount_path, dtype=str)
    zs_discount_columns = ["ticker", "name", "tcode", "tname", "ttype", "tmin", "tmax", "discount"]
    funds_discount_raw.columns = zs_discount_columns
    return funds_discount_raw


def getZS_Company_combination(file_path):
    '''
        读取公司的组合配置结果
    '''
    funds_combination_raw = pd.read_csv(file_path, dtype=str)
    combination_columns = ["userid", "date", "ticker", "name", "percent"]
    funds_combination_raw.columns = combination_columns
    return funds_combination_raw


def getZS_Funds_tdays():
    '''
        读取基金赎回的到账日期
    '''
    funds_tdays_raw = pd.read_csv(funds_tdays_path, dtype=str)
    zs_tdays_columns = ["ticker", "name", "tacode", "ttype", "tdays"]
    funds_tdays_raw.columns = zs_tdays_columns
    return funds_tdays_raw


def getFunds_Net():
    '''
        读取公募基金的每日净值数据
    '''
    funds_net_raw = pd.read_csv(funds_net_path, dtype=str)
    zs_net_columns = ["ticker", "date", "net"]
    funds_net_raw.columns = zs_net_columns
    return funds_net_raw


def getFunds_Profit():
    '''
        读取货币基金的每日万份收益
    '''
    funds_profit_raw = pd.read_csv(funds_profit_path, dtype=str)
    zs_profit_columns = ["ticker", "date", "net"]
    funds_profit_raw.columns = zs_profit_columns
    return funds_profit_raw


def getZS_users():
    '''
        读取用户列表
    '''
    users_raw = pd.read_csv(users_path, dtype=str)
    user_money_df = users_raw[['客户id', '客户投资总金额（万）']]
    users_columns = ["userid", "moneyamount"]
    user_money_df.columns = users_columns
    return user_money_df


def getZS_users_complete():
    '''
        读取用户列表
    '''
    users_raw = pd.read_csv(users_path, dtype=str)
    user_money_df = users_raw[['客户id', '客户投资总金额（万）', '客户风险测评总分', '客户风险偏好类型']]
    users_columns = ["userid", "moneyamount", "risk_score", "risk_type"]
    user_money_df.columns = users_columns
    return user_money_df


def get_funds_pool_bytype(typelist):
    funds = pd.read_csv(fundspool_path, dtype=str)
    funds_filter = funds[funds["类型"].isin(typelist)]
    return funds_filter


def getZS_funds_net():
    '''
        读取浙商代销的所有基金的每日净值
    '''
    funds_net_raw = getFunds_Net()
    funds_discount_raw = getZS_Funds_discount()
    zs_funds_set = set(funds_discount_raw["ticker"].values.tolist())
    funds_net_raw = funds_net_raw[funds_net_raw["ticker"].isin(zs_funds_set)]
    funds_net = pd.DataFrame(index=set(funds_net_raw["date"].values.tolist()))
    zs_funds_set_list = list(zs_funds_set)
    zs_funds_set_list.sort()
    for fund_ticker in zs_funds_set_list:
        if fund_ticker in funds_net_raw["ticker"].values.tolist():
            try:
                fund_net_ticker = funds_net_raw[funds_net_raw["ticker"] == fund_ticker]
                fund_net_ticker = fund_net_ticker.drop_duplicates("date")
                fund_net_ticker = fund_net_ticker.set_index("date")
                funds_net[fund_ticker] = fund_net_ticker["net"].astype('float64')
            except ValueError as e:
                print(fund_ticker)
    funds_net = funds_net.sort_index()
    funds_net = funds_net.fillna(method="pad")
    funds_net = funds_net.fillna(method="bfill")
    return funds_net


def getZS_funds_Profit():
    '''
        读取浙商代销的所有基金的每日净值
    '''
    funds_profit_raw = getFunds_Profit()
    funds_discount_raw = getZS_Funds_discount()
    zs_funds_set = set(funds_discount_raw["ticker"].values.tolist())
    funds_profit_raw = funds_profit_raw[funds_profit_raw["ticker"].isin(zs_funds_set)]
    funds_net = pd.DataFrame(index=set(funds_profit_raw["date"].values.tolist()))
    for fund_ticker in zs_funds_set:
        if fund_ticker in funds_profit_raw["ticker"].values.tolist():
            try:
                fund_net_ticker = funds_profit_raw[funds_profit_raw["ticker"] == fund_ticker]
                fund_net_ticker = fund_net_ticker.drop_duplicates("date")
                fund_net_ticker = fund_net_ticker.set_index("date")
                funds_net[fund_ticker] = fund_net_ticker["net"].astype('float64')
            except ValueError as e:
                print(fund_ticker)
    funds_net = funds_net.sort_index()
    funds_net = funds_net.fillna(method="pad")
    funds_net = funds_net.fillna(method="bfill")
    return funds_net


if __name__ == '__main__':
    zsfunds = getZS_funds_net()
    print(zsfunds)
