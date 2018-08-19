import json
import pandas as pd
import re
import glob
import os
import numpy as np
import tzlocal
from datetime import datetime
from pandas.io.json import json_normalize
from IPython.display import display, HTML

def readFiles():
    all_files = []
    for file_name in glob.glob("./data/*"):
            f = open(file_name, 'r')
            all_files.append(f.readlines())
            f.close()
    return all_files

def sparseJSON(all_files):
    json_sensors = []
    for index, element in enumerate(all_files):
        match_obj = re.findall(r"(\{\"sensors\":[\s\[\]\w\"\-:,\.\/]*\{[\s\[\]\w\"\-:,\.\/]*\}[\s\[\]\w\"\-:,\.\/]*"
                           r"\{[\s\[\]\w\"\-:,\.\/]*\{[\s\[\]\w\"\-:,\.\/]*\{[\s\[\]\w\"\-:,\.\/]*\}[\s\[\]\w\"\-:,\.\/]"
                           r"*\}\}\})", element[0], re.M)
        for obj in match_obj:
            json_sensors.append(json.loads(obj))
    return(json_sensors)

def getTime(timestamp):

    unix_timestamp = float(timestamp)
    local_timezone = tzlocal.get_localzone()  # get pytz timezone
    local_time = datetime.fromtimestamp(unix_timestamp, local_timezone)
    # Existing types to display time
    # ("%Y-%m-%d %H:%M:%S.%f%z (%Z)"))
    # ("%B %d %Y"))
    return(local_time.strftime("%Y-%m-%d %H:%M:%S"))


def processDataFrame(json_sensors):
    df = pd.DataFrame.from_dict(json_normalize(json_sensors), orient='columns')
    df.columns = ['message_destination', 'message_payload_rssi', 'message_payload_suData_bat',
                  'message_payload_suData_sensor_config', 'message_payload_suData_temp', 'message_payload_suID',
                  'receiverid', 'request_responseTime', 'request_status', 'sensors', 'timestamp']
    df['sensors'] = df['sensors'].astype('str')
    for i in range(len(df.sensors)):
        df.at[i, 'sensors'] = df.at[i, 'sensors'][2:-2]
    return(df)

def printStats(df):
    floats = df.select_dtypes(include='float64')
    objects = df.select_dtypes(include='object')
    print("\nStatistics of the columns:\n")
    for col_name in floats.columns.tolist():
        print(df[col_name].describe())
    print("\nUnique values of the columns:\n")
    for col_name in objects.columns.tolist():
        un = df[col_name].unique()
        print(len(un), un)




def differenceTime(diff_timestamp):
    date_format = "%Y-%m-%d %H:%M:%S"                               # (%Z)"
    a = datetime.strptime('1970-01-01 01:00:00', date_format)      # (CET)', date_format)
    b = datetime.strptime(getTime(diff_timestamp), date_format)
    delta = b - a
    return(delta)


def changeDifferenceInTime(df, stringFrom, stringTo):
    df[stringTo] =  df[stringFrom].astype('str')
    for i in range(len(df[stringTo])):
        df.at[i, stringTo] = differenceTime(df.at[i, stringTo])
    return df

def changeTimestamp(df, stringFrom, stringTo):
    df[stringTo] =  df[stringFrom].astype('str')
    for i in range(len(df[stringTo])):
        df.at[i, stringTo] = getTime(df.at[i, stringTo])
    return df

def findTimeDifferenceDataFrame(df):
    # we are changing here df as well
    df['diff'] = df.groupby(by=['sensors', 'receiverid'])['timestamp'].transform(lambda x: x.max() - x.min())
    select_diff = df[['sensors', 'receiverid', 'message_payload_rssi', 'timestamp', 'time_std', 'diff']]
    return select_diff

def minMaxTimeDataFrame(df):
    #print("_______________________________________________________________________\n")
    #print("Min and max time when every sensor's message was received by a receiver")
    #print("_______________________________________________________________________")
    select_diff = findTimeDifferenceDataFrame(df)
    timestamps_df = select_diff.groupby(['sensors', 'receiverid']).agg(
        {'timestamp': [np.min, np.max]}).reset_index()
    dict_timestamps = {'sensors': timestamps_df.sensors,
                       'receiverid': timestamps_df.receiverid,
                       'timestamp_min': timestamps_df['timestamp'].amin,
                       'timestamp_max': timestamps_df['timestamp'].amax}

    new_timestamps = pd.DataFrame(data=dict_timestamps)
    new_timestamps = changeTimestamp(new_timestamps, 'timestamp_min', 'time_std_min')
    new_timestamps = changeTimestamp(new_timestamps, 'timestamp_max', 'time_std_max')

    return(new_timestamps)
def rssiDataFrame(df):
    #print("_______________________________________________________________________\n")
    #print("\t\tMain RSSI table")
    #print("_______________________________________________________________________")
    select_diff = findTimeDifferenceDataFrame(df)
    result_df = select_diff.groupby(['sensors', 'receiverid']).agg(
        {'message_payload_rssi': [np.min, np.max, np.median], 'diff': np.max,
         'timestamp': [np.min, np.max]}).reset_index()
    my_dict_result = {'sensors': result_df.sensors,
                      'receiverid': result_df.receiverid,
                      'message_payload_rssi_min': result_df.message_payload_rssi.amin,
                      'message_payload_rssi_max': result_df.message_payload_rssi.amax,
                      'message_payload_rssi_median': result_df.message_payload_rssi['median'],
                      'diff': result_df['diff'].amax,
                      'timestamp_min': result_df['timestamp'].amin,
                      'timestamp_max': result_df['timestamp'].amax}
    df_result = pd.DataFrame(data=my_dict_result)
    df_result = changeTimestamp(df_result, 'timestamp_min', 'time_std_min')
    df_result = changeTimestamp(df_result, 'timestamp_max', 'time_std_max')
    df_result = changeDifferenceInTime(df_result, 'diff', 'time_diff')

    return df_result

def getFullTable():
    all_files = readFiles()
    json_sensors = sparseJSON(all_files)
    df = processDataFrame(json_sensors)
    df = changeTimestamp(df, 'timestamp', 'time_std')
    return df

def getRSSITable():

    all_files = readFiles()
    json_sensors = sparseJSON(all_files)
    df = processDataFrame(json_sensors)
    df = changeTimestamp(df, 'timestamp', 'time_std')
    df_rssi = rssiDataFrame(df)
    return(df_rssi)

def rssiMinMaxToString(df, sensor_name):
    df_small = df[df['sensors'] == sensor_name].reset_index()
    names = []
    for i in range(len(df_small)):
        string = 'rssi: [ ' + str(df_small['message_payload_rssi_min'][i]) + ' ..' + str(df_small['message_payload_rssi_max'][i])+' ]'
        names.append(string)
    return names
