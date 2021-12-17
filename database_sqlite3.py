from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,Float,String,DateTime,Boolean
from sqlalchemy import desc,asc
import os
import pandas as pd
from sqlalchemy.sql.sqltypes import Boolean, String
import mysql.connector


#Create用関数
def create_database(name,id,date_time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag):
    database_file = os.path.join(os.path.abspath(os.getcwd()),'DB_'+name+'_'+str(id)+'.db')
    engine = create_engine('sqlite:///'+database_file,convert_unicode =True,echo=True)
    db_session = scoped_session(
        sessionmaker(
            autocommit = False,#自動コミット
            autoflush = False,
            bind = engine
        )
    )

    Base = declarative_base()
    Base.query = db_session.query_property()

    #tableはエクセルでいうシート
    class Data(Base):
        __tablename__ ='Data_30min' #tableの名前の定義
        id = Column(Integer, primary_key = True)  #idを主キーにしておく
        time = Column(DateTime,unique=True)#一旦False
        PV_pre = Column(Float,unique = False)
        PV_actual = Column(Float,unique = False,nullable = True)
        kaiden = Column(Float,unique = False,nullable = True)
        demand_pre = Column(Float,unique = False)
        #蓄電池
        battery_status = Column(String, unique = False,nullable = True)
        SOC = Column(Integer,unique = False,nullable = True)
        chargable_amount = Column(Float,unique = False,nullable = True)
        dischargable_amount = Column(Float,unique = False,nullable = True)
        remaining_amount = Column(Float,unique = False,nullable = True)
        SOC_updown = Column(Integer, unique = False,nullable = True)
        chargable_amount_updown = Column(Float,unique = False,nullable = True)
        dischargable_amount_updown = Column(Float,unique = False,nullable = True)
        remaining_amount_updown = Column(Float,unique = False,nullable = True)
        Batt_Direction = Column(Float,unique = False)
        #エコキュート
        Ecocute_status = Column(String, unique = False,nullable = True)
        Ecocute_mode = Column(String, unique = False,nullable = True)
        Ecocute_heating = Column(String, unique = False,nullable = True)
        Ecocute_participateInEnergyShift = Column(Boolean, unique = False, nullable=True)
        Ecocute_timeToStartHeating = Column(Integer, unique = False, nullable=True)
        Ecocute_numberOfEnergyShift = Column(Integer, unique = False, nullable=True)
        Ecocute_daytimeHeatingShiftTime1 = Column(Integer, unique = False,nullable= True)
        Ecocute_Direction = Column(Integer, unique = False,nullable= True)
        #エアコン
        Aircon_status = Column(String, unique = False,nullable = True)
        Aircon_mode = Column(String, unique = False,nullable = True)
        Aircon_temp = Column(Integer,unique = False,nullable = True)
        #温湿度計
        Thermo_temp = Column(Integer,unique = False,nullable = True)
        Thermo_humid = Column(Float,unique = False,nullable = True)
        Thermo_battery = Column(Float,unique = False,nullable = True)

        def __init__(self,time = None,PV_pre = None,PV_actual = None,kaiden = None,demand_pre=None,
            battery_status=None,SOC=None,chargable_amount=None,dischargable_amount=None,remaining_amount=None,
            SOC_updown=None,chargable_amount_updown=None,dischargable_amount_updown=None,remaining_amount_updown=None,Batt_Direction=None,
            Ecocute_status=None,Ecocute_mode=None,Ecocute_heating=None,Ecocute_participateInEnergyShift=None,Ecocute_timeToStartHeating=None,Ecocute_numberOfEnergyShift=None,Ecocute_daytimeHeatingShiftTime1=None,Ecocute_Direction=None,
            Aircon_status=None,Aircon_mode=None,Aircon_temp=None,            
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

    Base.metadata.create_all(bind=engine)#データベースを初期化するイメージ(作られたくらい)
    #ここでデフォルトの値を決めておくと便利。
    user = 'user'
    PV_pre = None
    PV_actual = None
    kaiden = None
    demand_pre = None
    battery_status = None
    SOC = None
    chargable_amount = None
    dischargable_amount = None
    remaining_amount = None
    SOC_updown = None
    chargable_amount_updown = None
    dischargable_amount_updown = None
    remaining_amount_updown = None
    Batt_Direction = None
    Ecocute_status = None
    Ecocute_mode = None
    Ecocute_heating = None
    Ecocute_participateInEnergyShift = None
    Ecocute_timeToStartHeating = None
    Ecocute_numberOfEnergyShift = None
    Ecocute_daytimeHeatingShiftTime1 = None
    Ecocute_Direction = None
    Aircon_status = None
    Aircon_mode = None
    Aircon_temp = None
    Thermo_temp = None
    Thermo_humid = None
    Thermo_battery = None

    #PV発電予測プログラム実行によって得るデータ
    if flag == 'PV_pre':
        print('createにて、PV予測値を格納します')
        data_30min = Data(time=date_time,PV_pre=value_1)
    #需要電力予測プログラム実行によって得るデータ
    if flag == 'demand_pre':
        print('createにて、demand予測値を格納します')
        data_30min = Data(time=date_time,demand_pre=value_1)
    #get操作によって得るデータ。一発でcreateしたい。。。
    else:
        if 'PVactual' in flag:
            PV_actual = value_1
        if 'kaiden' in flag:
            kaiden = value_2
        if 'Battery' in flag:
            battery_status = list_battery[0]
            SOC = list_battery[1]
            chargable_amount = list_battery[2]
            dischargable_amount = list_battery[3]
            remaining_amount = list_battery[4]
        if 'B_updown' in flag:
            SOC_updown = list_battery_2[0]
            chargable_amount_updown = list_battery_2[1]
            dischargable_amount_updown = list_battery_2[2]
            remaining_amount_updown = list_battery_2[3]
        if 'B_direction' in flag:
            Batt_Direction = value_1
        if 'Ecocute' in flag:
            Ecocute_status = list_ecocute[0]
            Ecocute_mode = list_ecocute[1]
            Ecocute_heating = list_ecocute[2]
            Ecocute_participateInEnergyShift = list_ecocute[3]
            Ecocute_timeToStartHeating = list_ecocute[4]
            Ecocute_numberOfEnergyShift = list_ecocute[5]
            Ecocute_daytimeHeatingShiftTime1 = list_ecocute[6]
        if 'E_direction' in flag:
            Ecocute_Direction = value_1
        if 'Aircon' in flag:
            Aircon_status = list_aircon[0]
            Aircon_mode = list_aircon[1]
            Aircon_temp = list_aircon[2]
        if 'Thermo' in flag:
            Thermo_temp = list_thermo[0]
            Thermo_humid = list_thermo[1]
            Thermo_battery = list_thermo[2]
 
        data_30min = Data(time=date_time,kaiden=kaiden,PV_actual=PV_actual,
        battery_status=battery_status,SOC=SOC,chargable_amount=chargable_amount,dischargable_amount=dischargable_amount,remaining_amount=remaining_amount,
        SOC_updown=SOC_updown,chargable_amount_updown=chargable_amount_updown,dischargable_amount_updown=dischargable_amount_updown,remaining_amount_updown=remaining_amount_updown,Batt_Direction=Batt_Direction,
        Ecocute_status=Ecocute_status,Ecocute_mode=Ecocute_mode,Ecocute_heating=Ecocute_heating,Ecocute_participateInEnergyShift=Ecocute_participateInEnergyShift,Ecocute_timeToStartHeating=Ecocute_timeToStartHeating,Ecocute_numberOfEnergyShift=Ecocute_numberOfEnergyShift,Ecocute_daytimeHeatingShiftTime1=Ecocute_daytimeHeatingShiftTime1,Ecocute_Direction=Ecocute_Direction,
        Aircon_status=Aircon_status,Aircon_mode=Aircon_mode,Aircon_temp=Aircon_temp,
        Thermo_temp=Thermo_temp,Thermo_humid=Thermo_humid,Thermo_battery=Thermo_battery)     

    if data_30min == 'user':
        print('createもupdateもするデータがありません。')
    else:
        db_session.add(data_30min)
        db_session.commit()


#UPDATE用関数
def update_database(name,id,date_time,value_1,value_2,list_battery,list_battery_2,list_ecocute,list_aircon,list_thermo,flag):
    database_file = os.path.join(os.path.abspath(os.getcwd()),'DB_'+name+'_'+str(id)+'.db')
    engine = create_engine('sqlite:///'+database_file,convert_unicode =True,echo=True)
    db_session = scoped_session(
        sessionmaker(
            autocommit = False,#自動コミット
            autoflush = False,
            bind = engine
        )
    )

    Base = declarative_base()
    Base.query = db_session.query_property()

    #tableはエクセルでいうシート
    class Data(Base):
        __tablename__ ='Data_30min' #tableの名前の定義
        id = Column(Integer, primary_key = True)  #idを主キーにしておく
        time = Column(DateTime,unique=True)#一旦False
        PV_pre = Column(Float,unique = False)
        PV_actual = Column(Float,unique = False,nullable = True)
        kaiden = Column(Float,unique = False,nullable = True)
        demand_pre = Column(Float,unique = False)
        #蓄電池
        battery_status = Column(String, unique = False,nullable = True)
        SOC = Column(Integer,unique = False,nullable = True)
        chargable_amount = Column(Float,unique = False,nullable = True)
        dischargable_amount = Column(Float,unique = False,nullable = True)
        remaining_amount = Column(Float,unique = False,nullable = True)
        SOC_updown = Column(String, unique = False,nullable = True)
        chargable_amount_updown = Column(Float,unique = False,nullable = True)
        dischargable_amount_updown = Column(Float,unique = False,nullable = True)
        remaining_amount_updown = Column(Float,unique = False,nullable = True)
        Batt_Direction = Column(Float,unique = False)
        #エコキュート
        Ecocute_status = Column(String, unique = False,nullable = True)
        Ecocute_mode = Column(String, unique = False,nullable = True)
        Ecocute_heating = Column(String, unique = False,nullable = True)
        Ecocute_participateInEnergyShift = Column(Boolean, unique = False,nullable = True)
        Ecocute_timeToStartHeating = Column(Integer, unique = False, nullable = True)
        Ecocute_numberOfEnergyShift = Column(Integer, unique = False, nullable = True)
        Ecocute_daytimeHeatingShiftTime1 = Column(Integer, unique = False, nullable = True)
        Ecocute_Direction = Column(Integer, unique = False,nullable= True)
        #エアコン
        Aircon_status = Column(String, unique = False,nullable = True)
        Aircon_mode = Column(String, unique = False,nullable = True)
        Aircon_temp = Column(Integer,unique = False,nullable = True)
        #温湿度計
        Thermo_temp = Column(Integer,unique = False,nullable = True)
        Thermo_humid = Column(Float,unique = False,nullable = True)
        Thermo_battery = Column(Float,unique = False,nullable = True)

        def __init__(self,time = None,PV_pre = None,PV_actual = None,kaiden = None,demand_pre=None,
            battery_status=None,SOC=None,chargable_amount=None,dischargable_amount=None,remaining_amount=None,
            SOC_updown=None,chargable_amount_updown=None,dischargable_amount_updown=None,remaining_amount_updown=None,Batt_Direction=None,
            Ecocute_status=None,Ecocute_mode=None,Ecocute_heating=None,Ecocute_participateInEnergyShift=None,Ecocute_timeToStartHeating=None,Ecocute_numberOfEnergyShift=None,Ecocute_daytimeHeatingShiftTime1=None,Ecocute_Direction=None,
            Aircon_status=None,Aircon_mode=None,Aircon_temp=None,
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

    Base.metadata.create_all(bind=engine)#データベースを初期化するイメージ(作られたくらい)

    db = db_session.query(Data).filter(Data.time==date_time).first()#最初の１個だけ取ってくる

    if 'PV_pre' in flag:
        print('updateにて、PV予測値を格納します。')
        db.PV_pre = value_1#直接入れ込んで、
    if 'demand_pre' in flag:
        print('updateにて、demand予測値を格納します')
        db.demand_pre = value_1
    if 'PVactual' in flag:
        print('updateにて、PV発電量を格納します')
        db.PV_actual = value_1
    if 'kaiden' in flag:
        print('updateにて、買電量を格納します')
        db.kaiden = value_2
    if 'Battery' in flag:
        db.battery_status = list_battery[0]
        db.SOC = list_battery[1]
        db.chargable_amount = list_battery[2]
        db.dischargable_amount = list_battery[3]
        db.remaining_amount = list_battery[4]
    if 'B_updown' in flag:
        db.SOC_updown = list_battery_2[0]
        db.chargable_amount_updown = list_battery_2[1]
        db.dischargable_amount_updown = list_battery_2[2]
        db.remaining_amount_updown = list_battery_2[3]
    if 'B_direction' in flag:
        db.Batt_Direction = value_1
    if 'Ecocute' in flag:
        db.Ecocute_status = list_ecocute[0]
        db.Ecocute_mode = list_ecocute[1]
        db.Ecocute_heating = list_ecocute[2]
        db.Ecocute_participateInEnergyShift = list_ecocute[3]
        db.Ecocute_timeToStartHeating = list_ecocute[4]
        db.Ecocute_numberOfEnergyShift = list_ecocute[5]
        db.Ecocute_daytimeHeatingShiftTime1 = list_ecocute[6]
    if 'E_direction' in flag:
        Ecocute_Direction = value_1
    if  'Aircon' in flag:
        print('updateにて、エアコンデータを格納します')
        db.Aircon_status = list_aircon[0]
        db.Aircon_mode = list_aircon[1]
        db.Aircon_temp = list_aircon[2]
    if 'Thermo' in flag:
        db.Thermo_temp = list_thermo[0]
        db.Thermo_humid = list_thermo[1]
        db.Thermo_battery = list_thermo[2]
    else:
        print('flagが不正です',flag)

    db_session.commit()#コミットする

    """
    db = db_session.query(User).all()
    for row in db:
        print(row.id,row.time,row.PV_pre,row.PV_actual,row.kaiden,row.demand_pre,row.battery_status,row.SOC)
    """



#create_database(name,id,datetime(2021,8,12,12,0),9)
#os.chdir(os.path.dirname(os.path.abspath(__file__)))
#一度dbを作るとカラム名を変えるとエラーになる
#csvデータをデータベースへ格納する関数
"""
def read_data():
    df = pd.read_csv('sample2.csv',encoding='shift-JIS')
    for index, _df in df.iterrows():
        tdatetime = datetime.strptime(_df['日時'], '%Y/%m/%d %H:%M')
        row = User(time = tdatetime,battery_status=_df['battery状態'],PV_pre=_df['PV発電量'])
        db_session.add(row)
    db_session.commit()
"""
#read_data()
#Read

#db = db_session.query(User).all()
"""
db = db_session.query(Wine).filter(Wine.hue >1.0).all()#条件抽出
db = db_session.query(Wine).limit(20).all()#
db = db_session.query(Wine).order_by(desc(Wine.hue)).limit(20).all()#降順
"""
#Create
"""
User = User(time=datetime(2016, 1, 31, 10, 20),battery_status='OK',PV_pre=1.0)
#PV_preを入れなければ、Noneになる。
db_session.add(User)
db_session.commit()
"""
"""
#Update
db = db_session.query(User).filter(User.battery_status=='OK').first()#最初の１個だけ取ってくる
db.battery_status = 'KK'#直接入れ込んで、
db_session.commit()#コミットする
"""
"""
#Delete
db_session.query(Wine).filter(Wine.proline==1).delete()
db = db_session.query(Wine).all()
"""

#db = db_session.query(User).limit(20).all()#
"""
db = db_session.query(User).filter(User.battery_status=='KK').all()
for row in db:
    print(row.id,row.time,row.battery_status,row.PV_pre)
"""