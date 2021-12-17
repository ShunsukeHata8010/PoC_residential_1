import os

from numpy.lib.type_check import imag
from nextdriveAPI_class import House
import pandas as pd
from get_info_from_userlist import get_info_from_userlist
from datetime import datetime, date, timedelta
import numpy as np
from database_mysql import create_database, update_database
import sqlalchemy
import math


if __name__ == '__main__':
    #os.chdir('C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報')
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)  #備考行は削除

    for number in df_user.index:
        i = number-1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        #nameとIDがある行に対して、インスタンスを作成
        if flag_battery =='No':
            print(name,'は蓄電池を含んでいないので状態取得しません。')
        else:
            House_battery = House(name,id)
            battery_latest_status,gettime = House_battery.Get_latest_StgBattery_info()
            df = House_battery.Calc_latest_StgBattery_behavior()
            print(df)
            list_ = []
            for i in df['最終_時刻']:
                print(i)
                #iがnanの場合がある
                try:
                    #time = datetime.strptime(i, '%Y-%m-%d %H:%M:%S')
                    time = i.to_pydatetime()
                except AttributeError:
                    print(name,'は蓄電池がオフラインの可能性があります')
                else:
                    time_0 = time.replace(minute=0, second=0, microsecond=0)
                    time_30 = time.replace(minute=30, second=0, microsecond=0)
                    if time.hour ==23:
                        time_next_0 =time.replace(hour=0,minute=0, second=0, microsecond=0)
                    else:
                        time_next_0  = time.replace(hour=time.hour+1,minute=0, second=0, microsecond=0)
                    #9:05だとすると、9:00,9:30,10:00の中から9:00を選択
                    #8:55だとすると、8:00,8:30,9:00の中から9:00を選択
                    #8:35だとすると、8:00,8:30,9:00の中から8:30を選択
                    #するようにする
                    min_time = min(abs(time_30 - time) ,abs(time_0-time),abs(time_next_0-time))
                    if min_time == abs(time_30 - time):
                        df['日時']=time_30
                    elif min_time == abs(time_0-time):
                        df['日時']=time_0
                    elif min_time == abs(time_next_0-time):
                        df['日時']=time_next_0
                
                    list_.append(df)

                    df = pd.concat(list_, join='inner') # joinをinnerに指定
                    df['充放電量[Wh]'] = (df['放電可能量_増減']-df['充電量可能量_増減'])/2
                    df.drop(columns=['最終_時刻', '初期_時刻','経過時間','初期_状態','最終_状態','SOC_初期','SOC_最終'], inplace=True)
                    df = df.sort_values(['日時']) #予報時刻を優先してソート            
                    df = df.reindex(columns=['日時', 'SOC_増減', '充電量可能量_増減','放電可能量_増減','残電力量_増減'])
                    df = df.reset_index(drop=True) #インデックスの振り直し

                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                    
                    list_battery = []
                    list_battery_2 = []
                    list_aircon = []
                    list_ecocute = []
                    list_thermo = []
                    value_1 = None
                    value_2 = None
                    flag = 'B_updown'

                    for index ,row in df.iterrows():
                        time = row['日時']
                        if 'SOC_増減' in df.columns:#単位はkWhにそろえる
                            list_battery_2.append(row['SOC_増減'])
                            list_battery_2.append(row['充電量可能量_増減']/1000)
                            list_battery_2.append(row['放電可能量_増減']/1000)
                            if math.isnan(row['残電力量_増減']):
                                list_battery_2.append((-row['充電量可能量_増減']/1000+row['放電可能量_増減']/1000)/2)
                            else:
                                list_battery_2.append(row['残電力量_増減']/1000)
                            #time = dt.strptime(row['予測時刻'], '%Y-%m-%d %H:%M:%S')
                        try:
                            create_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
                        except sqlalchemy.exc.IntegrityError:
                            print('日時に重複があります')
                            update_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
