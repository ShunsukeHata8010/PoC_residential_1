from database_mysql import create_database,update_database
from datetime import datetime
import os
import pandas as pd
from get_info_from_userlist import get_info_from_userlist
from prediction_generation_for_each_house import calc_generation
import sqlalchemy
from logging import getLogger, Formatter, FileHandler, DEBUG
import configparser

#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']
#ロガーの設定
logger = getLogger('main_pv_prediction')#実行ファイル名
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

    for number in df_user.index:
        i = number - 1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        if flag_pv == 'No':
            print(name,'はPVを含んでいませんので予測しません。')
        else:
            print(name,id,'のPV予測を開始します')
            df = calc_generation(Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku,kage_x,kage_y,kage_h,kage_Φ)
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            list_battery = []
            list_battery_2 = []
            list_aircon = []
            list_ecocute = []
            list_thermo = []
            value_1 = None
            value_2 = None
            flag ='PV_pre'
            for index ,row in df.iterrows():
                time = row['予測時刻']
                #time = dt.strptime(row['予測時刻'], '%Y-%m-%d %H:%M:%S')
                try:
                    value_1 = row['予測値_PV']/2 #ここで単位を整える(kW→kWh)
                    create_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
                except sqlalchemy.exc.IntegrityError:
                    print('日時に重複があります')
                    value_1 = row['予測値_PV']/2 #ここで単位を整える(kW→kWh)
                    update_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
