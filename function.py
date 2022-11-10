# -*- coding: utf-8 -*-
"""
事件研究法所有用到的函数

"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import math
import tushare as ts
pro=ts.pro_api('8f05588b513af3bae5df8312ccf5e6d724712ef425b18be9f5b77ee0')

#%% 按照天数标准筛选
def select_data (target_df, standard_days, ):
    selected = pd.DataFrame(columns=['代码','名称', '公告日期'])
    standard_delta = pd.Timedelta(days = standard_days)
    
    #放入第一个：
    selected.loc[0]=[target_df.iloc[0, 0],target_df.iloc[0, 1], target_df.iloc[0,2]]
    for i in range (1, target_df.shape[0]): #漏第一个
        if target_df.iloc[i, 0] != target_df.iloc[i-1, 0]: #当前和上一个名称不同，当前的进入slected
            selected.loc[i]=[target_df.iloc[i, 0],target_df.iloc[i, 1], target_df.iloc[i, 2]]
            a = selected.iloc[-1, 2] #最新selected
            i+=1
        else:  
            a = selected.iloc[-1, 2]
            delta = target_df.iloc[i, 2] - a
            if delta > standard_delta:  #如果大于一个月，当前进入selected
                selected.loc[i]=[target_df.iloc[i, 0],target_df.iloc[i, 1], target_df.iloc[i, 2]]
                a = selected.iloc[-1, 2]
                i+=1
            else: #如果小于等于一个月，当前的跳过
                i+=1
    selected = selected.reset_index(drop=True)  
    return selected




#%% 计算各个事件区间
def set_range(df, estimate_1, estimate_2, happen_1, happen_2):
    区间 = pd.DataFrame(columns=['代码','名称', '公告日期', '估计区间1', '估计区间2','事件区间1','事件区间2'])
    for k in range (0, len(df)):
        估计区间1 = df.iloc[k, 2] + pd.Timedelta(days = estimate_1)
        估计区间2 = df.iloc[k, 2] + pd.Timedelta(days = estimate_2)
        事件区间1 = df.iloc[k, 2] + pd.Timedelta(days = happen_1)
        事件区间2 = df.iloc[k, 2] + pd.Timedelta(days = happen_2)
        区间.loc[k]=[df.iloc[k, 0],df.iloc[k, 1], df.iloc[k, 2],估计区间1,估计区间2, 事件区间1, 事件区间2]
    return 区间

#%% 计算ar
def ar(target_df, range_df, market_df, workingday_df, range_day_1, range_day_2):
    total_day = -range_day_1 + range_day_2 + 1
    temp = pd.DataFrame(index = list(range (0, total_day)), 
                     columns = list(range (0, len(target_df))))
    for w in range (0, len(target_df)):
        try:
            print ('当前是第', w,'次','估计个股数据')
            估计区间1 = range_df.iloc[w, 3].strftime('%Y%m%d')
            估计区间2 = range_df.iloc[w, 4].strftime('%Y%m%d')
            代码 = range_df.iloc[w, 0]
            个股_估计 = pro.daily(ts_code=代码, start_date=估计区间1, end_date=估计区间2, fields='ts_code,trade_date, close')
            个股_估计.sort_values(by="trade_date" , inplace=True, ascending=True) 
            个股_估计['log_price'] = np.log(个股_估计.close)
            个股_估计['个股日收益率'] = 个股_估计.log_price.diff()
            个股_估计.dropna(inplace = True)
            个股_估计.drop(['close','log_price'], inplace=True, axis = 1)
            估计区间1 = 个股_估计.iloc[0, 1] #修正工作日的影响
            估计区间2 = 个股_估计.iloc[-1, 1]
            个股_估计 = 个股_估计.reset_index(drop = True)
            
            print ('当前是第', w,'次','估计指数数据')
            index_1 = market_df[market_df['年月日'] == 估计区间1].index.tolist()[0]
            index_2 = market_df[market_df['年月日'] == 估计区间2].index.tolist()[0]
            指数_估计 = market_df.iloc[index_1:index_2+1, [1,2]]
            指数_估计 = 指数_估计.reset_index(drop = True)
            
            print ('当前是第', w,'次','OLS')
            ols = pd.DataFrame({
                '估计区间内个股收益率': 个股_估计.个股日收益率,
                '估计区间内指数收益率': 指数_估计.指数日收益率}) 
            ols_result = smf.ols("估计区间内个股收益率 ~ 估计区间内指数收益率", data = ols).fit()
            α = ols_result.params[0]
            β = ols_result.params[1]
            
            print ('当前是第', w,'次','事件预期收益率')
            估计区间2 = pd.to_datetime(估计区间2)
            定位 = workingday_df[workingday_df['年月日'] == 估计区间2].index.tolist()[0]
            事件区间1 = workingday_df.iloc[定位+1, 1].strftime('%Y%m%d')
            事件区间2 = workingday_df.iloc[定位+total_day, 1].strftime('%Y%m%d')
            index_1 = market_df[market_df['年月日'] == 事件区间1].index.tolist()[0]
            index_2 = market_df[market_df['年月日'] == 事件区间2].index.tolist()[0]
            事件 = market_df.iloc[index_1:index_2+1, [1,2]]
            事件 = 事件.reset_index(drop = True)
            事件['个股预期收益率'] = ''
            for q in range (0, total_day):
                事件.iloc[q, 2] = α + β*事件.iloc[q, 0]
                事件["个股预期收益率"] = pd.to_numeric(事件["个股预期收益率"],errors='coerce')
            
            
            print ('当前是第', w,'次','超额收益率')
            估计区间2 = 估计区间2.strftime('%Y%m%d')
            个股_事件 = pro.daily(ts_code=代码, start_date=估计区间2, end_date=事件区间2, fields='ts_code,trade_date, close')
            个股_事件.sort_values(by="trade_date" , inplace=True, ascending=True) 
            个股_事件['log_price'] = np.log(个股_事件.close)
            个股_事件['个股实际日收益率'] = 个股_事件.log_price.diff()
            个股_事件.dropna(inplace = True)
            个股_事件.drop(['close','log_price'], inplace=True, axis = 1)
            个股_事件 = 个股_事件.reset_index(drop = True)
            事件['个股实际日收益率'] = 个股_事件['个股实际日收益率']
            事件['AR'] = 事件['个股实际日收益率']-事件['个股预期收益率']
            temp.iloc[:, w] = 事件['AR']
        
            w+=1
            
   
        except IndexError:
            print(w, '出错！')
        continue
    df_result = temp.copy()
    #df_result.dropna(axis=1, how='any', inplace=True)
    return df_result

#%% 计算caar
def caar(total_df ):
    total_df['AAR'] = total_df.sum(axis=1)/total_df.shape[1]
    CAR = pd.Series(total_df.sum(axis = 0), name = 'CAR')
    total_df = total_df.append(CAR)
    total_df.loc['CAR','AAR'] = None
    total_df['CAAR'] = total_df['AAR'].cumsum()
    result_df=total_df.copy()
    #result_df.columns = range(result_df.shape[1])
    return result_df

#%% t检验
def t_test(result_df, range_day_1, range_day_2):
    total_day = -range_day_1 + range_day_2 + 1
    aar_caar = result_df[['AAR', 'CAAR']]
    aar_caar = aar_caar.drop('CAR', axis=0)
    std_aar = np.std(aar_caar['AAR'], ddof = 1)
    std_caar = np.std(aar_caar['CAAR'], ddof = 1)
    aar_caar['AAR_t'] = aar_caar['AAR']*math.sqrt(total_day)/std_aar
    aar_caar['CAAR_t'] = aar_caar['CAAR']*math.sqrt(total_day)/std_caar
    aar_caar = aar_caar[['AAR','AAR_t','CAAR','CAAR_t']]
    aar_caar['star_aar'] = ''
    aar_caar['star_caar'] = ''
    #t检验 双尾  41  1.685  2.023   2.708

    for i in range (0,total_day):
        target = aar_caar.iloc[i, 1]
        if target <= -2.708 or target >= 2.708:
            aar_caar.iloc[i, 4] = "***"
        if (target >= 2.023 and target <2.708) or (target <= -2.023 and target > -2.708):
            aar_caar.iloc[i, 4] = "**"
        if (target >= 1.685 and target < 2.023) or (target <= -1.685 and target > -2.023):
            aar_caar.iloc[i, 4] = "*"
        
    for i in range (0, total_day):
        target = aar_caar.iloc[i, 3]
        if target <= -2.708 or target >= 2.708:
            aar_caar.iloc[i, 5] = "***"
        if (target >= 2.023 and target <2.708) or (target <= -2.023 and target > -2.708):
            aar_caar.iloc[i, 5] = "**"
        if (target >= 1.685 and target < 2.023) or (target <= -1.685 and target > -2.023):
            aar_caar.iloc[i, 5] = "*"

    aar_caar = aar_caar[['AAR','AAR_t','star_aar','CAAR','CAAR_t','star_caar']]
    temp_list = list(range(range_day_1,range_day_2+1))
    aar_caar.insert(loc = 0, column = '天数', value = temp_list)
    return aar_caar
