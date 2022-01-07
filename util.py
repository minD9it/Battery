import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

from dateutil.parser import parse
from datetime import timedelta
from tqdm import tqdm

def make_timedelt(time_str):
    time = time_str.replace("오전", "AM").replace("오후", "PM")
    
    time_split = time.split(" ")
    
    tmp = time_split[1]
    time_split[1] = time_split[2]
    time_split[2] = tmp
    
    tm = parse((" ").join(time_split))
    
    return tm    


def parse_date(time_array):
    date_=[] #replace korean to english

    for i in time_array:
        i = i.replace("오전", "AM")
        i = i.replace("오후", "PM")
        date_.append(i)
    
    date__=[] #split blank

    for i in date_:
        date__.append(i.split(" "))
    
    date___=[] #switch index

    for i in date__: #위치 변경
        tmp = i[1] 
        i[1] = i[2]
        i[2] = tmp
        date___.append(i)

    date=[]

    for i in tqdm(date___):
        #print('parsing: ', i, "=", (" ").join(i))
        dt = parse((" ").join(i)) #list to string
        #print(dt)
        #print()
        date.append(dt)

    date = np.array(date)
        
    return date


def cal_time(time_array):
    time_array = [np.array(time_array)[0], np.array(time_array)[-1]]
    
    date_=[] #replace korean to english

    for i in time_array:
        i = i.replace("오전", "AM")
        i = i.replace("오후", "PM")
        date_.append(i)

    date__=[] #split blank

    for i in date_:
        date__.append(i.split(" "))

    date___=[] #switch index

    for i in date__: #위치 변경
        tmp = i[1] 
        i[1] = i[2]
        i[2] = tmp
        date___.append(i)

    parsing_date=[]

    for i in tqdm(date___):
        #print('parsing: ', i, "=", (" ").join(i))
        dt = parse((" ").join(i)) #list to string
        #print(dt)
        #print()
        parsing_date.append(dt)

    parsing_date = np.array(parsing_date)
    
    time = parsing_date[1] - parsing_date[0]
        
    return time
    
def cal_hour(start_time, end_time):
    s_time = parse_date(start_time)
    e_time = parse_date(end_time)
    
    return (e_time - s_time).hour
    
def cal_capability(mA, time_array):
    start_time = time_array[0]
    end_time = time_array[-1]
    
    s_time = parse_date(start_time)
    e_time = parse_date(end_time)
    
    hour = (e_time - s_time).hour
    
    return mA * hour


def cal_usage(mA, time_array, end_index, dodi_index):
#     time_array = np.array(time_array)
    
    start_time = np.array(time_array)[0]
    end_time = np.array(time_array)[end_index]
    dodi_time = np.array(time_array)[dodi_index]
    
    s_time = make_timedelt(start_time)
    e_time = make_timedelt(end_time)
    d_time = make_timedelt(dodi_time)
    
    total_hour = ((e_time - s_time).days * 24) + ((e_time - s_time).seconds / 3600)
    total_cap = mA * total_hour
    
    dodi_hour = ((d_time - s_time).days * 24) + ((d_time - s_time).seconds / 3600)
    dodi_cap = mA * dodi_hour
    
    return dodi_cap, total_cap, (dodi_cap / total_cap) * 100


def make_result(fileName, array, cal_time):
    f = open(fileName, "w")
    f.write("recovery_time(s),max_rate\n")

    for i in range(int(len(array))):
        f.write(str(cal_time[i]) + ", " + str(cal_time[i]) + "\n")
    
    f.close()
    
def remove_serial_number(serial_arr):
    new_arr = np.array(serial_arr[0])
    
    for index in range(serial_arr.shape[0]-1):
        if serial_arr[index]+1 != serial_arr[index+1]:
            new_arr = np.append(new_arr, serial_arr[index+1])
            
    return new_arr

def remove_serial_number_reversed(serial_arr):
    new_arr = np.array([], dtype=int)
    
    for index in reversed(range(serial_arr.shape[0]-1)):
        if serial_arr[index]+1 != serial_arr[index+1]:
            new_arr = np.append(new_arr, serial_arr[index])
            
    return np.flip(new_arr)

def remove_n(origin_arr, start_index, step_n, data_type=int):
    new_arr = np.array([], dtype=data_type)
    
    for index in range(start_index, len(origin_arr), step_n):
        new_arr = np.append(new_arr, np.array(origin_arr[index]))
        
    return new_arr

def adjust_index(voltage_serial, current_serial, origin_arr):
    tmp_arr = origin_arr - 1    
    ref_arr = np.array([], dtype=int)
    
    for t in tqdm(tmp_arr):
        tmp = t  #tmp는 >0.020 이전의 전압 인덱스
    
        for i in range(1, 5): #4번 loop
            #전압(+): t < t-1
            if (voltage_serial[tmp] < voltage_serial[t-i]):
                #t-1 > t-2 => 인덱스 변경: t-i
                if voltage_serial[t-i] >= voltage_serial[t-i-1]: #이전 이전의 전압이 더 작으면
                    tmp = t-i
                    break
                else:
                    tmp = t- i
            #전압 (-), 전류 (+) => 인덱스 변경: t-i
            elif (voltage_serial[tmp] > voltage_serial[t-i]) and (current_serial[tmp] < current_serial[t-i]) and (current_serial[tmp] != 0.0000) and (current_serial[t-i] > 0.020):
                tmp = t-i
            #전압(-) => 인덱스 유지
            elif voltage_serial[tmp] > voltage_serial[t-i]:
                break
            #전압이 같음: t == t-1
            elif voltage_serial[tmp] == voltage_serial[t-i]:
                #t-1 < t-2 => 인덱스 변경: t-i-1
                if voltage_serial[t-i] < voltage_serial[t-i-1]:
                    tmp = t-i-1
                    break
            
        ref_arr = np.append(ref_arr, tmp)
            
    ref_arr = np.unique(ref_arr) #중복 값 제거
    
    return ref_arr


def voltage_change_rate_cc_anal(data_arr, first_index, last_index):
    ref_volt = data_arr['Voltage(V)'][0] #최고 전압이 기준 전압
    rate_arr = np.array([])
    volt_arr = np.array([])
    
    for i in tqdm(range(first_index, last_index)):
        rate_c = (ref_volt - data_arr['Voltage(V)'][i]) / ref_volt * 100
        rate_arr = np.append(rate_arr, np.array([rate_c]))
        volt_arr = np.append(volt_arr, np.array([data_arr['Voltage(V)'][i]]))
            
    return np.max(rate_arr), np.argmax(rate_arr)+first_index