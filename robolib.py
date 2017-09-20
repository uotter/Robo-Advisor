# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import pandas as pd
import time as time
import datetime as datetime
import matplotlib.pyplot as plt
from pylab import *
import calendar

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']


# start和end是形如"2017-01-01"的字符串，分别表示开始时间和结束时间
# 返回在开始时间和结束时间之间的日期字符串类表（不包括end这一天）
def dateRange(start, end, step=1, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    return [strftime(strptime(start, format) + datetime.timedelta(i), format) for i in range(0, days, step)]


def get_date_by_year_month_weekcount_weekday(year, month, weekcount, weekday):
    """
        返回某年某月第几周星期几是具体哪个日期
        返回格式 : 2017-08-15 or False
    """
    month_info = calendar.month(year, month)
    s = month_info.split('\n')[2:]
    week = s[weekcount - 1]
    day = week[weekday * 3: weekday * 3 + 2].strip()
    if not day:
        return False
    else:
        return "%s-%02d-%02d" % (year, month, int(day))


# 将年利率形式的收益表示为每天万份收益的表示形式
def yearrate_to_dayprofit(yearrate):
    dayrate = yearrate / 365
    return dayrate * 10000


def getLastDayProfit(date, fund, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    count = 0
    while date not in fund.index.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=-1), format)
        count += 1
        if count > len(fund.index.tolist()):
            return 0.0, 0.0, "0"
    return fund.at[date, "dailyProfit"], fund.at[date, "weeklyYield"], date


def fillFund(datelist, fund):
    for date in datelist:
        if date not in fund.index.tolist():
            dailyProfit, weeklyYield, lastdate = getLastDayProfit(date, fund, format="%Y-%m-%d")
            insertrow = pd.DataFrame(
                columns=["ticker", "secShortName", "dailyProfit", "weeklyYield", "publishDate", "currencyCd"],
                index=[date])
            if lastdate != "0":
                insertrow.at[date, "dailyProfit"] = dailyProfit
                insertrow.at[date, "weeklyYield"] = weeklyYield
            else:
                insertrow.at[date, "dailyProfit"] = 0.0
                insertrow.at[date, "weeklyYield"] = 0.0
            fund = pd.concat([fund, insertrow], ignore_index=False)
    return fund


def getRandomDepsoit(start, end):
    datelist = dateRange(start, end)
    days = len(datelist)
    depsoit_rate = (np.random.rand(days, 1) * 2. + 2.) / 100.
    df = pd.DataFrame(depsoit_rate, index=datelist, columns=['depsoit_rate'])
    return df


def getConstantDepsoit(start, end, constant):
    datelist = dateRange(start, end)
    days = len(datelist)
    depsoit_rate = np.ones((days, 1)) * constant
    df = pd.DataFrame(depsoit_rate, index=datelist, columns=['depsoit_rate'])
    return df


def getMaxdown(base_yearrate, combination, start, end):
    datelist = dateRange(start, end)
    base_dayprofit = yearrate_to_dayprofit(base_yearrate)
    maxdown = 0
    for i in range(0, len(datelist)):
        for j in range(i, len(datelist)):
            base_benefit = base_dayprofit['depsoit_rate'][i:j].sum()
            combination_benefit = combination['combination_profit'][i:j].sum()
            if combination_benefit > 0:
                benefit_rel = combination_benefit - base_benefit
                down = benefit_rel / base_benefit
                if maxdown > down:
                    maxdown = down
            else:
                continue
    return maxdown


def getCombinationProfit(fundpercent, fundprofit):
    depsoitpercent = fundpercent["depsoit"]
    fund1percent = fundpercent["fund1"]
    fund2percent = fundpercent["fund2"]
    fund3percent = fundpercent["fund3"]
    depsoitprofit = fundprofit["depsoit"]
    fund1profit = fundprofit["fund1"]
    fund2profit = fundprofit["fund2"]
    fund3profit = fundprofit["fund3"]
    comprofit = pd.DataFrame(np.zeros((len(depsoitprofit.index.tolist()), 1)), index=depsoitprofit.index.tolist(),
                             columns=["combination_profit"])
    for index, row in depsoitprofit.iterrows():
        depsoitpart = depsoitpercent * depsoitprofit.loc[index, "depsoit_rate"]
        fund1part = fund1percent * fund1profit.loc[index, "dailyProfit"]
        fund2part = fund2percent * fund2profit.loc[index, "dailyProfit"]
        fund3part = fund3percent * fund3profit.loc[index, "dailyProfit"]
        comprofit.loc[index, "combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
    return comprofit


def getCombinationProfit_changeby_weekcount_weekday_profitpercent(fundpercent, fundprofit, change_weekcount=3,
                                                                  change_weekday=2):
    change_weekcount = 3
    change_weekday = 2
    depsoitpercent = fundpercent["depsoit"]
    fund1percent = fundpercent["fund1"]
    fund2percent = fundpercent["fund2"]
    fund3percent = fundpercent["fund3"]
    depsoitprofit = fundprofit["depsoit"]
    fund1profit = fundprofit["fund1"]
    fund2profit = fundprofit["fund2"]
    fund3profit = fundprofit["fund3"]
    comprofit = pd.DataFrame(np.zeros((len(depsoitprofit.index.tolist()), 1)), index=depsoitprofit.index.tolist(),
                             columns=["combination_profit"])
    fund1_month_total = 0
    fund2_month_total = 0
    fund3_month_total = 0

    for index, row in depsoitprofit.iterrows():
        year = int(index[0:4])
        month = int(index[5:7])
        day = int(index[9:])
        # 判断当天的日期是不是当月的第三个周二
        if index == get_date_by_year_month_weekcount_weekday(year, month, change_weekcount, change_weekday):
            profit_total_last_month = fund1_month_total + fund2_month_total + fund3_month_total
            fund1percent = (1 - depsoitpercent) * fund1_month_total / profit_total_last_month
            fund2percent = (1 - depsoitpercent) * fund2_month_total / profit_total_last_month
            fund3percent = (1 - depsoitpercent) * fund3_month_total / profit_total_last_month
            fund1_month_total = fund2_month_total = fund3_month_total = 0
            depsoitpart = depsoitpercent * depsoitprofit.loc[index, "depsoit_rate"]
            fund1part = fund1percent * fund1profit.loc[index, "dailyProfit"]
            fund2part = fund2percent * fund2profit.loc[index, "dailyProfit"]
            fund3part = fund3percent * fund3profit.loc[index, "dailyProfit"]
            comprofit.loc[index, "combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
        else:
            fund1_month_total += fund1profit.loc[index, "dailyProfit"]
            fund2_month_total += fund2profit.loc[index, "dailyProfit"]
            fund3_month_total += fund3profit.loc[index, "dailyProfit"]
            depsoitpart = depsoitpercent * depsoitprofit.loc[index, "depsoit_rate"]
            fund1part = fund1percent * fund1profit.loc[index, "dailyProfit"]
            fund2part = fund2percent * fund2profit.loc[index, "dailyProfit"]
            fund3part = fund3percent * fund3profit.loc[index, "dailyProfit"]
            comprofit.loc[index, "combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
    return comprofit


def year_rate(combination, start, end, profit_name, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    profit_total = 0
    for index, row in combination.iterrows():
        profit_total = profit_total + combination.loc[index, profit_name]
    year_rate_value = (profit_total / 100.0) / (days / 365.0)
    return year_rate_value




# 计算并输出该组合最大回撤
# print(getMaxdown(base_yearrate, combination, startday_str, endday_str))
