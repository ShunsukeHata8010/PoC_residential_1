from datetime import time,datetime,timedelta
import os
from altair.vegalite.v4.schema.core import Encoding
from numpy.lib.shape_base import tile
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from nextdriveAPI_class import House
from create_csv_from_database import read_database,Data
import sqlalchemy
import time
from database_mysql_for_jepx import read_database_jepx,Data_jepx

#タイトルを入れる
def input_title():
    st.set_page_config(layout="wide")
    title = '住宅実証_管理画面'
    st.title(title)

#スライダーにフォルダ名の一覧をボックスを作って、選ばれたユーザーのデータのパスを返す

def make_select_users():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))#このファイルのあるディレクトリへ移動
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'

    files = os.listdir(path_userinfo)
    allfolder = [f for f in files if os.path.isdir(os.path.join(path_userinfo, f))]
    selected_user = st.sidebar.selectbox(
        '表示するユーザーを選択：',#デフォルトで表示している文字
        allfolder#表示するリスト
    )
    st.write(f"""
    {selected_user}さんの
    """)
    selected_name = selected_user.replace(path_userinfo,'').split('_')[0]
    selected_id = selected_user.replace(path_userinfo,'').split('_')[1]

    return selected_name,selected_id

#スライダーに表示したい期間を表現する
def make_duration():
    selected_duration = st.sidebar.slider('取得する日数',1,10,4)
    cut_dutation = st.sidebar.slider('カットする日数',0,10,1)
    st.write(f"""
    概ね{cut_dutation-1}日前から{selected_duration-1}日前のデータをグラフ化しています。
    """)
    return selected_duration,cut_dutation

@st.cache(suppress_st_warning=True)
def df_from_database(name,id):
    now = datetime.now()
    #ここで現在コマより新しい行だけをとってくるための作業をする            
    day_20ago = now.replace(minute=0, second=0, microsecond=0) - timedelta(20)
    print(day_20ago)
    db_session = read_database(name,id)
    db = db_session.query(Data).all()
    #db = db_session.query(Data).filter(Data.time >day_20ago)
    columns=['id','日時','予測値_PV','PV発電量','買電量','予測値_demand',
    'battery状態','SOC','充電可能量','放電可能量','残電力量','SOC_増減',
    '充電量可能量_増減','放電可能量_増減','残電力量_増減','充放電指示量',
    'EQ動作状態','沸き上げ自動設定','沸き上げ中状態',
    'ｴﾈﾙｷﾞｰｼﾌﾄ参加状態','沸き上げ開始基準時刻','ｴﾈﾙｷﾞｰｼﾌﾄ参回数','昼間沸き上げｼﾌﾄ時刻1','EQ指示時刻',
    'ｴｱｺﾝ状態','ｴｱｺﾝmode','ｴｱｺﾝ設定温度','気温','湿度','温度計_残電池']
    df = pd.DataFrame(columns=columns)

    for row in db:
        #行だが、結局はDataオブジェクトなので、.で取り出すしかない
        #dataframeなので、nanがいい気がするがNoneのままにしている。(nanとnoneが混在している)
        s = pd.Series([row.id,row.time,row.PV_pre,row.PV_actual,row.kaiden,row.demand_pre,
        row.battery_status,row.SOC,row.chargable_amount,row.dischargable_amount,row.remaining_amount,row.SOC_updown,
        row.chargable_amount_updown,row.dischargable_amount_updown,row.remaining_amount_updown,row.Batt_Direction,
        row.Ecocute_status,row.Ecocute_mode,row.Ecocute_heating,
        row.Ecocute_participateInEnergyShift,row.Ecocute_timeToStartHeating,row.Ecocute_numberOfEnergyShift,row.Ecocute_daytimeHeatingShiftTime1,row.Ecocute_Direction,
        row.Aircon_status,row.Aircon_mode,row.Aircon_temp,row.Thermo_temp,row.Thermo_humid,row.Thermo_battery],index=columns)

        df = df.append(s,ignore_index=True)

    df = df.set_index('id')
    df = df.replace({None:np.nan})#Noneのままのところもある。
    df = df.dropna(how='all', axis=1)#すべてがnanの列を削除
    df = df.dropna(how='all', axis=0)#すべてがnanの行を削除(日時すらnanのやつが入り込んだとき用)
    df = df.sort_values('日時', ascending=True)#一応ソートしておく
    df = df.drop_duplicates(subset='日時')#日時が重複するデータは削除
    time.sleep(0.05)
    return df

def make_1st_chart(df,selected_duration,cut_duration,df_jepx,power_com):
    print(df_jepx)
    df_jepx['価格(10分の1)_'+power_com] = df_jepx['価格'] * 0.1
    df = pd.merge(df, df_jepx, on='日時', how='outer')
    print(df)
    selected_koma = selected_duration*48
    cut_koma = cut_duration*48
    df_length = len(df)

    if df_length >= selected_koma:
        min_display = df_length - selected_koma
    else:
        min_display = 0

    if df_length >= cut_koma:
        max_display = df_length - cut_koma
    else:
        max_display = df_length
    print(min_display,max_display)
    df = df.iloc[min_display:max_display,:]
    print(df)
    list_linechart_1 = []
    list_linechart_2= []
    list_barchart_1 = []
    list_tick_1 = []
    y_heating_onoff = []
    y_aircon = []
    df_copy = df.copy()#SettingWithCopyWarning防止用
    #print(df_copy)

    if '価格(10分の1)_'+power_com in df.columns:
        list_linechart_2.append('価格(10分の1)_'+power_com)

    if '予測値_PV'in df.columns:
        list_linechart_1.append('予測値_PV')

    if 'PV発電量'in df.columns:
        list_linechart_1.append('PV発電量')

    if '予測値_demand'in df.columns:
        list_linechart_1.append('予測値_demand')

    if '買電量'in df.columns:
        if 'PV発電量'in df.columns:
            df_copy['需要_実績'] = df['買電量'] + df['PV発電量']
            list_linechart_1.append('需要_実績')
        else:
            if '予測値_PV'in df.columns:
                df_copy['需要_実績'] = df['買電量'] + df['予測値_PV']
                list_linechart_1.append('需要_実績')
            else:
                df_copy['需要_実績'] = df['買電量']
                list_linechart_1.append('需要_実績')

        list_linechart_1.append('買電量')

    if '残電力量_増減'in df.columns:
        df_copy = df_copy.rename(columns={'残電力量_増減': '蓄電池_充放電(kWh)'})
        list_barchart_1.append('蓄電池_充放電(kWh)')

    if '充放電指示量' in df.columns:
        df_copy['蓄電池_指示量(kWh)'] = df['充放電指示量']
        list_tick_1.append('蓄電池_指示量(kWh)')

    if '沸き上げ中状態'in df.columns:
        for i in df['沸き上げ中状態'].values.tolist():
            if i =='Heating':
                y_heating_onoff.append(0.5*0.8)
            elif i =='Not heating':
                y_heating_onoff.append(0)
            else:
                y_heating_onoff.append(0)
        df_copy['EQ動作実績(kWh)'] = y_heating_onoff
        list_barchart_1.append('EQ動作実績(kWh)')

    if 'SOC'in df.columns:
        df_copy['蓄電池SOC'] = df['SOC']/100
        list_linechart_1.append('蓄電池SOC')

    if 'ｴｱｺﾝ状態'in df.columns:
        for i in df['ｴｱｺﾝ状態'].values.tolist():
            if i =='ON':
                y_aircon.append(1)
            else:
                y_aircon.append(0)

        df_copy['ｴｱｺﾝ状態']=y_aircon
        list_linechart_1.append('ｴｱｺﾝ状態')

    selected_line_data_1 = st.sidebar.multiselect(
    'グラフに折れ線として入れるデータ種類を選んでください',
    list_linechart_1+list_linechart_2
    )
    selected_bar_data_1 = st.sidebar.multiselect(
    'グラフに棒グラフとして入れるデータ種類を選んでください',
    list_barchart_1
    )
    selected_tick_data_1 = st.sidebar.multiselect(
    'グラフに横棒として入れるデータ種類を選んでください',
    list_tick_1
    )

    selected_line_data_1.append('日時')
    selected_bar_data_1.append('日時')
    selected_tick_data_1.append('日時')

    df_line_1 = df_copy.loc[:,selected_line_data_1]
    df_bar_1 = df_copy.loc[:,selected_bar_data_1]
    df_tick_1 = df_copy.loc[:,selected_tick_data_1]

    df_line_1 = pd.melt(df_line_1,id_vars=['日時']).rename(columns={'value':'kWh'})
    df_bar_1 = pd.melt(df_bar_1,id_vars=['日時']).rename(columns={'value':'kWh'})
    df_tick_1 = pd.melt(df_tick_1,id_vars=['日時']).rename(columns={'value':'kWh'})
    #print(df_line_1)
    #どうも、以下で、タイムゾーンがずれている！→ scale=alt.Scale(type="utc")を入れて解決
    line1 = alt.Chart(df_line_1).mark_line(opacity=0.8).encode(
        x=alt.X('日時:T', scale=alt.Scale(type="utc")),
        y=alt.Y('kWh:Q',stack=None),
        color='variable:N'
        ).properties(
        width=1200,
        height=600
        ).interactive()
    bar1 = alt.Chart(df_bar_1).mark_bar(opacity=0.8).encode(
        x=alt.X('日時:T', scale=alt.Scale(type="utc")),
        y=alt.Y('kWh:Q'),
        color='variable:N'
        ).properties(
        width=1200,
        height=600
        ).interactive()

    tick1 = alt.Chart(df_tick_1).mark_tick(opacity=0.8,thickness=2).encode(
        x=alt.X('日時:T', scale=alt.Scale(type="utc")),
        y=alt.Y('kWh:Q'),
        color='variable:N'
        ).properties(
        width=1200,
        height=600
        ).interactive()

    st.altair_chart(line1 + bar1 + tick1,use_container_width=True)

    return df

#@st.cache(suppress_st_warning=True)
def download_jepx(power_com):
    power_com = power_com.replace('北海道','Hokkaido').replace('東北','Tohoku').replace('東京','Tokyo').replace('中部','Chubu').replace('北陸','Hokuriku').replace('関西','Kansai').replace('中国','Chugoku').replace('四国','Shikoku').replace('九州','Kyushu')
    db_session = read_database_jepx(power_com)
    db = db_session.query(Data_jepx).all()
    df = pd.DataFrame()
    for row in db:
        s = pd.Series([row.id,row.time,row.price])
        df = df.append(s,ignore_index=True)
    
    df = df.rename(columns={0:'id',1:'日時',2:'価格'})
    
    return df

def recent_30min_get(name,id):
    selected_item = st.sidebar.radio('どの機器の直近30分の状況を見ますか?',
                             ['スマートメーター','PV','蓄電池','温湿度計','エアコン','エコキュート'])
    button_30min = st.sidebar.button('直近30分の機器状況を見る')

    if button_30min:
        # 最後の試行で下のボタンがクリックされた
        st.write('直近30分の',selected_item+'状況')

        Person = House(name,id)
        if selected_item =='スマートメーター':
            df,endtime = Person.DataRetrieval_SmartMeter_30min()
            if type(df) is bool:
                if df==False:
                    st.write('スマートメーターは接続されていません。')
            else:
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                st.table(df)

        elif selected_item =='PV':
            df,endtime = Person.DataRetrieval_SolarPW_30min()
            if type(df) is bool:
                if df==False:
                    st.write('PVは接続されていません。')
            else:
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                st.table(df)

        elif selected_item =='蓄電池':
            df,endtime = Person.DataRetrieval_StgBattery_30min()
            if type(df) is bool:
                if df==False:
                    st.write('蓄電池は接続されていません。')
            else:
                value =[]
                str_value=[]
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                #value列はintとstrの混合であるため、これはst.できないらしいので、その対応
                for index,row in df.iterrows():
                    if type(row.value) is str:
                        str_value.append(row.value)
                        value.append(np.nan)
                    elif type(row.value) is int or float:
                        str_value.append(np.nan)
                        value.append(row.value)
                df['value']=value
                df['str_value']=str_value
                
                st.table(df)
        
        elif selected_item =='温湿度計':
            df,endtime = Person.DataRetrieval_thermometer_30min()
            if type(df) is bool:
                if df==False:
                    st.write('温湿度計は接続されていません。')
            else:
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                st.table(df)

        elif selected_item =='エアコン':
            df,endtime = Person.DataRetrieval_AirCon_living_30min()
            if type(df) is bool:
                if df==False:
                    st.write('エアコンは接続されていません。')
            else:
                value =[]
                str_value=[]
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                for index,row in df.iterrows():
                    if type(row.value) is str:
                        str_value.append(row.value)
                        value.append(np.nan)
                    elif type(row.value) is int or float:
                        str_value.append(np.nan)
                        value.append(row.value)
                df['value']=value
                df['str_value']=str_value

                st.table(df)

        elif selected_item =='エコキュート':
            df,endtime = Person.DataRetrieval_ElecWaterHeater_30min()
            if type(df) is bool:
                if df==False:
                    st.write('エコキュートは接続されていません。')
            else:
                value =[]
                str_value=[]
                df = df[['scope', 'generatedTime', 'uploadedTime','value']]
                df = df.sort_values('generatedTime', ascending=False)#降順に設定
                for index,row in df.iterrows():
                    if type(row.value) is str:
                        str_value.append(row.value)
                        value.append(np.nan)
                    elif type(row.value) is int or float:
                        str_value.append(np.nan)
                        value.append(row.value)
                df['value']=value
                df['str_value']=str_value
                st.table(df)

        os.chdir(os.path.dirname(os.path.abspath(__file__)))

#@st.cache(suppress_st_warning=True)
def select_power_com(id):
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('Product ID')
    power_com = df_user.loc[str(id),'電力管内']
    os.chdir(path_origin)
    
    return power_com 

if __name__ == "__main__":
    pd.set_option('display.max_rows', 1500)
    input_title()
    name,id = make_select_users()
    power_com = select_power_com(id)
    df_jepx = download_jepx(power_com)
    try:
        df = df_from_database(name,id)
    except sqlalchemy.exc.OperationalError:
        print(name,'は、まだデータベースに登録されていません。')
    else:
        selected_duration,cut_duration = make_duration()
        make_1st_chart(df,selected_duration,cut_duration,df_jepx,power_com)
    finally:
        recent_30min_get(name,id)


