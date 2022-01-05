import pandas as pd
import pulp
import numpy as np
import os
import matplotlib.pyplot as plt
import math
#import datetime
from datetime import datetime, date, timedelta
import sqlalchemy
from weather_warning import warning
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))#1つ上のディレクトリからインポートするとき
from nextdriveAPI_class import House
from database_mysql import create_database,update_database
from solver_residential_battery import merge,solver_residential_battery,graph_residential_battery


def calc_control_battery_NOT_warning(instruction_to_battery):        
    if instruction_to_battery==0:
        operationMode='Standby'#スペル注意!
        acChargeAmountSetting=0
        acDischargeAmountSetting=0
    elif instruction_to_battery>0:#充電の場合
        operationMode='Charging'
        acChargeAmountSetting=instruction_to_battery*1000 #単位はWh。定格出力で充電しようとして指定のWhが充電すると待機に入る。
        acDischargeAmountSetting=0
    elif instruction_to_battery<0:#放電の場合
        operationMode='Discharging'
        acChargeAmountSetting= 0 
        acDischargeAmountSetting=-1*instruction_to_battery*1000#単位はWh。定格出力で放電しようとして指定のWhが放電すると待機に入る。
    else:
        print('充放電指示が不正です。')

    return operationMode,acChargeAmountSetting,acDischargeAmountSetting

def calc_control_battery_WARNING(instruction_to_battery,latest_SOC):
    print('警報発令中！！！')
    print('現在のSOC：',latest_SOC)
    if latest_SOC>0.9:#最新のSOCが90%以上なら待機指示
        operationMode='Standby'
        acChargeAmountSetting=0
        acDischargeAmountSetting=0
    elif latest_SOC<=0.9:#最新のSOCが90%未満ならフル充電指示＝instruction_to_battery自体がフル充電量
        operationMode='Charging'
        acChargeAmountSetting=instruction_to_battery*1000 #単位はWh。定格出力で充電しようとして指定のWhが充電すると待機に入る。
        acDischargeAmountSetting=0
    return operationMode,acChargeAmountSetting,acDischargeAmountSetting


def calc_battery_direction(name,id,power_com,House,df_jepx,pv_pre,demand_pre,address,inputpower_batt,capacity_batt,outputpower_batt,maxSOC_batt,minSOC_batt,effi_batt):
    battery_latest_status,gettime = House.Get_latest_StgBattery_info()
    df_battery_latest_behabior = House.Calc_latest_StgBattery_behavior()
    #print(df_battery_latest_behabior)
    if type(df_battery_latest_behabior) is str :
        print('蓄電池が無いもしくは蓄電池がオフになっている可能性があります！')
        df_battery_latest_behabior = pd.DataFrame()#df_battery_latest_behabiorは正常時はdataframeだが、ここではStgBattery is Not activeという文字列であるため、一回リフレッシュ
        list_jikoku=[]
        list_jikoku.append(datetime.now())
        df_battery_latest_behabior['初期_時刻']=list_jikoku
    else:
        latest_SOC = battery_latest_status['SOC'].iloc[0]/100#SOCを%単位で取得
        now = datetime.now()
        if math.isnan(latest_SOC):#SOCがnan=取れていないときの指示
            print('SOCが取得出来ていません。蓄電池がオフになっている可能性があります！')
            operationMode,acChargeAmountSetting,acDischargeAmountSetting ='Standby',0,0
            juuhouderyou_for_kiroku =0
        else:
            #ここで現在コマより古い行を削除するための作業をする(DBからとってくるときにやっているが、もう一度やる)         
            #（JEPXは毎日10時15分に翌日の結果をダウンロードしている。）
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

            df_pre = merge(pv_pre,demand_pre,df_jepx)
            df_pre = df_pre.set_index('日時')
            print(df_pre)
            df_pre_old =df_pre.index[(df_pre.index <= current_koma)]

            df_pre = df_pre.drop(df_pre_old)

            #########警報があれば、無条件でinstruction_to_batteryをフル充電。
            Warning,warninglist,area = warning(address)
            if Warning ==True:#警報が出ているとき
                instruction_to_battery=inputpower_batt/2#30分当たりのkWhに変換する
                operationMode,acChargeAmountSetting,acDischargeAmountSetting = calc_control_battery_WARNING(instruction_to_battery,latest_SOC)
                print("蓄電池への指示量(kWh)：",acChargeAmountSetting)
                juuhouderyou_for_kiroku=acChargeAmountSetting

            else:#警報が出ていないとき
                df_solution,solver_status = solver_residential_battery(df_pre,capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,latest_SOC,power_com)
                #graph_residential_battery(df_solution,power_com)#グラフを表示する場合
                instruction_to_battery = df_solution['蓄電池_充放電量'].iloc[0] #直近コマの充放電量だけ取り出し。これは元々30分当たりのkWhのはず！！
                #calc_control_battery_NOT_warningの中でkWhからWhへの変換もする。
                operationMode,acChargeAmountSetting,acDischargeAmountSetting = calc_control_battery_NOT_warning(instruction_to_battery)

                print("蓄電池への指示量(kWh)：",instruction_to_battery)

                if solver_status == 1:
                    print('最適化成功')
                elif solver_status == -1:
                    print('最適化失敗（Infeasible）！！！！！！！！！！！！！！！')
                else:
                    print('最適化失敗(Undefined,Unbounded,Not Solved)')
                print("計算結果：", pulp.LpStatus[solver_status])

            time_0 = now.replace(minute=0, second=0, microsecond=0)
            time_30 = now.replace(minute=30, second=0, microsecond=0)
            time_next_0  = now.replace(hour=now.hour+1,minute=0, second=0, microsecond=0)
            #9:05だとすると、9:00,9:30,10:00 この件では、9:30にしたい
            #8:55だとすると、8:00,8:30,9:00　この件では、9:30にしたい
            #8:35だとすると、8:00,8:30,9:00  この件では、9:00にしたい
            #なので、この３パターンのどれかということでOK
            min_time = min(abs(time_30 - now) ,abs(time_0-now),abs(time_next_0-now))
            if min_time == abs(time_30 - now):
                time = time_next_0
            elif min_time == abs(time_0-now):
                time = time_30
            elif min_time == abs(time_next_0-now):
                time = time_30.replace(hour=time_30.hour+1)

            #指示内容のデータベースへの格納
            list_battery = []
            list_battery_2 = []
            list_aircon = []
            list_ecocute = []
            list_thermo = []
            value_1 = None
            value_2 = None
            flag ='B_direction'
            try:
                value_1 = instruction_to_battery
                create_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)
            except sqlalchemy.exc.IntegrityError:
                print('日時に重複があります')
                value_1 =  instruction_to_battery
                update_database(name,id,time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag)

            #蓄電池への指示の発信
            response = House.Control_StgBattery(operationMode,acChargeAmountSetting,acDischargeAmountSetting)
            if acChargeAmountSetting==0 and acDischargeAmountSetting==0:
                print('指示充放電量: 0Wh',response)
            elif acChargeAmountSetting==0:
                print('指示充放電量: ',acDischargeAmountSetting,'Wh',response)
            elif acDischargeAmountSetting==0:
                print('指示充放電量: ',acChargeAmountSetting,'Wh',response)
            #elapsed_time = time.time() - start
            #print ("elapsed_time:{0}".format(round(elapsed_time,1)) + "[sec]")
