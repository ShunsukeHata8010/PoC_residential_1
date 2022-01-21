import pandas as pd
import numpy as np
import os
from datetime import datetime, date, timedelta
import sys
from nextdriveAPI_class import House
from main_create_csv_from_database import read_database,Data,create_df_pre
from database_mysql_for_jepx import read_database_jepx,Data_jepx,create_df_jepx
from get_info_from_userlist import get_info_from_userlist
from calc_battery_direction import calc_battery_direction

import configparser
from logging import getLogger, Formatter, FileHandler, DEBUG

#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']

#ロガーの設定
logger = getLogger('main_solver')#実行ファイル名
logger.setLevel(DEBUG)
file_handler = FileHandler(filename=LOG_FILE_NAME_1, encoding='utf-8')#logファイルは全部共通にする
file_handler.setLevel(DEBUG)
handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(handler_format)
logger.addHandler(file_handler)

if __name__ == '__main__':
    os.chdir(USER_INFORMATION_FOLDER)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除
    pd.set_option('display.max_rows', 1500)
    for number in df_user.index:
        i = number - 1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        if flag_battery == 'Yes' and flag_ecocute == 'No':#蓄電池のみのケース
            print(name,'は、蓄電池のみを持っており、後続の計算を行います。')
            house = House(name,id)
            now = datetime.now()
            #現在時刻から分を0にした時刻、分を30にした時刻、分を次の時間の0にした時刻を出す           
            time_0 = now.replace(minute=0, second=0, microsecond=0)
            time_30 = now.replace(minute=30, second=0, microsecond=0)
            if now.hour == 23:
                time_next_0 = now.replace(hour=0,minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                time_next_0 = now.replace(hour=now.hour+1,minute=0, second=0, microsecond=0)
            #今のコマを算出する
            if time_0 - now  and time_0 - now <=  timedelta(minutes=30):
                current_koma = time_0
            if time_30 - now  and time_30 - now <=  timedelta(minutes=30):
                current_koma = time_30
            if time_next_0 - now and time_next_0 - now <=  timedelta(minutes=30):
                current_koma = time_next_0

            db_session_house = read_database(name,id)
            #今のコマより新しいレコードだけとる
            db_house = db_session_house.query(Data.time,Data.PV_pre,Data.demand_pre).filter(Data.time >=current_koma)
            df_pre = create_df_pre(db_house)
            if type(df_pre) is str:
                print(name,'データベースが作成されていない可能性があります。')
            else:
                pv_pre = df_pre.loc[:,['日時','予測値_PV']]
                pv_pre = pv_pre.replace({None:np.nan})#Noneのままのところもある。
                pv_pre = pv_pre.dropna(how='all', axis=1)#全部がnanだと削除

                db_session_jepx = read_database_jepx(power_com)
                #今のコマより新しいレコードだけとる
                db_jepx = db_session_jepx.query(Data_jepx.time,Data_jepx.price).filter(Data_jepx.time >= current_koma)
                df_jepx = create_df_jepx(db_jepx)
                df_jepx = df_jepx.loc[:,['日時','価格']]
                df_jepx = df_jepx.dropna(how='all', axis=1)#全部がnanだと削除

                if not '予測値_PV' in pv_pre.columns :
                    print('PV予測値がありませんでした')
                if not '価格' in df_jepx.columns:
                    print('jepxの価格がありませんでした')
                else:
                    demand_pre = df_pre.loc[:,['日時','予測値_demand']]
                    demand_pre = demand_pre.replace({None:np.nan})#Noneのままのところもある。
                    demand_pre = demand_pre.dropna(how='all', axis=1)#すべてがnanの列を削除
                    if not '予測値_demand' in demand_pre.columns :
                        print('需要電力予測値がありませんでした')
                    else:
                        calc_battery_direction(name,id,power_com,house,df_jepx,pv_pre,demand_pre,address,inputpower_batt,capacity_batt,outputpower_batt,maxSOC_batt,minSOC_batt,effi_batt)
                        print(name,'の蓄電池への指示を終了します')
        elif flag_battery == 'No' and flag_ecocute == 'Yes':#エコキュートのみのケース
            print('エコキュートの方を作ってそれをコピーする')
        
        elif flag_battery == 'Yes' and flag_ecocute == 'Yes':#両方のケース
            print('エコキュートと蓄電池の両方はまだ作っていません。')#エコキュートは22時頃の実行で、その結果をどこかに保持しておく、蓄電池は30分毎
            #現在時刻を拾ってきて、22時頃ならエコキュート実行、それ以外は保持している場所からエコキュート稼働計画を取得して蓄電池最適化を回す
        else:
            print(name,'は蓄電池もエコキュートももっていないため、何もしません。')