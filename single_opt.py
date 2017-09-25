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
fund1 = pd.read_csv(fund1_path).set_index("endDate")
fund2 = pd.read_csv(fund2_path).set_index("endDate")
fund3 = pd.read_csv(fund3_path).set_index("endDate")

startday_str = "2017-01-01"
endday_str = "2017-08-31"
startday = datetime.datetime.strptime(startday_str, '%Y-%m-%d')
endday = datetime.datetime.strptime(endday_str, '%Y-%m-%d')
datelist = rl.dateRange(startday_str, endday_str, step=1, format="%Y-%m-%d")
fund1 = rl.fillFund(datelist, fund1)
fund2 = rl.fillFund(datelist, fund2)
fund3 = rl.fillFund(datelist, fund3)
depsoit_rate_dic = {0: 0.028, 8: 0.033, 16: 0.035, 31: 0.038, 91: 0.039, 181: 0.04, 366: 0.045}
# 活期存款利率
depsoit_current_rate = 0.0035
# 活期存款日万份收益序列计算
profit_rate = rl.getConstantDepsoit(startday_str, endday_str, depsoit_current_rate)
base_yearrate = profit_rate
base_dayprofit = rl.yearrate_to_dayprofit(base_yearrate)

compare = pd.DataFrame()
fundpercent = {"depsoit": 0.2, "fund1": 0.21, "fund2": 0.27, "fund3": 0.32}
fundprofit = {"depsoit": base_dayprofit, "fund1": fund1, "fund2": fund2, "fund3": fund3}
combination = rl.getCombinationProfit(fundpercent, fundprofit,"")
combination_changeby_weekcount_weekday_profitpercent = rl.getCombinationProfit_changeby_weekcount_weekday_profitpercent(
    fundpercent, fundprofit,"")

# 绘制该组合每日波动情况与基本各情况的图示
compare = combination.join(base_dayprofit)
# compare = compare.join(fund1["dailyProfit"])
# compare.rename(columns={"dailyProfit": "基金1"}, inplace=True)
# compare = compare.join(fund2["dailyProfit"])
# compare.rename(columns={"dailyProfit": "基金2"}, inplace=True)
# compare = compare.join(fund3["dailyProfit"])
# compare.rename(columns={"dailyProfit": "基金3"}, inplace=True)
compare.rename(columns={"-combination_profit": "组合理财(固定基金比例)", "depsoit_rate": "浮动存款"}, inplace=True)
compare = compare.join(combination_changeby_weekcount_weekday_profitpercent)
compare.rename(columns={"-combination_profit": "组合理财(按月调整基金比例)"}, inplace=True)
compare.plot(title=u"C5-新客户-男")

# 计算并输出该组合最大回撤
print("组合理财(固定基金比例)最大回撤" + ": " + str(rl.getMaxdown(base_yearrate, combination, startday_str, endday_str)))
print("组合理财(按月调整基金比例)最大回撤" + ": " + str(
    rl.getMaxdown(base_yearrate, combination_changeby_weekcount_weekday_profitpercent, startday_str, endday_str)))
# 计算并输出该组合年化利率
year_rate_outside = rl.year_rate(combination, startday_str, endday_str, "-combination_profit", format="%Y-%m-%d")
print("组合理财(固定基金比例)平均年化利率" + ": " + str(year_rate_outside) + "%")
year_rate_outside = rl.year_rate(combination_changeby_weekcount_weekday_profitpercent, startday_str, endday_str,
                              "-combination_profit", format="%Y-%m-%d")
print("组合理财(按月调整基金比例)平均年化利率" + ": " + str(year_rate_outside) + "%")
plt.show()

