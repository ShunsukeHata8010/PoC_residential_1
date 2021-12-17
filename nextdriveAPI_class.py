import numpy as np
from numpy.core.fromnumeric import reshape
import requests
import json
import pandas as pd
import os
from datetime import datetime, date, timedelta
from nextdriveAPI_functions import dict_SolarPW,dict_SmartMeter,dict_AirCon_living,dict_StgBattery,dict_thermometer,dict_AirCon_bedroom, store_StgBattery_FOR_COMPARISON_INFO, store_StgBattery_FOR_LATEST_INFO,dict_ElecWaterHeater,store_ElecWaterHeater
from nextdriveAPI_functions import DataRetrieval_30min,set_time_30min,DataRetrieval_10min
from nextdriveAPI_functions import store_SolarPW,store_SmartMeter,store_AirCon,store_StgBattery,store_thermometer
from nextdriveAPI_functions import devices,Control_AirCon,Control_StgBattery,Control_ElecWaterHeater


base_url = 'https://ioeapi.nextdrive.io/v1/gateways/'

headers = {
    #'X-ND-TOKEN':'wDqFBnuuZPMbfpwC958pSjT7x+kX9raG8PX4Rl3',#旧APIキー
    'X-ND-TOKEN':'WhxgcOFnTMR0ZvC4qAj8Waovr4turnsmslO74gb',#新APIキー
    'content-type':'application/json'
}

class House_init:#uuidを取得する前のクラス
    #属性を定義する。
    def __init__(self,name,name_id):#name_uuidは辞書型
        self.name = name
        self.name_id = name_id
    #メソッドを定義する。
    def devices(self):
        devices_url = base_url + self.name_id +'/devices'
        response = requests.get(devices_url,headers=headers)
        #print(response.json())
    #getやpostの回数制限あり?。
        data = response.json()
        data = data['devices']#devicesしか特に入っていない。
        df_devices = pd.DataFrame()
        name =[]
        Uuid =[]
        model =[]
        onlineStatus = []
        for i in data:
            name.append(i['name'])
            Uuid.append(i['deviceUuid'])
            model.append(i['model'])
            onlineStatus.append(i['onlineStatus'])
        df_devices['機器名'] = model
        df_devices['あだ名'] =name 
        df_devices['Uuid'] = Uuid
        df_devices['Status'] = onlineStatus
        #Pixi-HTはthermometerへ、Pixi-Gはmotionsensorへ置き換え
        df_devices['機器名'] = df_devices['機器名'].str.replace('Pixi-HT', 'thermometer')
        df_devices['機器名'] = df_devices['機器名'].str.replace('Pixi-G', 'motionsensor')
        #もし、AirConの数が１つながら、AirCon_livingに置き換える
        if (df_devices['機器名']=='AirCon').sum()==1 :
            df_devices['機器名'] = df_devices['機器名'].str.replace('AirCon','AirCon_living')
        return df_devices
    
    def store_uuid(self):
        devices_url = base_url + self.name_id +'/devices'
        response = requests.get(devices_url,headers=headers)
        #print(response.json())
    #getやpostの回数制限あり?。
        data = response.json()
        #print(data)
        try:
            data = data['devices']#devicesしか特に入っていない。

        except:
            print('クラスHouse_initの関数store_uuid:',self.name_id,'はidな不正なものです')
        else:
            df_sonomama = pd.DataFrame()
            name =[]
            Uuid =[]
            model =[]
            onlineStatus = []
            for i in data:
                name.append(i['name'])
                Uuid.append(i['deviceUuid'])
                model.append(i['model'])
                onlineStatus.append(i['onlineStatus'])
            df_sonomama['機器名'] = model
            df_sonomama['あだ名'] =name 
            df_sonomama['Uuid'] = Uuid
            df_sonomama['Status'] = onlineStatus

            df = df_sonomama.drop(['あだ名', 'Status'],axis=1)
            
            #Pixi-HTはthermometerへ、Pixi-Gはmotionsensorへ置き換え
            df['機器名'] = df['機器名'].str.replace('Pixi-HT', 'thermometer')
            df['機器名'] = df['機器名'].str.replace('Pixi-G', 'motionsensor')
            #もし、AirConの数が１つながら、AirCon_livingに置き換える
            if (df['機器名']=='AirCon').sum()==1 :
                df['機器名'] = df['機器名'].str.replace('AirCon','AirCon_living')
            df = df.set_index('機器名')
            dict = df.to_dict()
            dict = dict['Uuid']
    
            path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
            path_userinfo = path_origin +'\\ユーザー情報'
            # 存在チェック
            dir = path_userinfo + '\\' + self.name +'_'+self.name_id
            if os.path.isdir(dir):
                print("ディレクトリが存在します")       
            # ディレクトリがない場合、作成する
            if not os.path.exists(dir):
                print("ディレクトリを作成します")
                os.makedirs(dir)
                os.chdir(dir)
                filename = '取得のままの'+'uuid_'+self.name +'_'+self.name_id+'.csv'
                df_sonomama.to_csv(filename,encoding='shift_jis')

                if self.name =='oda':
                    dict = {#エアコンが二つがあるのが小田さんだけなので、とりあえず特別対応
                            "beep":"75e78a41-61d2-41f7-b6ea-345c810bc29a",
                            "thermometer":"e4a4e01a-a41e-48cb-8afd-4f30eda2838a",
                            "SmartMeter":"a1d69c43-560b-4b9f-9574-5763518704f6",
                            "AirCon_bedroom":"b48c81ed-3330-4482-a311-2680252ef95f",
                            "motionsensor":"13e7b7ea-15b8-4ac7-8118-d865aa543c0a",
                            "AirCon_living":"03a34ea9-ada6-411d-94c9-3568a6c39572"
                    }
        
                filename_json = 'uuid_'+self.name +'_'+self.name_id+'.json'
                tf = open(filename_json, "w")
                json.dump(dict,tf)
                tf.close()
                #検証用jsonファイルのオープン
                json_open = open(filename_json, 'r')
                json_load = json.load(json_open)
                #print(json_load)
            
    #return なし


class House:
    #属性を定義する。
    def __init__(self,name,name_id):#name_uuidは辞書型
        self.name = name
        self.name_id = name_id
        #direct = 'C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報\\'
        path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
        path_userinfo = path_origin +'\\ユーザー情報'
        direct = path_userinfo+'\\' +self.name +'_'+self.name_id
        try:
            os.chdir(direct)
        except:
            print('クラスHouseの_init_:',name_id,'は不正なidです')
        else:
            filename_json = 'uuid_'+self.name+'_'+self.name_id+'.json'
            json_open = open(filename_json, 'r')
            json_load = json.load(json_open)

            self.name_uuid = json_load#辞書型

    #メソッドを定義する。
    def devices(self):
        devices_url = base_url + self.name_id +'/devices'
        response = requests.get(devices_url,headers=headers)
        #print(response.json())
    #getやpostの回数制限あり?。
        data = response.json()
        data = data['devices']#devicesしか特に入っていない。
        df_devices = pd.DataFrame()
        name =[]
        Uuid =[]
        model =[]
        onlineStatus = []
        for i in data:
            name.append(i['name'])
            Uuid.append(i['deviceUuid'])
            model.append(i['model'])
            onlineStatus.append(i['onlineStatus'])
        df_devices['機器名'] = model
        df_devices['あだ名'] =name 
        df_devices['Uuid'] = Uuid
        df_devices['Status'] = onlineStatus
        #Pixi-HTはthermometerへ、Pixi-Gはmotionsensorへ置き換え(-が入っているため)
        df_devices['機器名'] = df_devices['機器名'].str.replace('Pixi-HT', 'thermometer')
        df_devices['機器名'] = df_devices['機器名'].str.replace('Pixi-G', 'motionsensor')
        #もし、AirConの数が１つながら、AirCon_livingに置き換える
        if (df_devices['機器名']=='AirCon').sum()==1 :
            df_devices['機器名'] = df_devices['機器名'].str.replace('AirCon','AirCon_living')

        return df_devices

    def SmartMeter(self):
        if dict_SmartMeter(self.name_uuid)==False:
            return False
        else:
            return 'SmartMeter',dict_SmartMeter(self.name_uuid)

    def SolarPW(self):
        if dict_SolarPW(self.name_uuid)==False:
            return False
        else:
            return 'SolarPW',dict_SolarPW(self.name_uuid)

    def StgBattery(self):
        if dict_StgBattery(self.name_uuid)==False:
            return False,False
        else:
            return 'StgBattery',dict_StgBattery(self.name_uuid)

    def thermometer(self):
        if dict_thermometer(self.name_uuid)==False:
            return False,False
        else:
            return 'thermometer',dict_thermometer(self.name_uuid)

    def AirCon_living(self):
        if dict_AirCon_living(self.name_uuid)==False:
            return False,False
        else:
            return 'AirCon_living',dict_AirCon_living(self.name_uuid)

    def AirCon_bedroom(self):
        if dict_AirCon_bedroom(self.name_uuid)==False:
            return False,False
        else:
            return 'AirCon_bedroom',dict_AirCon_bedroom(self.name_uuid)

    def ElecWaterHeater(self):
        if dict_ElecWaterHeater(self.name_uuid)==False:
            return False,False
        else:
            return 'ElecWaterHeater',dict_ElecWaterHeater(self.name_uuid)            

    def DataRetrieval_SmartMeter_30min(self):
        if dict_SmartMeter(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_SmartMeter(self.name_uuid)
            scope = ["instanceElectricity"]
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)
        return df,endtime

    def DataRetrieval_SolarPW_30min(self):#単位はWで取れる
        if dict_SolarPW(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_SolarPW(self.name_uuid)
            scope = ["instanceElectricity"]
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)
        return df,endtime

    def DataRetrieval_StgBattery_30min(self):
        if dict_StgBattery(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_StgBattery(self.name_uuid)
            scope = ['workingOperationStatus','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','storedElectricity','acChargingEnergy','acDischargingEnergy']
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)

            df = df.replace(65, 'Rapid charging')
            df = df.replace(66, 'Charging')
            df = df.replace(67, 'Discharging')
            df = df.replace(68, 'Standby')
            df = df.replace(70, 'Automatic')

        return df,endtime

    def Get_latest_StgBattery_info(self):
        if  type(dict_StgBattery(self.name_uuid)) is str:#StgBatteryがあれば、
            uuid_StgBattery =dict_StgBattery(self.name_uuid)            
            df_StgBattery,endtime = store_StgBattery_FOR_LATEST_INFO(self.name_id,uuid_StgBattery)

            return df_StgBattery,endtime
        else:
            return 'no StgBattery'

    def Calc_latest_StgBattery_behavior(self):
        if  type(dict_StgBattery(self.name_uuid)) is str:#StgBatteryがあれば、
            uuid_StgBattery =dict_StgBattery(self.name_uuid)
            df_StgBattery,endtime = store_StgBattery_FOR_COMPARISON_INFO(self.name_id,uuid_StgBattery)
            list_shoki_jikan=[]
            list_saishu_jikan=[]
            list_shoki =[]
            list_saishu=[]
            list_soc_zougen=[]
            list_juuden_zougen=[]
            list_houden_zougen=[]
            list_zanden_zougen=[]
            list_soc_shoki=[]
            list_soc_saishuu=[]
            print(df_StgBattery)
            df_latest_StgBattery_behavior = pd.DataFrame()
            try:
                list_shoki_jikan.append(df_StgBattery.iloc[0]['時刻'])
                list_saishu_jikan.append(df_StgBattery.iloc[1]['時刻'])
                list_shoki.append(df_StgBattery.iloc[0]['battery状態'])
                list_saishu.append(df_StgBattery.iloc[1]['battery状態'])
                list_soc_shoki.append(df_StgBattery.iloc[0]['SOC'])
                list_soc_saishuu.append(df_StgBattery.iloc[1]['SOC'])
                list_soc_zougen.append(df_StgBattery.iloc[1]['SOC']-df_StgBattery.iloc[0]['SOC'])
                list_juuden_zougen.append(df_StgBattery.iloc[1]['充電可能量']-df_StgBattery.iloc[0]['充電可能量'])
                list_houden_zougen.append(df_StgBattery.iloc[1]['放電可能量']-df_StgBattery.iloc[0]['放電可能量'])
                try:
                    list_zanden_zougen.append(df_StgBattery.iloc[1]['残電力量']-df_StgBattery.iloc[0]['残電力量'])
                except TypeError:
                    list_zanden_zougen.append(np.nan)
                df_latest_StgBattery_behavior['初期_時刻'] = list_shoki_jikan
                df_latest_StgBattery_behavior['最終_時刻'] = list_saishu_jikan
                df_latest_StgBattery_behavior['経過時間'] =  df_latest_StgBattery_behavior['最終_時刻']-df_latest_StgBattery_behavior['初期_時刻']
                df_latest_StgBattery_behavior['初期_状態'] = list_shoki
                df_latest_StgBattery_behavior['最終_状態'] = list_saishu
                df_latest_StgBattery_behavior['SOC_初期'] = list_soc_shoki
                df_latest_StgBattery_behavior['SOC_最終'] = list_soc_saishuu
                df_latest_StgBattery_behavior['SOC_増減'] = list_soc_zougen
                df_latest_StgBattery_behavior['充電量可能量_増減'] = list_juuden_zougen
                df_latest_StgBattery_behavior['放電可能量_増減'] = list_houden_zougen
                df_latest_StgBattery_behavior['残電力量_増減'] = list_zanden_zougen
            except IndexError:#これは蓄電池オフラインの時のエラーをキャッチ
                list_shoki_jikan=[]
                list_saishu_jikan=[]
                list_shoki =[]
                list_saishu=[]
                list_soc_zougen=[]
                list_juuden_zougen=[]
                list_houden_zougen=[]
                list_zanden_zougen=[]
                list_soc_shoki=[]
                list_soc_saishuu=[]

                list_shoki_jikan.append(np.nan)
                list_saishu_jikan.append(np.nan)
                list_shoki.append(np.nan)
                list_saishu.append(np.nan)
                list_soc_shoki.append(np.nan)
                list_soc_saishuu.append(np.nan)
                list_soc_zougen.append(np.nan)
                list_juuden_zougen.append(np.nan)
                list_houden_zougen.append(np.nan)
                list_zanden_zougen.append(np.nan)
                df_latest_StgBattery_behavior['初期_時刻'] = list_shoki_jikan
                df_latest_StgBattery_behavior['最終_時刻'] = list_saishu_jikan
                df_latest_StgBattery_behavior['経過時間'] =  df_latest_StgBattery_behavior['最終_時刻']-df_latest_StgBattery_behavior['初期_時刻']
                df_latest_StgBattery_behavior['初期_状態'] = list_shoki
                df_latest_StgBattery_behavior['最終_状態'] = list_saishu
                df_latest_StgBattery_behavior['SOC_初期'] = list_soc_shoki
                df_latest_StgBattery_behavior['SOC_最終'] = list_soc_saishuu
                df_latest_StgBattery_behavior['SOC_増減'] = list_soc_zougen
                df_latest_StgBattery_behavior['充電量可能量_増減'] = list_juuden_zougen
                df_latest_StgBattery_behavior['放電可能量_増減'] = list_houden_zougen
                df_latest_StgBattery_behavior['残電力量_増減'] = list_zanden_zougen

                return df_latest_StgBattery_behavior

            return df_latest_StgBattery_behavior
        else:
            return 'no StgBattery'

    def DataRetrieval_StgBattery_10min(self):#StgBatteryだけ10分を作っておく
        if dict_StgBattery(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_StgBattery(self.name_uuid)
            scope = ['workingOperationStatus','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','storedElectricity','acChargingEnergy','acDischargingEnergy']
            df,endtime = DataRetrieval_10min(self.name_id,uuid,scope)

            df = df.replace(65, 'Rapid charging')
            df = df.replace(66, 'Charging')
            df = df.replace(67, 'Discharging')
            df = df.replace(68, 'Standby')

        return df,endtime

    def DataRetrieval_thermometer_30min(self):
        if dict_thermometer(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_thermometer(self.name_uuid)
            scope =['temperature','humidity','battery']
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)

        return df,endtime

    def DataRetrieval_AirCon_bedroom_30min(self):
        if dict_AirCon_bedroom(self.name_uuid)==False:
            return False
        else:
            uuid=dict_AirCon_bedroom(self.name_uuid)
            scope =  ["operationStatus","operationMode","temperatureSetting"]
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)

            df = df.replace(48, 'ON')
            df = df.replace(49, 'OFF')
            df = df.replace(65, 'Automatic')
            df = df.replace(66, 'Cooling')
            df = df.replace(67, 'Heating')
            df = df.replace(68, 'Dehumidification')
            df = df.replace(68, 'Aircirculator')
            df = df.replace(64, 'Other')
        return df,endtime

    def DataRetrieval_AirCon_living_30min(self):
        if dict_AirCon_living(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_AirCon_living(self.name_uuid)
            scope =  ["operationStatus","operationMode","temperatureSetting"]
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)

            df = df.replace(48, 'ON')
            df = df.replace(49, 'OFF')
            df = df.replace(65, 'Automatic')
            df = df.replace(66, 'Cooling')
            df = df.replace(67, 'Heating')
            df = df.replace(68, 'Dehumidification')
            df = df.replace(68, 'Aircirculator')
            df = df.replace(64, 'Other')

        return df,endtime

    def DataRetrieval_ElecWaterHeater_30min(self):
        if dict_ElecWaterHeater(self.name_uuid)==False:
            return False,False
        else:
            uuid=dict_ElecWaterHeater(self.name_uuid)
            scope =  ["operationStatus","autoWaterHeatingMode","waterHeaterStatus",'participateInEnergyShift','timeToStartHeating','numberOfEnergyShift','daytimeHeatingShiftTime1']
            df,endtime = DataRetrieval_30min(self.name_id,uuid,scope)
            df_new =pd.DataFrame()
            #operationStatusだけを取り出し、置き換え
            df_operationStatus = df.query('scope=="operationStatus"')
            df_operationStatus = df_operationStatus.replace(48,'ON')
            df_operationStatus = df_operationStatus.replace(47,'OFF')
            df_operationStatus = pd.concat([df_new,df_operationStatus], axis=0)
            #autoWaterHeatingModeだけを取り出し、置き換え
            df_autoWaterHeatingMode = df.query('scope=="autoWaterHeatingMode"')
            df_autoWaterHeatingMode = df_autoWaterHeatingMode.replace(65,'Automatic water heating function used')
            df_autoWaterHeatingMode = df_autoWaterHeatingMode.replace(67,'Non-automatic water heating function stopped')
            df_autoWaterHeatingMode = df_autoWaterHeatingMode.replace(66,'Nonautomatic water heating function used')
            df_autoWaterHeatingMode = pd.concat([df_operationStatus,df_autoWaterHeatingMode], axis=0)
            #waterHeaterStatusだけを取り出し、置き換え
            df_waterHeaterStatus = df.query('scope=="waterHeaterStatus"')
            df_waterHeaterStatus = df_waterHeaterStatus.replace(65,'Heating')
            df_waterHeaterStatus = df_waterHeaterStatus.replace(66,'Not heating')
            df_waterHeaterStatus = pd.concat([df_autoWaterHeatingMode,df_waterHeaterStatus], axis=0)
            #participateInEnergyShiftだけを取り出し、置き換え
            df_participateInEnergyShift = df.query('scope=="participateInEnergyShift"')
            df_participateInEnergyShift = pd.concat([df_waterHeaterStatus,df_participateInEnergyShift], axis=0)
            df = df_waterHeaterStatus
            df = df.sort_index(axis='index')

        return df,endtime

#SolarPW,スマメ,エアコン,蓄電池,温度計があれば、それらをこの順番で保存する。なければそれはスキップする。
#UUidがあってもオフラインのものはどうなる？
    def store_30min(self):
        df_SolarPW = pd.DataFrame()
        df_SmartMeter = pd.DataFrame()
        df_AirCon_living = pd.DataFrame()
        df_AirCon_bedroom = pd.DataFrame()
        df_StgBattery = pd.DataFrame()
        df_thermometer = pd.DataFrame()
        df_ElecWaterHeater = pd.DataFrame()
    
        try:
            if  type(dict_SolarPW(self.name_uuid)) is str:#SolarPWがあれば、
                uuid_SolarPW =dict_SolarPW(self.name_uuid)
                df_SolarPW,endtime = store_SolarPW(self.name_id,uuid_SolarPW)
                print(df_SolarPW)
            if  type(dict_SmartMeter(self.name_uuid)) is str:#SmartMeterがあれば、
                uuid_SmartMeter =dict_SmartMeter(self.name_uuid)
                df_SmartMeter,endtime = store_SmartMeter(self.name_id,uuid_SmartMeter)

            if  type(dict_AirCon_living(self.name_uuid)) is str:#AirCon_livingがあれば、
                uuid_AirCon_living =dict_AirCon_living(self.name_uuid)
                df_AirCon_living,endtime = store_AirCon(self.name_id,uuid_AirCon_living)
            
            if  type(dict_AirCon_bedroom(self.name_uuid)) is str:#AirCon_bedroomがあれば、
                uuid_AirCon_bedroom =dict_AirCon_bedroom(self.name_uuid)
                df_AirCon_bedroom,endtime = store_AirCon(self.name_id,uuid_AirCon_bedroom)

            if  type(dict_StgBattery(self.name_uuid)) is str:#StgBatteryがあれば、
                uuid_StgBattery =dict_StgBattery(self.name_uuid)
                df_StgBattery,endtime = store_StgBattery(self.name_id,uuid_StgBattery)

            if  type(dict_thermometer(self.name_uuid)) is str:#thermometerがあれば、
                uuid_thermometer =dict_thermometer(self.name_uuid)
                df_thermometer,endtime = store_thermometer(self.name_id,uuid_thermometer)

            if  type(dict_ElecWaterHeater(self.name_uuid)) is str:#ElecWaterHeaterがあれば、
                uuid_ElecWaterHeater =dict_ElecWaterHeater(self.name_uuid)
                df_ElecWaterHeater,endtime = store_ElecWaterHeater(self.name_id,uuid_ElecWaterHeater)
        
            #Noneの場合は飛ばす(NoneをconcatしてもOK)#横に結合
            df = pd.concat([df_SolarPW,df_SmartMeter,df_AirCon_living,df_AirCon_bedroom,df_StgBattery,df_thermometer,df_ElecWaterHeater], axis=1)

            #os.chdir(os.path.dirname(os.path.abspath(__file__)))
            
            return df

        except AttributeError:#idが入っていないなどの時
            print(self.name,'についてstore時にエラーが発生しましたが、次にいきます')
    #リビングのエアコンの制御
    #引数の大文字小文字に注意！！
    def Control_AirCon_living(self,operationStatus,operationMode,temperature):#dataはこの時点では辞書型
        name,uuid = self.AirCon_living()#クラス内の他のメソッドの呼び出し
        response = Control_AirCon(operationStatus,operationMode,temperature,name,uuid)
        return response
    #寝室のエアコンの制御
    def Control_AirCon_bedroom(self,operationStatus,operationMode,temperature):#dataはこの時点では辞書型
        name,uuid = self.AirCon_bedroom()#クラス内の他のメソッドの呼び出し
        response = Control_AirCon(operationStatus,operationMode,temperature,name,uuid)
        return response

    def Control_StgBattery(self,operationMode,acChargeAmountSetting,acDischargeAmountSetting):
        name,uuid = self.StgBattery()#クラス内の他のメソッドの呼び出し
        #Charging,Discharging,Standby,Automatic,restartのみ入力可能の状態
        response = Control_StgBattery(operationMode,acChargeAmountSetting,acDischargeAmountSetting,name,uuid)
        return response

    def Control_ElecWaterHeater(self,operationStatus,operationMode):
        name,uuid = self.ElecWaterHeater()#クラス内の他のメソッドの呼び出し
        #Charging,Discharging,Standby,Automatic,restartのみ入力可能の状態
        response = Control_ElecWaterHeater(operationStatus,operationMode,name,uuid)
        return response

    def Uuid_register(name,id):#Uuidを登録するときにだけ実行する
        house = House_init(name,id)
        house.store_uuid()
        