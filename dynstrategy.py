# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import robolib as rl
from pylab import *
import mpt as mpt
import pandas as pd
import iolib as il


def getMW_MaxReturn(funds_input):
    """
        根据马科维茨理论获得最大收益情况下的资产组合
    """
    mpt.funds_daily = funds_input
    mpt.nod = len(funds_input)
    mpt.nof = len(funds_input.columns)
    mpt.funds = rl.getNetWorthFromDailyProfit(funds_input)
    mpt.returns = np.log(mpt.funds / mpt.funds.shift(1))
    optr = mpt.MK_MaxReturn()
    return optr['x']


def getMW_MaxSharp(funds_input):
    """
        根据马科维茨理论获得最大夏普情况下的资产组合
    """
    mpt.funds_daily = funds_input
    mpt.nod = len(funds_input)
    mpt.nof = len(funds_input.columns)
    mpt.funds = rl.getNetWorthFromDailyProfit(funds_input)
    mpt.returns = np.log(mpt.funds / mpt.funds.shift(1))
    optr = mpt.MK_MaxSharp()
    return optr['x']


def getMW_MinVariance(funds_input):
    """
        根据马科维茨理论获得最小方差（风险）情况下的资产组合
    """
    mpt.funds_daily = funds_input
    mpt.nod = len(funds_input)
    mpt.nof = len(funds_input.columns)
    mpt.funds = rl.getNetWorthFromDailyProfit(funds_input)
    mpt.returns = np.log(mpt.funds / mpt.funds.shift(1))
    optr = mpt.MK_MinVariance()
    return optr['x']


def getCombinationProfit_Month_Mk(fundpercent, fundprofit, combinationname, change_weekcount=3, change_weekday=2,
                                  returnexp=0, optgoal="maxsharp"):
    lastindex = fundprofit.index[0]
    comprofit = pd.DataFrame(np.zeros((len(fundprofit.index.tolist()), 1)), index=fundprofit.index.tolist(),
                             columns=[combinationname + "-combination_profit"])
    fundweight = [fundpercent["depsoit"], fundpercent["fund1"], fundpercent["fund2"], fundpercent["fund3"]]
    temp_df = pd.DataFrame([fundweight],
                           columns=["存款比例", "基金1比例", "基金2比例", "基金3比例"])
    percent_detail = temp_df

    fundweightnparr = np.array(fundweight)
    for index, row in fundprofit.iterrows():
        year = int(index[0:4])
        month = int(index[5:7])
        day = int(index[9:])
        # 判断当天的日期是不是当月的第三个周二
        comprofit.loc[index] = np.sum(fundweightnparr * fundprofit.loc[index])
        # 使用下面这种语句方式可以记录每一天的仓位情况
        # percent_detail.loc[index] = fundweightnparr
        if index == rl.get_date_by_year_month_weekcount_weekday(year, month, change_weekcount, change_weekday):
            fundinput = fundprofit[lastindex:index]
            fundinput = fundinput[["fund1", "fund2", "fund3"]]
            if optgoal == "maxsharp":
                fundweighttemp = getMW_MaxSharp(fundinput)
            elif optgoal == "minvariance":
                fundweighttemp = getMW_MinVariance(fundinput)
            else:
                fundweighttemp = getMW_MaxReturn(fundinput)
            fundweighttemp = np.array(fundweighttemp)
            fundweighttemp = fundweighttemp / np.sum(fundweighttemp)
            fundweightnparr[1] = (1 - fundweightnparr[0]) * fundweighttemp[0]
            fundweightnparr[2] = (1 - fundweightnparr[0]) * fundweighttemp[1]
            fundweightnparr[3] = (1 - fundweightnparr[0]) * fundweighttemp[2]
            lastindex = index
            # 使用下面这种方式则只在调仓时记录数据
            temp_df = pd.DataFrame([fundweightnparr],
                                   columns=["存款比例", "基金1比例", "基金2比例", "基金3比例"])
            if percent_detail.empty:
                percent_detail = temp_df
            else:
                percent_detail = pd.concat([percent_detail, temp_df])
    return comprofit, percent_detail


if __name__ == '__main__':
    user_type_str_mw = "test"
    funds_daily_df = il.getFunds_Everyday(startday_str="2017-01-01", endday_str="2017-08-31")
    fundpercent = {"depsoit": 0.25, "fund1": 0.25, "fund2": 0.25, "fund3": 0.25}
    # 根据马科维茨最优化理论进行调仓
    combination_mw, percent_detail = getCombinationProfit_Month_Mk(fundpercent, funds_daily_df, user_type_str_mw)
    print(combination_mw)
    print(percent_detail)
