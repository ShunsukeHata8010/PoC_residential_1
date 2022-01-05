from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,Float,String,DateTime,Boolean
from sqlalchemy import desc,asc
import pandas as pd
from sqlalchemy.sql.sqltypes import Boolean, String
import mysql.connector
import sqlalchemy


def create_database_for_jepx(power_com,date_time,price):
    #とりあえず、データベースを作ろうとさせて
    try:
        conn = mysql.connector.connect(host='127.0.0.1',user='root',password='@Idemitsu1')
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE '+'JEPX_'+power_com) #これはSQL文
    except mysql.connector.errors.DatabaseError :#すでにあるときにエラー   
        print('すでにデータベースが存在しています')
    finally:#どっちにしろ、add(Create)の作業に進む
        database = 'JEPX_'+power_com
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

        #tableはエクセルでいうシート
        class Data(Base):
            __tablename__ ='Data_30min' #tableの名前の定義
            id = Column(Integer, primary_key = True)  #idを主キーにしておく
            time = Column(DateTime,unique=True)
            price = Column(Float,unique = False)

            def __init__(self,time = None, price = None):
                self.time = time
                self.price = price

        Base.metadata.create_all(bind=engine)#データベースを初期化するイメージ(作られたくらい)

        data_30min = Data(time = date_time,price=price)

        db_session.add(data_30min)
        db_session.commit()


#UPDATE用関数
def update_database_for_jepx(power_com,date_time,price):
    database = 'JEPX_'+power_com
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

    #tableはエクセルでいうシート
    class Data(Base):
        __tablename__ ='Data_30min' #tableの名前の定義
        id = Column(Integer, primary_key = True)  #idを主キーにしておく
        time = Column(DateTime,unique=True)
        price = Column(Float,unique = False)

        def __init__(self,time = None, price = None):
            self.time = time
            self.price = price

    Base.metadata.create_all(bind=engine)#データベースを初期化するイメージ(作られたくらい)

    db = db_session.query(Data).filter(Data.time==date_time).first()#最初の１個だけ取ってくる
    db.price = price

    db_session.commit()#コミットする


#Read用関数
def read_database_jepx(power_com):
    power_com = power_com.replace('北海道','Hokkaido').replace('東北','Tohoku').replace('東京','Tokyo').replace('中部','Chubu').replace('北陸','Hokuriku').replace('関西','Kansai').replace('中国','Chugoku').replace('四国','Shikoku').replace('九州','Kyushu')
    database = 'JEPX_'+power_com
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
        print(power_com,'は、データベースがありません。')
    
    return db_session

Base = declarative_base()
class Data_jepx(Base):
    __tablename__ ='Data_30min' #tableの名前の定義
    id = Column(Integer, primary_key = True)  #idを主キーにしておく
    time = Column(DateTime,unique=True)
    price = Column(Float,unique = False)

    def __init__(self,time = None,price = None):
        self.time = time
        self.price = price

def create_df_jepx(db):
    columns=['日時','価格']
    df = pd.DataFrame()

    for row in db:
        #行だが、結局はDataオブジェクトなので、.で取り出すしかない
        #dataframeなので、nanがいい気がするがNoneのままにしている。(nanとnoneが混在している)
        s = pd.Series([row.time,row.price],index=columns)
        df = df.append(s,ignore_index=True)


    return df


