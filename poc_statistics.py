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

company_file_names = ["zs_betago", "zs_kmrd"]

startday_str = "2017-07-01"
endday_str = "2017-10-29"
format = "%Y-%m-%d"
strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
datelist = rl.dateRange(startday_str, endday_str)
datelist_possible = list(set(funds_net["date"].values.tolist()))
datelist_possible.sort(key=funds_net["date"].values.tolist().index)
datelist_possible_moneyfund = list(set(funds_profit["date"].values.tolist()))
datelist_possible_moneyfund.sort(key=funds_profit["date"].values.tolist().index)


def poc_sta(datepairs):
    ini_money = users.pop("moneyamount")
    ini_money = ini_money.map(lambda x: float(x) * 10000)
    for company_file in company_file_names:
        user_sta = pd.DataFrame(index=range(0, 100))
        for startday_str_sta, endday_str_sta in datepairs:
            datelist_sta_temp = rl.dateRange(startday_str_sta, endday_str_sta)
            datelist_sta = [w for w in datelist_sta_temp if w.replace("-", "") in datelist_possible]
            company_df1 = pd.read_csv(il.cwd + r"\result\\" + company_file + "_result_nofee.csv")
            company_df = company_df1.ix[:, 1:]
            if startday_str_sta not in company_df.columns:
                company_df.insert(0, startday_str_sta, ini_money)
            # company_df = company_df.reindex(range(1, 101))
            company_result = company_df.T
            company_result_this_period = company_result[company_result.index.isin(datelist_sta)]
            company_result_this_period_shift = company_result_this_period.shift(1)
            profit_detail = (company_result_this_period - company_result_this_period_shift) / company_result_this_period
            result_des = profit_detail.describe().T
            user_sta[startday_str_sta + "-" + endday_str_sta + "-std"] = result_des.pop("std")
            user_sta[startday_str_sta + "-" + endday_str_sta + "-year_rate"] = (
                ((company_result_this_period.iloc[-1] - company_result_this_period.iloc[0]) /
                 company_result_this_period.iloc[0]) / (len(datelist_sta_temp) / 365))
        user_sta.to_csv(il.cwd + r"\result\\" + company_file + "_sta_nofee.csv")
        print(user_sta)


def getUserCombinationByDate(date, user_combination):
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
        return return_dic
    else:
        combination_dates_list.append(date)
        combination_dates_list.sort()
        date_index = combination_dates_list.index(date)
        if date_index == 0:
            return False
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
            return return_dic


def get_user_hold_by_date(date, user_combination, usermoney):
    return_user_hold = {}
    return_buy_money = {}
    left_money = usermoney
    user_combination_date = user_combination[user_combination["date"] == date]
    for index2, row2 in user_combination_date.iterrows():
        # 对该公司对该用户组合在当天日期内的每个配置情况循环买入基金
        fund_ticker = row2["ticker"]
        # 基金编号
        fund_percent = float(row2["percent"])
        # 基金比例
        buymoney = float(usermoney) * float(fund_percent)
        if fund_ticker in funds_net["ticker"].values.tolist():
            if date in datelist_possible:
                exchange_date = date
            else:
                datelist_possible_temp = datelist_possible.copy()
                datelist_possible_temp.append(date)
                datelist_possible_temp.sort()
                date_index = datelist_possible_temp.index(date)
                if date_index + 1 < len(datelist_possible_temp) - 1:
                    exchange_date = datelist_possible_temp[date_index + 1]
                else:
                    exchange_date = "last-day"
            if not exchange_date == "last-day":
                fund_net = rl.getFundsNetNext_byTickerDate(fund_ticker, exchange_date.replace("-", ""),
                                                           funds_net,
                                                           "%Y%m%d")
                return_user_hold[fund_ticker] = buymoney / fund_net
                left_money = left_money - buymoney
                return_buy_money[fund_ticker] = buymoney
        elif fund_ticker in funds_profit["ticker"].values.tolist():
            if date in datelist_possible_moneyfund:
                exchange_date = date
            else:
                datelist_possible_temp = datelist_possible_moneyfund.copy()
                datelist_possible_temp.append(date)
                datelist_possible_temp.sort()
                date_index = datelist_possible_temp.index(date)
                if date_index + 1 < len(datelist_possible_temp) - 1:
                    exchange_date = datelist_possible_temp[date_index + 1]
                else:
                    exchange_date = "last-day"
            if not exchange_date == "last-day":
                fund_profit = rl.getFundsNetNext_byTickerDate(fund_ticker, exchange_date.replace("-", ""),
                                                              funds_profit,
                                                              "%Y%m%d")
                return_user_hold[fund_ticker] = float(fund_profit) * (buymoney / 10000) + buymoney
                left_money = left_money - buymoney
                return_buy_money[fund_ticker] = buymoney
    return return_user_hold, return_buy_money, left_money


def compute_value_by_date(user_funds_hold, buymoney, date):
    return_money = 0
    return_user_holde = user_funds_hold.copy()
    for holdeticker, holdamount in user_funds_hold.items():
        if holdeticker in funds_net["ticker"].values.tolist():
            if date.replace("-", "") in datelist_possible:
                value_date = date
            else:
                datelist_possible_temp = datelist_possible.copy()
                datelist_possible_temp.append(date)
                datelist_possible_temp.sort()
                date_index = datelist_possible_temp.index(date)
                if date_index - 1 > 0:
                    value_date = datelist_possible_temp[date_index - 1]
                else:
                    value_date = "first-day"
            if not value_date == "first-day":
                fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, value_date.replace("-", ""),
                                                           funds_net,
                                                           "%Y%m%d")
                return_money = return_money + fund_net * holdamount
            else:
                return_money = return_money + buymoney[holdeticker]
        elif holdeticker in funds_profit["ticker"].values.tolist():
            if date.replace("-", "") in datelist_possible_moneyfund:
                value_date = date
            else:
                datelist_possible_temp = datelist_possible_moneyfund.copy()
                datelist_possible_temp.append(date)
                datelist_possible_temp.sort()
                date_index = datelist_possible_temp.index(date)
                if date_index - 1 > 0:
                    value_date = datelist_possible_temp[date_index - 1]
                else:
                    value_date = "first-day"
            if not value_date == "first-day":
                fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, value_date.replace("-", ""),
                                                           funds_profit,
                                                           "%Y%m%d")
                return_money = return_money + fund_net * (holdamount / 10000) + holdamount
                return_user_holde[holdeticker] = fund_net * (holdamount / 10000) + holdamount
            else:
                return_money = return_money + buymoney[holdeticker]
    return return_money, return_user_holde


def poc_detail_compute_nofee():
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件,不计算费率和赎回过程中的资金延迟
    '''
    for company_file in company_file_names:
        # 对每一个公司给出的配置情况循环
        company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + company_file + ".csv")
        company_detial = pd.DataFrame()
        time_cost = 0.0
        for index, row in users.iterrows():
            start = time.clock()
            print("计算第" + str(index) + "/" + str(len(users)) + "个用户.")
            # 对每一个用户循环
            userid = row["userid"]
            leftusermoney = usermoney = float(row["moneyamount"]) * 10000
            user_combination = company_df[company_df['userid'] == userid]
            user_funds_hold = {}
            user_marketcap = {}
            buy_money = {}
            last_change_date = ""
            for date in datelist:
                # print("当前回测日期为" + str(date) + ".")
                # 对回测时间段内的每一个日期循环
                if not bool(user_funds_hold):
                    if date in user_combination["date"].values.tolist():
                        user_marketcap[date] = usermoney
                        user_funds_hold, buy_money, leftusermoney = get_user_hold_by_date(date, user_combination,
                                                                                          usermoney)
                    else:
                        user_marketcap[date] = usermoney
                elif date in user_combination["date"].values.tolist():
                    marketcap_date, user_funds_hold = compute_value_by_date(user_funds_hold, buy_money, date.replace("-", ""))
                    user_marketcap[date] = marketcap_date + leftusermoney
                    user_funds_hold, buy_money, leftusermoney = get_user_hold_by_date(date, user_combination,
                                                                                      marketcap_date)
                else:
                    marketcap_date, user_funds_hold = compute_value_by_date(user_funds_hold, buy_money, date.replace("-", ""))
                    user_marketcap[date] = marketcap_date + leftusermoney
            company_detial = company_detial.append(user_marketcap, ignore_index=True)
            elapsed = (time.clock() - start)
            time_cost += elapsed
            print("Time used:", elapsed)
            print("Time Left Estimated:", (time_cost / (int(index) + 1)) * len(users) - time_cost)
        company_detial.to_csv(il.cwd + r"\result\\" + company_file + "_result_nofee.csv")


def poc_detail_compute():
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件
    '''
    for company_file in company_file_names:
        # 对每一个公司给出的配置情况循环
        company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + company_file + ".csv")
        company_detial = pd.DataFrame()
        time_cost = 0.0
        for index, row in users[99:].iterrows():
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
                                fund_net = rl.getFundsNetNext_byTickerDate(fund_ticker, date.replace("-", ""),
                                                                           funds_net,
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
                                        user_funds_hold[fund_ticker] = 0.0
                                    else:
                                        fund_fee_ratio = fund_fee_ratio_df.iloc[0]["buyratio"]
                                        fund_fee_discount_df = zs_funds_discount[
                                            zs_funds_discount['ticker'] == fund_ticker]
                                        fund_fee_discount_df = fund_fee_discount_df[
                                            fund_fee_discount_df["tname"] == "产品申购"]
                                        fund_fee_discount_df = fund_fee_discount_df[
                                            fund_fee_discount_df["ttype"] == "网银"]
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
                                fund_net = rl.getFundsNetNext_byTickerDate(fund_ticker, date.replace("-", ""),
                                                                           funds_profit,
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
                                # 如果该基金是货币基金，则没有手续费
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


if __name__ == '__main__':
    date_pairs = [("2017-07-01", "2017-07-31"), ("2017-08-01", "2017-08-31"), ("2017-09-01", "2017-09-30"),
                  ("2017-10-01", "2017-10-31"), ("2017-07-01", "2017-10-31")]
    poc_sta(date_pairs)
    # poc_detail_compute_nofee()
