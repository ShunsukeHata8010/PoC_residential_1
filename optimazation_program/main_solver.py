from numpy.lib.financial import pv
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from weather_warning import warning
import sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))#2つ上のディレクトリからインポートするとき
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))#1つ上のディレクトリからインポートするとき
from nextdriveAPI_class import House
from create_csv_from_database import read_database,Data,create_df,create_df_pre
from database_mysql_for_jepx import read_database_jepx,Data_jepx,create_df_jepx
from get_info_from_userlist import get_info_from_userlist
from calc_battery_direction import calc_battery_direction


if __name__ == '__main__':
#ユーザー情報からの取り出し（1件ずつ）
    path_origin = os.path.dirname(os.path.abspath(__file__)).replace('\\optimazation_program','')  #このファイルのあるディレクトリの一つ上のパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除
    pd.set_option('display.max_rows', 1500)
    #number=2#予測を実行したい施設の番号を記入（2は岩村さん宅）
    #i=number-1
    for number in df_user.index:
        i=number-1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        if name=='kojima' and flag_battery=='Yes'and flag_ecocute=='No':#蓄電池のみのケース
            print(name,'は、蓄電池のみを持っており、後続の計算を行います。')
            house = House(name,id)
            now = datetime.now()
            #ここで現在コマより新しい行だけをとってくるための作業をする            
            time_0 = now.replace(minute=0, second=0, microsecond=0)
            time_30 = now.replace(minute=30, second=0, microsecond=0)
            time_next_0  = now.replace(hour=now.hour+1,minute=0, second=0, microsecond=0)
            #今9:05だとすると、今のコマは9:30、9:00,9:30,10:00 この件では、9:30にしたい
            #今8:55だとすると、今のコマは9:00、8:00,8:30,9:00　この件では、9:00にしたい
            #今8:35だとすると、今のコマは9:00、8:00,8:30,9:00  この件では、9:00にしたい
            #今8:29だとすると、今のコマは8:30、8:00,8:30,9:00    この件では、8:30にしたい
            #なので、この３パターンのどれかということでOK
            if time_0 - now  and time_0 - now <=  timedelta(minutes=30):
                current_koma = time_0
            if time_30 - now  and time_30 - now <=  timedelta(minutes=30):
                current_koma = time_30
            if time_next_0 - now and time_next_0 - now <=  timedelta(minutes=30):
                current_koma = time_next_0

            db_session_house = read_database(name,id)
            db_house = db_session_house.query(Data.time,Data.PV_pre,Data.demand_pre).filter(Data.time >=current_koma)
            df_pre = create_df_pre(db_house)
            pv_pre = df_pre.loc[:,['日時','予測値_PV']]
            pv_pre = pv_pre.replace({None:np.nan})#Noneのままのところもある。
            #pv_pre = pv_pre.dropna(how='all', axis=1)#すべてがnanの列を削除

            db_session_jepx = read_database_jepx(power_com)
            db_jepx = db_session_jepx.query(Data_jepx.time,Data_jepx.price).filter(Data_jepx.time >= current_koma)
            df_jepx = create_df_jepx(db_jepx)
            df_jepx = df_jepx.loc[:,['日時','価格']]

            if not '予測値_PV' in df_pre.columns :#これは意味ないが、、
                print('PV予測値がありませんでした')
            else:
                demand_pre = df_pre.loc[:,['日時','予測値_demand']]
                demand_pre = demand_pre.replace({None:np.nan})#Noneのままのところもある。
                demand_pre = demand_pre.dropna(how='all', axis=1)#すべてがnanの列を削除
                #print(demand_pre)
                if not '予測値_demand' in df_pre.columns :
                    print('需要電力予測値がありませんでした')
                else:
                    calc_battery_direction(name,id,power_com,house,df_jepx,pv_pre,demand_pre,address,inputpower_batt,capacity_batt,outputpower_batt,maxSOC_batt,minSOC_batt,effi_batt)
                    print(name,'の蓄電池への指示を終了します')
        elif flag_battery=='No'and flag_ecocute=='Yes':#エコキュートのみのケース
            print('エコキュートの方を作ってそれをコピーする')
        
        elif flag_battery=='Yes'and flag_ecocute=='Yes':#両方のケース
            print('エコキュートと蓄電池の両方はまだ作っていません。')#エコキュートは22時頃の実行で、その結果をどこかに保持しておく、蓄電池は30分毎
            #現在時刻を拾ってきて、22時頃ならエコキュート実行、それ以外は保持している場所からエコキュート稼働計画を取得して蓄電池最適化を回す
        else:
            print(name,'は蓄電池もエコキュートももっていないため、何もしません。')