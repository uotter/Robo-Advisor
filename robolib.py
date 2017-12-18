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
import os

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']


# start和end是形如"2017-01-01"的字符串，分别表示开始时间和结束时间
# 返回在开始时间和结束时间之间的日期字符串列表（不包括end这一天）
def dateRange(start, end, step=1, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    return [strftime(strptime(start, format) + datetime.timedelta(i), format) for i in range(0, days, step)]


# end是形如"2017-01-01"的字符串，表示结束时间，返回当天之前days天的日期列表（不包括end这一天）
def dateRange_daysbefore(end, days, step=1, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    returnlist = [strftime(strptime(end, format) - datetime.timedelta(i), format) for i in range(0, days, step)]
    returnlist.sort()
    return returnlist


# start和end是形如"2017-01-01"的字符串，分别表示开始时间和结束时间
# 返回在开始时间和结束时间之间的日期字符串列表（包括end这一天）
def dateRange_endinclude(start, end, step=1, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days + 1
    return [strftime(strptime(start, format) + datetime.timedelta(i), format) for i in range(0, days, step)]


def get_date_by_year_month_weekcount_weekday(year, month, weekcount, weekday):
    """
        返回某年某月第几周星期几是具体哪个日期
        返回格式 : 2017-08-15 or False
    """
    weekday = weekday - 1
    month_info = calendar.month(year, month)
    s = month_info.split('\n')[2:]
    week = s[weekcount - 1]
    day = week[weekday * 3: weekday * 3 + 2].strip()
    if not day:
        return False
    else:
        return "%s-%02d-%02d" % (year, month, int(day))


def getNetWorthFromDailyProfit(funds):
    '''
        从基金数据的日万份收益计算器净值，以方便后续计算对数收益率,由于使用了万份净值，初始净值按照一万分计算
        按复利计算
    '''
    returnpd = funds.copy(deep=True)
    returnpd.ix[0] = returnpd.ix[0] + 10000
    nod = len(funds)
    for i in range(1, nod):
        returnpd.ix[i] = returnpd.ix[i - 1] + funds.ix[i] * (returnpd.ix[i - 1] / 10000)
    return returnpd


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


# 将年利率形式的收益表示为每天万份收益的表示形式
def yearrate_to_dayprofit(yearrate, columnname, percentorreal):
    if columnname == "single_number":
        dayrate = yearrate / 365
        return dayrate * 10000
    else:
        for index, row in yearrate.iterrows():
            year_rate_daily = yearrate.loc[index, columnname]
            if percentorreal == "percent":
                dailyprofit = ((year_rate_daily / 365) * 10000) / 100
                yearrate.loc[index, columnname] = dailyprofit
            else:
                dailyprofit = (year_rate_daily / 365) * 10000
                yearrate.loc[index, columnname] = dailyprofit
        return yearrate


def getLastDayProfit(date, fund, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    count = 0
    while date not in fund.index.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=-1), format)
        count += 1
        if count > len(fund.index.tolist()):
            return 0.0, 0.0, "0"
    return fund.at[date, "dailyProfit"], fund.at[date, "weeklyYield"], date


def getLastDayProfitbyList(date, fund, columnlist, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    count = 0
    returnlist = []
    while date not in fund.index.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=-1), format)
        count += 1
        if count > len(fund.index.tolist()):
            return 0.0, 0.0, "0"
    for columnname in columnlist:
        returnlist.append(fund.at[date, columnname])
    returnlist.append(date)
    return returnlist


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


def fillDepsoit(start, end, depsoitdf, columnname):
    datelist = dateRange(start, end)
    for date in datelist:
        insertrow = pd.DataFrame(
            columns=["O/N", columnname, "2W", "1M", "3M", "6M", "9M"],
            index=[date])
        if date not in depsoitdf.index.tolist():
            dailyDepsoitrate = getLastDayProfitbyList(date, depsoitdf, [columnname], format="%Y-%m-%d")
            depsoit_rate = dailyDepsoitrate[0]
            lastdate = dailyDepsoitrate[1]
            if lastdate != "0":
                insertrow.at[date, columnname] = depsoit_rate
            else:
                insertrow.at[date, columnname] = 0.0
            depsoitdf = pd.concat([depsoitdf, insertrow], ignore_index=False)
    return depsoitdf


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


def getSigma():
    sigma = 0
    return sigma


def getMaxdown(base_yearrate, combination, start, end, user_type_str):
    datelist = dateRange(start, end)
    base_dayprofit = yearrate_to_dayprofit(base_yearrate, "depsoit_rate", "percent")
    maxdown = 0
    for i in range(0, len(datelist)):
        for j in range(i, len(datelist)):
            base_benefit = base_dayprofit['depsoit_rate'][i:j].sum()
            combination_benefit = combination[user_type_str + '-combination_profit'][i:j].sum()
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
    percent_detail = pd.DataFrame(
        columns=["存款比例", "基金1比例", "基金2比例", "基金3比例"])
    temp_df = pd.DataFrame([[depsoitpercent, fund1percent, fund2percent, fund3percent]],
                           columns=["存款比例", "基金1比例", "基金2比例", "基金3比例"])
    percent_detail = temp_df
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
            temp_df = pd.DataFrame([[depsoitpercent, fund1percent, fund2percent, fund3percent]],
                                   columns=["存款比例", "基金1比例", "基金2比例", "基金3比例"])
            if percent_detail.empty:
                percent_detail = temp_df
            else:
                percent_detail = pd.concat([percent_detail, temp_df])
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
    return comprofit, percent_detail


# 计算序列的统计参数，输入的combination为每日万份收益的dataframe
def statisticscompute(combination, start, end, profit_name, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    profit_total = 0
    combination = combination.sort_index()
    statistics = combination.strftime()
    count = statistics.loc["count", profit_name]
    mean = statistics.loc["mean", profit_name]
    std = statistics.loc["std", profit_name]
    year_rate = (count * mean / 100.0) / (days / 365.0)
    sharp = year_rate / std
    # for index, row in combination.iterrows():
    #     if strptime(end, format) > strptime(index, format):
    #         profit_total = profit_total + combination.loc[index, profit_name]
    # year_rate_value = (profit_total / 100.0) / (days / 365.0)
    return year_rate, std, sharp


# 计算序列的年化收益率，输入的combination为每日万份收益的dataframe
def year_rate(combination, start, end, profit_name, format="%Y-%m-%d"):
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    days = (strptime(end, format) - strptime(start, format)).days
    profit_total = 0
    combination = combination.sort_index()
    for index, row in combination.iterrows():
        if strptime(end, format) > strptime(index, format):
            profit_total = profit_total + combination.loc[index, profit_name]
    year_rate_value = (profit_total / 100.0) / (days / 365.0)
    return year_rate_value


def getFundsNetNext_byTickerDate(ticker, date, funds_df, format="%Y-%m-%d"):
    '''
        根据基金编号和基金日期返回基金净值或日万份收益,如果当天没有，则返回后面第一天的值，
        如果后面都没有值，则返回0
        :param funds_df: 列表形式的基金净值dataframe，index为序号，date列为日期，ticker列为基金编号，net列为基金净值
    '''
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    funds_ticker = funds_df[funds_df["ticker"] == ticker]
    datemax = funds_ticker.iloc[-1]["date"]
    while date not in funds_ticker["date"].values.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=1), format)
        if datetime.datetime.strptime(str(date), format) > datetime.datetime.strptime(str(datemax), format):
            return 0.0
    return float(funds_ticker[funds_ticker["date"] == date].iloc[0]["net"])


def getFundsNetBefore_byTickerDate(ticker, date, funds_df, format="%Y-%m-%d"):
    '''
        根据基金编号和基金日期返回基金净值或日万份收益,如果当天没有，则返回前面一天的值，
        如果前面都没有值，则返回0
        :param funds_df: 列表形式的基金净值dataframe，index为序号，date列为日期，ticker列为基金编号，net列为基金净值
    '''
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    funds_ticker = funds_df[funds_df["ticker"] == ticker]
    datemin = funds_ticker.iloc[0]["date"]
    while date not in funds_ticker["date"].values.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=-1), format)
        if datetime.datetime.strptime(str(date), format) < datetime.datetime.strptime(str(datemin), format):
            return 0.0
    return float(funds_ticker[funds_ticker["date"] == date].iloc[0]["net"])

def getFundsNetNext_byTickerDate_MartrixFundsDf(ticker, date, funds_df, format="%Y-%m-%d"):
    '''
        根据基金编号和基金日期返回基金净值或日万份收益,如果当天没有，则返回后面第一天的值，
        如果后面都没有值，则返回0
        :param funds_df: 矩阵形式的基金净值dataframe，index为日期，column为基金ticker，矩阵中的每一个值为基金净值
    '''
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    funds_ticker = funds_df[ticker]
    datemax = funds_ticker.index.tolist[-1]
    while date not in funds_ticker.index.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=1), format)
        if datetime.datetime.strptime(str(date), format) > datetime.datetime.strptime(str(datemax), format):
            return 0.0
    return float(funds_ticker[date])


def getFundsNetBefore_byTickerDate_MartrixFundsDf(ticker, date, funds_df, format="%Y-%m-%d"):
    '''
        根据基金编号和基金日期返回基金净值或日万份收益,如果当天没有，则返回前面一天的值，
        如果前面都没有值，则返回0
        :param funds_df: 矩阵形式的基金净值dataframe，index为日期，column为基金ticker，矩阵中的每一个值为基金净值
    '''
    strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
    funds_ticker = funds_df[ticker]
    datemin = funds_ticker.index.tolist()[0]
    while date not in funds_ticker.index.tolist():
        date = strftime(strptime(date, format) + datetime.timedelta(days=-1), format)
        if datetime.datetime.strptime(str(date), format) < datetime.datetime.strptime(str(datemin), format):
            return 0.0
    return float(funds_ticker[date])


def getUserCombinationByDate(date, user_combination):
    '''
        根据日期得到用户的资金组合字典
        :param date: 要获取的日期，str
        :param user_combination:该用户的所有组合，dataframe
        :return return_dic:基金组合，dic，key:基金编号，value:基金比例
        :return combination_dates_df:基金组合，dataframe
        :return date: 组合的日期，因为如果传入的日期没有组合数据的话，会选择最近的一个之前的日期，因此此处回传一下选择的日期，str
    '''
    return_dic = {}
    combination_dates_list = list(set(user_combination["date"].values.tolist()))
    if date in combination_dates_list:
        combination_dates_df = user_combination[user_combination["date"] == date]
        for index2, row2 in combination_dates_df.iterrows():
            # 根据该用户在当天的组合情况计算其总净值
            fund_ticker = row2["ticker"]
            # 基金编号
            fund_percent = float(row2["percent"])
            # 基金比例
            return_dic[fund_ticker] = fund_percent
        return return_dic, combination_dates_df, date
    else:
        combination_dates_list.append(date)
        combination_dates_list.sort()
        date_index = combination_dates_list.index(date)
        if date_index == 0:
            return return_dic, pd.DataFrame(), "null"
        else:
            combination_date = combination_dates_list[date_index - 1]
            combination_dates_df = user_combination[user_combination["date"] == combination_date]
            for index2, row2 in combination_dates_df.iterrows():
                # 根据该用户在当天的组合情况计算其总净值
                fund_ticker = row2["ticker"]
                # 基金编号
                fund_percent = float(row2["percent"])
                # 基金比例
                return_dic[fund_ticker] = fund_percent
            return return_dic, combination_dates_df, combination_date


if __name__ == '__main__':
    # cwd = os.getcwd()
    # fund1_path = cwd + r"\history_data\fund1.txt"
    # fund2_path = cwd + r"\history_data\fund2.txt"
    # fund3_path = cwd + r"\history_data\fund3.txt"
    # user_type_percent_path = cwd + r"\initial_percent\zengjinbao_v3_for_machine.csv"
    # result_path_csv = cwd + r"\result\zengjinbao_result.csv"
    # result_path_html = cwd + r"\result\zengjinbao_result.html"
    # percent_path_csv = cwd + r"\result\percent_result.csv"
    # compare_path_csv = cwd + r"\result\zengjinbao_result_compare.csv"
    # holiday_path = cwd + r"\usefuldata\holidays.csv"
    # shibor_path = cwd + r"\history_data\Shibor.csv"
    #
    # fund1 = pd.read_csv(fund1_path).set_index("endDate")
    # fund2 = pd.read_csv(fund2_path).set_index("endDate")
    # fund3 = pd.read_csv(fund3_path).set_index("endDate")
    # shibor = pd.read_csv(shibor_path).set_index("date")
    # user_type_percent = pd.read_csv(user_type_percent_path)
    #
    # startday_str = "2017-01-01"
    endday_str = "2017-08-31"
    # startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
    # endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
    # datelist = dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
    # holidays = pd.read_csv(holiday_path)
    # filter_str = "all"
    #
    # fund1 = smoothfund(holidays, fund1)
    # fund2 = smoothfund(holidays, fund2)
    # fund3 = smoothfund(holidays, fund3)
    # # 活期存款利率
    # depsoit_current_rate = 0.0035
    # profit_rate = getConstantDepsoit(startday_str, endday_str, depsoit_current_rate)
    # # shibor作为活期存款
    # sort_date_shibor = (fillDepsoit(startday_str, endday_str, shibor, "depsoit_rate")).sort_index()
    # sort_date_shibor.loc["2017-01-01", "depsoit_rate"] = 2.589
    # sort_date_shibor.loc["2017-01-02", "depsoit_rate"] = 2.589
    # base_yearrate = sort_date_shibor
    # base_dayprofit = yearrate_to_dayprofit(base_yearrate, "depsoit_rate", "percent")
    # fundprofit = {"depsoit": base_dayprofit, "fund1": fund1, "fund2": fund2, "fund3": fund3}
    # fundpercent = {"depsoit": 0.873, "fund1": 0.04, "fund2": 0.001, "fund3": 0.086}
    # result = getCombinationProfit(fundpercent, fundprofit, "test")
    # r2 = statisticscompute(result, startday_str, endday_str, "test-combination_profit", format="%Y-%m-%d")
    # print(r2)
    days = 30
    datelist_inside = dateRange_daysbefore(endday_str, days)
    print(datelist_inside)
