from re import T
import requests
import json
import pandas as pd
import datetime
from datetime import datetime, date, timedelta
import numpy as np
import configparser
from logging import getLogger


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
QUERY_URL_NextDrive = config['NextDrive']['QUERY_URL_NextDrive']
APIKEY_NextDrive = config['NextDrive']['APIKEY_NextDrive']
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
LOG_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']

headers = {
    'X-ND-TOKEN': APIKEY_NextDrive,
    'content-type':'application/json'
    }


def dict_SolarPW(dict):#辞書を引数として,SolarPWというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['SolarPW'] == '':
            return False
        else:
            return dict['SolarPW']
    except:
        return False #bool型のFalse

def dict_SmartMeter(dict):#辞書を引数として、SmartMeterというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['SmartMeter'] == '':
            return False
        else:
            return dict['SmartMeter']
    except:
        return False #bool型のFalse

def dict_AirCon_living(dict):#辞書を引数として、AirCon_livingというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['AirCon_living'] == 0:
            return False
        else:
            return dict['AirCon_living']
    except:
        return False

def dict_StgBattery(dict):#辞書を引数として、StgBatteryというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['StgBattery'] == '':
            return False
        else:
            return dict['StgBattery']
    except:
        return False

def dict_thermometer(dict):#辞書を引数として、thermometerというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['thermometer'] == '':
            return False
        else:
            return dict['thermometer']
    except:
        return False

def dict_AirCon_bedroom(dict):#辞書を引数として、AirCon_bedroomというキーがあればそのUuidを返す。なければ無いと返す。
    try:
        if dict['AirCon_bedroom'] == '':
            return False
        else:
            return dict['AirCon_bedroom']
    except:
        return False

def dict_ElecWaterHeater(dict):
    try:
        if dict['ElecWaterHeater'] == '':
            return False
        else:
            return dict['ElecWaterHeater']
    except:
        return False

def DataRetrieval_30min(id,Uuid,scope):#すぐ前の"コマの"30分間のデータを取得する。Uuidとscopeは引数
    startTime,endTime = set_time_30min()
    print(startTime)
    print(endTime)
    endTime_hokan = endTime
    #queryは複数のUuidにも対応しているが、エラーになりやすいので、とりあえず1個ずつやるとする。
    maxCount = 100#とりあえず多めにしておく
    df_results = pd.DataFrame()

    data = {"queries":[{"deviceUuid":Uuid,"scopes":scope}],"time":{"startTime":startTime,"endTime":endTime},"maxCount":maxCount}
    data =json.dumps(data)#data=に入れる前にdumpしてやる必要あり。(辞書型からstrへの変換)
    response = requests.post(QUERY_URL_NextDrive,data=data,headers= headers)
    data = response.json()    
    print(id,'のDataRetrieval_30minに対するresponse：',response)
    #200だが、データが空っぽの時は、{'results': [], 'offset': 0, 'totalCount': 0}となる。
    #404エラー(Not Found)が出るとdata ={'status': 404, 'title': 'Not Found', 'message': 'Device Uuid (47b36d3e-7dd1-4a6b-bd0b-c2afb5751865) not found', 'requestId': 'ba4565b0-16b3-11ec-97a2-83b98a931409', 
    # 'path': '/v1/device-data/query', 'timestamp': '2021-09-16T06:02:52.220Z'}のようにresultsが存在しない    
    try:
        data = data['results']    #データ（timeで指定）が過ぎると、[]で返ってくる。
    except:#404エラーの時など
        data = []
    
    pid = []
    Uuid = []
    scope = []
    generatedTime = []
    uploadedTime = []
    value = []

    for i in data:
        pid.append(i['pid'])
        Uuid.append(i['deviceUuid'])
        scope.append(i['scope'])
        generatedTime.append(datetime.fromtimestamp(i['generatedTime']/1000).replace(microsecond=0))#unixtimeからdatetimeへの変換(10桁のunixtimeに戻す)
        uploadedTime.append(datetime.fromtimestamp(i['uploadedTime']/1000).replace(microsecond=0))
        #よく確認していないが、i['value']は1,2.0の数字であってもすべてstr、たまにfalseというstr
        try:
            value.append(round(float(i['value'])))
        except ValueError:#falseというstrのとき
            logger = getLogger('main_get_info.DataRetrieval_30min')
            logger.warning('{0}:{1}:{2}'.format(id,i['value'],type(i['value'])))
            value.append(None)

    logger = getLogger('main_get_info.DataRetrieval_30min')
    logger.info('{0}:{1}'.format(id,'正常にデータ取得完了'))
    df_results['ProductID'] = pid
    df_results['scope'] = scope
    df_results['generatedTime'] = generatedTime
    df_results['uploadedTime'] = uploadedTime
    df_results['value'] = value

    endTime_hokan = datetime.fromtimestamp(endTime_hokan/1000).replace(microsecond=0)

    return df_results,endTime_hokan#endTime_hokanはdatetime型とする

def DataRetrieval_LATEST_Xmin(id,Uuid,scope,min):#本当の直前X分間のデータを取得する。Uuidとscopeは引数
    startTime,endTime = set_time_LATEST_Xmin(min)
    endTime_hokan = endTime
    #queryは複数のUuidにも対応しているが、エラーになりやすいので、とりあえず1個ずつやるとする。
    maxCount = 100#とりあえず多めにしておく
    df_results = pd.DataFrame()

    data = {"queries":[{"deviceUuid":Uuid,"scopes":scope}],"time":{"startTime":startTime,"endTime":endTime},"maxCount":maxCount}
    data =json.dumps(data)#data=に入れる前にdumpsしてやる必要あり。(辞書型からstrへの変換)
    response = requests.post(QUERY_URL_NextDrive,data=data,headers=headers)
    data = response.json()
    #ここで蓄電池がオフラインの対策を入れておく
    pid = []
    Uuid = []
    scope = []
    generatedTime = []
    uploadedTime = []
    value = []

    try:
        data = data['results']    #データ（timeで指定）が過ぎると、[]で返ってくる。
    except:
        pid.append(np.nan)
        scope.append(np.nan)
        generatedTime.append(np.nan)
        uploadedTime.append(np.nan)
        value.append(np.nan)
    else:
        for i in data:
            pid.append(i['pid'])
            Uuid.append(i['deviceUuid'])
            scope.append(i['scope'])
            generatedTime.append(datetime.fromtimestamp(i['generatedTime']/1000).replace(microsecond=0))#unixtimeからdatetimeへの変換(10桁のunixtimeに戻す)
            uploadedTime.append(datetime.fromtimestamp(i['uploadedTime']/1000).replace(microsecond=0))
            value.append(round(float(i['value'])))

    df_results['ProductID'] = pid
    df_results['scope'] = scope
    df_results['generatedTime'] = generatedTime
    df_results['uploadedTime'] = uploadedTime
    df_results['value'] = value 

    endTime_hokan = datetime.fromtimestamp(endTime_hokan/1000).replace(microsecond=0)

    return df_results,endTime_hokan#endTime_hokanはdatetime型とする

def set_time_30min():
    now = datetime.now()
    if now.minute < 30:
        startTime = now - timedelta(minutes=now.minute,seconds=now.second,microseconds=now.microsecond) -timedelta(minutes=30)
        endTime = now - timedelta(minutes=now.minute,seconds=now.second,microseconds=now.microsecond)
    elif now.minute >= 30:
        startTime = now - timedelta(minutes=now.minute,seconds=now.second,microseconds=now.microsecond) 
        endTime = now - timedelta(minutes=now.minute,seconds=now.second,microseconds=now.microsecond)+timedelta(minutes=30)
    #datetime型からunixtimeへの変換（nextdrive仕様が13桁タイプのなので、*1000）
    startTime =startTime.timestamp() * 1000
    endTime = endTime.timestamp() * 1000
    return startTime,endTime

def set_time_LATEST_Xmin(min):
    now = datetime.now()
    startTime = now - timedelta(minutes=0,seconds=now.second,microseconds=now.microsecond) -timedelta(minutes=min)
    endTime = now - timedelta(minutes=0,seconds=now.second,microseconds=now.microsecond)
    #datetime型からunixtimeへの変換（nextdrive仕様が13桁タイプのなので、*1000）
    startTime =startTime.timestamp()*1000
    endTime = endTime.timestamp()*1000
    return startTime,endTime


def set_scope(kiki_type):
    if 'thermometer' in kiki_type == True:
        scope = ['temperature','humidity','battery']
    if 'SmartMeter' in kiki_type == True:
        scope = ["instanceElectricity"]
    if 'AirCon' in kiki_type == True:
        scope =  ["operationStatus","operationMode","temperatureSetting"]
    if 'StgBattery' in kiki_type == True:
        scope = ['workingOperationStatus','operationMode','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','acChargeAmountSetting','acDischargeAmountSetting','storedElectricity','acChargeAmountSetting']

    return scope

def store_SolarPW(id,Uuid_SolarPW):#scopeはこの関数内で定義
    df_hokan = pd.DataFrame()
    list_hokan_SolarPW = []
    list_hokan_jikoku =[]
    scope_SolarPW = ["instanceElectricity"]
    df_SolarPW,endtime_SolarPW = DataRetrieval_30min(id,Uuid_SolarPW,scope_SolarPW)
    list_hokan_jikoku.append(endtime_SolarPW)

    #df_SolarPWが空ということもあり得る.
    if df_SolarPW.empty == True:
        #空であればNoneを入れる。PythonではNullをNoneとして扱い、NoneのみがNoneである。
        #DataFrameを作ると、ある要素が空の場合その要素は自動的にNaNになる
        #nanとnullの使い分けについては以下。
        # https://gensasaki.hatenablog.com/entry/2018/11/23/065125
        list_hokan_SolarPW.append(np.nan)
    else:
        list_hokan_SolarPW.append(round(df_SolarPW['value'].mean(),1))
    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['PV発電量'] = list_hokan_SolarPW

    return df_hokan,endtime_SolarPW

def store_SmartMeter(id,Uuid_smart):#scopeはこの関数内で定義
    df_hokan = pd.DataFrame()
    list_hokan_jikoku = []
    list_hokan_SmartMeter = []
    scope_SmartMeter = ["instanceElectricity"]
    df_SmartMeter,endtime_SmartMeter = DataRetrieval_30min(id,Uuid_smart,scope_SmartMeter)
    df = df_SmartMeter.query('scope=="instanceElectricity"')
    list_hokan_jikoku.append(endtime_SmartMeter)

    #df_airconが空ということもあり得る！！！！
    if df_SmartMeter.empty == True:#空であればNanを入れる。
        list_hokan_SmartMeter.append(None)
    else:
        list_hokan_SmartMeter.append(round(df['value'].mean(),1))

    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['順潮流'] = list_hokan_SmartMeter

    return df_hokan,endtime_SmartMeter


def store_AirCon(id,Uuid_aircon):#scopeはこの関数内で定義
    df_hokan = pd.DataFrame()
    list_hokan_aircon_operationStatus = []
    list_hokan_aircon_operationMode = []
    list_hokan_aircon_temperatureSetting = []
    list_hokan_jikoku = []
    scope_aircon = ["operationStatus","operationMode","temperatureSetting"]

    df_aircon,endtime_aircon = DataRetrieval_30min(id,Uuid_aircon,scope_aircon)
    list_hokan_jikoku.append(endtime_aircon)
    #df_airconが空ということもあり得る！！！！
    if df_aircon.empty == True:#空であればNanを入れる。
        list_hokan_aircon_operationStatus.append(None)
        list_hokan_aircon_operationMode.append(None)
        list_hokan_aircon_temperatureSetting.append(None)
    else:
        df = df_aircon.query('scope=="operationStatus"')
        if df.tail(1).iloc[0]['value'] == 48:
            list_hokan_aircon_operationStatus.append("ON")
        elif df.tail(1).iloc[0]['value'] == 49:
            list_hokan_aircon_operationStatus.append("OFF")

        df = df_aircon.query('scope=="operationMode"')
        if df.tail(1).iloc[0]['value'] == 65:
            list_hokan_aircon_operationMode.append("Automatic")
        elif df.tail(1).iloc[0]['value'] == 66:
            list_hokan_aircon_operationMode.append("Cooling")
        elif df.tail(1).iloc[0]['value'] == 67:
            list_hokan_aircon_operationMode.append("Heating")
        elif df.tail(1).iloc[0]['value'] == 68:
            list_hokan_aircon_operationMode.append("Dehumidification")
        elif df.tail(1).iloc[0]['value'] == 69:
            list_hokan_aircon_operationMode.append("Aircirculator")
        elif df.tail(1).iloc[0]['value'] == 64:
            list_hokan_aircon_operationMode.append("Other")

        df = df_aircon.query('scope=="temperatureSetting"')
        list_hokan_aircon_temperatureSetting.append(df.tail(1).iloc[0]['value'])

    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['ｴｱｺﾝ状態'] = list_hokan_aircon_operationStatus
    df_hokan['ｴｱｺﾝmode'] = list_hokan_aircon_operationMode
    df_hokan['ｴｱｺﾝ設定温度'] = list_hokan_aircon_temperatureSetting

    return df_hokan,endtime_aircon

def store_StgBattery(id,Uuid_StgBattery):
    df_hokan = pd.DataFrame()
    list_hokan_StgBattery_workingOperationStatus = []
    list_hokan_StgBattery_storedElectricityPercent = []
    list_hokan_StgBattery_acChargeableElectricEnergy = []
    list_hokan_StgBattery_acDischargeableElectricEnergy = []
    list_hokan_StgBattery_storedElectricity = []
    list_hokan_jikoku =[]
    scope_StgBattery = ['workingOperationStatus','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','storedElectricity']

    df_StgBattery,endtime_StgBattery = DataRetrieval_30min(id,Uuid_StgBattery,scope_StgBattery)
    list_hokan_jikoku.append(endtime_StgBattery)

    #df_airconが空ということもあり得る！！！！
    if df_StgBattery.empty == True:#空であればNanを入れる。
        list_hokan_StgBattery_workingOperationStatus.append(None)
        list_hokan_StgBattery_storedElectricityPercent.append(None)
        list_hokan_StgBattery_acChargeableElectricEnergy.append(None)
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(None)
        list_hokan_StgBattery_storedElectricity.append(None)
    else:      
        df = df_StgBattery.query('scope=="workingOperationStatus"')
        df = df.replace(65, 'Rapid charging')
        df = df.replace(66, 'Charging')
        df = df.replace(67, 'Discharging')
        df = df.replace(68, 'Standby')
        list_hokan_StgBattery_workingOperationStatus.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="storedElectricityPercent"')
        list_hokan_StgBattery_storedElectricityPercent.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="acChargeableElectricEnergy"')
        list_hokan_StgBattery_acChargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="acDischargeableElectricEnergy"')
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="storedElectricity"')
        try:
            list_hokan_StgBattery_storedElectricity.append(df.tail(1).iloc[0]['value'])
        except IndexError:
            list_hokan_StgBattery_storedElectricity.append(np.nan)
    df_hokan['時刻']=list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['battery状態']=list_hokan_StgBattery_workingOperationStatus
    df_hokan['SOC']=list_hokan_StgBattery_storedElectricityPercent
    df_hokan['充電可能量'] = list_hokan_StgBattery_acChargeableElectricEnergy
    df_hokan['放電可能量'] = list_hokan_StgBattery_acDischargeableElectricEnergy
    df_hokan['残電力量'] = list_hokan_StgBattery_storedElectricity

    return df_hokan,endtime_StgBattery

def store_ElecWaterHeater(id,Uuid_ElecWaterHeater):
    df_hokan = pd.DataFrame()
    list_hokan_jikoku = []
    list_hokan_operationStatus = []
    list_hokan_autoWaterHeatingMode = []
    list_hokan_waterHeaterStatus = []
    list_hokan_participateInEnergyShift = []
    list_hokan_timeToStartHeating = []
    list_hokan_numberOfEnergyShift =[]
    list_hokan_daytimeHeatingShiftTime1 =[]

    scope_ElecWaterHeater =  ["operationStatus","autoWaterHeatingMode","waterHeaterStatus",'participateInEnergyShift','timeToStartHeating','numberOfEnergyShift','daytimeHeatingShiftTime1']
    df_ElecWaterHeater,endtime_ElecWaterHeater = DataRetrieval_30min(id,Uuid_ElecWaterHeater,scope_ElecWaterHeater)
    list_hokan_jikoku.append(endtime_ElecWaterHeater)

    #df_ElecWaterHeaterが空ということもあり得る！！！！
    if df_ElecWaterHeater.empty == True:#空であればNanを入れる。
        list_hokan_operationStatus.append(None)
        list_hokan_autoWaterHeatingMode.append(None)
        list_hokan_waterHeaterStatus.append(None)
        list_hokan_participateInEnergyShift.append(None)
        list_hokan_timeToStartHeating.append(None)
        list_hokan_numberOfEnergyShift.append(None)
        list_hokan_daytimeHeatingShiftTime1.append(None)
    else:
        df = df_ElecWaterHeater.query('scope=="operationStatus"')
        if df.empty == True:#operationStatusだけがないパターンもあり得る。。
            list_hokan_operationStatus.append(None)
        else:
            df = df.replace(48,'ON')
            df = df.replace(47,'OFF')
            list_hokan_operationStatus.append(df.tail(1).iloc[0]['value'])

        df = df_ElecWaterHeater.query('scope=="autoWaterHeatingMode"')
        if df.empty == True:#autoWaterHeatingModeだけがないパターンもあり得る。。
            list_hokan_autoWaterHeatingMode.append(None)
        else:
            df = df.replace(65,'Automatic water heating function used')
            df = df.replace(67,'Non-automatic water heating function stopped')
            df = df.replace(66,'Nonautomatic water heating function used')
            list_hokan_autoWaterHeatingMode.append(df.tail(1).iloc[0]['value'])

        df = df_ElecWaterHeater.query('scope=="waterHeaterStatus"')
        if df.empty == True:#waterHeaterStatusだけがないパターンもあり得る。。
            list_hokan_waterHeaterStatus.append(None)

        else:
            df = df.replace(65,'Heating')
            df = df.replace(66,'Not heating')
            list_hokan_waterHeaterStatus.append(df.tail(1).iloc[0]['value'])
        
        df = df_ElecWaterHeater.query('scope=="participateInEnergyShift"')
        if df.empty == True:#participateInEnergyShiftだけがないパターンもあり得る。。
            list_hokan_participateInEnergyShift.append(None)
        else:
            list_hokan_waterHeaterStatus.append(df.tail(1).iloc[0]['value'])
        
        df = df_ElecWaterHeater.query('scope=="timeToStartHeating"')
        if df.empty == True:#participateInEnergyShiftだけがないパターンもあり得る。。
            list_hokan_timeToStartHeating.append(None)
        else:
            list_hokan_timeToStartHeating.append(df.tail(1).iloc[0]['value'])

        df = df_ElecWaterHeater.query('scope=="numberOfEnergyShift"')
        if df.empty == True:#numberOfEnergyShiftだけがないパターンもあり得る。。
            list_hokan_numberOfEnergyShift.append(None)
        else:
            list_hokan_numberOfEnergyShift.append(df.tail(1).iloc[0]['value'])

        df = df_ElecWaterHeater.query('scope=="daytimeHeatingShiftTime1"')
        if df.empty == True:#daytimeHeatingShiftTime1だけがないパターンもあり得る。。
            list_hokan_daytimeHeatingShiftTime1.append(None)
        else:
            list_hokan_daytimeHeatingShiftTime1.append(df.tail(1).iloc[0]['value'])
    
    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['動作状態'] = list_hokan_operationStatus
    df_hokan['沸き上げ自動設定'] = list_hokan_autoWaterHeatingMode
    df_hokan['沸き上げ中状態'] = list_hokan_waterHeaterStatus
    df_hokan['エネルギーシフト参加状態'] = list_hokan_participateInEnergyShift
    df_hokan['沸き上げ開始基準時刻'] = list_hokan_timeToStartHeating
    df_hokan['エネルギーシフト回数'] = list_hokan_numberOfEnergyShift
    df_hokan['昼間沸き上げシフト時刻1'] = list_hokan_daytimeHeatingShiftTime1
    
    return df_hokan,endtime_ElecWaterHeater


def store_StgBattery_FOR_LATEST_INFO(id,Uuid_StgBattery):
    #ある一定期間の最新のデータを１行で返却
    df_hokan = pd.DataFrame()
    list_hokan_StgBattery_workingOperationStatus = []
    list_hokan_StgBattery_storedElectricityPercent = []
    list_hokan_StgBattery_acChargeableElectricEnergy = []
    list_hokan_StgBattery_acDischargeableElectricEnergy = []
    list_hokan_StgBattery_storedElectricity = []
    list_hokan_jikoku = []
    scope_StgBattery = ['workingOperationStatus','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','storedElectricity']
    min = 30 #X = minという関係
    df_StgBattery,endtime_StgBattery = DataRetrieval_LATEST_Xmin(id,Uuid_StgBattery,scope_StgBattery,min)
    list_hokan_jikoku.append(endtime_StgBattery)
    #df_StgBatteryが空ということもあり得る！！！！
    if df_StgBattery.empty == True or len(df_StgBattery) < 2:#空であればNoneを入れる。
        list_hokan_StgBattery_workingOperationStatus.append(None)
        list_hokan_StgBattery_storedElectricityPercent.append(None)
        list_hokan_StgBattery_acChargeableElectricEnergy.append(None)
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(None)
        list_hokan_StgBattery_storedElectricity.append(None)
    else:
        df = df_StgBattery.query('scope=="workingOperationStatus"')
        df = df.replace(65, 'Rapid charging')
        df = df.replace(66, 'Charging')
        df = df.replace(67, 'Discharging')
        df = df.replace(68, 'Standby')
        list_hokan_StgBattery_workingOperationStatus.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="storedElectricityPercent"')
        list_hokan_StgBattery_storedElectricityPercent.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="acChargeableElectricEnergy"')
        list_hokan_StgBattery_acChargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="acDischargeableElectricEnergy"')
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])
        df = df_StgBattery.query('scope=="storedElectricity"')
        try:
            list_hokan_StgBattery_storedElectricity.append(df.tail(1).iloc[0]['value'])
        except IndexError:
            list_hokan_StgBattery_storedElectricity.append(None)
    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['battery状態'] = list_hokan_StgBattery_workingOperationStatus
    df_hokan['SOC'] = list_hokan_StgBattery_storedElectricityPercent
    df_hokan['充電可能量'] = list_hokan_StgBattery_acChargeableElectricEnergy
    df_hokan['放電可能量'] = list_hokan_StgBattery_acDischargeableElectricEnergy
    df_hokan['残電力量'] = list_hokan_StgBattery_storedElectricity

    return df_hokan,endtime_StgBattery

def store_StgBattery_FOR_COMPARISON_INFO(id,Uuid_StgBattery):
    #ある一定時間の最初と最後のデータを２行にして返却
    df_hokan = pd.DataFrame()
    list_hokan_StgBattery_workingOperationStatus = []
    list_hokan_StgBattery_storedElectricityPercent = []
    list_hokan_StgBattery_acChargeableElectricEnergy = []
    list_hokan_StgBattery_acDischargeableElectricEnergy = []
    list_hokan_StgBattery_storedElectricity = []
    list_hokan_jikoku = []
    scope_StgBattery = ['workingOperationStatus','storedElectricityPercent','acChargeableElectricEnergy','acDischargeableElectricEnergy','storedElectricity']
    min = 60 #
    df_StgBattery,endtime_StgBattery = DataRetrieval_LATEST_Xmin(id,Uuid_StgBattery,scope_StgBattery,min)

    #df_StgBatteryが空ということもあり得る！！！！
    if df_StgBattery.empty == True or len(df_StgBattery) < 2:#空であればNoneを入れる。
        list_hokan_StgBattery_workingOperationStatus.append(None)
        list_hokan_StgBattery_storedElectricityPercent.append(None)
        list_hokan_StgBattery_acChargeableElectricEnergy.append(None)
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(None)
        list_hokan_StgBattery_storedElectricity.append(None)
    else:
        now = datetime.now()
        #このタイミングでgeneratedTimeで範囲を絞る
        #今が16:05だと、15:30～16:00
        #今が16:31だと、16:00～16:00
        #今が16:59だと、16:00～16:30　と言いたいところだが、
        #10分程度のタイムラグを考慮して、
        #15:40～16:10→15:00～15:30
        #16:10～16:40→15:30～16:00
        #→要するに、10分以上40分以内に実行してくれということになる。
        # =10分以内だと１個前のコマが取れるということ。
        #今が16:05だと、15:00～15:30
        #今が16:31だと、15:30～16:00
        #今が16:59だと、16:00～16:30
        if now.minute <= 10:
            if now.hour == 0:
                start_time = now.replace(minute=0,second=0, microsecond=0) - timedelta(hours=1)
            else:
                start_time = now.replace(hour=now.hour-1,minute=0,second=0, microsecond=0)
            end_time = now.replace(hour=now.hour-1,minute=30,second=0, microsecond=0)
        elif now.minute > 10 and now.minute <= 40:
            if now.hour == 0:
                start_time = now.replace(minute=30,second=0, microsecond=0) - timedelta(hours=1)
            else:
                start_time = now.replace(hour=now.hour-1,minute=30,second=0, microsecond=0)
            end_time = now.replace(hour=now.hour,minute=0,second=0, microsecond=0)
        elif now.minute > 40:
            start_time = now.replace(hour=now.hour,minute=0,second=0, microsecond=0)
            end_time = now.replace(hour=now.hour,minute=30,second=0, microsecond=0)       
        #かつ上下3分ずつ多めに見ておく(5分だと長すぎる)
        start_time = start_time - timedelta(minutes=3)
        end_time = end_time + timedelta(minutes=3)
        #そしてこの範囲のdfだけにする
        df_StgBattery = df_StgBattery[df_StgBattery['generatedTime'] < end_time]
        df_StgBattery = df_StgBattery[df_StgBattery['generatedTime'] > start_time]

        df = df_StgBattery.query('scope=="workingOperationStatus"')
        df = df.replace(65, 'Rapid charging')
        df = df.replace(66, 'Charging')
        df = df.replace(67, 'Discharging')
        df = df.replace(68, 'Standby')

        list_hokan_StgBattery_workingOperationStatus.append(df.head(1).iloc[0]['value'])
        list_hokan_StgBattery_workingOperationStatus.append(df.tail(1).iloc[0]['value'])

        df = df_StgBattery.query('scope=="storedElectricityPercent"')
        list_hokan_StgBattery_storedElectricityPercent.append(df.head(1).iloc[0]['value'])
        list_hokan_StgBattery_storedElectricityPercent.append(df.tail(1).iloc[0]['value'])

        df = df_StgBattery.query('scope=="acChargeableElectricEnergy"')
        list_hokan_StgBattery_acChargeableElectricEnergy.append(df.head(1).iloc[0]['value'])
        list_hokan_StgBattery_acChargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])
        list_hokan_jikoku.append(df.head(1).iloc[0]['generatedTime'])#acChargeableElectricEnergyが取れた時刻を一応取っておく
        list_hokan_jikoku.append(df.tail(1).iloc[0]['generatedTime'])

        df = df_StgBattery.query('scope=="acDischargeableElectricEnergy"')
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(df.head(1).iloc[0]['value'])
        list_hokan_StgBattery_acDischargeableElectricEnergy.append(df.tail(1).iloc[0]['value'])

        df = df_StgBattery.query('scope=="storedElectricity"')
    
        try:#蓄電池のメーカによっては残電力量が取れない
            list_hokan_StgBattery_storedElectricity.append(df.head(1).iloc[0]['value'])
            list_hokan_StgBattery_storedElectricity.append(df.tail(1).iloc[0]['value'])
        except IndexError:
            list_hokan_StgBattery_storedElectricity.append(None)
            list_hokan_StgBattery_storedElectricity.append(None)
    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan['battery状態'] = list_hokan_StgBattery_workingOperationStatus
    df_hokan['SOC'] = list_hokan_StgBattery_storedElectricityPercent
    df_hokan['充電可能量'] = list_hokan_StgBattery_acChargeableElectricEnergy
    df_hokan['放電可能量'] = list_hokan_StgBattery_acDischargeableElectricEnergy
    df_hokan['残電力量'] = list_hokan_StgBattery_storedElectricity

    return df_hokan,endtime_StgBattery

def store_thermometer(id,Uuid_smart):#scopeはこの関数内で定義
    df_hokan = pd.DataFrame()
    list_hokan_jikoku = []
    list_hokan_temperature = []
    list_hokan_humidity = []
    list_hokan_battery = []

    scope_thermometer=['temperature','humidity','battery']
    df_thermometer,endtime_thermometer = DataRetrieval_30min(id,Uuid_smart,scope_thermometer)
    df = df_thermometer.query('scope=="temperature"')
    list_hokan_temperature.append(round(df['value'].mean(),1))
    df = df_thermometer.query('scope=="humidity"')
    list_hokan_humidity.append(round(df['value'].mean(),1))
    df = df_thermometer.query('scope=="battery"')
    list_hokan_battery.append(round(df['value'].mean(),1))

    list_hokan_jikoku.append(endtime_thermometer)
    df_hokan['時刻'] = list_hokan_jikoku
    df_hokan = df_hokan.set_index('時刻')
    df_hokan['気温'] = list_hokan_temperature
    df_hokan['湿度'] = list_hokan_humidity
    df_hokan['温度計_残電池'] = list_hokan_battery

    return df_hokan,endtime_thermometer


def devices(id):#これはクラスのメソッドではなく、
    base_url = 'https://ioeapi.nextdrive.io/v1/gateways/'
    devices_url = base_url + id +'/devices'
    response = requests.get(devices_url,headers=headers)
    data = response.json()
    data = data['devices']#devicesしか特に入っていない。
    df_devices = pd.DataFrame()
    name =[]
    Uuid =[]
    onlineStatus = []
    for i in data:
        name.append(i['name'])
        Uuid.append(i['deviceUuid'])
        onlineStatus.append(i['onlineStatus'])
    df_devices['device名'] =name 
    df_devices['Uuid'] = Uuid
    df_devices['Status'] = onlineStatus
    
    return df_devices

def Control_AirCon(operationStatus,operationMode,temperature,name,Uuid):
    if operationStatus == 'ON':
        operationStatus = 48
    if operationStatus == 'OFF':
        operationStatus = 49
    if operationMode == 'Cooling':
        operationMode = 66
    if operationMode == 'Heating':
        operationMode = 67
    if operationMode == 'Dehumidification':
        operationMode = 68

    if name == False:
        return 'no such device'
    else:
        url = 'https://ioeapi.nextdrive.io/v1/devices/'+Uuid+'/control'
        data = {"scopes":[{"operationStatus":operationStatus},{"operationMode":operationMode},{"temperatureSetting":temperature}]}

        data = json.dumps(data)
        response = requests.put(url,headers=headers, data=data)

    return response

#充電指示ならacDischargeAmountSettingはゼロ、待機指示ならacDischargeAmountSettingもacDischargeAmountSettingもゼロという仕様
def Control_StgBattery(operationMode,acChargeAmountSetting,acDischargeAmountSetting,name,Uuid):
    if operationMode == 'Charging':
        operationMode = 66
    elif operationMode == 'Discharging':
        operationMode = 67
    elif operationMode == 'Standby':#スペル注意!
        operationMode = 68
    elif operationMode == 'Automatic':
        operationMode = 70
    elif operationMode == 'Restart':
        operationMode = 72
    else:
        print(name,'のoperationModeが異常です!!!!')

    if name == False:
        return 'no such device'
    else:
        url = 'https://ioeapi.nextdrive.io/v1/devices/'+Uuid+'/control'
        #事実上、待機もしくは自動指示の場合
        if acChargeAmountSetting==0 and acDischargeAmountSetting==0:
            data = {"scopes":[{"operationMode":operationMode}]}
        #事実上、充電指示の場合
        elif acDischargeAmountSetting==0:
            data = {"scopes":[{"operationMode":operationMode},{"acChargeAmountSetting":acChargeAmountSetting}]}
        #事実上、放電指示の場合
        elif acChargeAmountSetting==0:
            data = {"scopes":[{"operationMode":operationMode},{"acDischargeAmountSetting":acDischargeAmountSetting}]}
        print(name,'の蓄電池への指示内容：',data)
        data = json.dumps(data)
        #一旦待機指示を出す(SF厚木にある蓄電池はなぜか必要だったが、他は必要ない)
        """
        data_standby = {"scopes":[{"operationMode":68}]}
        data_standby = json.dumps(data_standby)
        response_standby = requests.put(url,headers=headers, data=data_standby)
        print('一旦待機指示：',response_standby)
        time.sleep(5) 
        """

        response = requests.put(url,headers=headers, data=data)

    return response

#エコキュート
def Control_ElecWaterHeater(operationStatus,autoWaterHeatingMode,name,Uuid):
    if operationStatus == 'ON':
        operationStatus = 48
    elif operationStatus == 'OFF':
        operationStatus = 49
    else:
        print(name,'のoperationStatusが異常です。')      
    if autoWaterHeatingMode == 'Automatic water heating functionused':
        autoWaterHeatingMode = 65
    elif autoWaterHeatingMode == 'Non-automatic waterheating function stopped':
        autoWaterHeatingMode = 67
    elif autoWaterHeatingMode == 'Nonautomaticwater heating functionused':
        autoWaterHeatingMode = 66
    else:
        print(name,'のautoWaterHeatingModeが異常です。')

    if name == False:
        return 'no such device'
    else:
        url = 'https://ioeapi.nextdrive.io/v1/devices/'+Uuid+'/control'
        #オフの指示の場合、
        if operationStatus == 49:
            data = {"scopes":[{"operationStatus":operationStatus}]}

        #オンの指示の場合
        elif operationStatus == 48:
            data = {"scopes":[{"autoWaterHeatingMode":autoWaterHeatingMode},{"operationStatus":operationStatus}]}
        
        data = json.dumps(data)
        response = requests.put(url,headers=headers, data=data)
        print(name,id,'のエコキュートのコントロール指示：',response)
        return response