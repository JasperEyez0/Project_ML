# -*- coding: utf-8 -*-
"""Predict_Health_Outcomes_of_Horses.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mJVqGxbjURGscpOu0kgE_boBmzoR-mKX
"""

!pip install catboost

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import joblib

import warnings

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import f1_score, accuracy_score

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import catboost as cb

from sklearn.model_selection import GridSearchCV

train = pd.read_csv('/content/train.csv', index_col = "id")
test = pd.read_csv('/content/test.csv', index_col = "id")

train

train.dtypes

label = LabelEncoder()

train_rows = train.shape[0]
merged_df = pd.concat([train, test])

tmp_ext = {"None": -1, "warm": 1, "normal": 0, "cool": 2, "cold": 3}
per_purse = {"None": -1, "absent": 1, "reduced": 2, "normal": 0, "increased": 3}
cap_ref = {"None": -1, "less_3_sec": 1, "3": 2, "more_3_sec": 3}
pn = {"depressed": 1, "mild_pain": 2, "severe_pain": 3, "extreme_pain": 4, "alert": 5}
prtls = {"None": -1, "absent": 1, "hypomotile": 2, "normal": 0, "hypermotile": 3}
abd_dis = {"None": -1, "none": 0, "slight": 1, "moderate": 2, "severe": 3}
nag_tube = {"None": -1, "none": 0, "slight": 1, "significant": 2}
nag_flux = {"None": -1, "none": 0, "slight": 1, "less_1_liter": 2, "more_1_liter": 3}
rec_ex = {"None": -1, "absent": 1, "decreased": 2, "normal": 0, "increased": 3}
abd = {"None": -1, "firm": 1, "distend_small": 2, "normal": 0, "distend_large": 3}
abd_app = {"None": -1, "clear": 0, "cloudy": 1, "serosanguious": 2}

for col in ["surgery", "age", "mucous_membrane", "surgical_lesion", "cp_data", "outcome"]:
    merged_df[col] = label.fit_transform(merged_df[col])

merged_df["temp_of_extremities"] = merged_df["temp_of_extremities"].map(tmp_ext)
merged_df["peripheral_pulse"] = merged_df["peripheral_pulse"].map(per_purse)
merged_df["capillary_refill_time"] = merged_df["capillary_refill_time"].map(cap_ref)
merged_df["pain"] = merged_df["pain"].map(pn)
merged_df["peristalsis"] = merged_df["peristalsis"].map(prtls)
merged_df["abdominal_distention"] = merged_df["abdominal_distention"].map(abd_dis)
merged_df["nasogastric_tube"] = merged_df["nasogastric_tube"].map(nag_tube)
merged_df["nasogastric_reflux"] = merged_df["nasogastric_reflux"].map(nag_flux)
merged_df["rectal_exam_feces"] = merged_df["rectal_exam_feces"].map(rec_ex)
merged_df["abdomen"] = merged_df["abdomen"].map(abd)
merged_df["abdomo_appearance"] = merged_df["abdomo_appearance"].map(abd_app)

train = merged_df.iloc[:train_rows]
test = merged_df.iloc[train_rows:].drop(columns = 'outcome')

for df in [train, test]:
    df.drop(columns = ["hospital_number"], inplace=True)
    df.fillna(method = "ffill", inplace = True)

df

missing_perc_df = pd.DataFrame(index = ['train_dataframe', 'test_dataframe'], columns = test.columns)

for i, col in enumerate(test.columns):
    missing_perc_df.loc[missing_perc_df.index == 'train_dataframe', col] = np.round(train.isna().sum()[i] / train[col].shape * 100, 3)
    missing_perc_df.loc[missing_perc_df.index == 'test_dataframe', col] = np.round(test.isna().sum()[i] / test[col].shape * 100, 3)

for col in test.columns:
    missing_perc_df[col] = missing_perc_df[col].astype(str) + '%'

missing_perc_df

X = train.iloc[:, :-1]
y = train.iloc[:, -1]

N_SPLITS = 5
kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

models = {
    'logistic_regressor': LogisticRegression(random_state=42, max_iter = 1000),
    'randomforest_classifier': RandomForestClassifier(random_state=42, verbose = 0),
    'xgb_classifier': xgb.XGBClassifier(random_state=42, verbosity = 0),
    'catboost_classifier': cb.CatBoostClassifier(random_state = 42, logging_level="Silent")
}

for model_name, model in models.items():
    f1_scores = cross_val_score(model, X, y, cv=kf, scoring='f1_micro')
    avg_f1_score = f1_scores.mean()
    print(f'{model_name}\'s average F1 score across {N_SPLITS}-Fold CV is {avg_f1_score * 100:.3f}%')

model = xgb.XGBClassifier(n_estimators = 100,max_depth = 3, learning_rate = 0.5)
model.fit(X, y)

scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
mean_accuracy = scores.mean()
print(f"accuracy: {mean_accuracy * 100:.3f}%")

xgb_model = xgb.XGBClassifier(random_state=42, verbosity=0)

param = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 4, 5],
    'learning_rate': [0.01, 0.1, 0.2],
    'min_child_weight': [1, 2, 3]
}

grid_search = GridSearchCV(xgb_model, param, cv=kf, scoring='f1_micro')

grid_search.fit(X, y)

best_params = grid_search.best_params_
best_score = grid_search.best_score_
print(f'Best Hyperparameters: {best_params}')
print(f'Best F1 Score: {best_score * 100:.3f}%')

model = xgb.XGBClassifier(random_state = 42, verbosity = 0, n_estimators = 100,
                          min_child_weight = 2, max_depth = 3, learning_rate = 0.1)
model.fit(X, y)

status = {0: 'died', 1: 'euthanized', 2: 'lived'}
submission = pd.DataFrame({'id': test.index, 'outcome': model.predict(test).astype(int)
})
submission['outcome'] = submission['outcome'].map(status)
submission.to_csv('submission.csv', index=False)

!pip install -q streamlit

!npm install -g localtunnel

import pickle

with open('model.pkl', 'wb') as file:
    pickle.dump(model, file)

# Commented out IPython magic to ensure Python compatibility.
# %%writefile app.py
# 
# import streamlit as st
# import pickle
# import pandas as pd
# 
# def user_input_features():
#   surgery = st.sidebar.slider('surgery', 0, 1)
#   age = st.sidebar.slider('age', 0, 1)
#   rectal_temp = st.sidebar.slider('rectal_temp', 35.4, 40.8, 0.1)
#   pulse = st.sidebar.slider('pulse', 30.0, 184.0, 1.0)
#   respiratory_rate = st.sidebar.slider('respiratory_rate', 8.0, 96.0, 1.0)
#   temp_of_extremities = st.sidebar.slider('temp_of_extremities', -1, 3, 1)
#   peripheral_pulse = st.sidebar.slider('peripheral_pulse', -1, 3, 1)
#   mucous_membrane = st.sidebar.slider('mucous_membrane', 0, 6, 1)
#   capillary_refill_time = st.sidebar.slider('capillary_refill_time', -1, 3, 1)
#   pain = st.sidebar.slider('pain', -1.0, 5.0, 1.0)
#   peristalsis = st.sidebar.slider('peristalsis', -1.0, 3.0, 1.0)
#   abdominal_distention = st.sidebar.slider('abdominal_distention', -1, 3, 1)
#   nasogastric_tube = st.sidebar.slider('nasogastric_tube', -1, 2, 1)
#   nasogastric_reflux = st.sidebar.slider('nasogastric_reflux', -1, 3, 1)
#   nasogastric_reflux_ph = st.sidebar.slider('nasogastric_reflux_ph', 1.0, 7.5, 0.1)
#   rectal_exam_feces = st.sidebar.slider('rectal_exam_feces', -1.0, 3.0, 1.0)
#   abdomen = st.sidebar.slider('abdomen', -1.0, 3.0, 1.0)
#   packed_cell_volume = st.sidebar.slider('packed_cell_volume', 23.0, 75.0, 0.1)
#   total_protein = st.sidebar.slider('total_protein', 3.9, 89.0, 0.1)
#   abdomo_appearance = st.sidebar.slider('abdomo_appearance', -1, 2, 1)
#   abdomo_protein = st.sidebar.slider('abdomo_protein', 0.1, 10.1, 0.1)
#   surgical_lesion = st.sidebar.slider('surgical_lesion', 0, 1)
#   lesion_1 = st.sidebar.slider('lesion_1', 0, 31110, 1)
#   lesion_2 = st.sidebar.slider('lesion_2', 0, 4300, 1)
#   lesion_3 = 0
#   cp_data = st.sidebar.slider('cp_data', 0, 1)
# 
# 
#   user_input_data = {'surgery': surgery,
#                'age': age,
#                'rectal_temp': rectal_temp,
#                'pulse': pulse,
#                'respiratory_rate': respiratory_rate,
#                'temp_of_extremities': temp_of_extremities,
#                'peripheral_pulse': peripheral_pulse,
#                'mucous_membrane': mucous_membrane,
#                'capillary_refill_time': capillary_refill_time,
#                'pain': pain,
#                'peristalsis': peristalsis,
#                'abdominal_distention': abdominal_distention,
#                'nasogastric_tube': nasogastric_tube,
#                'nasogastric_reflux': nasogastric_reflux,
#                'nasogastric_reflux_ph': nasogastric_reflux_ph,
#                'rectal_exam_feces': rectal_exam_feces,
#                'abdomen': abdomen,
#                'packed_cell_volume': packed_cell_volume,
#                'total_protein': total_protein,
#                'abdomo_appearance': abdomo_appearance,
#                'abdomo_protein': abdomo_protein,
#                'surgical_lesion': surgical_lesion,
#                'lesion_1': lesion_1,
#                'lesion_2': lesion_2,
#                'lesion_3': lesion_3,
#                'cp_data': cp_data}
# 
# 
#   features = pd.DataFrame(user_input_data, index=['0'])     ## create dataframe for user's inputs'
#   return features
# 
# with open('model.pkl', 'rb') as file:                       ## load pickle model
#    model = pickle.load(file)
# 
# labels = ['died', 'euthanized' , 'lived']
# 
# st.write('''Predict Health Outcomes of Horses''')
# st.sidebar.header('User Input Parameters')
# 
# df = user_input_features()                   ##  read input from user
# 
# st.subheader('User Input Parameters')
# st.write(df)
# 
# prediction = model.predict(df)
# prediction_probabilities = model.predict_proba(df)
# 
# st.subheader('Prediction')
# st.write(labels[prediction[0]])
# 
# st.subheader('Class labels and their corresponding index number')
# st.write(labels)
# 
# st.subheader('Prediction Probability')
# st.write(prediction_probabilities)

!streamlit run /content/app.py & npx localtunnel --port 8501