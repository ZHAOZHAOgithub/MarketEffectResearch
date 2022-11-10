# -*- coding: utf-8 -*-
"""
线性回归用到的所有函数
"""
import pandas as pd
import baostock as bs

#%% 大股东兼任高管(兼任是1，否则是0)
def manager(target):
    高管 = pd.read_excel('大股东兼任高管.xls', usecols=['代码'] )
    高管['兼任高管'] = 1
    target['兼任高管'] = 0
    company = target[['代码','兼任高管']]
    temp = pd.merge(company, 高管, on='代码' ,how='left')
    for i in range (0, len(temp)):
        if temp.iloc[i, 2]== 1:
            temp.iloc[i, 1] =1
            i+=1
        else:
            i+=1
    target['兼任高管'] = temp['兼任高管_x']
    return target



#%% 公司所有权（国有是1，非国有是0）
def owner(target):
    实际控制人 = pd.read_excel('上市公司实际控制人.xls', usecols=['代码'] )
    实际控制人['所有权'] = 1
    target['所有权'] = 0
    company = target[['代码','所有权']]
    temp = pd.merge(company, 实际控制人, on='代码' ,how='left')
    for i in range (0, len(temp)):
        if temp.iloc[i, 2]== 1:
            temp.iloc[i, 1] =1
            i+=1
        else:
            i+=1
    target['所有权'] = temp['所有权_x']
    return target
#%%净资产收益率（企业盈利水平）

def roe(target):   
    target['roe'] = 'nan'
    position = target.columns.get_loc('roe')
    bs.login()
    for i in range (0, len(target)):
        try:
            print('当前是第',i,'次')
            bs.login()
            dupont_list=[]
            code = target.iloc[i, 0]
            year = target.iloc[i, 2].year
            quarter = target.iloc[i,2].quarter 
            rs_dupont = bs.query_dupont_data(code, year, quarter)
            while (rs_dupont.error_code == '0') & rs_dupont.next():
                dupont_list.append(rs_dupont.get_row_data())
            result_profit = pd.DataFrame(dupont_list, columns=rs_dupont.fields)
            roe = result_profit.iloc[0,3]
            target.iloc[i, position] = roe
        except IndexError:
            print(i, '出错！')
        continue
    bs.logout()
    return target

#%% 每股收益
def eps(target):   
    target['每股收益'] = 'nan'
    position = target.columns.get_loc('每股收益')
    bs.login()
    for i in range (0, len(target)):
        try:
            print('当前是第',i,'次')
            bs.login()
            profit_list = []
            code = target.iloc[i, 0]
            year = target.iloc[i, 2].year
            quarter = target.iloc[i,2].quarter 
            rs_profit = bs.query_profit_data(code, year, quarter)
            while (rs_profit.error_code == '0') & rs_profit.next():
                profit_list.append(rs_profit.get_row_data())
            result_profit = pd.DataFrame(profit_list, columns=rs_profit.fields)
            eps = result_profit.iloc[0,7]
            target.iloc[i, position] = eps
        except IndexError:
            print(i, '出错！')
        continue
    bs.logout()
    return target


#%% 资产负债率

def liabilityToAsset(target):
    target['资产负债率'] = 'nan'
    position = target.columns.get_loc('资产负债率')
    bs.login()
    for i in range (0, len(target)):
        try:
            print('当前是第',i,'次')
            bs.login()
            balance_list = []
            code = target.iloc[i, 0]
            year = target.iloc[i, 2].year
            quarter = target.iloc[i, 2].quarter 
            rs_balance = bs.query_balance_data(code, year, quarter)
            while (rs_balance.error_code == '0') & rs_balance.next():
                balance_list.append(rs_balance.get_row_data())
            result_balance = pd.DataFrame(balance_list, columns = rs_balance.fields)
            lta = result_balance.iloc[0,7]
            target.iloc[i, position] = lta
        except IndexError:
            print(i, '出错！')
        continue
    bs.logout()
    return target

#%% 总资产周转率

def dupontAssetTurn(target):   
    target['总资产周转率'] = 'nan'
    position = target.columns.get_loc('总资产周转率')
    bs.login()
    for i in range (0, len(target)):
        try:
            print('当前是第',i,'次')
            bs.login()
            dupont_list=[]
            code = target.iloc[i, 0]
            year = target.iloc[i, 2].year
            quarter = target.iloc[i,2].quarter 
            rs_dupont = bs.query_dupont_data(code, year, quarter)
            while (rs_dupont.error_code == '0') & rs_dupont.next():
                dupont_list.append(rs_dupont.get_row_data())
            result_profit = pd.DataFrame(dupont_list, columns=rs_dupont.fields)
            AssetTurn = result_profit.iloc[0,5]
            target.iloc[i, position] = AssetTurn
        except IndexError:
            print(i, '出错！')
        continue
    bs.logout()
    return target

