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
fund1_path = cwd+r"\history_data\fund1.txt"
fund2_path = cwd+r"\history_data\fund2.txt"
fund3_path = cwd+r"\history_data\fund3.txt"
user_type_percent_path = cwd+r"\initial_percent\zengjinbao_v3_for_machine.csv"
result_path_csv = cwd+r"\result\zengjinbao_result.csv"
result_path_html = cwd+r"\result\zengjinbao_result.html"
percent_path_csv = cwd+r"\result\percent_result.csv"
compare_path_csv = cwd+r"\result\zengjinbao_result_compare.csv"
holiday_path = cwd+r"\usefuldata\holidays.csv"
shibor_path = cwd+r"\history_data\Shibor.csv"





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




if __name__ == '__main__':
    test = getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
    print(test)
