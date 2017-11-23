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
import poc_statistics as pocs

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


def poc_detail_corr(company_file_names_poc, poctype, users_inside):
    '''
        计算不同厂家给出的配置相关系数，并输出为文件
    '''
    funds_net_df = il.getZS_funds_net()
    company_detail = pd.DataFrame()
    user_corr_df = pd.DataFrame()
    for company_file in company_file_names_poc:
        # 对每一个公司给出的配置情况循环
        company_df = il.getZS_Company_combination(il.cwd + r"\history_data\\" + poctype + "_" + company_file + ".csv")
        time_cost = 0.0
        count = 0
        user_corr_dic = {}
        for index, row in users_inside.iterrows():
            count += 1
            start = time.clock()
            print("计算第" + str(count) + "/" + str(len(users_inside)) + "个用户.")
            # 对每一个用户循环
            userid = row["userid"]
            user_combination = company_df[company_df['userid'] == userid]
            user_corr = {}
            user_corr_avg = 0.0
            for date in datelist:
                # print("当前回测日期为" + str(date) + ".")
                # 对回测时间段内的每一个日期循环
                funds_dic = pocs.getUserCombinationByDate(date, user_combination)
                if bool(funds_dic):
                    fund_net_combination = pd.DataFrame(index=funds_net_df.index.tolist())
                    for fund, percent in funds_dic.items():
                        if fund in funds_net_df.columns.values.tolist():
                            fund_net_combination[fund] = funds_net_df[fund]
                    if not fund_net_combination.empty:
                        funds_raito = np.log(fund_net_combination / fund_net_combination.shift(1))
                        funds_combination_corr = funds_raito.corr()
                        funds_combination_corr_abs_avg = (abs(funds_combination_corr).mean()).mean()
                        user_corr[date] = funds_combination_corr_abs_avg
                        if user_corr_avg == 0.0:
                            user_corr_avg = funds_combination_corr_abs_avg
                        else:
                            user_corr_avg = (user_corr_avg + funds_combination_corr_abs_avg) / 2
            elapsed = (time.clock() - start)
            time_cost += elapsed
            print("Time used:", elapsed)
            print("Time Left Estimated:", (time_cost / (int(count))) * len(users_inside) - time_cost)
            user_corr_dic[userid] = user_corr_avg
            company_detail = company_detail.append(user_corr, ignore_index=True)
        company_detail.to_csv(il.cwd + r"\result\\" + company_file + "_corrdetail_combine_" + poctype + ".csv")
        print("File saved:", il.cwd + r"\result\\" + company_file + "_corrdetail_combine_" + poctype + ".csv")
        user_corr_df = user_corr_df.append(user_corr_dic, ignore_index=True)
    user_corr_df = user_corr_df.T
    user_corr_df.columns = company_file_names_poc
    user_corr_df.to_csv(il.cwd + r"\result\\all_corr_combine_" + poctype + ".csv")
    print("File saved:", il.cwd + r"\result\\all_corr_combine_" + poctype + ".csv")


if __name__ == '__main__':
    poctype_out_list = ["zs"]
    for poctype_out in poctype_out_list:
        # company_file_names_poc = ["sz"]
        company_file_names_poc = ["kmrd", "betago", "sz", "xj"]
        poc_detail_corr(company_file_names_poc, poctype_out, users)
