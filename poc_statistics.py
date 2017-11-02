# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:42:12 2017

@author: wangm
"""
import numpy as np
import robolib as rl
from pylab import *
import pandas as pd
import iolib as il
import time as time

zs_funds_fee = il.getZS_Funds_Fee()
zs_funds_discount = il.getZS_Funds_discount()
zs_funds_tdays = il.getZS_Funds_tdays()
users = il.getZS_users()

funds_net = il.getFunds_Net()
funds_profit = il.getFunds_Profit()

company_file_names = ["zs_kmrd"]

startday_str = "2017-07-01"
endday_str = "2017-10-29"
format = "%Y-%m-%d"
strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
datelist = rl.dateRange(startday_str, endday_str)
datelist_possible = list(set(funds_net["date"].values.tolist()))
datelist_possible.sort(key=funds_net["date"].values.tolist().index)

for company_file in company_file_names:
    # 对每一个公司给出的配置情况循环
    company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + company_file + ".csv")
    company_detial = pd.DataFrame()
    time_cost = 0.0
    for index, row in users[6:20].iterrows():
        start = time.clock()
        print("计算第" + str(index) + "/" + str(len(users)) + "个用户.")
        # 对每一个用户循环
        userid = row["userid"]
        leftusermoney = usermoney = float(row["moneyamount"]) * 10000
        user_combination = company_df[company_df['userid'] == userid]
        user_funds_hold = {}
        user_marketcap = {}
        last_change_date = ""
        for date in datelist:
            # print("当前回测日期为" + str(date) + ".")
            # 对回测时间段内的每一个日期循环
            if last_change_date == "":
                date_in_bool = date in user_combination["date"].values.tolist()
            else:
                date_in_bool = True
            # 如果之前有过调仓，则last_change_date不为空，此时认为date in user_combination["date"].values.tolist()为真
            # 因为需要进入第二个if内部执行买入操作
            if not date_in_bool and not bool(user_funds_hold):
                # 如果公司给出的组合中不包含这一日期的数据并且目前该用户的组合持仓为空，则当天用户空仓，资金不变
                if date.replace("-", "") not in datelist_possible:
                    pass
                else:
                    if last_change_date == "":
                        user_marketcap[date] = usermoney
            elif date_in_bool and not bool(user_funds_hold):
                # 如果公司给出的组合中包含这一日期的数据（或者之前有过调仓的要求）并且目前该用户的组合持仓为空，则要买入公司给出组合的基金
                buy_flag = True
                if last_change_date == "":
                    user_combination_date = user_combination[user_combination["date"] == date]
                    buy_flag = True
                elif int((strptime(date, format) - strptime(last_change_date, format)).days) > 2:
                    user_combination_date = user_combination[user_combination["date"] == last_change_date]
                    buy_flag = True
                else:
                    buy_flag = False
                if buy_flag:
                    for index2, row2 in user_combination_date.iterrows():
                        # 对该公司对该用户组合在当天日期内的每个配置情况循环买入基金
                        fund_ticker = row2["ticker"]
                        # 基金编号
                        fund_percent = float(row2["percent"])
                        # 基金比例
                        fund_net = 0.0
                        # 基金净值
                        if fund_ticker in funds_net["ticker"].values.tolist():
                            # 如果该基金为开放式公募基金，非货币基金
                            fund_net = rl.getFundsNetNext_byTickerDate(fund_ticker, date.replace("-", ""), funds_net,
                                                                       "%Y%m%d")
                            if fund_net == 0.0:
                                # 如果返回基金净值为0，证明当前日期以及当前日期之后没有基金净值数据，则作为该基金持有量为0处理
                                user_funds_hold[fund_ticker] = 0.0
                            else:
                                # 如果返回基金净值不为0，则可以按照返回的基金净值进行基金买入
                                user_funds_hold[fund_ticker] = (float(usermoney) * float(fund_percent)) / fund_net
                                # 计算买入基金的数量
                                fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == fund_ticker]
                                if fund_fee_ratio_df.empty:
                                    # 找不到费率，说明这个基金不在我行的代销列表中
                                    user_funds_hold[fund_ticker]=0.0
                                else:
                                    fund_fee_ratio = fund_fee_ratio_df.iloc[0]["buyratio"]
                                    fund_fee_discount_df = zs_funds_discount[zs_funds_discount['ticker'] == fund_ticker]
                                    fund_fee_discount_df = fund_fee_discount_df[fund_fee_discount_df["tname"] == "产品申购"]
                                    fund_fee_discount_df = fund_fee_discount_df[fund_fee_discount_df["ttype"] == "网银"]
                                    fund_fee_base = float(usermoney) * fund_percent
                                    fund_fee = 0
                                    for index3, row3 in fund_fee_discount_df.iterrows():
                                        tmin = float(row3["tmin"])
                                        tmax = float(row3["tmax"])
                                        discount = float(row3["discount"])
                                        if fund_fee_base < tmax:
                                            fund_fee = fund_fee + (fund_fee_base - tmin) * discount * fund_fee_ratio
                                            break
                                        else:
                                            fund_fee = fund_fee + (tmax - tmin) * discount * fund_fee_ratio
                                    # 以上为计算买入的申购费用
                                    leftusermoney = leftusermoney - (float(usermoney) * fund_percent) - fund_fee
                                    # 从剩余的现金中减去申购手续费和基金费用
                        elif fund_ticker in funds_profit["ticker"].values.tolist():
                            # 如果该基金是货币基金，则没有手续费，直接记录初次买入的金额
                            fund_net = rl.getFundsNetNext_byTickerDate(fund_ticker, date.replace("-", ""), funds_profit,
                                                                       "%Y%m%d")
                            if fund_net == 0:
                                user_funds_hold[fund_ticker] = 0
                            else:
                                user_funds_hold[fund_ticker] = float(usermoney) * float(fund_percent)
                                # 记录买入金额
                                leftusermoney = leftusermoney - (float(usermoney) * float(fund_percent))
                                # 从剩余现金中减去买货币基金所花费的数额
                        else:
                            pass
                if date.replace("-", "") not in datelist_possible:
                    # 如果当天不是交易日，直接跳过
                    pass
                else:
                    # 如果当天是交易日，则因为买入有时间差，当天的用户持有基金市值仍为用户未购买前的现金总额
                    user_marketcap[date] = float(usermoney)
            elif not date_in_bool and bool(user_funds_hold):
                # 如果该日期不在公司提供的用户组合中，但是用户已有持仓，则为未调仓情况下计算当天收益
                if date.replace("-", "") not in datelist_possible:
                    # 如果当天不是交易日，直接跳过
                    pass
                else:
                    hold_fund_net = 0.0
                    user_marketcap_value = 0.0
                    user_funds_hold_temp = {}
                    for holdeticker, holdamount in user_funds_hold.items():
                        if holdeticker in funds_net["ticker"].values.tolist():
                            # 如果该基金为开放式公募基金，非货币基金
                            hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker, date.replace("-", ""),
                                                                              funds_net, "%Y%m%d")
                            if hold_fund_net == 0.0:
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_net, "%Y%m%d")
                            fund_marketcap = holdamount * hold_fund_net
                        elif fund_ticker in funds_profit["ticker"].values.tolist():
                            # 如果该基金是货币基金，则没有手续费，直接记录初次买入的金额
                            hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker, date.replace("-", ""),
                                                                              funds_profit, "%Y%m%d")
                            if hold_fund_net == 0.0:
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_net, "%Y%m%d")
                            fund_marketcap = holdamount + (holdamount / 10000) * hold_fund_net
                            user_funds_hold_temp[holdeticker] = fund_marketcap
                            # 新建一个货币基金编号和市值的临时字典保存更新后的货币基金持有市值
                        user_marketcap_value = user_marketcap_value + fund_marketcap
                    user_marketcap[date] = user_marketcap_value + leftusermoney
                    for moneyfundticker, moneyfundamount in user_funds_hold_temp.items():
                        if moneyfundticker in user_funds_hold.keys():
                            user_funds_hold[moneyfundticker] = moneyfundamount
                            # 以上for循环更新user_funds_hold中持有货币基金的市值
            elif date_in_bool and bool(user_funds_hold):
                # 如果该日期在公司提供的用户组合中，但是用户已有持仓，则说明当天要调仓
                if date.replace("-", "") not in datelist_possible:
                    # 如果当天不是交易日，直接跳过
                    pass
                else:
                    user_marketcap_value = 0.0
                    for holdeticker, holdamount in user_funds_hold.items():
                        if holdeticker in funds_net["ticker"].values.tolist():
                            # 如果该基金为开放式公募基金，非货币基金
                            hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker, date.replace("-", ""),
                                                                              funds_net,
                                                                              "%Y%m%d")
                            if hold_fund_net == 0:
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_net, "%Y%m%d")
                            fund_marketcap = float(holdamount) * float(hold_fund_net)
                            fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == holdeticker]
                            if fund_fee_ratio_df.empty:
                                # 找不到费率，说明这个基金不在我行的代销列表中
                                pass
                            else:
                                fund_fee_ratio = fund_fee_ratio_df.iloc[0]["sellratio"]
                                fund_fee = float(fund_fee_ratio) * float(fund_marketcap)
                                # 计算基金赎回费用
                                fund_marketcap = fund_marketcap - fund_fee
                        elif fund_ticker in funds_profit["ticker"].values.tolist():
                            # 如果该基金是货币基金，则没有手续费，直接记录初次买入的金额
                            hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker, date.replace("-", ""),
                                                                              funds_profit,
                                                                              "%Y%m%d")
                            if hold_fund_net == 0:
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_net, "%Y%m%d")
                            fund_marketcap = holdamount + (holdamount / 10000) * hold_fund_net
                            user_funds_hold_temp[holdeticker] = fund_marketcap
                            # 新建一个货币基金编号和市值的临时字典保存更新后的货币基金持有市值
                        user_marketcap_value = user_marketcap_value + fund_marketcap
                    user_marketcap[date] = user_marketcap_value + leftusermoney
                    leftusermoney = usermoney = float(user_marketcap[date])
                    last_change_date = date
                    user_funds_hold.clear()
        company_detial = company_detial.append(user_marketcap, ignore_index=True)
        elapsed = (time.clock() - start)
        time_cost += elapsed
        print("Time used:", elapsed)
        print("Time Left Estimated:", (time_cost / (int(index) + 1)) * len(users) - time_cost)
        company_detial.to_csv(il.cwd + r"\result\\" + company_file + "_result.csv")
