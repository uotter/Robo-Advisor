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
    weekday = weekday-1
    month_info = calendar.month(year, month)
    s = month_info.split('\n')[2:]
    week = s[weekcount - 1]
    day = week[weekday * 3: weekday * 3 + 2].strip()
    if not day:
        return False
    else:
        return "%s-%02d-%02d" % (year, month, int(day))


def allweeks(year):
    '''计算一年内所有周的具体日期,从1月1号开始，12.31号结束
    输出如{1: ['2019-01-01','2019-01-06'],...} 只有六天
    '''
    start_date = datetime.datetime.strptime(str(year) + '-01-01', '%Y-%m-%d')
    end_date = datetime.datetime.strptime(str(year) + '-12-31', '%Y-%m-%d')
    _u = datetime.timedelta(days=1)
    n = 0
    week_date = {}
    while 1:
        _time = start_date + n * _u
        w = str(int(_time.strftime('%W')) + 1)
        week_date.setdefault(w, []).append(_time.strftime('%Y-%m-%d'))
        n = n + 1
        if _time == end_date:
            break
    week_date_start_end = {}
    for i in week_date:
        week_date_start_end[i] = [week_date[i][0], week_date[i][-1]]
    print(week_date)
    print(week_date_start_end)
    return week_date


def getholidaydic(yearlist):
    for i in range(len(yearlist)):
        year = yearlist[i]


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


def smoothfund(holidaydf, fund):
    missdatelist = []
    for index, row in holidaydf.iterrows():
        date = row["datestr"]
        weekend = row["weekday"]
        if date not in fund.index.tolist():
            missdatelist.append(date)
        elif len(missdatelist) > 0:
            smoothdailyProfit = fund.loc[date, "dailyProfit"] / (len(missdatelist) + 1)
            for missdate in missdatelist:
                insertrow = pd.DataFrame(
                    columns=["ticker", "secShortName", "dailyProfit", "weeklyYield", "publishDate", "currencyCd"],
                    index=[missdate])
                insertrow.at[missdate, "dailyProfit"] = smoothdailyProfit
                fund = pd.concat([fund, insertrow], ignore_index=False)
            fund.at[date, "dailyProfit"] = smoothdailyProfit
            missdatelist.clear()
    return fund


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


def getCombinationProfit(fundpercent, fundprofit, combinationname):
    depsoitpercent = fundpercent["depsoit"]
    fund1percent = fundpercent["fund1"]
    fund2percent = fundpercent["fund2"]
    fund3percent = fundpercent["fund3"]
    depsoitprofit = fundprofit["depsoit"]
    fund1profit = fundprofit["fund1"]
    fund2profit = fundprofit["fund2"]
    fund3profit = fundprofit["fund3"]
    comprofit = pd.DataFrame(np.zeros((len(depsoitprofit.index.tolist()), 1)), index=depsoitprofit.index.tolist(),
                             columns=[combinationname + "-combination_profit"])
    for index, row in depsoitprofit.iterrows():
        depsoitpart = depsoitpercent * depsoitprofit.loc[index, "depsoit_rate"]
        fund1part = fund1percent * fund1profit.loc[index, "dailyProfit"]
        fund2part = fund2percent * fund2profit.loc[index, "dailyProfit"]
        fund3part = fund3percent * fund3profit.loc[index, "dailyProfit"]
        comprofit.loc[index, combinationname + "-combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
    return comprofit


def getCombinationProfit_changeby_weekcount_weekday_profitpercent(fundpercent, fundprofit, combinationname,
                                                                  change_weekcount=3,
                                                                  change_weekday=2):
    depsoitpercent = fundpercent["depsoit"]
    fund1percent = fundpercent["fund1"]
    fund2percent = fundpercent["fund2"]
    fund3percent = fundpercent["fund3"]
    depsoitprofit = fundprofit["depsoit"]
    fund1profit = fundprofit["fund1"]
    fund2profit = fundprofit["fund2"]
    fund3profit = fundprofit["fund3"]
    comprofit = pd.DataFrame(np.zeros((len(depsoitprofit.index.tolist()), 1)), index=depsoitprofit.index.tolist(),
                             columns=[combinationname + "-combination_profit"])
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
            comprofit.loc[
                index, combinationname + "-combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
        else:
            fund1_month_total += fund1profit.loc[index, "dailyProfit"]
            fund2_month_total += fund2profit.loc[index, "dailyProfit"]
            fund3_month_total += fund3profit.loc[index, "dailyProfit"]
            depsoitpart = depsoitpercent * depsoitprofit.loc[index, "depsoit_rate"]
            fund1part = fund1percent * fund1profit.loc[index, "dailyProfit"]
            fund2part = fund2percent * fund2profit.loc[index, "dailyProfit"]
            fund3part = fund3percent * fund3profit.loc[index, "dailyProfit"]
            comprofit.loc[
                index, combinationname + "-combination_profit"] = depsoitpart + fund1part + fund2part + fund3part
    return comprofit


def year_rate(combination, start, end, profit_name, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    profit_total = 0
    for index, row in combination.iterrows():
        profit_total = profit_total + combination.loc[index, profit_name]
    year_rate_value = (profit_total / 100.0) / (days / 365.0)
    return year_rate_value


if __name__ == '__main__':
    # read the funds' information from files
    fund1_path = r"F:\Code\Robo-Advisor\history_data\fund1.txt"
    # fund2_path = r"F:\Code\Robo-Advisor\history_data\fund2.txt"
    # fund3_path = r"F:\Code\Robo-Advisor\history_data\fund3.txt"
    holiday_path = r"F:\Code\Robo-Advisor\usefuldata\holidays.csv"
    fund1 = pd.read_csv(fund1_path).set_index("endDate")
    # fund2 = pd.read_csv(fund2_path).set_index("endDate")
    # fund3 = pd.read_csv(fund3_path).set_index("endDate")
    holidays = pd.read_csv(holiday_path)

    startday_str = "2017-01-01"
    endday_str = "2017-08-31"
    startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
    endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
    datelist = dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
    fund1 = smoothfund(holidays, fund1)
    # fund2 = fillFund(datelist, fund2)
    # fund3 = fillFund(datelist, fund3)

    fund1.sort_index()
    fund1.to_csv(r"F:\Code\Robo-Advisor\usefuldata\fundanalysis.csv", sep=',', header=True, index=True)
    print(fund1)
