import os
import time
from urllib.parse import urljoin
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, date, timedelta
import traceback
from database_mysql_for_jepx import create_database_for_jepx

def each_area(df,area):
    price_area = 'エリアプライス'+ area +'(円/kWh)'
    df = df[['年月日','時刻コード',price_area]]
    df = df.reset_index(drop=True)
    day = str(df.iat[0,0]).replace('/','')
    time = []
    for i in df['時刻コード']:
        if i <48:
            t = timedelta(hours=i/2)
            time.append(str(t))
        if i == 48:
            time.append('00:00:00')

    df['時刻']=time
    time_2 = []

    for i,j in zip(df['年月日'],df['時刻']):
        t = str(i).replace('/','-')
        if j =='00:00:00':
            x = datetime.strptime(t,'%Y-%m-%d')
            y = x +timedelta(days=1)
            time_2.append(y)    
        else:
            n = t +' '+ str(j)
            time_2.append(n)
    df['時刻']=time_2
    df = df[['時刻',price_area]]#これ以外はdrop
    filename = 'JEPX価格'+area+day+'.csv'
    try:
        os.chdir(path_origin+'\\JEPX\\'+area+'確定価格')
        df.to_csv(filename,encoding="shift_jis")
    except Exception as e:#何かのエラーでたら用(スクレイピングは不安定なので)
        t = traceback.format_exception_only(type(e), e)
        print(t)
        print(area,day,'上記のエラーがでました')


if __name__ == '__main__':
    url="http://www.jepx.org/market/"
    path_origin = os.path.dirname(os.path.abspath(__file__))#このファイルのあるディレクトリのパスを取得
    #ここは絶対パスになっている！！
    os.chdir("C:\\Users\\f-apl-admin\\Downloads")
    browser = webdriver.Chrome(ChromeDriverManager().install())#バージョンが違っても自動でアップデートしてくれる
    browser.implicitly_wait(3)
    browser.get(url)
    time.sleep(1)
    browser_form = browser.find_element_by_xpath('/html/body/div[2]/div[1]/div[1]/div[8]/table/tbody/tr[2]/td[2]/a')#翌日のボタン
    browser_form.click()
    time.sleep(5) 
    now = datetime.now()
    if now.month>=4:
        year = now.year
    else:
        year = now.year - 1

    while True:
        try:
            downloadfilename ='spot_'+str(year)+'.csv'#2021年度なら、spot_2021.csvというファイル名でダウンロードされるので、それに合わせる
            df = pd.read_csv(downloadfilename,encoding="shift_jis")
        except:#エラー発生したら2秒追加
            time.sleep(2)
        else:#エラー発生しなかったら脱出
            break
    browser.close()
    time.sleep(2)
    df = df.tail(48)
    area_list=['北海道','東北','東京','中部','北陸','関西','中国','九州','四国']
    for area in area_list:
        each_area(df,area)
    #ここは絶対パスになっている！！
    os.chdir("C:\\Users\\f-apl-admin\\Downloads")
    os.remove(downloadfilename)#最初にダウンロードしたファイルを削除
    time.sleep(1)
    if os.path.exists('spot_'+str(year)+'.csv.crdownload')== True:
        os.remove('spot_'+str(year)+'.csv.crdownload')
