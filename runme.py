# -*- coding: utf-8 -*-
"""
Created on Thu May 25 13:56:18 2017
https://www.joinquant.com/post/6113
多因子换挡反转策略的研究 2017.05.25
@author: talen
"""
import pandas as pd
import numpy as np
import os
import time
import pickle
start_time = time.time()

def GetCumulativeReturn(to_be_calculated):
    rows_num = len(to_be_calculated.index)
    tmp_cumu_return = np.array(to_be_calculated)
    ###############################################
    '''
    tmp_cumu_return[2] = (1+tmp_cumu_return[2]/100)
    for i in range(3,rows_num):
        tmp_cumu_return[i] = (1+tmp_cumu_return[i]/100) * tmp_cumu_return[i-1]
    '''
    ###############################################    
    tmp_cntr = 1
    for i in range(rows_num):
        if type(tmp_cumu_return[i,0]) == str:
            continue
        else:
            if tmp_cntr == 1:
                tmp_cumu_return[i] = (1+tmp_cumu_return[i]/100)
                tmp_cntr = 0
                continue
            else:
                tmp_cumu_return[i] = (1+tmp_cumu_return[i]/100) * tmp_cumu_return[i-1]
    results = pd.DataFrame(tmp_cumu_return,index=to_be_calculated.index,columns=to_be_calculated.columns)
    return results
def StockFilter(to_be_calculated_tmp):
    # 删除符合条件的股票里在所选周期内至少一天不开盘的企业
    target_stocks_indices_filtered = []
    target_stocks_indices  = to_be_calculated_tmp.columns
    for terms in target_stocks_indices:
        if '--' in list(to_be_calculated_tmp[terms]):
            continue
        else:
            target_stocks_indices_filtered.append(terms)
    return to_be_calculated_tmp[target_stocks_indices_filtered]
def GetReciprocal(weekly_tmp):
    tmp_weekly = np.array(weekly_tmp)
    for i in range(len(weekly_tmp.index)):
        for j in range(len(weekly_tmp.columns)):
            if type(tmp_weekly[i,j]) == str or tmp_weekly[i,j] == 0:
                continue
            else:
                tmp_weekly[i,j] = 1/tmp_weekly[i,j]
    return pd.DataFrame(tmp_weekly,index=weekly_tmp.index,columns=weekly_tmp.columns)
def MaxDrawdown(cumu_return):
    starting_index = 2
    dd_list = []
    for term in cumu_return.columns:
        tmp_return = list(cumu_return.ix[starting_index:,term])
        max_value = None
        min_value = None
        drawdown = None
        for i in range(len(tmp_return)):
            if max_value == None:
                max_value = tmp_return[i]
                continue
            elif tmp_return[i] > max_value:
                max_value = tmp_return[i]
                min_value = None
                continue
            elif tmp_return[i] <= max_value:
                if min_value == None:
                    min_value = tmp_return[i]
                    if drawdown == None:
                        drawdown = (max_value-min_value)/max_value
                    elif drawdown < (max_value-min_value)/max_value:
                        drawdown = (max_value-min_value)/max_value
                elif tmp_return[i] < min_value:
                    min_value = tmp_return[i]
                    if drawdown == None:
                        drawdown = (max_value-min_value)/max_value
                    elif drawdown < (max_value-min_value)/max_value:
                        drawdown = (max_value-min_value)/max_value
        dd_list.append(drawdown)
    # results = pd.DataFrame(dd_list,columns=list(cumu_return.columns))
    return dd_list
            
os.chdir('C:\\Users\\LH\\Desktop\\工作日志\\2017年5月第4周')
weekly_change = pd.read_excel('A股周涨跌幅1217.xlsx')
weekly_pe = pd.read_excel('A股周市盈率1217.xlsx')
tmp_quarter_debt_ratio = pd.read_excel('A股季度资产负债率1217.xls')
quarterly_debt_ratio = tmp_quarter_debt_ratio.T
del tmp_quarter_debt_ratio
quarterly_debt_ratio.columns = quarterly_debt_ratio.ix[0,:]
weekly_pcf = pd.read_excel('A股周市现率1217.xlsx')
weekly_pb = pd.read_excel('A股周市净率1217.xlsx')
weekly_bp = GetReciprocal(weekly_pb)
weekly_cfp = GetReciprocal(weekly_pcf)
sector_search = pickle.load(open('C:/Users/LH/Desktop/工作日志/2017年5月第4周/sectorandstocks.txt','rb'))
# the following index selection is given that the weekly_pb, weekly_change, weekly_pcf and weekly_pe share the same time and stocks
tmp_dates = list(weekly_pb.index)
year_span = [i for i in range(tmp_dates[3].year,tmp_dates[-1].year)]

quantile_point = 0.01 # top 1%
obs_duration = 'quarter' #观察时长
if obs_duration == 'quarter':
    obs_duration_indicator = 3
elif obs_duration == 'month':
    obs_duration_indicator = 1
###############################################################################
# select stocks by debt ratio
# eliminate '--' in spreadsheet, i.e. the days closed or not-go-public
season_of_debt_ratio = 19 # 2:2012Q1, 3: 2012Q2, 4: 2012Q3, 5: 2012Q4, 6: 2013Q1, 7: 2013Q2, 8: 2013Q3, 9:2013Q4, 10:2014Q1, 11:2014Q2, 12:2014Q3,
# 13:2014Q4, 14:2015Q1, 15: 2015Q2, 16: 2015Q3, 17: 2015Q4, 18: 2016Q1, 19:2016Q2, 20: 2016Q3, 21: 2016Q4, 22: 2017Q1
tmp = quarterly_debt_ratio.ix[season_of_debt_ratio,:][quarterly_debt_ratio.ix[season_of_debt_ratio,:]!='--']
target_stocks_indices = list(pd.DataFrame(tmp[tmp>tmp.quantile(1-quantile_point)]).index)
other_stocks_indices_by_debt = list(pd.DataFrame(tmp[tmp<=tmp.quantile(1-quantile_point)]).index)
del tmp
#obs_year = int((season_of_debt_ratio-2)/4) + 2012
obs_year = int((season_of_debt_ratio-1)/4) + 2012
months_list = [i for i in range(1,13)]
obs_months = months_list[((season_of_debt_ratio-1)%4)*3:((season_of_debt_ratio-1)%4)*3+obs_duration_indicator]
'''
if obs_duration_indicator == 1:
    if len(obs_months):
        obs_months = obs_months[0]
    else:
        print('impossible')
'''
del months_list
'''
if season_of_debt_ratio == 4:
    obs_year = 2012
    if obs_duration == 'quarter':
        obs_month = [10,11,12]
    elif obs_duration == 'month':
        obs_month = [10]
'''
# cumulative return is based on a quarter
trading_days_list = list(weekly_change.index)
trading_days_selected_index = [0,1]
for kk in range(2,len(trading_days_list)):
    if trading_days_list[kk].year == obs_year:
        if trading_days_list[kk].month in obs_months:
            trading_days_selected_index.append(kk)
    if trading_days_list[kk].year > obs_year:
        break
to_be_calculated_tmp = weekly_change.ix[trading_days_selected_index,target_stocks_indices]
to_be_calculated = StockFilter(to_be_calculated_tmp) #用于删除选择期内不交易的股票，删'--'
del to_be_calculated_tmp
cumu_return_selected_by_debt_ratio = GetCumulativeReturn(to_be_calculated)
###############################################################################
# 这部分的指标可通用于pb，pcf，pe，cfp，bp等
obs_year = int((season_of_debt_ratio-1)/4) + 2012
months_list = [i for i in range(1,13)]
obs_months = months_list[((season_of_debt_ratio-1)%4)*3:((season_of_debt_ratio-1)%4)*3+obs_duration_indicator]
'''
if obs_duration_indicator == 1:
    obs_months = [obs_months]
'''
del months_list
# (season_of_debt_ratio-2)%4 == 0: #Q1的数据，要用Q2的数据计算return
target_year = int((season_of_debt_ratio-2)/4) + 2012 # 用于计算标的的年和月
target_months = 3*((season_of_debt_ratio-2)%4) + 3 
###############################################################################
# select stocks by cfp
trading_days_list_in_cfp = list(weekly_cfp.index)
tmp_cntr = 0
for i in range(2,len(weekly_cfp.index)):
    if trading_days_list_in_cfp[i].year > target_year:
        break
    else:
        if trading_days_list_in_cfp[i].month != target_months:
            continue
        else:
            tmp_cntr = i
tmp = weekly_cfp.ix[i,:][weekly_cfp.ix[i,:]!='--']
target_stocks_indices_by_cfp = list(pd.DataFrame(tmp[tmp>tmp.quantile(1-quantile_point)]).index)
other_stocks_indices_by_cfp = list(pd.DataFrame(tmp[tmp<=tmp.quantile(1-quantile_point)]).index)
trading_days_list = list(weekly_change.index)
trading_days_selected_index = [0,1]
for kk in range(2,len(trading_days_list)):
    if trading_days_list[kk].year == obs_year:
        if trading_days_list[kk].month in obs_months:
            trading_days_selected_index.append(kk)
    if trading_days_list[kk].year > obs_year:
        break
to_be_calculated_tmp = weekly_change.ix[trading_days_selected_index,target_stocks_indices_by_cfp]
to_be_calculated = StockFilter(to_be_calculated_tmp) #用于删除选择期内不交易的股票，删'--'
del to_be_calculated_tmp
cumu_return_selected_by_cfp = GetCumulativeReturn(to_be_calculated)
###############################################################################
# select stocks by BP
trading_days_list_in_bp = list(weekly_bp.index)
tmp_cntr = 0
for i in range(2,len(weekly_bp.index)): # 选出合适时间段的股票
    if trading_days_list_in_bp[i].year > target_year:
        break
    else:
        if trading_days_list_in_bp[i].month != target_months:
            continue
        else:
            tmp_cntr = i
tmp = weekly_bp.ix[i,:][weekly_bp.ix[i,:]!='--']
target_stocks_indices_by_bp = list(pd.DataFrame(tmp[tmp>tmp.quantile(1-quantile_point)]).index)
other_stocks_indices_by_bp = list(pd.DataFrame(tmp[tmp<=tmp.quantile(1-quantile_point)]).index)
trading_days_list = list(weekly_change.index)
trading_days_selected_index = [0,1]
for kk in range(2,len(trading_days_list)):
    if trading_days_list[kk].year == obs_year:
        if trading_days_list[kk].month in obs_months:
            trading_days_selected_index.append(kk)
    if trading_days_list[kk].year > obs_year:
        break
to_be_calculated_tmp = weekly_change.ix[trading_days_selected_index,target_stocks_indices_by_bp]
to_be_calculated = StockFilter(to_be_calculated_tmp) #用于删除选择期内不交易的股票，删'--'
del to_be_calculated_tmp
cumu_return_selected_by_bp = GetCumulativeReturn(to_be_calculated)
stocks_of_the_best = set(cumu_return_selected_by_bp.columns) & set(cumu_return_selected_by_cfp.columns) & set(cumu_return_selected_by_debt_ratio.columns)

print('time collapsed: ',time.time()-start_time,' seconds')
'''
tmp = weekly_pcf.ix[3,:][weekly_pcf.ix[3,:]!='--']
# eliminate '--'
tmp.quantile(.99) # quantile point of top 1%
tmp.quantile(.01) # quantile point of top 99%
pd.DataFrame(tmp[tmp>tmp.quantile(.99)]).index # 得到满足这个条件的股票代码

'''
