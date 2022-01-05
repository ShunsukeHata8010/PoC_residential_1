from numpy.core.fromnumeric import reshape
import pandas as pd
import os
from datetime import datetime, date, timedelta
from nextdriveAPI_class import House_init,House
from database_mysql import create_database,update_database
import sqlalchemy


if __name__ == '__main__':
    base_url = 'https://ioeapi.nextdrive.io/v1/gateways/'
    headers = {
        #'X-ND-TOKEN':'wDqFBnuuZPMbfpwC958pSjT7x+kX9raG8PX4Rl3',#旧APIキー
        'X-ND-TOKEN':'WhxgcOFnTMR0ZvC4qAj8Waovr4turnsmslO74gb',#新APIキー
        'content-type':'application/json'
    }
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除

    #nameとIDがある行に対して、インスタンスを作成
    for status,name ,id in zip(df_user['active'],df_user['name'],df_user['Product ID']):
        name = str(name)
        id = str(id)
        print(name,id,'の情報取得作業を開始します')

        if status =='No':
            print(name,'はアクティブではありません。')
        else:
            House_init(name,id).store_uuid()#本当の1回目だけでOK（UUIDを格納したjsonファイルを作成する）
            df = House(name,id).store_30min()            
            list_aircon = []
            list_battery = []
            list_battery2 = []
            list_ecocute = []
            list_thermo = []
            value_1 = None
            value_2 = None
            if df is None:
                print(name,'取得したデータは空でした')
            else:
                df = df.loc[:,~df.columns.duplicated()]#エアコンが2台あったら1台目だけにする
                df = df.dropna(how='all', axis=1)
                flag = ''
                for index ,row in df.iterrows():
                    time = index
                    if 'PV発電量' in df.columns:
                        flag = flag +'PVactual_'
                        PV_actual = row['PV発電量']/1000/2#ここで単位を整える(W→kWh)
                        value_1 = PV_actual
                    if '順潮流' in df.columns:
                        flag = flag +'kaiden_'
                        kaiden = row['順潮流']/1000/2#ここで単位を整える（W→kWh）
                        value_2 = kaiden
                    if 'battery状態' in df.columns:
                        flag = flag +'Battery_'
                        list_battery.append(row['battery状態'])
                        list_battery.append(row['SOC'])
                        list_battery.append(row['充電可能量']/1000)#ここで単位をそろえる(Wh→kWh)
                        list_battery.append(row['放電可能量']/1000)#ここで単位をそろえる(Wh→kWh)
                        try:#残電力がnanの時（とりあえず対処療法）
                            list_battery.append(row['残電力量']/1000)#ここで単位をそろえる(Wh→kWh)
                        except KeyError:
                            list_battery.append(None)
                    if 'ｴｱｺﾝ状態'in df.columns:
                        flag = flag +'Aircon_'
                        list_aircon.append(row['ｴｱｺﾝ状態'])
                        list_aircon.append(row['ｴｱｺﾝmode'])
                        list_aircon.append(row['ｴｱｺﾝ設定温度'])
                    if '動作状態' in df.columns:
                        flag = flag +'Ecocute_'
                        list_ecocute.append(row['動作状態'])
                        list_ecocute.append(row['沸き上げ自動設定'])
                        list_ecocute.append(row['沸き上げ中状態'])
                        if 'エネルギーシフト参加状態' in df.columns:
                            list_ecocute.append(row['エネルギーシフト参加状態'])
                            list_ecocute.append(row['沸き上げ開始基準時刻'])
                            list_ecocute.append(row['エネルギーシフト回数'])
                            list_ecocute.append(row['昼間沸き上げシフト時刻1'])
                        else:
                            list_ecocute.append(None)
                            list_ecocute.append(None)
                            list_ecocute.append(None)
                            list_ecocute.append(None)
                        #データ取れていなければ、nanになる。
                    try:
                        create_database(name,id,time,value_1,value_2,list_battery,list_battery2,list_ecocute,list_aircon,list_thermo,flag)
                        print(name,'getによる取得データをadd(Create)します')
                    except sqlalchemy.exc.IntegrityError:
                        print(name,'日時に重複があるのでupdateにてデータを格納します')
                        update_database(name,id,time,value_1,value_2,list_battery,list_battery2,list_ecocute,list_aircon,list_thermo,flag)
