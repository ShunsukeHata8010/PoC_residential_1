from numpy.lib.financial import pv
import pandas as pd
import glob
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from weather_warning import warning
import sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))#2つ上のディレクトリからインポートするとき
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))#1つ上のディレクトリからインポートするとき
from nextdriveAPI_class import House
from create_csv_from_database import read_database,Data,create_df
from get_info_from_userlist import get_info_from_userlist
from calc_battery_direction import calc_battery_direction


if __name__ == '__main__':
#ユーザー情報からの取り出し（1件ずつ）
    #os.chdir("C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報")
    path_origin = os.path.dirname(os.path.abspath(__file__)).replace('\\optimazation_program','')  #このファイルのあるディレクトリの一つ上のパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除
    
    #number=2#予測を実行したい施設の番号を記入（2は岩村さん宅）
    #i=number-1
    for number in df_user.index:
        i=number-1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        if flag_battery=='Yes'and flag_ecocute=='No':#蓄電池のみのケース
            print(name,'は、蓄電池のみを持っており、後続の計算を行います。')
            house = House(name,id)
            db_session = read_database(name,id)
            db = db_session.query(Data).all()
            df = create_df(db)
            pv_yosoku = df.loc[:,['日時','予測値_PV']]
            pv_yosoku = pv_yosoku.replace({None:np.nan})#Noneのままのところもある。
            pv_yosoku = pv_yosoku.dropna(how='all', axis=1)#すべてがnanの列を削除
            
            if not '予測値_PV' in df.columns :
                print('PV予測値がありませんでした')
            else:
                demand_yosoku = df.loc[:,['日時','予測値_demand']]
                demand_yosoku = demand_yosoku.replace({None:np.nan})#Noneのままのところもある。
                demand_yosoku = demand_yosoku.dropna(how='all', axis=1)#すべてがnanの列を削除
                print(demand_yosoku)
                if not '予測値_demand' in df.columns :
                    print('需要電力予測値がありませんでした')
                else:
                    calc_battery_direction(name,id,house,power_com,pv_yosoku,demand_yosoku,address,inputpower_batt,capacity_batt,outputpower_batt,maxSOC_batt,minSOC_batt,effi_batt)
                    print(name,'の蓄電池への指示を終了します')
        elif flag_battery=='No'and flag_ecocute=='Yes':#エコキュートのみのケース
            print('エコキュートの方を作ってそれをコピーする')
        
        elif flag_battery=='Yes'and flag_ecocute=='Yes':#両方のケース
            print('エコキュートと蓄電池の両方はまだ作っていません。')#エコキュートは22時頃の実行で、その結果をどこかに保持しておく、蓄電池は30分毎
            #現在時刻を拾ってきて、22時頃ならエコキュート実行、それ以外は保持している場所からエコキュート稼働計画を取得して蓄電池最適化を回す
        else:
            print(name,'は蓄電池もエコキュートももっていないため、何もしません。')