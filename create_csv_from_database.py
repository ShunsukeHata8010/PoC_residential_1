from numpy.testing._private.utils import print_assert_equal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,Float,String,DateTime,Boolean
from sqlalchemy import desc,asc
import os
import pandas as pd
from sqlalchemy.sql.expression import column
from sqlalchemy.sql.sqltypes import String
import mysql.connector
import sqlalchemy


#Read用関数
def read_database(name,id):
    database = 'data_30min_'+name+'_'+id
    engine = create_engine('mysql+pymysql://root:@Idemitsu1@127.0.0.1/'+database,echo=True)

    db_session = scoped_session(
        sessionmaker(
            autocommit = False,#自動コミット
            autoflush = False,
            bind = engine
        )
    )
    Base = declarative_base()
    Base.query = db_session.query_property()
    try:
        Base.metadata.create_all(bind=engine)#データベースを初期化するイメージ(作られたくらい)
    except sqlalchemy.exc.OperationalError:
        print(name,'は、データベースがありません。')
    return db_session

Base = declarative_base()
#tableはエクセルでいうシート
class Data(Base):
    __tablename__ ='Data_30min' #tableの名前の定義
    id = Column(Integer, primary_key = True)  #idを主キーにしておく
    time = Column(DateTime,unique=True)#一旦False
    PV_pre = Column(Float,unique = False)
    PV_actual = Column(Float,unique = False)
    kaiden = Column(Float,unique = False)
    demand_pre = Column(Float,unique = False)
    #蓄電池
    battery_status = Column(String, unique = False)
    SOC = Column(Integer,unique = False)
    chargable_amount = Column(Float,unique = False)
    dischargable_amount = Column(Float,unique = False)
    remaining_amount = Column(Float,unique = False)
    SOC_updown = Column(Integer, unique = False)
    chargable_amount_updown = Column(Float,unique = False)
    dischargable_amount_updown = Column(Float,unique = False)
    remaining_amount_updown = Column(Float,unique = False)
    Batt_Direction = Column(Float,unique = False)
    #エコキュート
    Ecocute_status = Column(String, unique = False)
    Ecocute_mode = Column(String, unique = False)
    Ecocute_heating = Column(String, unique = False)
    Ecocute_participateInEnergyShift = Column(Boolean, unique = False)
    Ecocute_timeToStartHeating = Column(Integer, unique = False)
    Ecocute_numberOfEnergyShift = Column(Integer, unique = False)
    Ecocute_daytimeHeatingShiftTime1 = Column(Integer, unique = False)
    Ecocute_Direction = Column(Integer, unique = False,nullable= True)
    #エアコン
    Aircon_status = Column(String, unique = False)
    Aircon_mode = Column(String, unique = False)
    Aircon_temp = Column(Integer,unique = False)
    #温湿度計
    Thermo_temp = Column(Integer,unique = False)
    Thermo_humid = Column(Float,unique = False)
    Thermo_battery = Column(Float,unique = False)

    def __init__(self,time = None,PV_pre = None,PV_actual = None,kaiden = None,demand_pre=None,
        battery_status=None,SOC=None,chargable_amount=None,dischargable_amount=None,remaining_amount=None,
        SOC_updown=None,chargable_amount_updown=None,dischargable_amount_updown=None,remaining_amount_updown=None,Batt_Direction=None,
        Aircon_status=None,Aircon_mode=None,Aircon_temp=None,
        Ecocute_status=None,Ecocute_mode=None,Ecocute_heating=None,Ecocute_participateInEnergyShift=None,Ecocute_timeToStartHeating=None,Ecocute_numberOfEnergyShift=None,Ecocute_daytimeHeatingShiftTime1=None,Ecocute_Direction=None,
        Thermo_temp=None,Thermo_humid=None,Thermo_battery=None):
        self.time = time
        self.PV_pre = PV_pre
        self.PV_actual = PV_actual
        self.kaiden = kaiden
        self.demand_pre = demand_pre
        self.battery_status = battery_status
        self.SOC = SOC
        self.chargable_amount = chargable_amount
        self.dischargable_amount = dischargable_amount
        self.remaining_amount = remaining_amount
        self.SOC_updown = SOC_updown
        self.chargable_amount_updown = chargable_amount_updown
        self.dischargable_amount_updown = dischargable_amount_updown
        self.remaining_amount_updown = remaining_amount_updown
        self.Batt_Direction = Batt_Direction
        self.Ecocute_status = Ecocute_status
        self.Ecocute_mode = Ecocute_mode
        self.Ecocute_heating = Ecocute_heating
        self.Ecocute_participateInEnergyShift = Ecocute_participateInEnergyShift
        self.Ecocute_timeToStartHeating = Ecocute_timeToStartHeating
        self.Ecocute_numberOfEnergyShift = Ecocute_numberOfEnergyShift
        self.Ecocute_daytimeHeatingShiftTime1 = Ecocute_daytimeHeatingShiftTime1
        self.Ecocute_Direction = Ecocute_Direction
        self.Aircon_status = Aircon_status
        self.Aircon_mode = Aircon_mode
        self.Aircon_temp = Aircon_temp
        self.Thermo_temp = Thermo_temp
        self.Thermo_humid = Thermo_humid
        self.Thermo_battery = Thermo_battery


def create_df(db):
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

    return df



if __name__ == "__main__":
    #os.chdir("C:\\Users\\f-apl-admin\\住宅実証3\\ユーザー情報")
    path_origin = os.path.dirname(os.path.abspath(__file__)) #このファイルのあるディレクトリのパスを取得
    path_userinfo = path_origin +'\\ユーザー情報'
    os.chdir(path_userinfo)
    df_user = pd.read_excel('ユーザー情報.xlsx')
    df_user = df_user.set_index('番号')
    df_user = df_user.drop('備考', axis=0)#備考行は削除
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    #nameとIDがある行に対して、インスタンスを作成
    for status,name ,id in zip(df_user['active'],df_user['name'],df_user['Product ID']):
        name = str(name)
        id = str(id)
        print(name,id,'のデータベースからのデータ取得を開始します')

        if status =='No':
            print(name,'はアクティブではありません。')
        else:
            db_session = read_database(name,id)
            db = db_session.query(Data).all()
            df = create_df(db)
            filepath = path_origin + '\\mysqlから取得したデータ\\' + str(name)+'_'+str(id)
            if os.path.exists(filepath)==False:
                print(name+'_'+str(id)+'の格納する先のフォルダがないのでフォルダを作成します。')
                os.mkdir(filepath)
            os.chdir(filepath)
            filename =  str(name)+'_'+str(id) + '.csv'
            df.to_csv(filename,encoding="shift_jis")
            print(df)
