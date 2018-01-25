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
import os as os

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


def poc_sta_combine(user_inside, startday_str_sta, endday_str_sta, poctype, company_file_names_sta, lastdate_str,
                    symbolstr):
    '''
        计算不同厂家给出的配置计算收益率和标准差明细
    '''
    user_poc_sta = user_inside.copy()
    # if strptime(endday_str_sta, format) < strptime("2017-11-23", format):
    #     user_poc_sta = user_poc_sta.ix[:99, :]
    ini_money = user_poc_sta.pop("moneyamount")
    ini_money = ini_money.map(lambda x: float(x) * 10000)
    user_sta = pd.DataFrame(index=user_poc_sta.index)
    for company_file in company_file_names_sta:
        datelist_sta_temp = rl.dateRange(startday_str_sta, endday_str_sta)
        datelist_sta = [w for w in datelist_sta_temp if w.replace("-", "") in datelist_possible]
        filenames = ["", "nofee_"]
        for filename in filenames:
            company_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_" + filename + symbolstr + poctype + "_till" + lastdate_str + ".csv")

            company_df = company_df1.ix[:, 1:]
            if startday_str_sta not in company_df.columns:
                company_df.insert(0, startday_str_sta, ini_money)
            # company_df = company_df.reindex(range(1, 101))
            company_result = company_df.T
            company_result_this_period = company_result[company_result.index.isin(datelist_sta_temp)]
            company_result_this_period_shift = company_result_this_period.shift(1)
            profit_detail_bizhi = company_result_this_period / company_result_this_period_shift
            profit_detail_bizhi_profit = company_result_this_period - company_result_this_period_shift
            result_des_bizhi = profit_detail_bizhi.describe().T
            result_des_bizhi_profit = profit_detail_bizhi_profit.describe().T
            user_sta["0" + company_file + "_std_total_" + filename] = result_des_bizhi.pop("std")
            user_sta["1" + company_file + "_std_year_" + filename] = user_sta[
                                                                         "0" + company_file + "_std_total_" + filename] * np.sqrt(
                250)
            user_sta["2" + company_file + "_year_rate_" + filename] = (
                    ((company_result_this_period.iloc[-1] - company_result_this_period.iloc[0]) /
                     company_result_this_period.iloc[0]) / (len(datelist_sta_temp) / 365))

            # 以下计算最大回撤
            maxdown_user_dic = {}
            iloc_index = 0
            time_cost = 0
            for index, row in company_result_this_period.iterrows():
                if (iloc_index + 1) < len(company_result_this_period):
                    iloc_index += 1
                    start = time.clock()
                    left_df = company_result_this_period.iloc[iloc_index:]
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
                    if iloc_index % 30 == 0:
                        print(filename + company_file + " Max Down Time used:" +
                              str(elapsed) + ", " + str(iloc_index) + "/" + str(len(company_result_this_period)))
                        print(filename + company_file + " Max Down Time Left Estimated:",
                              (time_cost / (int(iloc_index))) * len(company_result_this_period) - time_cost)
            maxdown_user_dic_positive = {w: maxdown_user_dic[w] if maxdown_user_dic[w] > 0 else 0 for w
                                         in maxdown_user_dic.keys()}
            company_maxdown_detial = pd.Series(maxdown_user_dic_positive)
            user_sta["3" + company_file + "_maxdown_" + filename] = company_maxdown_detial
            user_sta["4" + company_file + "_sharp_ratio_" + filename] = np.log(user_sta[
                                                                                   "2" + company_file + "_year_rate_" + filename] / \
                                                                               user_sta[
                                                                                   "1" + company_file + "_std_year_" + filename])
    # userid_columns = [w for w in range(1, 101)]
    user_sta = user_sta.T.sort_index()
    # user_sta.columns = userid_columns
    user_sta = user_sta.T
    user_sta = user_sta.sort_index()
    user_poc_sta["userid"] = user_poc_sta["userid"].astype("int64")
    user_poc_sta = user_poc_sta.sort_values(by=["userid"])
    user_sta.insert(0, "risk_score", user_poc_sta["risk_score"])
    user_sta.insert(0, "risk_type", user_poc_sta["risk_type"])
    user_sta.insert(0, "userid", user_poc_sta["userid"])
    user_sta.set_index("userid")
    user_sta = user_sta.sort_values(by=["risk_type", "risk_score"])
    return user_sta


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
                if fund_ticker in user_funds_hold.keys():
                    user_funds_hold[fund_ticker] = user_funds_hold[fund_ticker] + (
                            float(usermoney) * float(fund_percent)) / fund_net
                    user_funds_hold_nofee[fund_ticker] = user_funds_hold_nofee[fund_ticker] + (
                            float(usermoney_nofee) * float(fund_percent)) / fund_net
                else:
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
                        # print(fund_ticker)
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
                if fund_ticker in user_funds_hold.keys():
                    user_funds_hold[fund_ticker] = user_funds_hold[fund_ticker] + float(usermoney) * float(fund_percent)
                    user_funds_hold_nofee[fund_ticker] = user_funds_hold_nofee[fund_ticker] + float(
                        usermoney_nofee) * float(fund_percent)
                else:
                    user_funds_hold[fund_ticker] = float(usermoney) * float(fund_percent)
                    user_funds_hold_nofee[fund_ticker] = float(usermoney_nofee) * float(fund_percent)
                # 记录买入金额
                leftusermoney = float(leftusermoney) - (float(usermoney) * float(fund_percent))
                # 从剩余现金中减去买货币基金所花费的数额
                leftusermoney_nofee = float(leftusermoney_nofee) - (float(usermoney_nofee) * float(fund_percent))
                moneyfund_net = getMoneyFund_Net(startday_str, date, fund_ticker)
                net_temp = net_temp + fund_percent * moneyfund_net
        else:
            funds_no_netdata.append(fund_ticker)
    return user_funds_hold, user_funds_hold_nofee, leftusermoney, leftusermoney_nofee, user_funds_percent, net_temp, fund_fee_total, funds_not_include, funds_no_netdata


def buyorsell_funds_combine(date, user_funds_hold, user_funds_hold_nofee, user_funds_percent, change_amount, poctype):
    usermoney = usermoney_nofee = np.abs(change_amount)
    user_combination_date = pd.DataFrame(user_funds_percent, index=[0]).T
    user_combination_date = user_combination_date.reset_index()
    user_combination_date.columns = ["ticker", "percent"]
    if change_amount > 0:
        user_funds_hold_change, user_funds_hold_nofee_change, leftusermoney, leftusermoney_nofee, _, net_temp, fund_fee_total, funds_not_include_temp, funds_no_netdata_temp = buy_funds_combine(
            user_combination_date, date, usermoney, usermoney_nofee, poctype)
        return_user_funds_hold = {}
        return_user_funds_hold_nofee = {}
        return_leftusermoney = leftusermoney
        return_leftusermoney_nofee = leftusermoney_nofee
        for key, value in user_funds_hold.items():
            return_user_funds_hold[key] = user_funds_hold[key] + user_funds_hold_change[key]
            return_user_funds_hold_nofee[key] = user_funds_hold_nofee[key] + user_funds_hold_nofee_change[key]
    else:
        user_funds_hold, user_funds_hold_nofee, user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include_temp, funds_no_netdata_temp = compute_funds(
            date, user_funds_hold, user_funds_hold_nofee, user_funds_percent)
        sell_ratio = np.abs(change_amount) / user_marketcap_value
        return_user_funds_hold = {}
        return_user_funds_hold_nofee = {}
        sell_user_funds_hold = {}
        sell_user_funds_hold_nofee = {}
        for key, value in user_funds_hold.items():
            sell_user_funds_hold[key] = value * sell_ratio
            return_user_funds_hold[key] = value * (1 - sell_ratio)
            sell_user_funds_hold_nofee[key] = user_funds_hold_nofee[key] * sell_ratio
            return_user_funds_hold_nofee[key] = user_funds_hold_nofee[key] * (1 - sell_ratio)
        user_marketcap_value, user_marketcap_value_nofee, net_temp, funds_not_include_temp, funds_no_netdata_temp = sell_funds_combine(
            date, sell_user_funds_hold, sell_user_funds_hold_nofee, user_funds_percent)
        return_leftusermoney = user_marketcap_value
        return_leftusermoney_nofee = user_marketcap_value_nofee
    return return_user_funds_hold, return_user_funds_hold_nofee, return_leftusermoney, return_leftusermoney_nofee


def get_updated_users_by_company(formaldate_str, oldusers_df, company_file_names_list, poctype, symbolstr):
    '''
        读入最新的用户信息表，其中用户的资金数目会更新为最新的资产市值
    '''
    users_info_dic = {}
    user_change_df_dic, user_changeamount_dic = il.getZS_users_change()
    for company_file in company_file_names_list:
        user_df = oldusers_df.copy()
        try:
            company_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_result_combine_" + symbolstr + poctype + "_till" + formaldate_str + ".csv")
            company_nofee_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_result_combine_nofee_" + symbolstr + poctype + "_till" + formaldate_str + ".csv")
            company_df = company_df1.ix[:, 1:]
            company_nofee_df = company_nofee_df1.ix[:, 1:]
            user_df = user_df.sort_values(by=["userid"])
            current_money_list = company_df.iloc[:, -1:].T.values.tolist()
            current_monye_nofee_list = company_nofee_df.iloc[:, -1:].T.values.tolist()
            current_money_se = pd.Series(
                {w: current_money_list[0][w - 1] for w in range(1, len(current_money_list[0]) + 1)})
            current_money_nofee_se = pd.Series(
                {w: current_monye_nofee_list[0][w - 1] for w in range(1, len(current_monye_nofee_list[0]) + 1)})
            user_df['userid'] = user_df['userid'].astype('int')
            user_df = user_df.set_index("userid")
            user_df.insert(0, "nofee_amount", current_money_nofee_se)
            user_df.insert(0, "fee_amount", current_money_se)
            user_df = user_df.ix[:len(company_df), :]
            for key, value in user_change_df_dic.items():
                change_date = key
                user_change_df = value
                for index, row in user_change_df.iterrows():
                    add_user_id = int(row["userid"])
                    add_user_amount = float(row["moneyamount"]) * 10000
                    add_user_dic = {"moneyamount": float(row["moneyamount"]), "nofee_amount": add_user_amount,
                                    "fee_amount": add_user_amount, "risk_score": float(row["risk_score"]),
                                    "risk_type": row["risk_type"]}
                    if add_user_id > 100 and add_user_id in user_df.index:
                        user_df.loc[add_user_id, "nofee_amount"] = add_user_amount
                        user_df.loc[add_user_id, "fee_amount"] = add_user_amount
                        user_df.loc[add_user_id, "moneyamount"] = float(row["moneyamount"])
                    elif add_user_id > 100 and add_user_id not in user_df.index:
                        user_df = user_df.append(pd.DataFrame(add_user_dic, index=[add_user_id]), ignore_index=False)
            user_df = user_df.sort_index()
            users_info_dic[company_file] = user_df
        except:
            pass
            user_money = oldusers_df["moneyamount"].copy()
            user_df.insert(0, "nofee_amount", user_money.astype('float') * 10000)
            user_df.insert(0, "fee_amount", user_money.astype('float') * 10000)
            user_df['userid'] = user_df['userid'].astype('int')
            user_df = user_df.set_index("userid")
            user_df = user_df.sort_index()
            users_info_dic[company_file] = user_df
    return users_info_dic


def company_detail_concat(formaldate_str, company_file_names_list, poctype, lastdate_str, symbolstr,
                          flag_former="total_", flag_later="unchanged_"):
    '''
        连接所有用户的每日市值表格
    '''
    company_return_yuan = pd.DataFrame()
    for company_file in company_file_names_list:
        try:
            company_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_" + flag_former + "result_combine_" + symbolstr + poctype + "_till" + formaldate_str + ".csv")
            company_df2 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
            company_return_yuan[company_file] = pd.Series(company_df2.iloc[:, -1].values.tolist()) - pd.Series(
                company_df2.iloc[:, 1].values.tolist())
            company_df1 = company_df1.ix[:, 1:]
            company_df2 = company_df2.ix[:, 1:]
            company_df = pd.concat([company_df1, company_df2], axis=1)
            company_nofee_df1 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_" + flag_former + "result_combine_nofee_" + symbolstr + poctype + "_till" + formaldate_str + ".csv")
            company_nofee_df2 = pd.read_csv(
                il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_nofee_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
            company_return_yuan[company_file + "_nofee"] = pd.Series(
                company_nofee_df2.iloc[:, -1].values.tolist()) - pd.Series(
                company_nofee_df2.iloc[:, 1].values.tolist())
            company_nofee_df1 = company_nofee_df1.ix[:, 1:]
            company_nofee_df2 = company_nofee_df2.ix[:, 1:]
            company_nofee_df = pd.concat([company_nofee_df1, company_nofee_df2], axis=1)
        except:
            print("Wrong concat files.")
        company_df.to_csv(
            il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
        company_nofee_df.to_csv(
            il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_nofee_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_" + flag_later + "result_combine_nofee_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
    userid_columns = [w for w in range(1, 151)]
    company_return_yuan = company_return_yuan.T
    company_return_yuan.columns = userid_columns
    company_return_yuan = company_return_yuan.T
    company_return_yuan.to_csv(
        il.cwd + r"\result\\result_combine_return_value_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
    print("File saved:",
          il.cwd + r"\result\\result_combine_return_value_" + symbolstr + poctype + "_till" + lastdate_str + ".csv")
    return True


def poc_detail_compute_combine(company_file_names_poc, poctype, users_inside_dic, datelist_in_poc_compute, symbolstr):
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件，计算时先对天循环，再对日期循环
    '''
    user_change_df_dic, user_changeamount_dic = il.getZS_users_change()
    for company_file in company_file_names_poc:
        # 对每一个公司给出的配置情况循环
        company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + poctype + "_" + company_file + ".csv")
        company_detial = pd.DataFrame()
        company_detial_nofee = pd.DataFrame()
        company_detial_net = pd.DataFrame()
        funds_not_include = []
        funds_no_netdata = []
        time_cost = 0.0
        count = 0
        users_inside = users_inside_dic[company_file]
        # 2,101-103,67,111,112
        users_test = pd.concat(
            [users_inside[1:2],users_inside[106:107], users_inside[86:87]], axis=0)
        for index, row in users_inside.iterrows():
            count += 1
            start = time.clock()
            print("计算第" + str(count) + "/" + str(len(users_inside)) + "个用户.")
            # 对每一个用户循环
            userid = str(index)
            leftusermoney_nofee = usermoney_nofee = row["nofee_amount"]
            leftusermoney = usermoney = row["fee_amount"]
            user_combination = company_df[company_df['userid'] == userid]
            user_funds_hold = {}
            user_funds_hold_nofee = {}
            user_funds_percent = {}
            user_marketcap = {}
            user_marketcap_nofee = {}
            user_net = {}
            last_change_date = ""
            last_market_value = 0
            for date in datelist_in_poc_compute:
                # print("当前回测日期为" + str(date) + ".")
                # 对回测时间段内的每一个日期循环
                if date in user_changeamount_dic.keys():
                    user_changeamount_inside_dic = user_changeamount_dic[date]
                    change_amount = user_changeamount_inside_dic[int(userid)]
                    if change_amount == 0:
                        pass
                    else:
                        if not bool(user_funds_hold):
                            usermoney = usermoney + change_amount * 10000
                            usermoney_nofee = usermoney_nofee + change_amount * 10000
                        else:
                            ########## 需要计算真实调仓下的情况是把下面的语句注释掉##########
                            change_amount = 0
                            ########## 需要计算真实调仓下的情况是把上面的语句注释掉##########
                            user_funds_hold, user_funds_hold_nofee, _, _ = buyorsell_funds_combine(
                                date, user_funds_hold, user_funds_hold_nofee, user_funds_percent, change_amount * 10000,
                                poctype)

                user_combination_date_dic, user_combination_date, buy_date = rl.getUserCombinationByDate(date,
                                                                                                         user_combination)
                if user_combination_date.empty and int(userid) > 100 and strptime(date, format) >= strptime(
                        list(user_changeamount_dic.keys())[0], format):
                    user_same_risk_df = users_inside[users_inside["risk_type"] == row["risk_type"]]
                    user_same_risk_id = user_same_risk_df[:1].index[0]
                    user_combination_same_risk_df = company_df[company_df['userid'] == str(user_same_risk_id)]
                    user_combination_date_dic, user_combination_date, buy_date = rl.getUserCombinationByDate(date,
                                                                                                             user_combination_same_risk_df)
                else:
                    pass
                if user_combination_date.empty:
                    print(
                        "User " + userid + " and/or users with same risk have no combination on " + date + " or before.")
                else:
                    if not bool(user_funds_hold):
                        # 如果用户持仓情况为空仓，则买入基金
                        user_funds_hold, user_funds_hold_nofee, leftusermoney, leftusermoney_nofee, user_funds_percent, net_temp, fund_fee_total, funds_not_include_temp, funds_no_netdata_temp = buy_funds_combine(
                            user_combination_date, date, usermoney, usermoney_nofee, poctype)
                        funds_not_include.extend(funds_not_include_temp)
                        funds_no_netdata.extend(funds_no_netdata_temp)
                        if date.replace("-", "") not in datelist_possible:
                            pass
                        else:
                            user_marketcap[date] = float(usermoney) - fund_fee_total
                            user_marketcap_nofee[date] = usermoney_nofee
                            last_market_value = float(usermoney) - fund_fee_total
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
        lastdate_str = datelist_in_poc_compute[-1]
        company_detial.to_csv(
            il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        company_detial_nofee.to_csv(
            il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_nofee_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_nofee_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        company_detial_net.to_csv(
            il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_net_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_net_" + symbolstr + poctype + "_" + lastdate_str + ".csv")
        file = open(
            il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_reg_" + symbolstr + poctype + "_" + lastdate_str + ".txt",
            'w')
        file.write("funds_not_include" + '\r\n')
        file.write(str(set(funds_not_include)) + '\r\n')
        file.write("funds_no_netdata" + '\r\n')
        file.write(str(set(funds_no_netdata)) + '\r\n')
        file.close()
        print("File saved:",
              il.cwd + r"\result\\" + company_file + "_unchanged_result_combine_reg_" + poctype + "_" + lastdate_str + ".txt")


if __name__ == '__main__':
    cwd = os.getcwd()
    poctype_out_list = ["zs"]
    symbolstr = "total_"
    flag_str = "unchanged_"
    users_inside = il.getZS_users_complete(cwd + r"\history_data\zs_user_change.csv")
    for poctype_out in poctype_out_list:
        # company_file_names_poc = ["zsmk"]
        # company_file_names_poc = ["varindex-90-minpercnet0.05-change_return0.05-indexcombine2-total"]
        company_file_names_poc = ["zsmk", "varindex-90-minpercnet0.05-change_return0.05-indexcombine2-total", "xj",
                                  "betago", "sz", "kmrd"]
        # company_file_names_poc = ["sz"]
        # date_pairs_total = [("2017-07-01", "2017-07-31"), ("2017-08-01", "2017-08-31"), ("2017-09-01", "2017-09-30"),
        #                     ("2017-10-01", "2017-10-31"), ("2017-07-01", "2017-10-31")]
        # date_pairs = [("2017-10-30", "2017-11-05"),("2017-11-06", "2017-11-12"),("2017-11-13", "2017-11-19"),("2017-11-20", "2017-11-26"), ("2017-11-27", "2017-12-03"), ("2017-12-04", "2017-12-10")]
        date_pairs = [("2017-07-01", "2018-01-14")]
        startdate_poc = "2017-11-19"
        enddate_poc = "2018-01-14"

        # users_dic_real = get_updated_users_by_company(startdate_poc, users_inside, company_file_names_poc, poctype_out,
        #                                               symbolstr=symbolstr)
        # datelist_in_poc_compute = rl.dateRange_endinclude(startdate_poc, enddate_poc)
        # poc_detail_compute_combine(company_file_names_poc, poctype_out, users_dic_real, datelist_in_poc_compute,
        #                            symbolstr)
        # company_detail_concat(startdate_poc, company_file_names_poc, poctype_out, enddate_poc, symbolstr, "", flag_str)
        for startday_str_sta, endday_str_sta in date_pairs:
            if strptime(endday_str_sta, format) >= strptime("2017-11-23", format):
                usersta1 = poc_sta_combine(users_inside.ix[:99, :], startday_str_sta, endday_str_sta, poctype_out,
                                           company_file_names_poc,
                                           enddate_poc, symbolstr)
                if strptime(startday_str_sta, format) >= strptime("2017-11-27", format):
                    usersta2 = poc_sta_combine(users_inside.ix[100:, :], startday_str_sta, endday_str_sta, poctype_out,
                                               company_file_names_poc,
                                               enddate_poc, symbolstr)
                else:
                    usersta2 = poc_sta_combine(users_inside.ix[100:, :], "2017-11-27", endday_str_sta, poctype_out,
                                               company_file_names_poc,
                                               enddate_poc, symbolstr)
                user_sta = pd.concat([usersta1, usersta2], axis=0)

            else:
                user_sta = poc_sta_combine(users_inside.ix[:99, :], startday_str_sta, endday_str_sta, poctype_out,
                                           company_file_names_poc,
                                           enddate_poc, symbolstr)
            company_join_str = "_".join(company_file_names_poc)
            user_sta.to_excel(
                il.cwd + r"\result\\" + startday_str_sta + "_" + endday_str_sta + "_sta_combine_" + poctype_out + "_" + flag_str + company_join_str + ".xls")
            print("File saved:",
                  il.cwd + r"\result\\" + startday_str_sta + "_" + endday_str_sta + "_sta_combine_" + poctype_out + "_" + flag_str + company_join_str + ".xls")
            print(user_sta)
