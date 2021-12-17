import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))#2つ上のディレクトリからインポートするとき
from nextdriveAPI_class import House
from get_info_from_userlist import get_info_from_userlist

if __name__ == '__main__':
#ユーザー情報からの取り出し（1件ずつ）
    #os.chdir("C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報")
    path_origin = os.path.dirname(os.path.abspath(__file__)).replace('\\optimazation_program','') #このファイルのあるディレクトリの一つ上のパスを取得
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
        
        if flag_battery=='Yes':
            house = House(name,id)
            print(house.Control_StgBattery('Automatic',0,0))
            print(name+'の蓄電池をリリース完了')