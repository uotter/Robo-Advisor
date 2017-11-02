# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import pandas as pd
import time as time
import datetime as datetime


# start和end是形如"2017-01-01"的字符串，分别表示开始时间和结束时间
# 返回在开始时间和结束时间之间的日期自字符串类表（不包括end这一天）
def dateRange(start, end, step=1, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    return [strftime(strptime(start, format) + datetime.timedelta(i), format) for i in range(0, days, step)]


# 将年利率形式的收益表示为每天万份收益的表示形式
def yearrate_to_dayprofit(yearrate):
    dayrate = yearrate / 365
    return dayrate * 10000


def getLastDayProfit(date, fund, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    count = 0
    while date not in fund.index.tolist():
        date = strptime(date, format) + datetime.timedelta(days=-1)
        count += 1
        if count > len(fund.index.tolist()):
            return 0.0
    return fund.at[strftime(date), "dailyProfit"], fund.at[strftime(date), "weeklyYield"]


def fillFund(datelist, fund):
    for date in datelist:
        if date not in fund.index.tolist():
            dailyProfit, weeklyYield = getLastDayProfit(date, fund, format="%Y-%m-%d")
            insertrow = pd.DataFrame([fund.loc[date]])
            insertrow.at[date, "dailyProfit"] = dailyProfit
            insertrow.at[date, "weeklyYield"] = weeklyYield
            fund = pd.concat([fund, insertrow], ignore_index=True)
    return fund


def getRandomDepsoit(start, end):
    datelist = dateRange(start, end)
    days = len(datelist)
    depsoit_rate = (np.random.rand(days, 1) * 2. + 2.) / 100.
    df = pd.DataFrame(depsoit_rate, index=datelist, columns=['depsoit_rate'])
    return df


def getMaxdown(base_yearrate, combination, start, end):
    datelist = dateRange(start, end)
    base_dayprofit = yearrate_to_dayprofit(base_yearrate)
    maxdown = 0
    for i in range(0, len(datelist)):
        for j in range(i, len(datelist)):
            base_benefit = base_dayprofit['depsoit_rate'][i:j].sum()
            combination_benefit = combination['dailyProfit'][i:j].sum()
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
                             columns=["dailyProfit"])
    for index, row in depsoitprofit.iterrows():
        comprofit.at[index, "dailyProfit"] = depsoitpercent * depsoitprofit.at[index, "depsoit_rate"] + fund1percent * \
                                                                                                        fund1profit.at[
                                                                                                            index,
                                                                                                            "dailyProfit"] + fund2percent * \
                                                                                                                             fund2profit.at[
                                                                                                                                 index, "dailyProfit"] + fund3percent * \
                                                                                                                                                         fund3profit.at[
                                                                                                                                                             index,
                                                                                                                                                             "dailyProfit"]
    return comprofit


# read the funds' information from files
fund1_path = r"F:\Code\Robo-Advisor\history_data\fund1.txt"
fund2_path = r"F:\Code\Robo-Advisor\history_data\fund2.txt"
fund3_path = r"F:\Code\Robo-Advisor\history_data\fund3.txt"
fund1 = pd.read_csv(fund1_path).set_index("endDate")
fund2 = pd.read_csv(fund2_path).set_index("endDate")
fund3 = pd.read_csv(fund3_path).set_index("endDate")

startday_str = "2017-01-01"
endday_str = "2017-08-31"
startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
datelist = dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
fund1 = fillFund(datelist, fund1)
fund2 = fillFund(datelist, fund2)
fund3 = fillFund(datelist, fund3)

base_yearrate = getRandomDepsoit(startday_str, endday_str)
base_dayprofit = yearrate_to_dayprofit(base_yearrate)
fundpercent = {"depsoit": 0.2, "fund1": 0.2, "fund2": 0.3, "fund3": 0.3}
fundprofit = {"depsoit": base_dayprofit, "fund1": fund1, "fund2": fund2, "fund3": fund3}
combination = getCombinationProfit(fundpercent, fundprofit)
combination.plot()
print(getMaxdown(base_yearrate, combination, startday_str, endday_str))
