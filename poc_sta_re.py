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

startday_str = "2017-07-01"
endday_str = "2017-10-29"
format = "%Y-%m-%d"
strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
datelist = rl.dateRange(startday_str, endday_str)
datelist_possible = list(set(funds_net["date"].values.tolist()))
datelist_possible.sort(key=funds_net["date"].values.tolist().index)
datelist_possible_moneyfund = list(set(funds_profit["date"].values.tolist()))
datelist_possible_moneyfund.sort(key=funds_profit["date"].values.tolist().index)


def getMoneyFund_Net(startdate, enddate, ticker):
    datelist_mondyfund = rl.dateRange(startdate, enddate)
    money_fund_profit = funds_profit[funds_profit["ticker"] == ticker]
    total_earn = 0
    for date in datelist_mondyfund:
        if date.replace("-", "") in money_fund_profit["date"].values.tolist():
            total_earn = total_earn + float(
                money_fund_profit[money_fund_profit["date"] == date.replace("-", "")].iloc[0]["net"])
    return 1 + total_earn / 10000


def poc_bs_detail_compute(company_file_names_poc, poctype, users_inside):
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件
    '''
    for company_file in company_file_names_poc:
        # 对每一个公司给出的配置情况循环
        company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + company_file + ".csv")
        company_detial = pd.DataFrame()
        company_detial_net = pd.DataFrame()
        funds_not_include = []
        funds_no_netdata = []
        time_cost = 0.0
        for index, row in users_inside.iterrows():
            start = time.clock()
            print("计算第" + str(index) + "/" + str(len(users)) + "个用户.")
            # 对每一个用户循环
            userid = row["userid"]
            leftusermoney = usermoney = float(row["moneyamount"]) * 10000
            user_combination = company_df[company_df['userid'] == userid]
            user_funds_hold = {}
            user_funds_percent = {}
            user_marketcap = {}
            user_net = {}
            last_change_date = ""
            last_market_value = 0
            for date in datelist:
                # print("当前回测日期为" + str(date) + ".")
                # 对回测时间段内的每一个日期循环
                user_combination_date = user_combination[user_combination["date"] == date]
                if not bool(user_funds_hold):
                    if date not in user_combination["date"].values.tolist():
                        pass
                    else:
                        net_temp = 0.0
                        fund_fee_total = 0.0
                        for index2, row2 in user_combination_date.iterrows():
                            # 对该公司对该用户组合在当天日期内的每个配置情况循环买入基金
                            fund_ticker = row2["ticker"]
                            # 基金编号
                            fund_percent = float(row2["percent"])
                            # 基金比例
                            user_funds_percent[fund_ticker] = fund_percent
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
                                    user_funds_hold[fund_ticker] = (float(usermoney) * float(
                                        fund_percent)) / fund_net
                                    # 计算买入基金的数量
                                    fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == fund_ticker]
                                    if poctype == "bs":
                                        # 如果计算的为博时基金的情况
                                        fund_fee_ratio = 0.012
                                        fund_fee_base = float(usermoney) * fund_percent
                                        discount = 0.4
                                        fund_fee = fund_fee_base * discount * fund_fee_ratio
                                        leftusermoney = leftusermoney - (float(usermoney) * fund_percent) - fund_fee
                                        fund_fee_total = fund_fee_total + fund_fee
                                    elif poctype == "bs_nofee" or poctype == "zs_nofee":
                                        # 如果计算的是不计费率的情况
                                        leftusermoney = leftusermoney - (float(usermoney) * fund_percent)
                                    else:
                                        if fund_fee_ratio_df.empty:
                                            # 找不到费率，说明这个基金不在我行的代销列表中
                                            user_funds_hold[fund_ticker] = 0.0
                                            funds_not_include.append(fund_ticker)
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
                                                    fund_fee = fund_fee + (
                                                                              fund_fee_base - tmin) * discount * fund_fee_ratio
                                                    break
                                                else:
                                                    fund_fee = fund_fee + (tmax - tmin) * discount * fund_fee_ratio
                                            # 以上为计算买入的申购费用
                                            leftusermoney = leftusermoney - (float(usermoney) * fund_percent) - fund_fee
                                            # 从剩余的现金中减去申购手续费和基金费用
                                            fund_fee_total = fund_fee_total + fund_fee
                                    net_temp = net_temp + fund_net * fund_percent
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
                                    moneyfund_net = getMoneyFund_Net(startday_str, date, fund_ticker)
                                    net_temp = net_temp + fund_percent * moneyfund_net
                            else:
                                funds_no_netdata.append(fund_ticker)
                        if date.replace("-", "") not in datelist_possible:
                            pass
                        else:
                            user_marketcap[date] = usermoney - fund_fee_total
                            last_market_value = usermoney - fund_fee_total
                            if fund_net > 0:
                                user_net[date] = net_temp
                else:
                    if date not in user_combination["date"].values.tolist():
                        if date.replace("-", "") not in datelist_possible:
                            # 非交易日跳过
                            pass
                        else:
                            # 交易日，根据持仓计算
                            user_marketcap_value = 0.0
                            net_temp = 0.0
                            user_funds_hold_temp = {}
                            for holdeticker, holdamount in user_funds_hold.items():
                                if holdeticker in funds_net["ticker"].values.tolist():
                                    # 如果该基金为开放式公募基金，非货币基金
                                    hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker,
                                                                                      date.replace("-", ""),
                                                                                      funds_net, "%Y%m%d")
                                    if hold_fund_net == 0.0:
                                        hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker,
                                                                                        date.replace("-", ""),
                                                                                        funds_net, "%Y%m%d")
                                    fund_marketcap = holdamount * hold_fund_net
                                    net_temp = net_temp + fund_net * user_funds_percent[holdeticker]
                                elif holdeticker in funds_profit["ticker"].values.tolist():
                                    # 如果该基金是货币基金
                                    hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker,
                                                                                      date.replace("-", ""),
                                                                                      funds_profit, "%Y%m%d")
                                    if hold_fund_net == 0.0:
                                        hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker,
                                                                                        date.replace("-", ""),
                                                                                        funds_net, "%Y%m%d")
                                    fund_marketcap = holdamount + (holdamount / 10000) * hold_fund_net
                                    moneyfund_net = getMoneyFund_Net(startday_str, date, holdeticker)
                                    net_temp = net_temp + moneyfund_net * user_funds_percent[holdeticker]
                                    user_funds_hold_temp[holdeticker] = fund_marketcap
                                    # 新建一个货币基金编号和市值的临时字典保存更新后的货币基金持有市值
                                else:
                                    funds_no_netdata.append(fund_ticker)
                                user_marketcap_value = user_marketcap_value + fund_marketcap
                            for moneyfundticker, moneyfundamount in user_funds_hold_temp.items():
                                if moneyfundticker in user_funds_hold.keys():
                                    user_funds_hold[moneyfundticker] = moneyfundamount
                                    # 以上for循环更新user_funds_hold中持有货币基金的市值
                            user_marketcap[date] = user_marketcap_value + leftusermoney
                            last_market_value = user_marketcap_value + leftusermoney
                            if fund_net > 0:
                                user_net[date] = net_temp
                    else:
                        user_marketcap_value = 0.0
                        for holdeticker, holdamount in user_funds_hold.items():
                            if holdeticker in funds_net["ticker"].values.tolist():
                                # 如果该基金为开放式公募基金，非货币基金
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_net,
                                                                                "%Y%m%d")
                                if hold_fund_net == 0:
                                    hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker,
                                                                                      date.replace("-", ""),
                                                                                      funds_net, "%Y%m%d")
                                fund_marketcap = float(holdamount) * float(hold_fund_net)
                                if poctype == "bs_nofee" or poctype == "zs_nofee":
                                    pass
                                else:
                                    fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == holdeticker]
                                    if fund_fee_ratio_df.empty:
                                        # 找不到费率，说明这个基金不在我行的代销列表中
                                        funds_not_include.append(holdeticker)
                                    else:
                                        fund_fee_ratio = fund_fee_ratio_df.iloc[0]["sellratio"]
                                        fund_fee = float(fund_fee_ratio) * float(fund_marketcap)
                                        # 计算基金赎回费用
                                        fund_marketcap = fund_marketcap - fund_fee
                            elif holdeticker in funds_profit["ticker"].values.tolist():
                                # 如果该基金是货币基金，则没有手续费，直接计算市值
                                hold_fund_net = rl.getFundsNetNext_byTickerDate(holdeticker, date.replace("-", ""),
                                                                                funds_profit,
                                                                                "%Y%m%d")
                                if hold_fund_net == 0:
                                    hold_fund_net = rl.getFundsNetBefore_byTickerDate(holdeticker,
                                                                                      date.replace("-", ""),
                                                                                      funds_net, "%Y%m%d")
                                fund_marketcap = holdamount + (holdamount / 10000) * hold_fund_net
                            else:
                                funds_no_netdata.append(fund_ticker)
                            user_marketcap_value = user_marketcap_value + fund_marketcap
                        user_funds_hold.clear()
                        leftusermoney = usermoney = user_marketcap_value + leftusermoney
                        # 以上为卖出基金，以下为买入基金
                        fund_fee_total = 0.0
                        net_temp = 0.0
                        for index2, row2 in user_combination_date.iterrows():
                            # 对该公司对该用户组合在当天日期内的每个配置情况循环买入基金
                            fund_ticker = row2["ticker"]
                            # 基金编号
                            fund_percent = float(row2["percent"])
                            # 基金比例
                            user_funds_percent[fund_ticker] = fund_percent
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
                                    user_funds_hold[fund_ticker] = (float(usermoney) * float(
                                        fund_percent)) / fund_net
                                    # 计算买入基金的数量
                                    fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == fund_ticker]
                                    if poctype == "bs":
                                        # 如果计算的为博时基金的情况
                                        fund_fee_ratio = 0.012
                                        fund_fee_base = float(usermoney) * fund_percent
                                        discount = 0.4
                                        fund_fee = fund_fee_base * discount * fund_fee_ratio
                                        leftusermoney = leftusermoney - (float(usermoney) * fund_percent) - fund_fee
                                        fund_fee_total = fund_fee_total + fund_fee
                                    elif poctype == "bs_nofee" or poctype == "zs_nofee":
                                        # 如果计算的是不计费率的情况
                                        leftusermoney = leftusermoney - (float(usermoney) * fund_percent)
                                    else:
                                        if fund_fee_ratio_df.empty:
                                            # 找不到费率，说明这个基金不在我行的代销列表中
                                            user_funds_hold[fund_ticker] = 0.0
                                            funds_not_include.append(fund_ticker)
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
                                                    fund_fee = fund_fee + (
                                                                              fund_fee_base - tmin) * discount * fund_fee_ratio
                                                    break
                                                else:
                                                    fund_fee = fund_fee + (tmax - tmin) * discount * fund_fee_ratio
                                            # 以上为计算买入的申购费用
                                            leftusermoney = leftusermoney - (
                                                float(usermoney) * fund_percent) - fund_fee
                                            # 从剩余的现金中减去申购手续费和基金费用
                                            fund_fee_total = fund_fee_total + fund_fee
                                    net_temp = net_temp + fund_net * fund_percent
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
                                    moneyfund_net = getMoneyFund_Net(startday_str, date, fund_ticker)
                                    net_temp = net_temp + fund_percent * moneyfund_net
                            else:
                                funds_no_netdata.append(fund_ticker)
                        if date.replace("-", "") not in datelist_possible:
                            # 非交易日跳过
                            pass
                        else:
                            user_marketcap[date] = usermoney - fund_fee_total
                            last_market_value = usermoney - fund_fee_total
                            if fund_net > 0:
                                user_net[date] = net_temp
            company_detial = company_detial.append(user_marketcap, ignore_index=True)
            company_detial_net = company_detial_net.append(user_net, ignore_index=True)
            elapsed = (time.clock() - start)
            time_cost += elapsed
            print("Time used:", elapsed)
            print("Time Left Estimated:", (time_cost / (int(index) + 1)) * len(users_inside) - time_cost)
        company_detial.to_csv(il.cwd + r"\result\\" + company_file + "_result_" + poctype + ".csv")
        print("File saved:", il.cwd + r"\result\\" + company_file + "_result_" + poctype + ".csv")
        company_detial_net.to_csv(il.cwd + r"\result\\" + company_file + "_result_net_" + poctype + ".csv")
        print("File saved:", il.cwd + r"\result\\" + company_file + "_result_net_" + poctype + ".csv")
        file = open(il.cwd + r"\result\\" + company_file + "_funds_reg_" + poctype + ".txt", 'w')
        file.write("funds_not_include" + '\r\n')
        file.write(str(set(funds_not_include)) + '\r\n')
        file.write("funds_no_netdata" + '\r\n')
        file.write(str(set(funds_no_netdata)) + '\r\n')
        file.close()
        print("File saved:", il.cwd + r"\result\\" + company_file + "_funds_reg_" + poctype + ".csv")


if __name__ == '__main__':
    poctype_out = "zs"
    company_file_names_poc = ["zs_xj"]
    poc_bs_detail_compute(company_file_names_poc, poctype_out, users[:9])
