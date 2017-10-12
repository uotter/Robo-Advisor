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
import robolib as rl
import calendar

# 设置绘图中所用的中文字体
mpl.rcParams['font.sans-serif'] = ['simhei']

# read the funds' information from files
fund1_path = r"F:\Code\Robo-Advisor\history_data\fund1.txt"
fund2_path = r"F:\Code\Robo-Advisor\history_data\fund2.txt"
fund3_path = r"F:\Code\Robo-Advisor\history_data\fund3.txt"
user_type_percent_path = r"F:\Code\Robo-Advisor\initial_percent\zengjinbao_v3_for_machine.csv"
result_path_csv = r"F:\Code\Robo-Advisor\result\zengjinbao_result.csv"
result_path_html = r"F:\Code\Robo-Advisor\result\zengjinbao_result.html"
percent_path_csv = r"F:\Code\Robo-Advisor\result\percent_result.csv"
compare_path_csv = r"F:\Code\Robo-Advisor\result\zengjinbao_result_compare.csv"
holiday_path = r"F:\Code\Robo-Advisor\usefuldata\holidays.csv"
shibor_path = r"F:\Code\Robo-Advisor\history_data\Shibor.csv"


def getFunds_Everyday(startday_str, endday_str):
    fund1 = pd.read_csv(fund1_path).set_index("endDate")
    fund2 = pd.read_csv(fund2_path).set_index("endDate")
    fund3 = pd.read_csv(fund3_path).set_index("endDate")
    shibor = pd.read_csv(shibor_path).set_index("date")
    user_type_percent = pd.read_csv(user_type_percent_path)
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
    sort_date_shibor = (rl.fillDepsoit(startday_str, endday_str, shibor, "depsoit_rate")).sort_index()
    sort_date_shibor.loc["2017-01-01", "depsoit_rate"] = 2.589
    sort_date_shibor.loc["2017-01-02", "depsoit_rate"] = 2.589
    base_yearrate = sort_date_shibor
    base_dayprofit = rl.yearrate_to_dayprofit(base_yearrate, "depsoit_rate", "percent")
    year_rate_fund1 = rl.year_rate(fund1, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
    year_rate_fund2 = rl.year_rate(fund2, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
    year_rate_fund3 = rl.year_rate(fund3, startday_str, endday_str, "dailyProfit", format="%Y-%m-%d")
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


if __name__ == '__main__':
    test = getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
    print(test)
