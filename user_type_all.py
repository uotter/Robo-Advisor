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
import robolib as rl

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

# read the funds' information from files
fund1_path = r"F:\Code\Robo-Advisor\history_data\fund1.txt"
fund2_path = r"F:\Code\Robo-Advisor\history_data\fund2.txt"
fund3_path = r"F:\Code\Robo-Advisor\history_data\fund3.txt"
user_type_percent_path = r"F:\Code\Robo-Advisor\initial_percent\zengjinbao_v3_for_machine.csv"
result_path_csv = r"F:\Code\Robo-Advisor\result\zengjinbao_result.csv"
result_path_html = r"F:\Code\Robo-Advisor\result\zengjinbao_result.html"
compare_path_csv = r"F:\Code\Robo-Advisor\result\zengjinbao_result_compare.csv"
holiday_path = r"F:\Code\Robo-Advisor\usefuldata\holidays.csv"
shibor_path = r"F:\Code\Robo-Advisor\history_data\Shibor.csv"

fund1 = pd.read_csv(fund1_path).set_index("endDate")
fund2 = pd.read_csv(fund2_path).set_index("endDate")
fund3 = pd.read_csv(fund3_path).set_index("endDate")
shibor = pd.read_csv(shibor_path).set_index("date")
user_type_percent = pd.read_csv(user_type_percent_path)

startday_str = "2017-01-01"
endday_str = "2017-08-31"
startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
datelist = rl.dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
holidays = pd.read_csv(holiday_path)
filter_str = "all"

fund1 = rl.smoothfund(holidays, fund1)
fund2 = rl.smoothfund(holidays, fund2)
fund3 = rl.smoothfund(holidays, fund3)
# 活期存款利率
depsoit_current_rate = 0.0035
profit_rate = rl.getConstantDepsoit(startday_str, endday_str, depsoit_current_rate)
# shibor作为活期存款
sort_date_shibor = (rl.fillDepsoit(startday_str,endday_str,shibor,"depsoit_rate")).sort_index()
sort_date_shibor.loc["2017-01-01","depsoit_rate"] = 2.589
sort_date_shibor.loc["2017-01-02","depsoit_rate"] = 2.589
base_yearrate = sort_date_shibor
base_dayprofit = rl.yearrate_to_dayprofit(base_yearrate,"depsoit_rate","percent")

backtesting_df = pd.DataFrame(
    columns=["客户风险能力类型", "新老客户种类", "性别", "(固定基金比例)最大回撤", "(固定基金比例)平均年化利率", "(按月调整基金比例)最大回撤", "(按月调整基金比例)平均年化利率"])

compare = pd.DataFrame(fund1["dailyProfit"])
compare.rename(columns={"dailyProfit": "基金1"}, inplace=True)
compare = compare.join(fund2["dailyProfit"])
compare.rename(columns={"dailyProfit": "基金2"}, inplace=True)
compare = compare.join(fund3["dailyProfit"])
compare.rename(columns={"dailyProfit": "基金3"}, inplace=True)
year_rate_fund1 = rl.year_rate(fund1, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
year_rate_fund2 = rl.year_rate(fund2, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
year_rate_fund3 = rl.year_rate(fund3, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
for index, row in user_type_percent.iterrows():
    print("开始处理第" + str(index) + "个")
    user_type_str = row["客户风险能力类型"] + "-" + row["新老客户种类"] + "-" + row["性别"]
    user_type_str_fix = user_type_str + "-fix"
    user_type_str_dyn = user_type_str + "-dyn"
    depsoit_percent = float(row["浮动利率存款"].replace("%", "")) / 100
    fund1_percent = float(row["增金宝一号"].replace("%", "")) / 100
    fund2_percent = float(row["增金宝二号"].replace("%", "")) / 100
    fund3_percent = float(row["增金宝三号"].replace("%", "")) / 100
    fundpercent = {"depsoit": depsoit_percent, "fund1": fund1_percent, "fund2": fund2_percent, "fund3": fund3_percent}
    fundprofit = {"depsoit": base_dayprofit, "fund1": fund1, "fund2": fund2, "fund3": fund3}
    backtesting_df.loc[index, "客户风险能力类型"] = row["客户风险能力类型"]
    backtesting_df.loc[index, "新老客户种类"] = row["新老客户种类"]
    backtesting_df.loc[index, "性别"] = row["性别"]
    backtesting_df.loc[index, "基金1"] = year_rate_fund1
    backtesting_df.loc[index, "基金2"] = year_rate_fund2
    backtesting_df.loc[index, "基金3"] = year_rate_fund3
    print("开始计算第" + str(index) + "个的回撤及收益")
    combination_fix = rl.getCombinationProfit(fundpercent, fundprofit, user_type_str_fix)
    # maxdown_fix = rl.getMaxdown(base_yearrate, combination_fix, startday_str, endday_str,user_type_str_fix)
    combination_dyn = rl.getCombinationProfit_changeby_weekcount_weekday_profitpercent(fundpercent, fundprofit,
                                                                                       user_type_str_dyn)
    # maxdown_dyn = rl.getMaxdown(base_yearrate, combination_dyn, startday_str, endday_str, user_type_str_dyn)
    year_rate_fix = rl.year_rate(combination_fix, startday_str, endday_str, user_type_str_fix + "-combination_profit",
                                 format="%Y-%m-%d")
    year_rate_dyn = rl.year_rate(combination_dyn, startday_str, endday_str, user_type_str_dyn + "-combination_profit",
                                 format="%Y-%m-%d")
    # backtesting_df.loc[index, "(固定基金比例)最大回撤"] = maxdown_fix
    backtesting_df.loc[index, "(固定基金比例)平均年化利率"] = year_rate_fix
    # backtesting_df.loc[index, "(按月调整基金比例)最大回撤"] = maxdown_dyn
    backtesting_df.loc[index, "(按月调整基金比例)平均年化利率"] = year_rate_dyn
    fund1
    if filter_str in user_type_str_fix or filter_str == "all":
        if compare.empty:
            compare = pd.DataFrame(combination_fix[user_type_str_fix + "-combination_profit"])
            compare = compare.join(combination_dyn[user_type_str_dyn + "-combination_profit"])
        else:
            compare = compare.join(combination_fix[user_type_str_fix + "-combination_profit"])
            compare = compare.join(combination_dyn[user_type_str_dyn + "-combination_profit"])
print(backtesting_df)
backtesting_df.to_csv(result_path_csv, sep=',', header=True, index=True)
compare.to_csv(compare_path_csv, sep=',', header=True, index=True)