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
fund1 = pd.read_csv(fund1_path).set_index("endDate")
fund2 = pd.read_csv(fund2_path).set_index("endDate")
fund3 = pd.read_csv(fund3_path).set_index("endDate")
user_type_percent = pd.read_csv(user_type_percent_path)

startday_str = "2017-01-01"
endday_str = "2017-08-31"
startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
datelist = rl.dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
fund1 = rl.fillFund(datelist, fund1)
fund2 = rl.fillFund(datelist, fund2)
fund3 = rl.fillFund(datelist, fund3)
# 活期存款利率
depsoit_current_rate = 0.0035
# 活期存款日万份收益序列计算
profit_rate = rl.getConstantDepsoit(startday_str, endday_str, depsoit_current_rate)
base_yearrate = profit_rate
base_dayprofit = rl.yearrate_to_dayprofit(base_yearrate)

backtesting_df = pd.DataFrame(
    columns=["客户风险能力类型", "新老客户种类", "性别", "(固定基金比例)最大回撤", "(固定基金比例)平均年化利率", "(按月调整基金比例)最大回撤", "(按月调整基金比例)平均年化利率"])
for index, row in user_type_percent.iterrows():
    print("开始处理第"+str(index)+"个")
    user_type_str = row["客户风险能力类型"] + "-" + row["新老客户种类"] + "-" + row["性别"]
    depsoit_percent = float(row["浮动利率存款"].replace("%", "")) / 100
    fund1_percent = float(row["增金宝一号"].replace("%", "")) / 100
    fund2_percent = float(row["增金宝二号"].replace("%", "")) / 100
    fund3_percent = float(row["增金宝三号"].replace("%", "")) / 100
    fundpercent = {"depsoit": depsoit_percent, "fund1": fund1_percent, "fund2": fund2_percent, "fund3": fund3_percent}
    fundprofit = {"depsoit": base_dayprofit, "fund1": fund1, "fund2": fund2, "fund3": fund3}
    backtesting_df.loc[index, "客户风险能力类型"] = row["客户风险能力类型"]
    backtesting_df.loc[index, "新老客户种类"] = row["新老客户种类"]
    backtesting_df.loc[index, "性别"] = row["性别"]
    print("开始计算第" + str(index) + "个的回撤及收益")
    combination_fix = rl.getCombinationProfit(fundpercent, fundprofit)
    # maxdown_fix = rl.getMaxdown(base_yearrate, combination_fix, startday_str, endday_str)
    combination_dyn = rl.getCombinationProfit_changeby_weekcount_weekday_profitpercent(fundpercent, fundprofit)
    # maxdown_dyn = rl.getMaxdown(base_yearrate, combination_dyn, startday_str, endday_str)
    year_rate_fix = rl.year_rate(combination_fix, startday_str, endday_str, "combination_profit", format="%Y-%m-%d")
    year_rate_dyn = rl.year_rate(combination_dyn, startday_str, endday_str, "combination_profit", format="%Y-%m-%d")
    # backtesting_df.loc[index, "(固定基金比例)最大回撤"] = maxdown_fix
    backtesting_df.loc[index, "(固定基金比例)平均年化利率"] = year_rate_fix
    # backtesting_df.loc[index, "(按月调整基金比例)最大回撤"] = maxdown_dyn
    backtesting_df.loc[index, "(按月调整基金比例)平均年化利率"] = year_rate_dyn

print(backtesting_df)
backtesting_df.to_csv(result_path_csv, sep=',', header=True, index=True)
