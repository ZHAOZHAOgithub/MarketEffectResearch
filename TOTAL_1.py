# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 16:10:18 2021

@author: Admin
"""

import pandas as pd
import tushare as ts
pro=ts.pro_api('8f05588b513af3bae5df8312ccf5e6d724712ef425b18be9f5b77ee0')
from function import set_range
from function import ar
from function import caar
from function import t_test
from function_2 import roe
from function_2 import liabilityToAsset
from function_2 import eps
from function_2 import dupontAssetTurn

#%% 导入数据
df1 = pd.read_excel('2019-0.1.xls')

df1.dtypes

df1.shape
df1.head()
df2 = df1[['代码','名称','公告日期','占流通股比例(%)']]

#先排序
df3 = df2.groupby(['代码','名称']).apply(lambda x: x.sort_values('公告日期'))
df3 = df3.reset_index(drop = True)

#转换时间格式
df3['日期'] = pd.to_datetime(df3['公告日期'], format='%Y-%m-%d')
df3.drop('公告日期', inplace=True, axis = 1)

#%% 按照增持比例区分

df3.rename(columns={'占流通股比例(%)':'增持比例(%)'}, inplace = True)

order = ['代码','名称', '日期','增持比例(%)']
df3 = df3 [order]



#%% 按照20日的标准筛选
selected = pd.DataFrame(columns=['代码','名称', '公告日期','增持比例(%)'])
standard_delta = pd.Timedelta(days = 20)

#放入第一个：
selected.loc[0]=[df3.iloc[0, 0],df3.iloc[0, 1], df3.iloc[0,2], df3.iloc[0, 3] ]
for i in range (1, df3.shape[0]): #漏第一个
    if df3.iloc[i, 0] != df3.iloc[i-1, 0]: #当前和上一个名称不同，当前的进入slected
        selected.loc[i]=[df3.iloc[i, 0],df3.iloc[i, 1], df3.iloc[i, 2], df3.iloc[i, 3]]
        a = selected.iloc[-1, 2] #最新selected
        i+=1
    else:  
        a = selected.iloc[-1, 2]
        delta = df3.iloc[i, 2] - a
        if delta > standard_delta:  #如果大于一个月，当前进入selected
            selected.loc[i]=[df3.iloc[i, 0],df3.iloc[i, 1], df3.iloc[i, 2],df3.iloc[i, 3]]
            a = selected.iloc[-1, 2]
            i+=1
        else: #如果小于等于一个月，当前的跳过
            i+=1
selected = selected.reset_index(drop=True)  

#%% 划分比例

增持比例 = selected['增持比例(%)'].to_list()

大比例 = selected[(selected['增持比例(%)']>=0.1)]
小比例 = selected[(selected['增持比例(%)']<0.1)]

#%% 区分国有控股和非国有控股
temp_df = pd.read_excel('上市公司实际控制人.xls')
国有列表 = temp_df['代码'].to_list()
国有 = selected[selected['代码'].isin(国有列表)]
非国有 = selected[~selected['代码'].isin(国有列表)]


#%% 区间函数
大比例区间 = set_range (大比例, -120, -21, -20, 20)
小比例区间 = set_range (小比例, -120, -21, -20, 20)
国有区间 = set_range (国有, -120, -21, -20, 20)
非国有区间 = set_range (非国有, -120, -21, -20, 20)
总样本区间 = set_range (selected, -120, -21, -20, 20)

#%% 确定个股的超额收益率

#首先，计算估计区间内的个股每天收益率和指数每天收益率。
#并用ols计算个股的预期收益率：R个股 = α + βR指数 
#然后运用ols带入事件区间计算预期收益
#计算事件区间内的实际收益
#实际收益-预期收益=超额收益率
#%%%准备工作
创业板指数 = pd.read_excel('创业板指.xls')
创业板指数.dtypes
创业板指数['年月日'] = pd.to_datetime(创业板指数['日期'], format='%Y-%m-%d')
创业板指数.drop('日期', inplace=True, axis = 1)
国内工作日 = 创业板指数['年月日']
国内工作日 = 国内工作日.reset_index()
创业板指数['年月日'] = 创业板指数['年月日'].apply(lambda x: x.strftime('%Y%m%d'))
#创建一个空的dataframe。行是种类；列是时间[-20,20]

#%%

total_大比例 = ar(大比例, 大比例区间, 创业板指数, 国内工作日,-20, 20)
total_小比例 = ar(小比例, 小比例区间, 创业板指数, 国内工作日,-20, 20)
total_国有 = ar(国有, 国有区间, 创业板指数, 国内工作日,-20, 20)
total_非国有 = ar(非国有, 非国有区间, 创业板指数, 国内工作日,-20, 20)
total_总样本 = ar(selected, 总样本区间, 创业板指数, 国内工作日,-20, 20)
total_总样本.to_excel('总样本car.xlsx')
#%% CAAR函数
#CAR（累计超额收益率）是某股票所有时刻相加
#AAR（平均超额收益）是某时刻所有股票相加后平均
#CAAR （累计平均超额收益率）是AAR的累计值

#%%
result_大比例 = caar(total_大比例)
result_小比例 = caar(total_小比例)
result_国有 = caar(total_国有)
result_非国有 = caar(total_非国有)
result_总样本 = caar(total_总样本)
result_总样本.to_excel('总样本caar.xlsx')
#%%检验统计量函数

大比例t = t_test(result_大比例,-20, 20)
大比例t.to_excel('大比例t值检验表.xlsx')

小比例t = t_test(result_小比例,-20, 20)
小比例t.to_excel('小比例t值检验表.xlsx')

国有t = t_test(result_国有,-20, 20)
国有t.to_excel('国有t值检验表.xlsx')

非国有t = t_test(result_非国有,-20, 20)
非国有t.to_excel('非国有t值检验表.xlsx')

总样本t = t_test(result_总样本, -20, 20)
总样本t.to_excel('总样本t值检验表.xlsx')

#%% 线性回归中的控制变量
异质性 = selected
roe(异质性)
liabilityToAsset(异质性)
dupontAssetTurn(异质性)
eps(异质性)
异质性.to_excel('控制变量.xlsx')

#%% 

