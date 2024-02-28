import numpy as np
import matplotlib.pyplot as plt
import csv
import time
import os
from utils import *
import pandas as pd
import pingouin as pg


column_names = ['id', 'condition', 'username', 'robot_teaching', 'user_learning', 'age', 'gender', 'ethnicity', 'education', 'robot']
robot_teaching = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
user_learning = ["Strongly Disagree","Disagree","Neutral","Agree","Strongly Agree"]
age = ["18-24","25-34","35-44","45-54","55-64", "65-74","75-84","85 or older"]
gender =  ["Male","Female","Other"]
education = ["Less than high school degree","High school graduate (high school diploma or equivalent including GED)","Some college but no degree","Associate degree in college (2-year)","Bachelor’s degree in college (4-year)","Master’s degree","Doctoral degree","Professional degree (JD, MD)"]
ethnicity = ["White","Black or African American","American Indian or Alaska Native","Asian","Native Hawaiian or Pacific Islander","Other"]
robot = ["Not at all","Slightly","Moderately","Very","Extremely"]
trial_column_names = []
for trial_num in range(1,11):
    trial_column_names.append('trial-'+str(trial_num))

user = {}
for col in column_names:
    user[col] = []
for col in trial_column_names:
    user[col] = []


#For each user.csv, do this
with open('result/user.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    created_time = time.gmtime(os.path.getctime('result/user.csv'))

    for row in reader:
        id = get_user_index(row['id'], created_time)
        user['id'].append(id)
        for col in column_names[1:]:
            if col == 'robot_teaching':
                user[col].append(robot_teaching[int(row[col])])
            elif col == 'user_learning':
                user[col].append(user_learning[int(row[col])])
            elif col == 'age':
                user[col].append(age[int(row[col])])
            elif col == 'gender':
                user[col].append(gender[int(row[col])])
            elif col == 'education':
                user[col].append(education[int(row[col])])
            elif col == 'ethnicity':
                user[col].append(ethnicity[int(row[col])])
            elif col == 'robot':
                user[col].append(robot[int(row[col])])
            elif col == 'condition':
                user[col].append('')
            else:
                user[col].append(row[col])
        for col in trial_column_names:
            user[col].append(0)

#Creates the dataframe
df = pd.DataFrame(user, index=user['id'])

#With each trial.csv, do this
with open('result/trial.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    created_time = time.gmtime(os.path.getctime('result/trial.csv'))

    for row in reader:
        id = get_user_index(row['user_id'], created_time)
        trial_num = row['trial_num']
        if row['text_feedback'] == 'Correct!':
            df.at[id, 'trial-'+trial_num] = 1
        df.at[id, 'condition'] = row['feedback_type']

df['accuracy'] = df[trial_column_names].mean(axis=1)
df['accuracy 1-5'] = df[trial_column_names[:5]].mean(axis=1)
df['accuracy 6-10'] = df[trial_column_names[5:]].mean(axis=1)
trial_accuracies = df[trial_column_names].mean(axis=0)
agent = [1.   ,      1. ,        0.5,        0.66666667, 0.5, 1, 1.  ,       1.      ,   0.5    ,    1.        ]
acc = pd.DataFrame({'agent':agent, 'human': trial_accuracies})

# aov = pg.anova(dv='accuracy 1-5', between='condition', data=df, detailed=True)
# print(aov)
# aov = pg.anova(dv='accuracy 6-10', between='condition', data=df, detailed=True)
# print(aov)

acc.plot.line()
plt.show()
