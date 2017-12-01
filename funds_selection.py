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
import iolib as il
import calendar
import os
from sklearn.cluster import KMeans
from sklearn.externals import joblib
import sklearn.preprocessing as prepro
from sklearn.preprocessing import MinMaxScaler

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


def funds_cluster(k, iteration, funds_net_df, eplison, modelname):
    '''
        计算不同厂家给出的配置相应的每日净值，并输出为文件
    '''

    data = funds_raito = np.log(funds_net_df / funds_net_df.shift(1))
    data_zs = data.iloc[1:].T
    # 归一化操作,eplison是为了防止标准差为0的情况干扰，但是有可能带来归一化后不准确的问题
    # data_zs = (data_zs - data_zs.mean()) / (data_zs.std() + eplison)
    model = KMeans(n_clusters=k, n_jobs=4, max_iter=iteration, init='k-means++')  # 分为k类, 并发数4
    print("Cluster Start")
    model.fit(data_zs)  # 开始聚类
    # 简单打印结果
    print("Cluster Complete")
    r1 = pd.Series(model.labels_).value_counts()  # 统计各个类别的数目
    r2 = pd.DataFrame(model.cluster_centers_)  # 找出聚类中心
    r = pd.concat([r2, r1], axis=1)  # 横向连接(0是纵向), 得到聚类中心对应的类别下的数目
    r.columns = list(data_zs.columns) + ["cluster_size"]  # 重命名表头,添加类别数目列
    print(r)
    # 详细输出原始数据及其类别
    r = pd.concat([data_zs, pd.Series(model.labels_, index=data_zs.index)], axis=1)
    # 详细输出每个样本对应的类别
    r.columns = list(data_zs.columns) + ["cluster_label"]  # 重命名表头，添加类别标签列
    # print(r)
    centroids = model.cluster_centers_
    # print(centroids)
    clusters = model.labels_.tolist()
    # print(clusters)
    joblib.dump(model, il.cwd + r"\result\\" + modelname + "_funds_cluster.pkl")
    cluster_list = list(set(clusters))
    cluster_list.sort()
    return centroids, r, cluster_list


def load_model_return(funds_net_df, eplison, modelname):
    data = funds_raito = np.log(funds_net_df / funds_net_df.shift(1))
    data_zs = data.iloc[1:].T
    data_zs = (data_zs - data_zs.mean()) / (data_zs.std() + eplison)
    model = joblib.load(il.cwd + r"\result\\" + modelname + "_funds_cluster.pkl")
    # 详细输出原始数据及其类别
    r = pd.concat([data_zs, pd.Series(model.labels_, index=data_zs.index)], axis=1)
    # 详细输出每个样本对应的类别
    r.columns = list(data_zs.columns) + ["cluster_label"]  # 重命名表头，添加类别标签列
    centroids = model.cluster_centers_
    clusters = model.labels_.tolist()
    cluster_list = list(set(clusters))
    cluster_list.sort()
    return centroids, r, cluster_list


def funds_select(funds_with_labels, cluster_list, method="max_mean_profit"):
    funds_list = {}
    for single_cluster in cluster_list:
        funds_for_single_cluster = funds_with_labels[funds_with_labels["cluster_label"] == single_cluster]
        funds_for_single_cluster_t = funds_for_single_cluster.T
        if method == "max_mean_profit":
            funds_mean = funds_for_single_cluster_t.mean()
            maxidx = funds_mean.idxmax()
            max_mean_value = funds_mean[maxidx]
            funds_list[single_cluster] = maxidx
        elif method == "max_mean_sharp":
            funds_mean = funds_for_single_cluster_t.mean()
            funds_std = funds_for_single_cluster_t.std()
            funds_sharp = funds_mean / funds_std
            maxidx = funds_sharp.idxmax()
            funds_list[single_cluster] = maxidx
    return funds_list


def funds_sta_for_type(funds_net_df, fund_type_list, funds_type_df,type_return_avg_df):
    type_funds_dic = {}
    for fund_type in fund_type_list:
        type_value_avg = type_return_avg_df[fund_type]
        fund_sta_df = pd.DataFrame(columns=["inverse-dis", "return", "var", "sharp"])
        type_log_return_avg_df = type_value_avg / type_value_avg.shift(1)
        funds_this_type_df = funds_type_df[funds_type_df["fund_type"] == fund_type]
        funds_ticker_list_this_type = funds_this_type_df["ticker"].values.tolist()
        funds_ticker_list_this_type = [funds_ticker_list_this_type[i] for i in range(
            len(funds_ticker_list_this_type)) if funds_ticker_list_this_type[i] in funds_net_df.columns.tolist()]
        for fund_ticker in funds_ticker_list_this_type:
            single_fund = funds_net_df[fund_ticker]
            single_fund_return = single_fund / single_fund.shift(1)
            type_log_return_avg_df = type_log_return_avg_df.sort_index()
            single_fund_return = single_fund_return.sort_index()
            type_log_return_avg_nd = type_log_return_avg_df.values
            single_fund_return_nd = single_fund_return.values
            vec_len = min(len(type_log_return_avg_nd), len(single_fund_return_nd))
            type_log_return_avg_nd = type_log_return_avg_nd[1:vec_len]
            single_fund_return_nd = single_fund_return_nd[1:vec_len]
            single_fund_dis = 1 / np.linalg.norm(type_log_return_avg_nd - single_fund_return_nd)
            single_fund_return = np.mean(single_fund_return_nd)
            single_fund_var = np.var(single_fund_return_nd)
            single_fund_sharp = single_fund_return / single_fund_var
            fund_sta_list = [single_fund_dis, single_fund_return, single_fund_var, single_fund_sharp]
            fund_sta_df.loc[fund_ticker] = fund_sta_list
        min_max_scaler = prepro.MinMaxScaler(feature_range=(0.05, 0.95))
        fund_sta_nd_norm = min_max_scaler.fit_transform(fund_sta_df)
        fund_sta_df_norm = pd.DataFrame(fund_sta_nd_norm, columns=fund_sta_df.columns,
                                        index=fund_sta_df.index)
        type_funds_dic[fund_type] = fund_sta_df_norm
    return type_funds_dic


def funds_select_for_type(funds_net_df, fund_type_list, funds_type_df,type_return_avg_df, funds_each_type=2,selectby="idissharp"):
    type_funds_dic = funds_sta_for_type(funds_net_df, fund_type_list, funds_type_df,type_return_avg_df)
    type_fundticker_dic = {}
    selected_fund_list = []
    for key, value in type_funds_dic.items():
        fund_sta_df_norm = value
        fund_type = key
        fund_sta_df_norm.insert(4, "idissharp", fund_sta_df_norm["inverse-dis"] * fund_sta_df_norm["sharp"])
        fund_sta_df_norm = fund_sta_df_norm.sort_values(by=selectby, ascending=False)
        # print(fund_sta_df_norm)
        type_fundticker_dic[fund_type] = fund_sta_df_norm[
                                         :funds_each_type if funds_each_type <= len(fund_sta_df_norm) else len(
                                             fund_sta_df_norm)].index.values.tolist()
        selected_fund_list.append(fund_sta_df_norm[:funds_each_type].index.values.tolist())
    return type_fundticker_dic, selected_fund_list


def type_return_avg(funds_net_df, fund_type_list, funds_type_df):
    type_return_avg_df = pd.DataFrame()
    for fund_type in fund_type_list:
        funds_this_type_df = funds_type_df[funds_type_df["fund_type"] == fund_type]
        funds_ticker_list_this_type = funds_this_type_df["ticker"].values.tolist()
        funds_ticker_list_this_type = [funds_ticker_list_this_type[i] for i in range(
            len(funds_ticker_list_this_type)) if funds_ticker_list_this_type[i] in funds_net_df.columns]
        funds_thistype_net_df = funds_net_df[funds_ticker_list_this_type]
        funds_thistype_net_df_ticker_index = funds_thistype_net_df.T
        funds_this_type_describe_df = funds_thistype_net_df_ticker_index.describe().T
        type_net_avg = pd.DataFrame(funds_this_type_describe_df["mean"])
        type_net_avg.columns = [fund_type]
        type_return_avg_df = pd.concat([type_return_avg_df, type_net_avg], axis=1)
    return type_return_avg_df


if __name__ == '__main__':
    funds_net_df = il.getZS_funds_net()
    funds_type_df, fund_type_list = il.get_funds_type()
    # km = joblib.load('doc_cluster.pkl')
    # k = 6
    # iteration = 300
    # eplison = 0.000000001
    # modelname = "test"
    # funds_cluster(k, iteration, funds_net_df, eplison, modelname)
    # centroids, funds_with_labels, cluster_list = load_model_return(funds_net_df, eplison, modelname)
    # funds_list = funds_select(funds_with_labels, cluster_list, method="max_mean_sharp")
    # funds = funds_net_df[list(funds_list.values())]
    funds1, funds2 = funds_select_for_type(funds_net_df, fund_type_list, funds_type_df, funds_each_type=2)
    for key, value in funds1.items():
        print(value)
    print(funds2)
