import os
import time
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, date, timedelta
from database_mysql_for_jepx import create_database_for_jepx, update_database_for_jepx
import sqlalchemy
import configparser
from logging import getLogger, Formatter, FileHandler, DEBUG

#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
JEPX_URL = config['JEPX']['JEPX_URL']
DEFAULT_DOWNLOAD_FOLDER = config['Folders']['DEFAULT_DOWNLOAD_FOLDER']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']

#ロガーの設定
logger = getLogger('main_download_jepx_each_area')
logger.setLevel(DEBUG)
file_handler = FileHandler(filename=LOG_FILE_NAME_1, encoding='utf-8')
file_handler.setLevel(DEBUG)
handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(handler_format)
logger.addHandler(file_handler)


def each_area(df,area):
    price_area = 'エリアプライス'+ area +'(円/kWh)'
    df = df[['年月日','時刻コード',price_area]]
    df = df.reset_index(drop=True)
    day = str(df.iat[0,0]).replace('/','')
    time = []
    for i in df['時刻コード']:
        if i < 48:
            t = timedelta(hours=i/2)
            time.append(str(t))
        if i == 48:
            time.append('00:00:00')

    df['時刻'] = time
    time_2 = []

    for i,j in zip(df['年月日'],df['時刻']):
        t = str(i).replace('/','-')
        if j == '00:00:00':
            x = datetime.strptime(t,'%Y-%m-%d')
            y = x +timedelta(days=1)
            time_2.append(y)    
        else:
            n = t +' '+ str(j)
            time_2.append(n)
    df['時刻'] = time_2
    df = df[['時刻',price_area]]#これ以外はdrop
    power_com = area.replace('北海道','Hokkaido').replace('東北','Tohoku').replace('東京','Tokyo').replace('中部','Chubu').replace('北陸','Hokuriku').replace('関西','Kansai').replace('中国','Chugoku').replace('四国','Shikoku').replace('九州','Kyushu')
    for index ,row in df.iterrows():
        time = row['時刻']
        try:
            price = row[price_area]
            create_database_for_jepx(power_com,time,price)
            print(area,'jepx価格を格納します')
        except sqlalchemy.exc.IntegrityError:
            print('日時に重複があります')
            price = row[price_area]
            update_database_for_jepx(power_com,time,price)


if __name__ == '__main__':
    os.chdir(DEFAULT_DOWNLOAD_FOLDER)
    browser = webdriver.Chrome(ChromeDriverManager().install())#バージョンが違っても自動でアップデートしてくれる
    browser.implicitly_wait(3)
    browser.get(JEPX_URL)
    time.sleep(1)
    browser_form = browser.find_element_by_xpath('/html/body/div[2]/div[1]/div[1]/div[8]/table/tbody/tr[2]/td[2]/a')#翌日のボタン
    browser_form.click()
    time.sleep(5) 
    now = datetime.now()
    if now.month >= 4:
        year = now.year
    else:
        year = now.year - 1

    while True:
        try:
            downloadfilename ='spot_'+ str(year)+ '.csv'#2021年なら、spot_2021.csvというファイル名でダウンロードされるので、それに合わせる
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
    os.chdir(DEFAULT_DOWNLOAD_FOLDER)
    os.remove(downloadfilename)#最初にダウンロードしたファイルを削除
    time.sleep(1)
    if os.path.exists('spot_'+str(year)+'.csv.crdownload')== True:
        os.remove('spot_'+str(year)+'.csv.crdownload')
