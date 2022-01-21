import os
import sys
import pandas as pd
import configparser
from logging import getLogger, Formatter, FileHandler, DEBUG

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))#2つ上のディレクトリからインポートするとき
from nextdriveAPI_class import House
from get_info_from_userlist import get_info_from_userlist

#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']
#ロガーの設定
logger = getLogger('battery_end')#実行ファイル名
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
    
    #number=2#予測を実行したい施設の番号を記入（2は岩村さん宅）
    for number in df_user.index:
        i = number - 1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)
        
        if flag_battery == 'Yes':
            house = House(name,id)
            response = house.Control_StgBattery('Automatic',0,0)
            if response.status_code == 200:
                print(name+'の蓄電池を無事にリリース完了しました')
            else:
                print(name,response,'エラーが出てリリースできませんでした')