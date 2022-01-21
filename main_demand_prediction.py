from database_mysql import create_database,update_database
from datetime import datetime
import os
import pandas as pd
from get_info_from_userlist import get_info_from_userlist
from prediction_demand_for_each_house import calc_demand
import sqlalchemy
from logging import getLogger, Formatter, FileHandler, DEBUG
import configparser

#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']

#ロガーの設定
logger = getLogger('main_demand_prediction')
logger.setLevel(DEBUG)
file_handler = FileHandler(filename=LOG_FILE_NAME_1, encoding='utf-8')
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
        
        if flag_smart == 'No':
            print(name,'はスマメを含んでいませんので予測しません。')
        else:
            df = calc_demand(name,id)
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            list_battery = []
            list_battery_2 = []
            list_aircon = []
            list_ecocute = []
            list_thermo = []
            value_1 = None
            value_2 = None
            flag = 'demand_pre'
            if df is None:
                #ロガー
                logger = getLogger('main_demand_prediction')
                logger.debug('{0}:{1}:{2}'.format(name,id,'需要予測できず(データ無し)'))
                print(name,'予測できませんでした。')
            elif type(df) is str:#１週間分無い時はdfは'not less than one week'というstr
                logger = getLogger('main_demand_prediction')
                logger.debug('{0}:{1}:{2}'.format(name,id,'需要予測できず(データ１週間分無し)'))
                print(name,'は一週間分のデータがなく予測できませんでした')
            else:
                for index ,row in df.iterrows():
                    time = index
                    #time = dt.strptime(row['予測時刻'], '%Y-%m-%d %H:%M:%S')
                    try:
                        value_1 = row['予測値_demand']#(単位は元々kWh)
                        create_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
                        print(name,'需要電力予測値をadd(Create)します')
                    except sqlalchemy.exc.IntegrityError:
                        print('日時に重複があります')
                        value = row['予測値_demand']#(単位は元々kWh)
                        update_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
                
                logger = getLogger('main_demand_prediction')
                logger.debug('{0}:{1}:{2}'.format(name,id,'需要予測完了'))