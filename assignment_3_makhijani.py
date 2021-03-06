# -*- coding: utf-8 -*-
"""Assignment_3_Makhijani.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iZ4E44PDoqad-Y8uiuE35csT6j1tDlzR
"""

import pandas as pd
from sklearn import preprocessing
from sklearn.cluster import KMeans
import numpy as np
import math
from scipy.stats import skew
from scipy.stats import tvar
from scipy.stats import kurtosis
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from scipy.special import sici
from scipy.stats import median_absolute_deviation
import collections
from past.builtins import xrange
import datetime
from datetime import timedelta
from pandas import DataFrame
from scipy.fftpack import fft, ifft,dct
import pywt
import scipy.stats as stats
from sklearn.metrics import classification_report, accuracy_score, make_scorer

import warnings
warnings.filterwarnings("ignore")

insulin_data1=pd.read_csv('InsulinData.csv',low_memory=False, parse_dates = [['Date', 'Time']])[['Date_Time', 'BWZ Carb Input (grams)']]
cgm_data1=pd.read_csv('CGMData.csv',low_memory=False,parse_dates = [['Date', 'Time']])

def trimData(insulin_data, cgm_data):
    min_insulin_time = min(insulin_data['Date_Time'])
    min_cgm_time = min(cgm_data['Date_Time'])
    min_timestamp = max(min_insulin_time, min_cgm_time)
    max_insulin_time = max(insulin_data['Date_Time'])
    max_cgm_time = max(cgm_data['Date_Time'])
    max_timestamp = min(max_insulin_time, max_cgm_time)
    insulin_trimmed = insulin_data[(insulin_data['Date_Time'] >= min_timestamp)]
    insulin_trimmed = insulin_trimmed.reset_index(drop=True)
    insulin_trimmed = insulin_data[(insulin_data['Date_Time'] <= max_timestamp)]
    insulin_trimmed = insulin_trimmed.reset_index(drop=True)
    cgm_trimmed = cgm_data[(cgm_data['Date_Time'] >= min_timestamp)]
    cgm_trimmed = cgm_trimmed.reset_index(drop=True)
    cgm_trimmed = cgm_data[(cgm_data['Date_Time'] <= max_timestamp)]
    cgm_trimmed = cgm_trimmed.reset_index(drop=True)
    return insulin_trimmed, cgm_trimmed

insulin_data1_trimmed, cgm_data1_trimmed = trimData(insulin_data1, cgm_data1)

Bool_carbinput_data1=pd.notnull(insulin_data1_trimmed['BWZ Carb Input (grams)'])
insuline_data_ext1=insulin_data1_trimmed[Bool_carbinput_data1]
insuline_data_ext1 = insuline_data_ext1[insuline_data_ext1['BWZ Carb Input (grams)'] != 0].sort_values(by=['Date_Time'], ignore_index = True)
insuline_data_ext1 = insuline_data_ext1.reset_index(drop=True)
print(insuline_data_ext1)

insulin_data_carblist= (insuline_data_ext1['BWZ Carb Input (grams)']).tolist()
max_carb_val=max(insulin_data_carblist)
min_carb_val=min(insulin_data_carblist)
bin_size=int(max_carb_val+min_carb_val)//20
bins=range(bin_size)
dict1={}
for i in range(1,len(bins)+1):
  if i ==1:
    dict1[i]=min_carb_val+20
  else:
    dict1[i]=dict1[i-1]+20

print(insulin_data_carblist)
print(dict1)
tot_bins=[]
for i in dict1.keys():
  list_bin=[]
  for val in insulin_data_carblist:
    if val>=dict1[i]-20 and val<dict1[i]:
      list_bin.append(val)
      #print(val,i)
  tot_bins.append(list_bin)  
print(tot_bins)
print(len(tot_bins))

def bin_dec(x):
  list1 = list(dict1.values())
  if x<=list1[0]:
    return 1
  elif x<=list1[1]:
    return 2
  elif x<=list1[2]:
    return 3
  elif x<=list1[3]:
    return 4
  elif x<=list1[4]:
    return 5
  elif x<=list1[5]:
    return 6

def extract_meal_cgm_timestamps(meal_dataframe):
    meal_data = []
    time_val = []
    time_bin = []
    meal_len = len(meal_dataframe)-1
    for row in range(0,meal_len):
        new_time = meal_dataframe.at[row, 'Date_Time'] + timedelta(hours = 2)
        if(new_time > meal_dataframe.at[row+1, 'Date_Time']):
           continue
        else:
             meal_data.append(meal_dataframe.at[row, 'Date_Time'])
             time_bin.append(bin_dec(meal_dataframe.at[row, 'BWZ Carb Input (grams)']))
             time_val.append(meal_dataframe.at[row, 'BWZ Carb Input (grams)'],)
    meal_dataframe_fin = pd.DataFrame(meal_data)
    meal_dataframe_fin['bins'] = time_bin
    meal_dataframe_fin['val'] = time_val
    
    return meal_dataframe_fin

meal_data1 = extract_meal_cgm_timestamps(insuline_data_ext1)
print(meal_data1)

cgm_data1_trimmed['Sensor Glucose (mg/dL)'] = cgm_data1_trimmed['Sensor Glucose (mg/dL)'].interpolate(method = 'linear')

cgm_data1_trimmed = cgm_data1_trimmed[['Date_Time','Sensor Glucose (mg/dL)']]
cgm_data1_trimmed = cgm_data1_trimmed.reindex(index=cgm_data1_trimmed.index[::-1])
cgm_data1_trimmed = cgm_data1_trimmed.reset_index(drop=True)

def meal_cgm_extraction(meal_cgm_dataframe, cgmdata):
    list1 = ['cgm_val'+str(x) for x in range(30)]
    meal_data = pd.DataFrame(columns = list1)
    for id in meal_cgm_dataframe.index:
        dict1 = dict()
        data_sets = cgmdata[cgmdata['Date_Time'] >= meal_cgm_dataframe[0][id]]
        data_set_list = list(cgmdata.loc[data_sets.index[0]-6: data_sets.index[0]+23, 'Sensor Glucose (mg/dL)'].values)
        cgm_list=[]
        for id1, cgm_val in enumerate(data_set_list):
            cgm_list.append(cgm_val)
            for cgm in cgm_list:
              dict1[list1[id1]] = cgm_val
        meal_data = meal_data.append(dict1, ignore_index = True)
    meal_data['bins']=list(meal_cgm_dataframe['bins'])
    return meal_data

cgm_meal1 = meal_cgm_extraction(meal_data1, cgm_data1_trimmed)
meal_cgm_master = cgm_meal1.reset_index(drop=True)
meal_cgm_master_list = meal_cgm_master.values.tolist()
meal_cgm_master

def diff_max_min_cgm(meal_list,row):
  max_cgm_val = max(meal_list[row])
  min_cgm_val = min(meal_list[row])
  result = max_cgm_val - min_cgm_val
  return (result)

difference_list_meal = []
for row in range (len(meal_cgm_master_list)):
  difference = diff_max_min_cgm(meal_cgm_master_list,row)
  difference_list_meal.append(difference)
difference_df_meal = pd.DataFrame(difference_list_meal) 
difference_df_meal

def skew_c(meal_list,row):
  result = skew(meal_list[row])
  return (result)

skew_list_meal = []
for row in range (len(meal_cgm_master_list)):
  skew_val = skew_c(meal_cgm_master_list,row)
  skew_list_meal.append(skew_val)
skew_df_meal = pd.DataFrame(skew_list_meal) 
skew_df_meal

def median_absolute_deviation_c(meal_list,row):
  result = median_absolute_deviation(meal_list[row])
  return (result)

median_absolute_deviation_list_meal = []
for row in range (len(meal_cgm_master_list)):
  median_absolute_deviation_val = median_absolute_deviation_c(meal_cgm_master_list,row)
  median_absolute_deviation_list_meal.append(median_absolute_deviation_val)
median_absolute_deviation_df_meal = pd.DataFrame(median_absolute_deviation_list_meal) 
median_absolute_deviation_df_meal

def tvar_c(meal_list,row):
  result = tvar(meal_list[row])
  return (result)

tvar_list_meal = []
for row in range (len(meal_cgm_master_list)):
  tvar_val = tvar_c(meal_cgm_master_list,row)
  tvar_list_meal.append(tvar_val)
tvar_df_meal = pd.DataFrame(tvar_list_meal) 
tvar_df_meal

def kurtosis_c(meal_list,row):
  result = kurtosis(meal_list[row])
  return (result)

kurtosis_list_meal = []
for row in range (len(meal_cgm_master_list)):
  kurtosis_val = kurtosis_c(meal_cgm_master_list,row)
  kurtosis_list_meal.append(kurtosis_val)
kurtosis_df_meal = pd.DataFrame(kurtosis_list_meal) 
kurtosis_df_meal

def coeff_of_var(meal_data,row):
  mean = np.mean(meal_data[row])
  std_dev = np.std(meal_data[row])
  result = mean/std_dev
  return (result)

coeff_of_var_meal_list = []
for row in range(len(meal_cgm_master_list)):
    coeff_val = coeff_of_var(meal_cgm_master_list,row)
    coeff_of_var_meal_list.append(coeff_val)
coeff_of_var_df_meal = pd.DataFrame(coeff_of_var_meal_list) 
coeff_of_var_df_meal

def discrete_wavelet_trans(meal_data,row):
  (cA,cD) = pywt.dwt(meal_data[row], 'db1')
  cA = cA[::-1][0:8]
  return (cA,cD)

x_meal=[]
for row in range(len(meal_cgm_master_list)):
  x1,y1 = discrete_wavelet_trans(meal_cgm_master_list,row)
  x_meal.append(list(x1))
  discrete_wavelet_df_meal = pd.DataFrame(x_meal)  
discrete_wavelet_df_meal

def windowed_mean(meal_list,row):
  w_size = 5
  window_averages =[]
  i=0
  while i < len(meal_list[row]) - w_size +1: 
    nw_size = meal_list[row][i : i + w_size]
    w_average = sum(nw_size)/w_size
    window_averages.append(w_average)
    i+=w_size
  # print(len(window_averages))
  return (window_averages[1:5]) 

windowed_average_list_meal = []
for row in range (len(meal_cgm_master_list)):
  average_list = windowed_mean(meal_cgm_master_list,row)
  windowed_average_list_meal.append(average_list)
windowed_average_list_df_meal = pd.DataFrame(windowed_average_list_meal)
windowed_average_list_df_meal

def calc_peaks_fouriertrans(meal_list,row):
    fouriertrans = list()
    peak_feat = list()
    arr = np.array(meal_list[row])
    # print(fft(arr))
    fouriertrans.append(abs(fft(arr)))
    for val in range(len(fouriertrans)):
      sets = set(fouriertrans[val])  
      set_list = list(sets)
      set_list.sort()
      set_list = set_list[::-1][0:8]
      # print(set_list)
      peak_feat+=set_list
    # print(peak_feat)
    return (fouriertrans,peak_feat)  


x_meal=[]
y_meal=[]
for row in range(len(meal_cgm_master_list)):
  x1,y1 = calc_peaks_fouriertrans(meal_cgm_master_list,row)
  x_meal.append(x1)
  y_meal.append(list(y1))
# print(len(y_meal))
peak_valdf_meal = pd.DataFrame(y_meal)
peak_valdf_meal

#def rank1(meal_cgm_master_list):
def calc_rank_row(meal_data,row):
  rank = [0 for x in range(len(meal_data[row]))]
  for j in range (len(meal_data[row])):
    (r,s)=(1,1)
    for k in range (len(meal_data[row])):
      if k != j and meal_data[row][k] < meal_data[row][j]:
        r += 1
      if k != j and meal_data[row][k] == meal_data[row][j]:
        s += 1       
    rank[j] = r + (s - 1) / 2
  return (rank) 

rank_list_meal=[]
for row in range(len(meal_cgm_master_list)):
    ranks_list_meal = calc_rank_row(meal_cgm_master_list,row)
    rank_list_meal.append(ranks_list_meal)

ranks_list_df_meal = pd.DataFrame(rank_list_meal)
ranks_list_df_meal = ranks_list_df_meal.iloc[:,:24]
ranks_list_df_meal

def z_score_feat(meal_list,row):
  z_score_arr = np.array(meal_list[row])
  z_score_list = stats.zscore(z_score_arr)
  return (z_score_list)

z_scores_meal=[]
for row in range (len(meal_cgm_master_list)):
  z_score_res_list = z_score_feat(meal_cgm_master_list,row)
  z_scores_meal.append(z_score_res_list)
z_score_res_list_df_meal = pd.DataFrame(z_scores_meal)
z_score_res_list_df_meal = z_score_res_list_df_meal.iloc[:,:24]
z_score_res_list_df_meal

from sklearn.cluster import DBSCAN 
from sklearn.preprocessing import StandardScaler 
from sklearn.preprocessing import normalize 
from sklearn.decomposition import PCA
meal_data = pd.concat([difference_df_meal,coeff_of_var_df_meal,discrete_wavelet_df_meal,windowed_average_list_df_meal,peak_valdf_meal,ranks_list_df_meal,z_score_res_list_df_meal,kurtosis_df_meal,skew_df_meal,tvar_df_meal,median_absolute_deviation_df_meal],axis=1)
dataset = (meal_data.fillna(0)).reset_index().drop(columns = ['index'])
kmeans = KMeans(n_clusters=6)
#model = KMeans(n_clusters=5, init='random', max_iter=100, n_init=1, verbose=1)
cluster = kmeans.fit_predict(dataset)
centroids = kmeans.cluster_centers_
#print(dataset)
kmeans_sse=kmeans.inertia_
print(kmeans_sse)
cluster_list=[]
for i in cluster:
  i+=1
  cluster_list.append(int (i))
dict1=collections.Counter(cluster_list)
print(dict1)
dataset['clusters']=cluster_list
print(dataset)
df=meal_cgm_master['bins'].fillna(1)
ground_truth_list = df.tolist()
gt_bin_list=[]
for i in ground_truth_list:
    i=int (i)
    gt_bin_list.append(i)  
print(gt_bin_list)

from sklearn.metrics import confusion_matrix
y_true = gt_bin_list
y_pred = cluster_list
x=confusion_matrix(y_true, y_pred)
entropy=[]
purity=[]
print(x)
for row in range(len(x)):
  lg_t = np.log((x[row,:]/sum(x[row,:]))/np.log(2))
  ent = sum((-x[row,:]/sum(x[row,:]))*lg_t)
  entropy.append(ent)
  pur = max(x[row,:])/sum(x[row,:])
  purity.append(pur)
print(entropy)
print(purity)
total_x = sum(x,1)
tot_purity1 = 0
tot_entropy_list=[]
tot_entropy1 = 0
for row in range (len(x)):
  sum_s = sum(x[row,:])/sum(total_x) 
  if(not np.isnan(sum_s*entropy[row])):
    # print(sum_s*entropy[row])                
    tot_entropy1 = tot_entropy1 + (sum_s*entropy[row])
  #print(sum_s*entropy[row])
  tot_purity1 = round(tot_purity1 + (sum_s*purity[row]),4)  
print(tot_purity1)  
print(tot_entropy1)

from sklearn.cluster import DBSCAN 
from sklearn.preprocessing import StandardScaler 
from sklearn.preprocessing import normalize 
from sklearn.decomposition import PCA

scaler = StandardScaler() 
dataset_scaled = scaler.fit_transform(dataset.drop(columns = ['clusters'])) 
dataset_normalized = normalize(dataset_scaled)
dataset_normalized = pd.DataFrame(dataset_normalized)
print(dataset_normalized)
pca = PCA(n_components = 7) 
dataset_principal = pca.fit_transform(dataset_normalized) 
dataset_principal = pd.DataFrame(dataset_principal) 
dataset_principal.columns = ['P1', 'P2','P3','P4','P5','P6','P7'] 
#print(dataset_principal.head())
db_clusters = DBSCAN(eps = 0.3999, min_samples =6).fit(dataset_principal) 
db_labels = db_clusters.labels_
dict1=collections.Counter(db_labels)
print(db_labels)
print(dict1)

centroids_list = centroids
print(len(centroids_list[0]))
centroid_dict = {i:centroids_list[i] for i in range(0,len(centroids_list))}
dataset_normalized['dblabels']=db_labels
# dataset_normalized.loc[0,'dblabels']
arr=[]
for idx,row in dataset_normalized.iterrows():
  if row.loc['dblabels']==-1.0:
    
    point = np.array(list(row)[:-1])
    # print(point,len(point))
    distances = []
    for j in centroid_dict:
      distances.append(np.linalg.norm(point-centroid_dict[j]))
    print(distances)
    dataset_normalized.at[idx,'dblabels'] = distances.index(min(distances))

    # df = DataFrame(row)
    # df=df.values.tolist()
    # print(df)
 
print(dataset_normalized)

def dbscan_sse(centroids, meal_data_val):
  cluster_sse = 0
  for row in meal_data_val:
    sse_eachrow = 0
    for i in range(len(row)):
      sse_eachrow = sse_eachrow + math.pow((centroids[i] - row[i]),2)
      cluster_sse = cluster_sse + sse_eachrow 
  return cluster_sse
def dbscan_func_sse(nums, centroids, dataset):
  dbscan_sse_val = 0
  for j in range(0,6):
    meal_data_val= dataset.loc[dataset['dblabels']==j].iloc[:,0:6]
    meal_arr = np.array(meal_data_val)
    dbscan_sse_val += dbscan_sse(centroids[j], meal_arr)
  return dbscan_sse_val
sse_db_scan=dbscan_func_sse(6,centroids,dataset_normalized)
print(sse_db_scan)

dict1=collections.Counter(dataset_normalized['dblabels'])
dict1
list1=(list(dataset_normalized['dblabels']))

db_pred=[]
for i in list1:
  i+=1
  db_pred.append(i)

y_true = gt_bin_list
x=confusion_matrix(y_true, db_pred)
entropy=[]
purity=[]
print(x)
for row in range(len(x)):
  lg_t = np.log((x[row,:]/sum(x[row,:]))/np.log(2))
  ent = sum((-x[row,:]/sum(x[row,:]))*lg_t)
  entropy.append(ent)
  pur = max(x[row,:])/sum(x[row,:])
  purity.append(pur)
total_x = sum(x,1)
tot_purity = 0
tot_entropy_list=[]
tot_entropy = 0
for row in range (len(x)):
  sum_s = sum(x[row,:])/sum(total_x) 
  if(not np.isnan(sum_s*entropy[row])):
    tot_entropy = tot_entropy + (sum_s*entropy[row])
  #print(sum_s*entropy[row])
  tot_purity = round(tot_purity + (sum_s*purity[row]),4)
print(tot_entropy)   
print(tot_purity)

fin_dataframe = DataFrame()
fin_dataframe['SSE for Kmeans']=[kmeans_sse]
fin_dataframe['SSE for dbscan']=[sse_db_scan]
fin_dataframe['Entropy for Kmeans']=[tot_entropy1]
fin_dataframe['Entropy for Dbscan']=[tot_entropy]
fin_dataframe['Purity for Kmeans']=[tot_purity1]
fin_dataframe['Purity for Dbscan']=[tot_purity]
print(fin_dataframe)

fin_dataframe.to_csv('Results.csv', index=False)