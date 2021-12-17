from math import pi
import os
import glob
import pandas as pd
import datetime
import jpholiday
from pandas.tseries.offsets import Minute
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from datetime import datetime, date, timedelta


def calc_demand(name,id):
    
    path_moto ="C:\\Users\\f-apl-admin\\住宅実証2\\データベース\\3.需要予測用学習データ\\"+name+'_'+id
    try:
        os.chdir(path_moto)
    except:
        print('需要予測学習データのフォルダに'+name+'_'+id +'のフォルダがありません。')
    else:

        allFiles = glob.glob(path_moto + "/*.csv")

        if len(allFiles)>1:
            print('読み込みファイルが2個以上あります。')
        else:
            for file in allFiles:#1つのファイルしかないという前提だが、forにしている。
                df = pd.read_csv(file,encoding="shift_jis")
 
        #今日と明日のカレンダー情報を取得
        today = datetime.today()
        tomorrow = today + timedelta(days=1)

        today_Yobi = today.strftime('%a') #曜日を取得
        tomorrow_Yobi= tomorrow.strftime('%a')
        today_Shuku = jpholiday.is_holiday(today)
        tomorrow_Shuku = jpholiday.is_holiday(tomorrow)
        tomorrow_month = tomorrow.month

        #一旦、全曜日0を入れる。（本日用）
        mon_today=tue_today=wed_today=thu_today=fri_today=sat_today=sun_today=hei_today=shuku_today=0
        if today_Yobi == "Mon":
            mon_today = 1
        if today_Yobi == "Tue":
            tue_today = 1
        if today_Yobi == "Wed":
            wed_today = 1
        if today_Yobi == "Thu":
            thu_today = 1
        if today_Yobi == "Fri":
            fri_today = 1
        if today_Yobi == "Sat":
            sat_today = 1
        if today_Yobi == "Sun":
            sun_today = 1
        if today_Shuku==True:
            shuku_today = 1
        if today_Shuku==False:
            hei_today = 1

        #一旦、全曜日0を入れる。（明日用）
        mon_tomo=tue_tomo=wed_tomo=thu_tomo=fri_tomo=sat_tomo=sun_tomo=hei_tomo=shuku_tomo=0
        if tomorrow_Yobi == "Mon":
            mon_tomo = 1
        if tomorrow_Yobi == "Tue":
            tue_tomo = 1
        if tomorrow_Yobi == "Wed":
            wed_tomo = 1
        if tomorrow_Yobi == "Thu":
            thu_tomo = 1
        if tomorrow_Yobi == "Fri":
            fri_tomo = 1
        if tomorrow_Yobi == "Sat":
            sat_tomo = 1
        if tomorrow_Yobi == "Sun":
            sun_tomo = 1
        if tomorrow_Shuku==True:
            shuku_tomo = 1
        if tomorrow_Shuku==False:
            hei_tomo = 1
            
        now = datetime.now()

        column_name ='予測値_demand'
        data = pd.DataFrame(columns=[column_name]) 
        #1～7=曜日,11～34=時間
        hour = now.hour
        if now.minute >=30:
            min = '00'
            hour = hour +1
            koma_min = 0
            
        if now.minute<30 :
            min ='30'
            koma_min=1

        genzai_koma = str(hour)+':'+min
        print(genzai_koma)
        koma = hour*2 + koma_min
        print(df.iloc[:,2])
        #予測実行時間帯以降の当日分
        #最低でも１週間データがたまっていることが前提！！！！
        for i in range(koma + 13,61): #14番目=0:30(これが1コマ目),60番目=23:30,komaは1以上
            x = df.iloc[:,[6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60]]
            #6～12が曜日,13～60がコマ
            y = df.iloc[:,2] #目的関数の設置。固定パターン。
            list_koma = [0]*49#とりあえず、全部0で要素数49個のリストを用意。先頭は無視するので49個
            #print(x,y)
            list_koma[i-13] = 1 #komaコマ目=i-12コマ目だけ1にする
            # 学習用データとする
            x_train = x
            y_train = y
            #曜日は残念ながらアルファベット順。
            x_test =[[fri_today,mon_today,sat_today,sun_today,thu_today,tue_today,wed_today,list_koma[1],list_koma[2],list_koma[3],list_koma[4],list_koma[5],list_koma[6],list_koma[7],list_koma[8],list_koma[9],list_koma[10],list_koma[11],list_koma[12],list_koma[13],list_koma[14],list_koma[15],list_koma[16],list_koma[17],list_koma[18],list_koma[19],list_koma[20],list_koma[21],list_koma[22],list_koma[23],list_koma[24],list_koma[25],list_koma[26],list_koma[27],list_koma[28],list_koma[29],list_koma[30],list_koma[31],list_koma[32],list_koma[33],list_koma[34],list_koma[35],list_koma[36],list_koma[37],list_koma[38],list_koma[39],list_koma[40],list_koma[41],list_koma[42],list_koma[43],list_koma[44],list_koma[45],list_koma[46],list_koma[47],list_koma[48]]]
            print(x_test)
            #xと形式が揃っているか確認
            # 学習 直線回帰
            model = LinearRegression(normalize=True)
            model.fit(x_train, y_train)

            #予測する
            y_pred = model.predict(x_test)#このままだとnumpy.ndarray型
            y_pred = pd.Series(y_pred)#これでseries型
            y_pred = sum(round(y_pred,2)) #これでfloatとして取り出す
            #print(y_pred)
            #time = timedelta(date=now.date(),hours=i-11)
            #iコマ目とは何時か？
            hour = (i-13)//2 #コマ数を割った時の商
            min = (i-13)%2 #コマ数を割った時の余り
            if min ==1:
                min =30

            time =datetime(today.year,today.month,today.day,hour, min, 0)
            #print(time)
            data.loc[time] = y_pred
            print(y_pred)
            
        for i in range(13,61): #13番目=0:00,60番目=23:30
            x = df.iloc[:,[6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60]]
            #5が土日祝日、6～12が曜日,13～60がコマ
            y = df.iloc[:,2] #目的関数の設置。固定パターン。
            list_koma = [0]*48#とりあえず、全部0で要素数48個のリストを用意。0番目は本当は48コマ目である0:00とする。
            #print(x,y)
            list_koma[i-13] = 1 #i=13から始まるのはしょうがない。komaコマ目=i-13コマ目だけ1にする

            # 学習用データとする
            x_train = x
            y_train = y
        #曜日は残念ながらアルファベット順。
            x_test =[[fri_today,mon_today,sat_today,sun_today,thu_today,tue_today,wed_today,list_koma[0],list_koma[1],list_koma[2],list_koma[3],list_koma[4],list_koma[5],list_koma[6],list_koma[7],list_koma[8],list_koma[9],list_koma[10],list_koma[11],list_koma[12],list_koma[13],list_koma[14],list_koma[15],list_koma[16],list_koma[17],list_koma[18],list_koma[19],list_koma[20],list_koma[21],list_koma[22],list_koma[23],list_koma[24],list_koma[25],list_koma[26],list_koma[27],list_koma[28],list_koma[29],list_koma[30],list_koma[31],list_koma[32],list_koma[33],list_koma[34],list_koma[35],list_koma[36],list_koma[37],list_koma[38],list_koma[39],list_koma[40],list_koma[41],list_koma[42],list_koma[43],list_koma[44],list_koma[45],list_koma[46],list_koma[47]]]
            # 学習 直線回帰
            model = LinearRegression(normalize=True)
            model.fit(x_train, y_train)

            #予測する
            y_pred = model.predict(x_test)#このままだとnumpy.ndarray型
            y_pred = pd.Series(y_pred)#これでseries型
            y_pred = sum(round(y_pred,2)) #これでfloatとして取り出す
            
            hour = (i-13)//2 #コマ数を割った時の商
            min = (i-13)%2 #コマ数を割った時の余り
            if min ==1:
                min =30
            #print(koma,hour,min)
            time =datetime(today.year,today.month,today.day,hour, min, 0)
            time =datetime(tomorrow.year,tomorrow.month,tomorrow.day, hour, min, 0)

            data.loc[time] = y_pred

        data.index.name ='予測時刻'

        #以下、あくまでも安全弁。異常値の排除。
        #5kWより大きければゼロにする。
        data = data.where(data['予測値_demand'] < 5, 0)
        #0kWより小さければゼロにする。
        data = data.where(data['予測値_demand'] > 0, 0)
        mean = round(data['予測値_demand'].mean(),2)
        #ゼロであれば全コマの平均値へ置き換え。
        data = data.where(data['予測値_demand'] !=0 , mean)

        return data

if __name__ == '__main__':
    pd.set_option('display.max_rows', 500)
    iwamura = 'iwamura'
    id ='A0D21C0847DBB3AA2'
    #path_moto ="C:\\Users\\f-apl-admin\\住宅実証\\最適化プログラム\\実行ファイル\\需要電力成形\\需要予測学習データ\\岩村さん"
    #df = pd.read_csv('需要電力データiwamura.csv',encoding="shift_jis")#結合で作ったcsvファイルを読み込む
    df = calc_demand(iwamura,id)

    print(df)#インデックス名に予測時刻、カラムは予測値_demandとする必要がある