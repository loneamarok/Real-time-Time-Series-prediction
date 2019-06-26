#Application to accept router name as input and continously collect data and make predictions

#inputs
router_connection_name="telnet 7.28.93.1"
lag=5

import pymongo
import numpy as np
import pandas as pd
import time
import pexpect
import re
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dateutil import parser
from timeloop import Timeloop
from datetime import timedelta



class router:
    
    def connect (self, router_connection_name):                     #COnnect to the device and return the child process created
        child = pexpect.spawn ("ssh srirrao@vayu-auto-lnx")
        child.expect ('password:')
        child.sendline ("11Srir@m11")
        child.expect('Kickstarted')
        #print("ssh done")
        child.sendline (router_connection_name)
        child.expect('User Access Verification')
        #print("Telnet done")
        child.sendline("lab")
        child.expect('Password:')
        #print("Telnet password")
        child.sendline("lab")
        child.expect(">")
        #print("Telnet done")
        child.sendline("en")  
        child.expect("Password: ")
        #print("Enable password request")
        child.sendline("lab")
        child.expect("#")
        #print(child.before)
        #child.sendline("terminal length 0")
        return child 
        #
        #
        #
    
    def start_cpu_data_collection (self, child, database_name, collection_name, ins_upd):  #Starts data collection from child process and store it in mongo db
        f=open("cpu_pexpect.txt","w")
        child.sendline("sh proce cpu plat hist 1min")
        
        child.expect("1 minutes ago, CPU utilization: [0-9]+%")
        #print(child.after)
        f.write(child.after)
        f.close()
        
        #print("data collecting")
        
        now = datetime.datetime.now().replace(second=0, microsecond=0) - datetime.timedelta(minutes=1) #time stamp of detected cpu usage
        next_minute = now + datetime.timedelta(minutes=1)
        
        f=open("cpu_pexpect.txt","r")
        a=f.read()
        f.close()
        x=re.findall("[0-9]+",a)
        #print x
        #a=np.array(x)
        #cpu=a.reshape(255,2)
        #print(cpu.shape)
        #print cpu
        #df=pd.DataFrame(data=cpu[0:,1:], index=cpu[0:,0], columns=cpu[0,1:]) 
        #df.columns=["cpu"]
        #df.to_csv("cpu_pexcept_csv.csv")        
        #
        #
        cpu_dict = {}
        cpu_list = []
        cpu_dict["_id"] = now
        cpu_dict["cpu"] = x[1]
        cpu_list.append(cpu_dict.copy())
        print(cpu_list)    
        #print cpu_list
        cpu_db = db()
        mongo_client = cpu_db.connect_to_mongo()
        if(ins_upd==1):
            cpu_db.insert_into_collection(mongo_client, database_name, collection_name, cpu_list)
        else:
            db_temp=mongo_client[database_name]
            col_temp=db_temp[collection_name]
            col_temp.update({"_id":now},{"$set":{"cpu":x[1]}})
        #print(x)
        #
        return True
    
    def stop_cpu_data_collection (self, child):               #Stops the process of data collection
        #
        #
        #
        return True
    
class db:
    
    def connect_to_mongo (self):        #Connects to local mongo database
        mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        return (mongo_client)
    
    def create_database (self, mongo_client, database_name):
        if (database_name in mongo_client.list_database_names()):
            print ("Error : Database exists!")
            return None
        database = mongo_client[database_name]
        return database
            
    def delete_database (self, mongo_client, database_name):
        if (not(database_name in mongo_client.list_database_names())):
            print ("Error : Database doest not exist!")
            return None
        mongo_client.drop_database(database_name)
        print ("Log : Database " + database_name + " deleted")
        return True
    
    def create_collection (self, mongo_client, database_name, collection_name):
        if (not(database_name in mongo_client.list_database_names())):
            print ("Error : Database doest not exist!")
            return None
        database = mongo_client[database_name]
        if (collection_name in database.list_collection_names()):
            print ("Error : Collection already exists!")
            return None            
        collection = database[collection_name]
        return True;      
    
    def delete_collection (self, mongo_client, database_name, collection_name):
        if (not(database_name in mongo_client.list_database_names())):
            print ("Error : Database doest not exist!")
            return None
        database = mongo_client[database_name]
        if (not(collection_name in database.list_collection_names())):
            print ("Error : Collection does not exist!")
            return None            
        database.drop_collection(collection_name)
        return True;        
    
    def insert_into_collection (self, mongo_client, database_name, collection_name, values_dict):
        #if (not(database_name in mongo_client.list_database_names())):
            #print ("Error : Database doest not exist!")
            #return None
        database = mongo_client[database_name]
        #if (not(collection_name in database.list_collection_names())):
            #print ("Error : Collection does not exist!")
            #return None            
        collection = database[collection_name]
        x = collection.insert_many(values_dict)
        return x.inserted_ids        
    
    def empty_collection (self, mongo_client, database_name, collection_name):
        if (not(database_name in mongo_client.list_database_names())):
            print ("Error : Database doest not exist!")
            return None
        database = mongo_client[database_name]
        if (not(collection_name in database.list_collection_names())):
            print ("Error : Collection does not exist!")
            return None            
        collection = database[collection_name]
        x = collection.delete_many({})
        return x.deleted_ids
    
    def last_n_data(self, mongo_client, database_name, collection_name, n):
        if (not(database_name in mongo_client.list_database_names())):
            print ("Error : Database doest not exist!")
            return None
        database = mongo_client[database_name]
        if (not(collection_name in database.list_collection_names())):
            print ("Error : Collection does not exist!")
            return None            
        collection = database[collection_name]
        cursor = collection.find({"$query": {}, "$orderby": {"$natural" : -1}}).limit(n)
        return cursor
        
class cpu:
    
    def start_data_collection(self, router_name, database_name, collection_name, ins_upd):   # starts data collection
            data_collection_router = router()
            child=data_collection_router.connect(router_name)
            data_collection_router.start_cpu_data_collection(child, database_name, collection_name)
        
    def train_lstm_model(self, training_data, epochs, batch_size, lag):
        m_train = training_data.shape[0]
        training_processed = training_data.iloc[:, 1:2].values 
        print(training_processed.shape)
 
        scaler = MinMaxScaler(feature_range = (0, 1))
        training_scaled = scaler.fit_transform(training_processed)  

        features_set = []  
        labels = []  
        for i in range(lag, m_train):  
            features_set.append(training_scaled[i-lag:i, 0])
            labels.append(training_scaled[i, 0])

        features_set, labels = np.array(features_set), np.array(labels) 
        features_set = np.reshape(features_set, (features_set.shape[0], features_set.shape[1], 1)) 

        model = Sequential()  
        model.add(LSTM(units=4, return_sequences=True, input_shape=(features_set.shape[1], 1))) 
        model.add(Dropout(0.2)) 

        model.add(LSTM(units=4, return_sequences=True))  
        model.add(Dropout(0.2))

        model.add(LSTM(units=4, return_sequences=True))  
        model.add(Dropout(0.2))

        model.add(LSTM(units=4))  
        model.add(Dropout(0.2)) 

        model.add(Dense(units = 1)) 

        model.compile(optimizer = 'adam', loss = 'mean_squared_error')  
        model.fit(features_set, labels, epochs = epochs, batch_size = batch_size) 
        return model
    
    def train_initial(self, epochs, batch_size, lag):   # Trains data available till now
        db_lstm=db()
        mongo_client=db_lstm.connect_to_mongo()
        cursor=db_lstm.read_from_collection(mongo_client, "cpu_database", "customers")
        m_train=db_lstm.collection_count(mongo_client, "cpu_database", "customers")
        
        cpu_training_complete_temp=list(cursor)
    
        cpu_training_complete=pd.DataFrame(cpu_training_complete_temp[0:m_train])
    
        model = train_lstm_model()
        return model
    
    def train_update(self, from_datetime, lag):    # Trains and predict for intervals of 1 second
        mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        database = mongo_client["cpu_database_test"]       
        collection = database["customers_test"]
        dt = from_datetime # put real time date-time
        #dt = parser.parse("2019-06-25T09:47:00Z")
        cursor = collection.find({"_id" : {"$gt":dt - datetime.timedelta(minutes=60)}})
        
        cpu_training_complete_temp=list(cursor)
        m_train = len(cpu_training_complete_temp)
        print(m_train)
        
        cpu_training_complete=pd.DataFrame(cpu_training_complete_temp[0:m_train])
        if(m_train>0):
            now=cpu_training_complete_temp[m_train-1]["_id"]
            next_datetime = now + datetime.timedelta(minutes=1)
        
            if(m_train > lag):
                model = self.train_lstm_model(cpu_training_complete, 10, 10, lag)
                cpu_predict_data = cpu_training_complete[m_train-lag:m_train]
                predict_processed = cpu_predict_data.iloc[:, 1:2].values
                scaler = MinMaxScaler(feature_range = (0, 1))
                predict_scaled = scaler.fit_transform(predict_processed)  
                test_features = np.array(predict_scaled)  
                test_features = np.reshape(test_features, (1, lag, 1)) 
                print(test_features.shape)
                print(test_features)
            
                predictions = model.predict(test_features)
                predictions = scaler.inverse_transform(predictions)
                print(predictions)
            
                return model
            else:
                print("Need at least "+str(lag)+" datapoints for training, Have only "+str(m_train)+", Please wait for some time")
        else:
            print("No data in database, Please Wait")
        #return cursor
        

  #  def if_new_data():     # To check and run train_update only if new data is available
        
    
    
def collect_and_store(router_name, model):
    mydb=db()
    test_cpu=cpu()
    database_name = router_name.replace(".","_")
    collection_name = "cpu"
    mongo_client=mydb.connect_to_mongo()
    
    now = datetime.datetime.now().replace(second=0, microsecond=0) - datetime.timedelta(minutes=1)
    database = mongo_client[database_name]
    collection = database[collection_name]
    #mydb.insert_into_collection(mongo_client, database_name, collection_name, [{"_id":now, "cpu":15}])
    
    
    dt = now # put real time date-time
    #dt = parser.parse("2019-06-25T09:47:00Z")
    cursor = collection.find({"_id" : {"$gt":dt - datetime.timedelta(minutes=60)}})
        
    cpu_training_complete_temp=list(cursor)
    m_train = len(cpu_training_complete_temp)
    print(m_train)
        
    cpu_training_complete=pd.DataFrame(cpu_training_complete_temp[0:m_train])
    if(m_train>0):
        now_datetime=cpu_training_complete_temp[m_train-1]["_id"]
        next_datetime = now + datetime.timedelta(minutes=1)
        
        if(m_train > lag):
            model = test_cpu.train_lstm_model(cpu_training_complete, 10, 10, lag)
            predict_processed = cpu_training_complete.iloc[:, 1:2].values
            
            test_features = []  
            for i in range(m_train-lag, m_train):  
                test_features.append(predict_processed[i])
                
            scaler = MinMaxScaler(feature_range = (0, 1))
            test_features = scaler.fit_transform(test_features)  
            test_features = np.array(test_features)  
            test_features = np.reshape(test_features, (1, lag, 1)) 
            print(test_features.shape)
            print(test_features)
            
            predictions = model.predict(test_features)
            predictions = scaler.inverse_transform(predictions)
            predictions = float(predictions[0,0])
            print(predictions)
            print(router_name)
            
            mydb.insert_into_collection(mongo_client, database_name, collection_name, [{"_id":next_datetime, "pred_cpu":predictions}])
            #test_cpu.start_data_collection("telnet "+str(router_name), database_name, collection_name, 0) #Update
            collection.update({"_id":now},{"$set":{"cpu":15}})
            return model
        
        else:
            #test_cpu.start_data_collection("telnet "+str(router_name), database_name, collection_name, 1) #insert
            collection.insert_many([{"_id":now, "cpu":15}])
            print("Need at least "+str(lag)+" datapoints for training, Have only "+str(m_train)+", Please wait for some time")
    else:
        mydb.insert_into_collection(mongo_client, database_name, collection_name, [{"_id":now, "cpu":15}])
        #test_cpu.start_data_collection("telnet "+str(router_name), database_name, collection_name, 1) #insert    
        print("No data in database, Please Wait")
    

def main():
    lag=5
    router_name="7.23.98.1"

    model = Sequential()  
    model.add(LSTM(units=4, return_sequences=True, input_shape=(lag, 1))) 
    model.add(Dropout(0.2)) 

    model.add(LSTM(units=4, return_sequences=True))  
    model.add(Dropout(0.2))

    model.add(LSTM(units=4, return_sequences=True))  
    model.add(Dropout(0.2))

    model.add(LSTM(units=4))  
    model.add(Dropout(0.2)) 

    model.add(Dense(units = 1)) 

    model.compile(optimizer = 'adam', loss = 'mean_squared_error') 
    #scheduler = BlockingScheduler()
    #scheduler.add_job(collect_and_store, 'interval', minutes=1)
    #scheduler.start()
    
    while(1):
        model = collect_and_store(router_name, model)
        time.sleep(60)
    
    #now = datetime.datetime.now().replace(second=0, microsecond=0) - datetime.timedelta(minutes=1)
    #cpu_obj=cpu()
    #model=cpu_obj.train_update(now,5)
    
    #tl = Timeloop()

    #@tl.job(interval=timedelta(seconds=60))
    #def sample_job_every_60s():
    #    collect_and_store()
        
    #tl.start(block=True)


    
if __name__== "__main__":
    main()
