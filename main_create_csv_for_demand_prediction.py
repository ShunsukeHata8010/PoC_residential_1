import os
import glob
import pandas as pd
import datetime
import jpholiday
import configparser
from logging import getLogger, Formatter, FileHandler, DEBUG
#設定の読み込み
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
USER_INFORMATION_FOLDER = config['Folders']['USER_INFORMATION_FOLDER']
FOR_DEMAND_PREDICTION_FOLDER = config['Folders']['FOR_DEMAND_PREDICTION_FOLDER']
DATA_FROM_DATABASE = config['Folders']['DATA_FROM_DATABASE']
LOG_FILE_NAME_1 = config['LOG']['LOG_FILE_NAME_1']

#ロガーの設定
logger = getLogger('main_create_csv_for_demand_prediction')#実行ファイル名
logger.setLevel(DEBUG)
file_handler = FileHandler(filename=LOG_FILE_NAME_1, encoding='utf-8')#logファイルは全部共通にする
file_handler.setLevel(DEBUG)
handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(handler_format)
logger.addHandler(file_handler)

def data_processing_for_prediction(name,id):
    path_saki = FOR_DEMAND_PREDICTION_FOLDER+ '\\'+str(name)+'_'+str(id)
    path_moto = DATA_FROM_DATABASE + '\\' + str(name)+'_'+str(id)
    
    if os.path.exists(path_saki) == False:
        print(name+'_'+str(id)+'は、需要電力予測用のデータを格納する先のフォルダがないので作成します。')
        os.mkdir(path_saki)

    allFiles = glob.glob(path_moto + "/*.csv")

    if len(allFiles) > 1:
        print(name+'_'+str(id)+'には、読み込みファイルが2個以上あります。')
    elif len(allFiles) == 0:
        print(name+'_'+str(id)+'には、読み込みファイルが一つもありません。')
    else:
        for file in allFiles:#1つのファイルしかないという前提だが、forにしている。
            df = pd.read_csv(file,encoding="shift_jis")
        
        data_youbi = []
        data_shuku = []
        data_jikan = []
        df = df.dropna(how='all', axis=1)#すべてnanの列=データ取得できていない列は削除

        if '買電量'not in df.columns:
            print('name'+'_'+str(id)+'は、買電量がもともと取得できていません。')
        else:
            if 'PV発電量' in df.columns:#PV発電量列があるとき
                df = df[['日時','PV発電量', '買電量']]
                df = df.dropna(how='any', axis=0)#nanが入っている行を削除
                df['需要電力']=df['PV発電量']+df['買電量']
            else:#PV発電量というカラムがないとき
                if '予測値_PV' in df.columns:#予測値はあるとき
                    df = df[['日時','予測値_PV','買電量']]
                    df = df.dropna(how='any', axis=0)#nanが入っている行を削除
                    df['需要電力']=df['予測値_PV']+df['買電量']
                else:
                    df = df[['日時','買電量']]
                    df = df.dropna(how='any', axis=0)#nanが入っている行を削除
                    df['需要電力']=df['買電量']

            df = df[["日時","需要電力"]]#PV発電量と順潮流はもう不要なので削除する。このような抽出タイプだと、他の列に何が入っていてもOK。

            for time in df['日時']:
                if type(time)is not datetime:#datetime型でないならdatetime型にする。
                    try:
                        time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                    except:
                        time = datetime.datetime.strptime(time, '%Y/%m/%d %H:%M')
                youbi= time.strftime('%A')#%AでWednesdayという形で取れる。
                data_youbi.append(youbi)
                hour = time.hour

                if len(str(hour)) == 1:#コマ順に並べる処置。だが0:00が一番最初に来てしまう。
                    hour = '0' + str(hour)

                if str(time.hour) == '00':
                    print(time.min)

                if time.minute == 0:
                    minute = '00'
                else:    
                    minute = time.minute
                jikan = str(hour) + str(':') + str(minute)
                data_jikan.append(jikan) #時間をstrで格納

                if time.weekday()>= 5 or jpholiday.is_holiday(time)==True:
                    shuku = 1
                else:
                    shuku = 0
                data_shuku.append(shuku)

            df['曜日'] = data_youbi
            df['コマ'] = data_jikan
            df['土日祝'] = data_shuku
            df_youbi = pd.get_dummies(df['曜日'])
            df_jikan = pd.get_dummies(df['コマ'])
            df = pd.concat([df, df_youbi,df_jikan], axis=1)
            os.chdir(path_saki)
            filename = '需要電力データ'+ str(name)+'_'+str(id) + '.csv'
            df.to_csv(filename,encoding="shift_jis")

            return df

if __name__ == '__main__':
    os.chdir(USER_INFORMATION_FOLDER)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除
    
    for name, id in zip(df_user['name'], df_user['Product ID']):
        filepath = DATA_FROM_DATABASE + '\\' + str(name)+'_'+str(id)
        if os.path.exists(filepath) == False:
            print(name+'_'+str(id)+'は、mysqlから取得したデータが格納されているフォルダがありません。処理終了')
        else:
            print(name+'_'+str(id)+'は、mysqlから取得したデータが格納されているフォルダがあるため、続きを実行します。')
            data_processing_for_prediction(name,id)
