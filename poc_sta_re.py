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
# funds_net_total = il.getFunds_Net_Total()
# funds_net = funds_net_total[["ticker", "date","net_total"]]
# funds_net.columns = ["ticker", "date", "net"]
funds_profit = il.getFunds_Profit()

startday_str = "2017-07-01"
endday_str = "2017-10-29"
format = "%Y-%m-%d"
strptime, strftime = datetime.datetime.strptime, datetime.datetime.strftime
datelist_inside = rl.dateRange_endinclude(startday_str, endday_str)
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


def poc_sta_combine(startday_str_sta, endday_str_sta, poctype, company_file_names_sta, symbolstr):
    '''
        计算不同厂家给出的配置计算收益率和标准差明细
    '''
    user_poc_sta = users.copy()
    ini_money = user_poc_sta.pop("moneyamount")
    ini_money = ini_money.map(lambda x: float(x) * 10000)
    user_sta = pd.DataFrame(index=range(0, 100))
    for company_file in company_file_names_sta:
        datelist_sta_temp = rl.dateRange(startday_str_sta, endday_str_sta)
        datelist_sta = [w for w in datelist_sta_temp if w.replace("-", "") in datelist_possible]
        filenames = ["", "nofee_"]
        for filename in filenames:
            company_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_result_combine_" + filename + poctype + ".csv")
            company_df = company_df1.ix[:, 1:]
            if startday_str_sta not in company_df.columns:
                company_df.insert(0, startday_str_sta, ini_money)
            # company_df = company_df.reindex(range(1, 101))
            company_result = company_df.T
            company_result_this_period = company_result[company_result.index.isin(datelist_sta_temp)]
            company_result_this_period_shift = company_result_this_period.shift(1)
            profit_detail_bizhi = company_result_this_period / company_result_this_period_shift
            result_des_bizhi = profit_detail_bizhi.describe().T
            user_sta[filename + company_file + "_std_total"] = result_des_bizhi.pop("std") * np.sqrt(250)
            user_sta[filename + company_file + "_year_rate"] = (
                    ((company_result_this_period.iloc[-1] - company_result_this_period.iloc[0]) /
                     company_result_this_period.iloc[0]) / (len(datelist_sta_temp) / 365))
            # 以下计算最大回撤
            maxdown_user_dic = {}
            iloc_index = 0
            time_cost = 0
            for index, row in company_df.T.iterrows():
                if (iloc_index + 1) < len(company_df.T):
                    iloc_index += 1
                    start = time.clock()
                    left_df = company_df.T.iloc[iloc_index:]
                    left_df_describe = left_df.describe()
                    left_se_max = left_df_describe.T["min"]
                    down_se = (row - left_se_max) / row
                    if not bool(maxdown_user_dic):
                        maxdown_user_dic = {w: down_se[w] for w in down_se.index}
                    else:
                        maxdown_user_dic = {w: down_se[w] if down_se[w] > maxdown_user_dic[w] else maxdown_user_dic[w]
                                            for w
                                            in down_se.index}
                    elapsed = (time.clock() - start)
                    time_cost += elapsed
                    if iloc_index % 10 == 0:
                        print(filename + company_file + " Max Down Time used:", elapsed)
                        print(filename + company_file + " Max Down Time Left Estimated:",
                              (time_cost / (int(iloc_index))) * len(company_df.T) - time_cost)
            maxdown_user_dic_positive = {w: maxdown_user_dic[w] if maxdown_user_dic[w] > 0 else 0 for w
                                         in maxdown_user_dic.keys()}
            company_maxdown_detial = pd.Series(maxdown_user_dic_positive)
            user_sta[filename + company_file + "_maxdown"] = company_maxdown_detial
    user_sta.to_csv(
        il.cwd + r"\result\\" + startday_str_sta + "_" + endday_str_sta + "_sta_combine_" + poctype + ".csv")
    print("File saved:",
          il.cwd + r"\result\\" + startday_str_sta + "_" + endday_str_sta + "_sta_combine_" + poctype + ".csv")
    print(user_sta)


def sell_funds_combine(date, user_funds_hold, user_funds_hold_nofee, user_funds_percent):
    user_marketcap_value_nofee = user_marketcap_value = 0.0
    funds_not_include = []
    funds_no_netdata = []
    net_temp = 0.0
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
            fund_marketcap_nofee = float(user_funds_hold_nofee[holdeticker]) * float(hold_fund_net)
            fund_fee_ratio_df = zs_funds_fee[zs_funds_fee['ticker'] == holdeticker]
            if fund_fee_ratio_df.empty:
                # 找不到费率，说明这个基金不在我行的代销列表中
                funds_not_include.append(holdeticker)
            else:
                fund_fee_ratio = fund_fee_ratio_df.iloc[0]["sellratio"]
                fund_fee = float(fund_fee_ratio) * float(fund_marketcap)
                # 计算基金赎回费用
                fund_marketcap = fund_marketcap - fund_fee
            net_temp = net_temp + hold_fund_net * user_funds_percent[holdeticker]
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
            fund_marketcap_nofee = user_funds_hold_nofee[holdeticker] + (user_funds_hold_nofee[
                                                                             holdeticker] / 10000) * hold_fund_net
            moneyfund_net = getMoneyFund_Net(startday_str, date, holdeticker)
            net_temp = net_temp + moneyfund_net * user_funds_percent[holdeticker]
        else:
            funds_no_netdata.append(holdeticker)
        user_marketcap_value = user_marketcap_value + fund_marketcap
        user_marketcap_value_nofee = user_marketcap_value_nofee + fund_marketcap_nofee
    return user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include, funds_no_netdata


def compute_funds(date, user_funds_hold, user_funds_hold_nofee, user_funds_percent):
    user_marketcap_value_nofee = user_marketcap_value = 0.0
    funds_not_include = []
    funds_no_netdata = []
    user_funds_hold_temp = {}
    user_funds_hold_temp_nofee = {}
    net_temp = 0.0
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
            fund_marketcap_nofee = float(user_funds_hold_nofee[holdeticker]) * hold_fund_net
            net_temp = net_temp + hold_fund_net * user_funds_percent[holdeticker]
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
            fund_marketcap_nofee = float(user_funds_hold_nofee[holdeticker]) + (float(
                user_funds_hold_nofee[holdeticker]) / 10000) * hold_fund_net
            moneyfund_net = getMoneyFund_Net(startday_str, date, holdeticker)
            net_temp = net_temp + moneyfund_net * user_funds_percent[holdeticker]
            user_funds_hold_temp[holdeticker] = fund_marketcap
            user_funds_hold_temp_nofee[holdeticker] = fund_marketcap_nofee
            # 新建一个货币基金编号和市值的临时字典保存更新后的货币基金持有市值
        else:
            funds_no_netdata.append(holdeticker)
        user_marketcap_value = user_marketcap_value + fund_marketcap
        user_marketcap_value_nofee = user_marketcap_value_nofee + fund_marketcap_nofee
    for moneyfundticker, moneyfundamount in user_funds_hold_temp.items():
        if moneyfundticker in user_funds_hold.keys():
            user_funds_hold[moneyfundticker] = moneyfundamount
            # 以上for循环更新user_funds_hold中持有货币基金的市值
    for moneyfundticker, moneyfundamount in user_funds_hold_temp_nofee.items():
        if moneyfundticker in user_funds_hold_nofee.keys():
            user_funds_hold_nofee[moneyfundticker] = moneyfundamount
            # 以上for循环更新user_funds_hold中持有货币基金的市值
    return user_funds_hold, user_funds_hold_nofee, user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include, funds_no_netdata


def buy_funds_combine(user_combination_date, date, usermoney, usermoney_nofee, poctype):
    user_funds_percent = {}
    user_funds_hold = {}
    user_funds_hold_nofee = {}
    funds_not_include = []
    funds_no_netdata = []
    net_temp = 0.0
    fund_fee_total = 0.0
    leftusermoney = usermoney
    leftusermoney_nofee = usermoney_nofee
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
                user_funds_hold[fund_ticker] = (float(usermoney) * float(fund_percent)) / fund_net
                user_funds_hold_nofee[fund_ticker] = (float(usermoney_nofee) * float(fund_percent)) / fund_net
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
                    leftusermoney_nofee = leftusermoney_nofee - (float(usermoney_nofee) * fund_percent)
                else:
                    if fund_fee_ratio_df.empty:
                        # 找不到费率，说明这个基金不在我行的代销列表中
                        user_funds_hold[fund_ticker] = 0.0
                        user_funds_hold_nofee[fund_ticker] = 0.0
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
                                fund_fee = fund_fee + (fund_fee_base - tmin) * discount * fund_fee_ratio
                                break
                            else:
                                fund_fee = fund_fee + (tmax - tmin) * discount * fund_fee_ratio
                        # 以上为计算买入的申购费用
                        leftusermoney = leftusermoney - (float(usermoney) * fund_percent) - fund_fee
                        # 从剩余的现金中减去申购手续费和基金费用
                        leftusermoney_nofee = leftusermoney_nofee - (float(usermoney_nofee) * fund_percent)
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
                user_funds_hold_nofee[fund_ticker] = float(usermoney_nofee) * float(fund_percent)
                # 记录买入金额
                leftusermoney = leftusermoney - (float(usermoney) * float(fund_percent))
                # 从剩余现金中减去买货币基金所花费的数额
                leftusermoney_nofee = leftusermoney_nofee - (float(usermoney_nofee) * float(fund_percent))
                moneyfund_net = getMoneyFund_Net(startday_str, date, fund_ticker)
                net_temp = net_temp + fund_percent * moneyfund_net
        else:
            funds_no_netdata.append(fund_ticker)
    return user_funds_hold, user_funds_hold_nofee, leftusermoney, leftusermoney_nofee, user_funds_percent, net_temp, fund_fee_total, funds_not_include, funds_no_netdata


def poc_detail_compute_combine(company_file_names_poc, poctype, users_inside, symbolstr, datelist_inside):
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件
    '''
    for company_file in company_file_names_poc:
        # 对每一个公司给出的配置情况循环
        try:
            company_df = il.getZS_Company_combination(
                il.cwd + r"\history_data\\" + poctype + "_" + company_file + ".csv")
        except:
            company_df = il.getZS_Company_combination_by_excel(
                il.cwd + r"\result\\" + poctype + "_" + company_file + ".xls")
        company_detial = pd.DataFrame()
        company_detial_nofee = pd.DataFrame()
        company_detial_net = pd.DataFrame()
        funds_not_include = []
        funds_no_netdata = []
        time_cost = 0.0
        count = 0
        for index, row in users_inside.iterrows():
            count += 1
            start = time.clock()
            print("计算第" + str(count) + "/" + str(len(users_inside)) + "个用户.")
            # 对每一个用户循环
            userid = row["userid"]
            leftusermoney_nofee = usermoney_nofee = leftusermoney = usermoney = float(row["moneyamount"]) * 10000
            user_combination = company_df[company_df['userid'] == userid]
            user_funds_hold = {}
            user_funds_hold_nofee = {}
            user_funds_percent = {}
            user_marketcap = {}
            user_marketcap_nofee = {}
            user_net = {}
            last_change_date = ""
            last_market_value = 0
            for date in datelist_inside:
                # print("当前回测日期为" + str(date) + ".")
                # 对回测时间段内的每一个日期循环
                user_combination_date = user_combination[user_combination["date"] == date]
                if not bool(user_funds_hold):
                    # 如果用户持仓情况为空仓，则买入基金
                    if date not in user_combination["date"].values.tolist():
                        pass
                    else:
                        user_funds_hold, user_funds_hold_nofee, leftusermoney, leftusermoney_nofee, user_funds_percent, net_temp, fund_fee_total, funds_not_include_temp, funds_no_netdata_temp = buy_funds_combine(
                            user_combination_date, date, usermoney, usermoney_nofee, poctype)
                        funds_not_include.extend(funds_not_include_temp)
                        funds_no_netdata.extend(funds_no_netdata_temp)
                        if date.replace("-", "") not in datelist_possible:
                            pass
                        else:
                            user_marketcap[date] = usermoney - fund_fee_total
                            user_marketcap_nofee[date] = usermoney_nofee
                            last_market_value = usermoney - fund_fee_total
                            if net_temp > 0:
                                user_net[date] = net_temp
                else:
                    # 如果用户已有持仓，则根据组合查看是否调仓
                    if date not in user_combination["date"].values.tolist():
                        if date.replace("-", "") not in datelist_possible:
                            # 非交易日跳过
                            pass
                        else:
                            # 交易日，根据持仓计算
                            user_funds_hold, user_funds_hold_nofee, user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include_temp, funds_no_netdata_temp = compute_funds(
                                date, user_funds_hold, user_funds_hold_nofee, user_funds_percent)
                            funds_not_include.extend(funds_not_include_temp)
                            funds_no_netdata.extend(funds_no_netdata_temp)
                            user_marketcap[date] = user_marketcap_value + leftusermoney
                            user_marketcap_nofee[date] = user_marketcap_value_nofee + leftusermoney_nofee
                            last_market_value = user_marketcap_value + leftusermoney
                            if net_temp > 0:
                                user_net[date] = net_temp
                    else:
                        user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include_temp, funds_no_netdata_temp = sell_funds_combine(
                            date, user_funds_hold, user_funds_hold_nofee, user_funds_percent)
                        funds_not_include.extend(funds_not_include_temp)
                        funds_no_netdata.extend(funds_no_netdata_temp)
                        user_funds_hold.clear()
                        user_funds_hold_nofee.clear()
                        leftusermoney = usermoney = user_marketcap_value + leftusermoney
                        leftusermoney_nofee = usermoney_nofee = user_marketcap_value_nofee + leftusermoney_nofee
                        # 以上为卖出基金，以下为买入基金
                        user_funds_hold, user_funds_hold_nofee, leftusermoney, leftusermoney_nofee, user_funds_percent, net_temp, fund_fee_total, funds_not_include_temp, funds_no_netdata_temp = buy_funds_combine(
                            user_combination_date, date, usermoney, usermoney_nofee, poctype)
                        funds_not_include.extend(funds_not_include_temp)
                        funds_no_netdata.extend(funds_no_netdata_temp)
                        if date.replace("-", "") not in datelist_possible:
                            # 非交易日跳过
                            pass
                        else:
                            user_marketcap[date] = usermoney - fund_fee_total
                            user_marketcap_nofee[date] = usermoney_nofee
                            last_market_value = usermoney - fund_fee_total
                            if net_temp > 0:
                                user_net[date] = net_temp
            company_detial = company_detial.append(user_marketcap, ignore_index=True)
            company_detial_nofee = company_detial_nofee.append(user_marketcap_nofee, ignore_index=True)
            company_detial_net = company_detial_net.append(user_net, ignore_index=True)
            elapsed = (time.clock() - start)
            time_cost += elapsed
            print("Time used (sec):", elapsed)
            print("Time Left Estimated (min):", str(((time_cost / (int(count))) * len(users_inside) - time_cost) / 60))
        company_detial.to_csv(
            il.cwd + r"\result\\" + company_file + "_result_combine_" + poctype + "_till" + datelist_inside[
                -1] + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_result_combine_" + poctype + "_till" +
              datelist_inside[-1] + ".csv")
        company_detial_nofee.to_csv(
            il.cwd + r"\result\\" + company_file + "_result_combine_nofee_" + poctype + "_till" +
            datelist_inside[-1] + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_result_combine_nofee_" + poctype + "_till" +
              datelist_inside[-1] + ".csv")
        company_detial_net.to_csv(
            il.cwd + r"\result\\" + company_file + "_result_combine_net_" + poctype + "_till" +
            datelist_inside[-1] + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_result_combine_net_" + poctype + "_till" +
              datelist_inside[-1] + ".csv")
        file = open(il.cwd + r"\result\\" + company_file + "_result_combine_reg_" + poctype + ".txt",
                    'w')
        file.write("funds_not_include" + '\r\n')
        file.write(str(set(funds_not_include)) + '\r\n')
        file.write("funds_no_netdata" + '\r\n')
        file.write(str(set(funds_no_netdata)) + '\r\n')
        file.close()
        print("File saved:", il.cwd + r"\result\\" + company_file + "_funds_reg_" + poctype + ".csv")


if __name__ == '__main__':
    poctype_out_list = ["zs"]
    symbolstr = ""
    for poctype_out in poctype_out_list:
        company_file_names_poc = ["varindex-90-minpercnet0.05-change_return0.05-indexcombine2-total",
                                  "bdnindex-90-minpercnet0.05-change_return0.05-indexcombine2-total"]
        # company_file_names_poc = ["kmrd", "betago", "sz"]
        # date_pairs_total = [("2017-07-01", "2017-07-31"), ("2017-08-01", "2017-08-31"), ("2017-09-01", "2017-09-30"),
        #                     ("2017-10-01", "2017-10-31"), ("2017-07-01", "2017-10-31")]
        date_pairs = [("2017-07-01", "2017-11-19"), ("2017-07-01", "2017-10-29"), ("2017-10-30", "2017-11-19")]
        datelist_inside = rl.dateRange_endinclude("2017-07-01", "2017-11-19")
        poc_detail_compute_combine(company_file_names_poc, poctype_out, users, symbolstr, datelist_inside)
        # for startday_str_sta, endday_str_sta in date_pairs:
        #     poc_sta_combine(startday_str_sta, endday_str_sta, poctype_out, company_file_names_poc, symbolstr)
