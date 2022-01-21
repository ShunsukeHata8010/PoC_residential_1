import requests 
import os 
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta


def get_areacode(address):
    area_list = []
    #市や町が混在する住所があるので、最初の市や町を抽出するようにする。
    #ただし、これだと市原市のように「市」が含まれる市だと上手くいかない
    #→結局市原市くらいなので、特別対応で良しとする
    if '市原市' in address:#「町山町」のような市町村があれば、ここに追記
        area = '千葉県市原市'
    else:
        city = address.find('市')
        city = address[:city+1] #ない場合は空白が返される
        if not city == '':
            area_list.append(city)
        ward = address.find('区')
        ward = address[:ward+1]
        if not ward == '':
            area_list.append(ward)
        town = address.find('町')
        town = address[:town+1]
        if not town == '':
            area_list.append(town)
        village = address.find('村')
        village = address[:village+1]
        if not village == '':
            area_list.append(village)
        area = min(area_list)#最小の長さのもの＝町や市が重複している場合短い方

    path_opt = os.path.dirname(os.path.abspath(__file__))#このファイルのあるディレクトリのパスを取得
    os.chdir(path_opt)
    df = pd.read_excel('注意報警報発表区_20210325.xlsx')

    for i,j in zip(df['地域名'],df['市町村コード']):
        if i == area:
            area_code = j
    #上記で重複など発生しないかは未確認

    return area_code,area

def warning(address):
    API_KEY = "3f21c45b9d939bd765ae3e6d39d98278" 
    api = "http://api.yumake.jp/1.0/weatherWarning.php?code={エリア}&format={形式名}"
    
    area_code,area = get_areacode(address)
    url = api.format(エリア=area_code,形式名="json") 

    params = {"key":API_KEY}

    response = requests.post(url,params=params)
    data = response.json()

    areaName = data['areaName']
    list_waningKind = data['warningKind']#list_waningKindは辞書のリスト
    Warninglist = []
    #無い場合、「{'warningName': '', 'warningCode': '', 'warningStatus': '発表警報・注意報はなし'}」
    for i in list_waningKind:
        W_Code = i['warningCode']#無い場合、空欄になる。
        if W_Code=='02' or W_Code=='03'or W_Code=='04' or W_Code=='05' or W_Code=='32' or W_Code=='33'or W_Code=='35' or W_Code=='36':
            #02:暴風雪警報,03:大雨警報,04:洪水警報,05:暴風警報,32:暴風雪特別警報,33:大雨特別警報,35:暴風特別警報,36:大雪特別警報
            warningName = i['warningName']
            Warninglist.append(warningName)
            
    if not Warninglist:#リストが空だったらFalse
        Warning = False
    else: 
        Warning = True#リストに何か入っていたらTrue

    return Warning,Warninglist,areaName#areaNameはAPIで取れているもの(再確認用)
