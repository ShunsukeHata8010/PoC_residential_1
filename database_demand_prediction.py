
from database_mysql import create_database,update_database
from datetime import datetime
import os
import pandas as pd
from get_info_from_userlist import get_info_from_userlist
from prediction_demand_for_each_house import calc_demand
import sqlalchemy


if __name__ == '__main__':
    #os.chdir("C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報")
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除

    for number in df_user.index:
        i=number-1
        name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
        capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
        flag_smart,flag_pv,flag_battery,flag_ecocute = get_info_from_userlist(df_user,i)

        #発電量予測値
        #nameとIDがある行に対して、インスタンスを作成
        if flag_smart =='No':
            print(name,'はスマメを含んでいませんので予測しません。')
        else:
            print(name,id)
            
            df = calc_demand(name,id)
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            print(df)
            
            list_battery = []
            list_battery_2 = []
            list_aircon = []
            list_ecocute = []
            list_thermo = []
            value_1 = None
            value_2 = None
            flag = 'demand_pre'
            if df is None:
                print(name,'予測できませんでした。')
            elif type(df) is str:#１週間分無い時はdfは'not less than one week'というstr
                print(df)
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
