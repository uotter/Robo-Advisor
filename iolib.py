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
import math as math

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
funds_type_path = cwd + r"\history_data\funds_type.csv"
index_net_path_part = cwd + r"\history_data\index_net_"
index_name_path = cwd + r"\history_data\index_name.csv"
funds_net_total_path = cwd + r"\history_data\funds_net_total.csv"
wind_index_net_path_part = cwd + r"\history_data\wind_index_net_"
wind_index2_net_path_part = cwd + r"\history_data\wind_index2_net_"
wind_index_name_path = cwd + r"\history_data\wind_index_name.xls"
users_change_path_part = cwd + r"\history_data\zs_user_"
wind_index_dic = {"003": "恒生指数", "S4575112": "标普100指数", "S4359423": "道琼斯美国石油和天然气指数",
                  "S3641030": "纳斯达克100指数", "S4503551": "中债高收益中期票据全价(总值)指数", "S6420427": "中债-中国高等级债券指数"}
caihui_index_dic = {"000300": "沪深300"}
wind_index2_dic = {"000905.SH": "中证500", "399102.SZ": "创业板综", "SP500.SPI": "S&P 500", "891800.MI": "MSCI新兴市场",
                   "GC.CMX": "COMEX黄金"}
model_index_dic = {"003": "恒生指数", "SP500.SPI": "S&P 500", "S4359423": "道琼斯美国石油和天然气指数", "S4503551": "中债高收益中期票据全价(总值)指数",
                   "S6420427": "中债-中国高等级债券指数", "000905.SH": "中证500", "000300": "沪深300", "399102.SZ": "创业板综",
                   "891800.MI": "MSCI新兴市场", "GC.CMX": "COMEX黄金"}
# wind_index_dic = {"098": "标普中国A股综合指数", "S4575112": "标普100指数", "S4359423": "道琼斯美国石油和天然气指数",
#                   "S3641030": "纳斯达克100指数","S4503551":"中债高收益中期票据全价(总值)指数","S5132141":"中债-中国高等级债券指数"}
# wind_index_list = ["S12425", "011", "S4075674", "S5132141", "S4503551", "S3752717", "G3599466", "S5097351"]
user_change_date_list = ["2017-11-23"]


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
    for index, row in funds_combination_raw.iterrows():
        if len(row["ticker"]) < 6:
            for i in range(6 - len(row["ticker"])):
                row["ticker"] = "0" + row["ticker"]
    return funds_combination_raw


def getZS_Company_combination_by_excel(file_path):
    '''
        读取公司的组合配置结果
    '''
    funds_combination_raw = pd.read_excel(file_path, dtype=str)
    combination_columns_old = ["userid", "date", "ticker", "name", "percent", "type"]
    combination_columns_new = ["userid", "date", "ticker", "name", "percent", "risk_score", "risk_type", "type"]
    try:
        funds_combination_raw.columns = combination_columns_old
    except:
        funds_combination_raw.columns = combination_columns_new
    for index, row in funds_combination_raw.iterrows():
        if len(row["ticker"]) < 6:
            for i in range(6 - len(row["ticker"])):
                row["ticker"] = "0" + row["ticker"]
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
    funds_net_raw = pd.read_csv(funds_net_total_path, dtype=str)
    zs_net_columns_total = ["ticker", "date", "net", "net_total"]
    zs_net_columns = ["ticker", "date", "net"]
    funds_net_raw.columns = zs_net_columns_total
    funds_net = funds_net_raw.drop_duplicates(['ticker', 'date'])
    funds_net = funds_net.sort_values(by=['ticker', 'date'], axis=0, ascending=True)
    funds_net = funds_net[["ticker", "date", "net_total"]]
    funds_net.columns = ["ticker", "date", "net"]
    return funds_net


def getFunds_Net_Total():
    '''
        读取公募基金的每日净值数据
    '''
    funds_net_raw = pd.read_csv(funds_net_total_path, dtype=str)
    zs_net_columns_total = ["ticker", "date", "net", "net_total"]
    zs_net_columns = ["ticker", "date", "net"]
    funds_net_raw.columns = zs_net_columns_total
    funds_net = funds_net_raw.drop_duplicates(['ticker', 'date'])
    funds_net = funds_net.sort_values(by=['ticker', 'date'], axis=0, ascending=True)
    return funds_net


def getFunds_Profit():
    '''
        读取货币基金的每日万份收益
    '''
    funds_profit_raw = pd.read_csv(funds_profit_path, dtype=str)
    zs_profit_columns = ["ticker", "date", "net"]
    funds_profit_raw.columns = zs_profit_columns
    funds_net = funds_profit_raw.drop_duplicates(['ticker', 'date'])
    funds_net = funds_profit_raw.sort_values(by=['ticker', 'date'], axis=0, ascending=True)
    return funds_net


def getZS_users():
    '''
        读取用户列表
    '''
    users_raw = pd.read_csv(users_path, dtype=str)
    user_money_df = users_raw[['客户id', '客户投资总金额（万）']]
    users_columns = ["userid", "moneyamount"]
    user_money_df.columns = users_columns
    # user_money_df = user_money_df.sort_values(by=["userid"])
    return user_money_df


def getZS_users_complete(users_file_path=users_path):
    '''
        读取用户列表
    '''
    users_raw = pd.read_csv(users_file_path, dtype=str)
    user_money_df = users_raw[['客户id', '客户投资总金额（万）', '客户风险测评总分', '客户风险偏好类型']]
    users_columns = ["userid", "moneyamount", "risk_score", "risk_type"]
    user_money_df.columns = users_columns
    return user_money_df


def getZS_users_change(user_change_date_inside_list=user_change_date_list):
    '''
        读取用户列表
    '''
    user_change_df_dic = {}
    user_changeamount_dic = {}
    for change_date in user_change_date_inside_list:
        users_change_raw = pd.read_excel(users_change_path_part + change_date + ".xls", dtype=str)
        user_money_df = users_change_raw[['客户id', '客户投资总金额（万）', '调整（新申购或加仓为正/减仓为负）', '客户风险测评总分', '客户风险偏好类型']].copy()
        users_columns = ["userid", "moneyamount", "change_amount", "risk_score", "risk_type"]
        user_money_df.columns = users_columns
        user_money_df["change_amount"] = user_money_df["change_amount"].astype("float64")
        fill_values = {'change_amount': 0}
        user_money_df = user_money_df.fillna(value=fill_values)
        user_changeamount_thisdate_dic = {}
        for index, row in user_money_df.iterrows():
            userid = int(row["userid"])
            change_amount = float(row["change_amount"])
            original_amount = float(row["moneyamount"])
            if math.isnan(original_amount):
                user_money_df.loc[index, "moneyamount"] = change_amount
                user_money_df.loc[index, "change_amount"] = 0.0
            user_changeamount_thisdate_dic[userid] = user_money_df.loc[index, "change_amount"].round(2)
        user_changeamount_dic[change_date] = user_changeamount_thisdate_dic
        user_change_df_dic[change_date] = user_money_df
    return user_change_df_dic, user_changeamount_dic


def get_funds_pool_bytype(typelist):
    funds = pd.read_csv(fundspool_path, dtype=str)
    funds_filter = funds[funds["类型"].isin(typelist)]
    return funds_filter


def get_index_net_matrix(start_date_str, end_date_str, fill=True, yearstr="2017"):
    index_return_df = pd.DataFrame()
    datelist = rl.dateRange(start_date_str, end_date_str)
    datelist_noconnect = [w.replace("-", "") for w in datelist]
    index_net_raw = pd.read_csv(index_net_path_part + yearstr + ".csv", dtype="str")
    index_net = index_net_raw[["icode", "mcap", "tdate"]]
    index_net_columns = ["symbol", "mcap", "date"]
    index_net.columns = index_net_columns
    index_net = index_net.drop_duplicates(["symbol", "date"])
    index_net = index_net[index_net["symbol"].isin(caihui_index_dic.keys())]
    index_net = index_net[index_net["date"].isin(datelist_noconnect)]
    index_symbol_list = list(set(index_net["symbol"].values.tolist()))
    for symbol in index_symbol_list:
        sub_index_df = index_net[index_net["symbol"] == symbol]
        sub_index_df = sub_index_df.set_index("date")
        sub_index_mcap_df = sub_index_df["mcap"].astype('float64')
        index_return_df.insert(0, caihui_index_dic[symbol], sub_index_mcap_df)
    index_return_df = index_return_df.sort_index()
    if fill:
        index_return_df = index_return_df.fillna(method="pad")
        index_return_df = index_return_df.fillna(method="bfill")
    return index_return_df


def get_wind_index_net_matrix(start_date_str, end_date_str, fill=True, yearstr="2017"):
    index_return_df = pd.DataFrame()
    datelist = rl.dateRange(start_date_str, end_date_str)
    datelist_noconnect = [w.replace("-", "") for w in datelist]
    index_net_raw = pd.read_csv(wind_index_net_path_part + yearstr + ".csv", dtype="str")
    index_net = index_net_raw[["f1_1288", "f2_1288", "f3_1288"]]
    index_net_columns = ["symbol", "mcap", "date"]
    index_net.columns = index_net_columns
    index_net = index_net.drop_duplicates(["symbol", "date"])
    index_net = index_net[index_net["symbol"].isin(wind_index_dic.keys())]
    index_net = index_net[index_net["date"].isin(datelist_noconnect)]
    index_symbol_list = list(set(index_net["symbol"].values.tolist()))
    for symbol in index_symbol_list:
        sub_index_df = index_net[index_net["symbol"] == symbol]
        sub_index_df = sub_index_df.set_index("date")
        sub_index_mcap_df = sub_index_df["mcap"].astype('float64')
        # print(sub_index_mcap_df[sub_index_mcap_df.index.duplicated()])
        index_return_df.insert(0, wind_index_dic[symbol], sub_index_mcap_df)
    index_return_df = index_return_df.sort_index()
    if fill:
        index_return_df = index_return_df.fillna(method="pad")
        index_return_df = index_return_df.fillna(method="bfill")
    return index_return_df


def get_wind_index2_net_matrix(start_date_str, end_date_str, fill=True, yearstr="2017"):
    datelist = rl.dateRange(start_date_str, end_date_str)
    datelist_noconnect = [w.replace("-", "") for w in datelist]
    index_net_raw = pd.read_csv(wind_index2_net_path_part + yearstr + ".csv",
                                dtype={"date": "str", "中证500": "float64", "创业板综": "float64", "S&P 500": "float64",
                                       "MSCI新兴市场": "float64", "COMEX黄金": "float64"})
    index_return_df = index_net_raw[index_net_raw["date"].isin(datelist_noconnect)]
    index_return_df = index_return_df.set_index("date")
    index_return_df = index_return_df.sort_index()
    if fill:
        index_return_df = index_return_df.fillna(method="pad")
        index_return_df = index_return_df.fillna(method="bfill")
    return index_return_df


def get_combine_index_net_matrix(start_date_str, end_date_str, fill=True, yearstr="2017"):
    wind_index_return_df = get_wind_index_net_matrix(start_date_str, end_date_str, fill, yearstr)
    caihui_index_return_df = get_index_net_matrix(start_date_str, end_date_str, fill, yearstr)
    wind_index2_return_df = get_wind_index2_net_matrix(start_date_str, end_date_str, fill, yearstr)
    index_return_df = pd.concat([wind_index_return_df, caihui_index_return_df, wind_index2_return_df], axis=1)
    index_return_df = index_return_df[list(model_index_dic.values())]
    if fill:
        index_return_df = index_return_df.fillna(method="pad")
        index_return_df = index_return_df.fillna(method="bfill")
    index_return_df = index_return_df.sort_index()
    return index_return_df


def get_index_name(index_symbol_list):
    index_name_raw = pd.read_csv(index_name_path, dtype="str")
    index_name = index_name_raw[index_name_raw["symbol"].isin(index_symbol_list)]
    return index_name


def get_wind_index_name(index_symbol_list):
    index_name_raw = pd.read_excel(wind_index_name_path, dtype="str")
    index_name = index_name_raw[index_name_raw["f2_1289"].isin(index_symbol_list)]
    return index_name


def get_funds_type():
    funds_type_df = pd.read_csv(funds_type_path, dtype=str)
    funds_type_columns = ["ticker", "name", "fund_type"]
    funds_type_df.columns = funds_type_columns
    funds_discount_raw = getZS_Funds_discount()
    zs_funds_set = set(funds_discount_raw["ticker"].values.tolist())
    funds_type_df = funds_type_df[funds_type_df["ticker"].isin(zs_funds_set)]
    fund_type_list = list(set(funds_type_df["fund_type"].values.tolist()))
    fund_type_list = [fund_type_list[i] for i in range(len(fund_type_list)) if not fund_type_list[i] == "货币型"]
    return funds_type_df, fund_type_list


def getZS_funds_net(fill=True, year="2017"):
    '''
        读取浙商代销的所有基金的每日净值
        :param fill: 是否填充空缺值 boolean
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
                if fund_net_ticker.count()["net"] > 200:
                    funds_net[fund_ticker] = fund_net_ticker["net"].astype('float64')
                else:
                    print("Not enough data:" + fund_ticker)
            except ValueError as e:
                print(fund_ticker)
    funds_net = funds_net.sort_index()
    if fill:
        funds_net = funds_net.fillna(method="pad")
        funds_net = funds_net.fillna(method="bfill")
    return funds_net


def getZS_funds_Profit():
    '''
        读取浙商代销的所有货币基金的每日万份收益
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
    start_date_str = "2017-01-01"
    end_date_str = "2017-12-31"
    index_net_df = get_combine_index_net_matrix(start_date_str, end_date_str, fill=True)
    index_name_df = get_index_name(index_net_df.columns.tolist())
    print(index_net_df)
    # index_name_df.to_csv(cwd + r"\result\index_with_values.csv")
    # print(index_name_df[["symbol","ianame","iname","memo"]])
    # user_change_df_dic, user_changeamount_dic = getZS_users_change()
    # print(user_change_df_dic["2017-11-23"])
    # print(user_changeamount_dic["2017-11-23"])
