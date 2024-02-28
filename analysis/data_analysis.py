import sqlite3
import pandas as pd
import pickle
import numpy as np
import scipy
from math import sqrt
from statsmodels.stats.power import TTestIndPower
import pdb
import pingouin as pg
import sys, os
import csv
from datetime import datetime
from scipy.stats import wilcoxon
import matplotlib.pyplot as plt
import seaborn as sns
import pdb

cur_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(cur_dir + '/../simple_game_test/app/augmented_taxi/policy_summarization'))
# import policy_summarization.BEC_helpers as BEC_helpers


# ---------------------------------- Global Variables ---------------------------------- #
LOOP_MAPPING = {'cl': 'Full', 'pl': 'Partial', 'open': 'Open', 'wt': 'Direct reward', 'wtcl': "Joint"}

alpha = 0.05

# ---------------------------------- Helper Functions ---------------------------------- #

def print_demographics(df_users):
    print("\n========== DEMOGRAPHICS ==========")

    print("Conditions Represented (want 68 of each): ")
    print(df_users.loop_condition.value_counts())
    print("Conditions Represented (want 34 of each): ")
    print("cl: ")
    print(df_users[df_users.loop_condition == 'cl'].domain_1.value_counts())
    print("pl: ")
    print(df_users[df_users.loop_condition == 'pl'].domain_1.value_counts())
    print("open: ")
    print(df_users[df_users.loop_condition == 'open'].domain_1.value_counts())
    print("wt: ")
    print(df_users[df_users.loop_condition == 'wt'].domain_1.value_counts())
    print("wtcl: ")
    print(df_users[df_users.loop_condition == 'wtcl'].domain_1.value_counts())

    print("Ages (description)")
    ages = pd.to_numeric(df_users.age)
    print(ages.describe())

    print("Genders: ")
    gender_vals = [0, 0, 0, 0]
    mapping = {0: 'Male', 1: 'Female', 2: 'Non-binary', 3: 'Prefer not to disclose'}
    answers = df_users.gender
    for answer in answers:
        gender_vals[int(answer)] += 1

    for idx, num in enumerate(gender_vals):
        print(mapping[idx] + " : " + str(num) + " (" + str(num / (np.sum(gender_vals))) + "%)")

def validate_submissions(df_users, df_trials, df_domain, use_csv=False):
    if use_csv:
        usernames = []

        # reading csv file
        with open('prolific.csv', 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)

            # extracting each data row one by one
            for row in csvreader:
                usernames.append(row[1])

        # reward_weight_data = df_trials[df_trials['unpickled_reward_ft_weights'].map(lambda d: len(d) > 0)].unpickled_reward_ft_weights
        # improvement_likert_data = df_trials[df_trials.likert > 0]

        # first entry is the column title
        usernames = usernames[1:]
    else:
        usernames = df_domain.username.unique()

    reward_weight_data = df_trials[df_trials['unpickled_reward_ft_weights'].map(lambda d: len(d) > 0)].unpickled_reward_ft_weights
    improvement_likert_data = df_trials[df_trials.likert > 0]

    for j, username in enumerate(usernames):
        flag = False

        if sum(df_trials[df_trials.username == username].interaction_type == 'final test') != 12:
            print("Has more or fewer than 12 tests")
            flag = True

        if len(df_domain[(df_domain.username == username)]) != 2:
            print("Has more or fewer teaching surveys")
            flag = True
        try:
            if df_trials[df_trials.username == username].loop_condition.iloc[0] in ['cl', 'pl', 'open', 'wtcl']:
                if df_trials[df_trials.username == username].loop_condition.iloc[0] in ['cl', 'pl', 'open']:
                    if len(reward_weight_data[df_trials.username == username]) != 2:
                        print("Didn't complete all 2 reward weight tests")
                        flag = True
        except:
            print("Wasn't able to check reward weight data")
            flag = True

            if len(improvement_likert_data[improvement_likert_data.username == username].likert) < 23:
                print("Not enough improvement likert scales")
                flag = True

        if flag:
            print("{} didn't pass the validation".format(username))
        else:
            print("{} passed the validation".format(username))


def print_means(data, dv, iv):
    for i in data[iv].unique():
        print("{} on {} mean: {}".format(i, dv, data[data[iv] == i][dv].mean()))

def perform_mixed_anova(dv, within, subject, between, data):
    aov = pg.mixed_anova(dv=dv, within=within, subject=subject, between=between,
                      data=data, correction=True)

    try: print(aov['p-GG-corr'])
    except: print(aov['p-unc'])
    pg.print_table(aov)

    df_between = data.groupby('username').agg({
        between: 'first',  # get the first loop_condition for each username
        dv: 'mean'  # get the mean of reward_diff for each username
    }).reset_index()

    df_between_within = data.groupby(['username', within]).agg({
        between: 'first',  # get the first loop_condition for each username
        dv: 'mean'  # get the mean of reward_diff for each username
    }).reset_index()

    post_hoc(aov, 0, dv, between, df_between)
    post_hoc(aov, 1, dv, within, df_between_within)

    if within == 'domain':
        data_at = data[data.domain == 'at']
        data_loop_at = data_at.groupby('username').agg({
            between: 'first',  # get the first loop_condition for each username
            dv: 'mean'  # get the mean of reward_diff for each username
        }).reset_index()

        data_sb = data[data.domain == 'sb']
        data_loop_sb = data_sb.groupby('username').agg({
            between: 'first',  # get the first loop_condition for each username
            dv: 'mean'  # get the mean of reward_diff for each username
        }).reset_index()

        print("at tukey")
        post_hoc(aov, 2, dv, between, data_loop_at)

        print("sb tukey")
        post_hoc(aov, 2, dv, between, data_loop_sb)
    else:
        data_low = data[data.test_difficulty == 'low']
        data_loop_low = data_low.groupby('username').agg({
            between: 'first',  # get the first loop_condition for each username
            dv: 'mean'  # get the mean of reward_diff for each username
        }).reset_index()
        data_medium = data[data.test_difficulty == 'medium']
        data_loop_medium = data_medium.groupby('username').agg({
            between: 'first',  # get the first loop_condition for each username
            dv: 'mean'  # get the mean of reward_diff for each username
        }).reset_index()
        data_high = data[data.test_difficulty == 'high']
        data_loop_high = data_high.groupby('username').agg({
            between: 'first',  # get the first loop_condition for each username
            dv: 'mean'  # get the mean of reward_diff for each username
        }).reset_index()

        print("low tukey")
        post_hoc(aov, 2, dv, between, data_loop_low)

        print("medium tukey")
        post_hoc(aov, 2, dv, between, data_loop_medium)

        print("high tukey")
        post_hoc(aov, 2, dv, between, data_loop_high)


# ---------------------------------- Subjective Metrics ---------------------------------- #


# ----------------------------------  Objective Metrics ---------------------------------- #
def post_hoc(aov, location, dv, between, data):
    if ('p-GG-corr' in aov and aov['p-GG-corr'].iloc[location] < alpha) or ('p-GG-corr' not in aov and aov['p-unc'].iloc[location] < alpha):
        print('Reject H0: different distributions across {}. Perform post-hoc Tukey HSD.'.format(aov['Source'][location]))
    else:
        print('Accept H0: Same distributions across {}.'.format(aov['Source'][location]))
    try:
        print("Corrected p-val: {}, DOF effect: {}, DOF error: {}, F: {}".format(aov['p-GG-corr'][location], aov['DF1'][location], aov['DF2'][location], aov['F'][location]))
    except:
        print("Uncorrected p-val: {}, DOF effect: {}, DOF error: {}, F: {}".format(aov['p-unc'][location], aov['DF1'][location], aov['DF2'][location], aov['F'][location]))

    if len(data[between].unique()) > 2:
        print("Tukey HSD")

        pt = pg.pairwise_tukey(dv=dv, between=between, data=data)
        pg.print_table(pt)
    else:
        print("T-test")

        vars = data[between].unique()
        pt = pg.ttest(data[data[between] == vars[0]][dv], data[data[between] == vars[1]][dv])
        pg.print_table(pt)

        for var in vars:
            print("{} mean: {}".format(var, data[data[between] == var][dv].mean()))

def compare_feedback_domain_on_performance(df_trials, dv='reward_diff', within='domain', plot=False):
    print("\n========== ANOVA: TEST DEMONSTRATION PERFORMANCE ==========")

    data = df_trials[df_trials.interaction_type == 'final test']
    perform_mixed_anova(dv, within, 'username', 'loop_condition', data)

    if plot:
        data = df_trials[df_trials.interaction_type == 'final test']
        ax = sns.barplot(data, x='loop_condition_string', y=dv, errorbar='ci',
                         order=["Open", "Partial", "Full"])
        ax.set(xlabel='Feedback Loop', ylabel='Average Reward Gap of Human Test Responses')
        ax.set(title='Effect of Feedback Loop on Reward Gap of Human Test Responses')
        # ax.set_ylim(0, 0.55) # for reward gap
        ax.set_ylim(0, 1)      # for scaled reward
        plt.show()


def compare_feedback_domain_on_engagement(df_domain, within='domain', plot=False):
    df_domain_engagement = pd.DataFrame(
        columns=['username', within, 'loop_condition', 'loop_condition_string', 'engagement', 'attn', 'use'])

    for username in np.unique(df_domain.username):
        for domain in np.unique(df_domain.domain):
            engagement = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 6

            # attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 3
            attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 2

            use = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 3

            loop_condition = df_domain[df_domain.username == username].loop_condition.values[0]
            loop_condition_string = df_domain[df_domain.username == username].loop_condition_string.values[0]

            df_domain_engagement = pd.concat((df_domain_engagement, pd.DataFrame({'username': username, 'loop_condition': loop_condition, 'domain': domain,
                               'loop_condition_string': loop_condition_string, 'engagement': engagement, 'attn': attn, 'use': use})), axis=0, ignore_index=True)

    # print("\n============================== ANOVA: ENGAGEMENT ==============================")
    # print_means(df_domain_engagement, 'engagement', 'loop_condition')
    # perform_mixed_anova(dv='engagement', within=within, subject='username', between='loop_condition',
    #                     data=df_domain_engagement)

    print("\n============================== ANOVA: ATTENTION ==============================")
    print_means(df_domain_engagement, 'attn', 'loop_condition')
    perform_mixed_anova(dv='attn', within=within, subject='username', between='loop_condition',
                        data=df_domain_engagement)

    df_domain_attn = df_domain[['attn1', 'attn2', 'attn3']]
    print("Overall cronbach's alpha: {}".format(pg.cronbach_alpha(df_domain_attn)))
    for key in df_domain_attn.keys():
        df_domain_attn_temp = df_domain_attn.drop(columns=key)
        print("Cronbach's alpha with {} dropped: {}".format(key, pg.cronbach_alpha(df_domain_attn_temp)))

    print("\n============================== ANOVA: USE ==============================")
    print_means(df_domain_engagement, 'use', 'loop_condition')
    perform_mixed_anova(dv='use', within=within, subject='username', between='loop_condition',
                        data=df_domain_engagement)

    df_domain_use = df_domain[['use1', 'use2', 'use3']]
    print("Overall cronbach's alpha: {}".format(pg.cronbach_alpha(df_domain_use)))
    for key in df_domain_use.keys():
        df_domain_use_temp = df_domain_use.drop(columns=key)
        print("Cronbach's alpha with {} dropped: {}".format(key, pg.cronbach_alpha(df_domain_use_temp)))

    if plot:
        ax = sns.barplot(df_domain_engagement[df_domain_engagement.domain == 'at'], x='loop_condition_string', y='use',
                         errorbar='ci',
                         order=["Open", "Partial", "Full"])
        ax.set(xlabel='Feedback Loop', ylabel='Perceived Usability')
        ax.set(title='Effect of Feedback Loop on Perceived Usability (Delivery Domain)')
        ax.set_ylim(-3.5, 0)
        plt.show()

def plot_joint(df_trials, df_domain, within='domain', between='reward_diff'):
    df_domain_engagement = pd.DataFrame(
        columns=['username', within, 'loop_condition', 'loop_condition_string', 'engagement', 'attn', 'use', between])

    for username in np.unique(df_domain.username):
        for domain in np.unique(df_domain.domain):
            # engagement = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 - \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 6

            # attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 3
            attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 2

            use = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 3

            loop_condition = df_domain[df_domain.username == username].loop_condition.values[0]
            loop_condition_string = df_domain[df_domain.username == username].loop_condition_string.values[0]

            if between == 'reward_diff':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].reward_diff)
            elif between == 'regret_norm':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].regret_norm)
            else:
                raise ValueError("Invalid between-subjects variable")

            df_domain_engagement = pd.concat((df_domain_engagement, pd.DataFrame({'username': username, 'loop_condition': loop_condition, 'domain': domain,
                               'loop_condition_string': loop_condition_string, 'attn': attn, 'use': use, between: between_val})), axis=0, ignore_index=True)


    # Increase the font size for all text elements
    plt.rcParams.update({'font.size': 14})
    bar_width = 0.7
    subtitle_font_size = 14
    fig, axs = plt.subplots(ncols=2, figsize=(7, 6))  # Adjust the figure size

    df_trials = df_trials[df_trials.interaction_type == 'final test']
    sns.barplot(data=df_trials, x='loop_condition_string', y=between, ax=axs[0], errorbar='ci',
                order=["Open", "Partial", "Full"], width=bar_width)  # Adjust the bar width
    axs[0].set(xlabel='Feedback Loop', ylabel='Normalized Regret of Human Test Responses')
    axs[0].set_title('Feedback Loop on Regret \n of Human Test Responses', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, 0.4) # use for regret norm
    axs[0].set_ylim(0, 0.55) # use for reward diff

    df_domain_engagement = df_domain_engagement[df_domain_engagement.domain == 'sb']
    sns.barplot(data=df_domain_engagement, x='loop_condition_string', y='use', ax=axs[1],
                errorbar='ci', order=["Open", "Partial", "Full"], width=bar_width)  # Adjust the bar width
    axs[1].set(xlabel='Feedback Loop', ylabel='Perceived Usability')
    axs[1].set_title('Feedback Loop on Perceived \n Usability (Skateboard Domain)', fontsize=subtitle_font_size-1)
    axs[1].set_ylim(0, 4.5)

    # plt.suptitle('Effect of Feedback Loop', fontsize=16)
    plt.tight_layout()
    plt.show()

def plot_joint_attn_improvement(df_trials, df_domain, within='domain', between='reward_diff'):
    df_domain_engagement = pd.DataFrame(
        columns=['username', within, 'loop_condition', 'loop_condition_string', 'engagement', 'attn', 'use', between])

    for username in np.unique(df_domain.username):
        for domain in np.unique(df_domain.domain):
            # engagement = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 - \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 6

            # attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 3
            attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 2

            use = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 3

            loop_condition = df_domain[df_domain.username == username].loop_condition.values[0]
            loop_condition_string = df_domain[df_domain.username == username].loop_condition_string.values[0]

            if between == 'reward_diff':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].reward_diff)
            elif between == 'regret_norm':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].regret_norm)
            else:
                raise ValueError("Invalid between-subjects variable")

            df_domain_engagement = pd.concat((df_domain_engagement, pd.DataFrame({'username': username, 'loop_condition': loop_condition, 'domain': domain,
                               'loop_condition_string': loop_condition_string, 'attn': attn, 'use': use, between: between_val})), axis=0, ignore_index=True)


    # Increase the font size for all text elements
    plt.rcParams.update({'font.size': 17})
    bar_width = 0.7
    subtitle_font_size = 19
    fig, axs = plt.subplots(ncols=3, figsize=(14, 9))  # Adjust the figure size

    # for plotting subjective results
    ylim = 5
    # ignore the first column (only keep to have the second two columns the same size as the first)
    # data = df_domain_engagement
    # sns.barplot(data=data, x='loop_condition_string', y='use', ax=axs[0],
    #             errorbar='ci', order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    # axs[0].set(xlabel='Explanation Type', ylabel='Perceived Usability')
    # axs[0].set_title('Main Effect (across both domains)', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, ylim)

    # for plotting objective results
    final_test_data = df_trials[df_trials.interaction_type == 'final test']
    sns.barplot(data=final_test_data, x='loop_condition_string', y=between, ax=axs[0], errorbar='ci',
                order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[0].set(xlabel='Explanation Type', ylabel='Regret of Human Test Responses')
    axs[0].set_title('Regret of Human Test Responses', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, 0.4) # use for regret norm
    axs[0].set_ylim(0, 0.95) # use for reward diff

    # attn
    data = df_domain_engagement
    sns.barplot(data=data, x='loop_condition_string', y='attn', ax=axs[1],
                errorbar='ci', order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[1].set(xlabel='Explanation Type', ylabel='Focused Attention Rating')
    axs[1].set_title('Focused Attention Rating', fontsize=subtitle_font_size)
    axs[1].set_ylim(1, ylim)

    # Get the current color cycle
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    # Create a new color cycle that starts with the second color
    new_colors = colors[1:] + colors[:1]
    # Set the color cycle
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=new_colors)

    # improvement
    data = df_trials[df_trials.likert > 0]
    sns.barplot(data=data, x='loop_condition_string', y='likert', ax=axs[2],
                errorbar='ci', order=["Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[2].set(xlabel='Explanation Type', ylabel='Improvement Rating')
    axs[2].set_title('Improvement Rating', fontsize=subtitle_font_size)
    axs[2].set_ylim(1, ylim)

    # plt.suptitle('Explanation Type on Perceived Usability', fontsize=20)

    plt.tight_layout()
    plt.show()

def plot_custom_followup(df_trials, df_domain, within='domain', between='reward_diff'):
    df_domain_engagement = pd.DataFrame(
        columns=['username', within, 'loop_condition', 'loop_condition_string', 'engagement', 'attn', 'use', between])

    for username in np.unique(df_domain.username):
        for domain in np.unique(df_domain.domain):
            # engagement = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 - \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 - df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 6

            # attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn2 + \
            #             df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 3
            attn = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn1 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].attn3) / 2

            use = (df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use1 + \
                        df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use2 + df_domain[(df_domain.username == username) & (df_domain.domain == domain)].use3) / 3

            loop_condition = df_domain[df_domain.username == username].loop_condition.values[0]
            loop_condition_string = df_domain[df_domain.username == username].loop_condition_string.values[0]

            if between == 'reward_diff':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].reward_diff)
            elif between == 'regret_norm':
                between_val = np.mean(
                    df_trials[(df_trials.username == username) & (df_trials.domain == domain)].regret_norm)
            else:
                raise ValueError("Invalid between-subjects variable")

            df_domain_engagement = pd.concat((df_domain_engagement, pd.DataFrame({'username': username, 'loop_condition': loop_condition, 'domain': domain,
                               'loop_condition_string': loop_condition_string, 'attn': attn, 'use': use, between: between_val})), axis=0, ignore_index=True)


    # Increase the font size for all text elements
    plt.rcParams.update({'font.size': 17})
    bar_width = 0.7
    subtitle_font_size = 17
    fig, axs = plt.subplots(ncols=3, figsize=(14, 9))  # Adjust the figure size

    # for plotting objective results
    final_test_data = df_trials[df_trials.interaction_type == 'final test']
    sns.barplot(data=final_test_data, x='loop_condition_string', y=between, ax=axs[0], errorbar='ci',
                order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[0].set(xlabel='Explanation Type', ylabel='Regret of Human Test Responses')
    axs[0].set_title('Main Effect (across both domains)', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, 0.4) # use for regret norm
    axs[0].set_ylim(0, 1.5) # use for reward diff

    data = final_test_data[final_test_data.domain == 'at']
    sns.barplot(data=data, x='loop_condition_string', y=between, ax=axs[1], errorbar='ci',
                order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[1].set(xlabel='Explanation Type', ylabel='Regret of Human Test Responses')
    axs[1].set_title('Delivery Domain', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, 0.4) # use for regret norm
    axs[1].set_ylim(0, 1.5) # use for reward diff

    data = final_test_data[final_test_data.domain == 'sb']
    sns.barplot(data=data, x='loop_condition_string', y=between, ax=axs[2], errorbar='ci',
                order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    axs[2].set(xlabel='Explanation Type', ylabel='Regret of Human Test Responses')
    axs[2].set_title('Skateboard Domain', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, 0.4) # use for regret norm
    axs[2].set_ylim(0, 1.5)  # use for reward diff
    plt.suptitle('Explanation Type on Regret of Human Test Responses', fontsize=20)

    # # for plotting subjective results
    # ylim = 4.55
    # data = df_domain_engagement
    # sns.barplot(data=data, x='loop_condition_string', y='use', ax=axs[0],
    #             errorbar='ci', order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    # axs[0].set(xlabel='Explanation Type', ylabel='Perceived Usability')
    # axs[0].set_title('Main Effect (across both domains)', fontsize=subtitle_font_size)
    # axs[0].set_ylim(0, ylim)
    #
    # data = df_domain_engagement[df_domain_engagement.domain == 'at']
    # sns.barplot(data=data, x='loop_condition_string', y='use', ax=axs[1],
    #             errorbar='ci', order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    # axs[1].set(xlabel='Explanation Type', ylabel='Perceived Usability')
    # axs[1].set_title('Delivery Domain', fontsize=subtitle_font_size)
    # axs[1].set_ylim(0, ylim)
    #
    # data = df_domain_engagement[df_domain_engagement.domain == 'sb']
    # sns.barplot(data=data, x='loop_condition_string', y='use', ax=axs[2],
    #             errorbar='ci', order=["Direct reward", "Full", "Joint"], width=bar_width)  # Adjust the bar width
    # axs[2].set(xlabel='Explanation Type', ylabel='Perceived Usability')
    # axs[2].set_title('Skateboard Domain', fontsize=subtitle_font_size)
    # axs[2].set_ylim(0, ylim)
    # plt.suptitle('Explanation Type on Perceived Usability', fontsize=20)

    plt.tight_layout()
    plt.show()

def compare_feedback_domain_on_understanding(df_domain, within='domain'):

    df_between = df_domain.groupby('username').agg({
        'loop_condition': 'first',  # get the first loop_condition for each username
        'understanding': 'median'  # get the mean of reward_diff for each username
    }).reset_index()

    kruskal = pg.kruskal(dv='understanding', between='loop_condition', data=df_between)
    pg.print_table(kruskal)

    if kruskal['p-unc'][0] < alpha:
        print("There is a significant difference of feedback loop on understanding!")
        print("mean understanding for open: {}".format(
            np.mean(df_between[df_between.loop_condition == 'open'].understanding)))
        print("mean understanding for pl: {}".format(
            np.mean(df_between[df_between.loop_condition == 'pl'].understanding)))
        print("mean understanding for cl: {}".format(
            np.mean(df_between[df_between.loop_condition == 'cl'].understanding)))
        print("mean understanding for wt: {}".format(
            np.mean(df_between[df_between.loop_condition == 'wt'].understanding)))
        print("mean understanding for wtcl: {}".format(
            np.mean(df_between[df_between.loop_condition == 'wtcl'].understanding)))

        for domain in df_domain[within].unique():
            print(domain)
            print("mean understanding for open: {}".format(
                np.mean(df_domain[(df_domain.loop_condition == 'open') & (df_domain.domain == domain)].understanding)))
            print("mean understanding for pl: {}".format(
                np.mean(df_domain[(df_domain.loop_condition == 'pl') & (df_domain.domain == domain)].understanding)))
            print("mean understanding for cl: {}".format(
                np.mean(df_domain[(df_domain.loop_condition == 'cl') & (df_domain.domain == domain)].understanding)))
            print("mean understanding for wt: {}".format(
                np.mean(df_domain[(df_domain.loop_condition == 'wt') & (df_domain.domain == domain)].understanding)))
            print("mean understanding for wtcl: {}".format(
                np.mean(df_domain[(df_domain.loop_condition == 'wtcl') & (df_domain.domain == domain)].understanding)))

        if ('wt' in df_between.loop_condition.unique() and 'cl' in df_between.loop_condition.unique() and 'wtcl' in df_between.loop_condition.unique()):
            print("cl vs wt")
            pg_wilcoxon = pg.wilcoxon(df_between[df_between.loop_condition == 'cl'].understanding,
                                      df_between[df_between.loop_condition == 'wt'].understanding)
            pg.print_table(pg_wilcoxon)

            print("wtcl vs wt")
            pg_wilcoxon = pg.wilcoxon(df_between[df_between.loop_condition == 'wtcl'].understanding,
                                      df_between[df_between.loop_condition == 'wt'].understanding)
            pg.print_table(pg_wilcoxon)

            print("cl vs wtcl")
            pg_wilcoxon = pg.wilcoxon(df_between[df_between.loop_condition == 'cl'].understanding,
                                      df_between[df_between.loop_condition == 'wtcl'].understanding)
            pg.print_table(pg_wilcoxon)
        else:
            raise Exception("Post-hoc analyses haven't been implemented for these conditions.")

    else:
        print("There is no significant difference of feedback loop on understanding!")

    print("domain on understanding")
    pg_wilcoxon = pg.wilcoxon(df_domain[df_domain.domain == 'at'].understanding, df_domain[df_domain.domain == 'sb'].understanding)
    pg.print_table(pg_wilcoxon)

    scipy_wilcoxon = wilcoxon(df_domain[df_domain.domain == 'at'].understanding, df_domain[df_domain.domain == 'sb'].understanding, method='approx')
    print("z-statistic: {}".format(scipy_wilcoxon.zstatistic))


    if pg_wilcoxon['p-val'][0] < alpha:
        print("There is a significant difference of domain on understanding!")
        print("mean understanding for taxi: {}".format(
            np.mean(df_domain[df_domain.domain == 'at'].understanding)))
        print("mean understanding for skateboard: {}".format(
            np.mean(df_domain[df_domain.domain == 'sb'].understanding)))

        print("median understanding for taxi: {}".format(
            np.median(df_domain[df_domain.domain == 'at'].understanding)))
        print("median understanding for skateboard: {}".format(
            np.median(df_domain[df_domain.domain == 'sb'].understanding)))
    else:
        print("There is no significant difference of domain on understanding!")

def compare_feedback_on_improvement(df_trials, within='domain'):
    print("\n========== KRUSKAL: IMPROVEMENT SUBJECTIVE RATING ==========")

    # check if feedback affects ratings on improvement
    data = df_trials[df_trials.likert > 0]

    print_means(data, 'likert', 'loop_condition')

    perform_mixed_anova('likert', within, 'username', 'loop_condition', data)

def calculate_median_num_interactions(df_trials, condition='cl'):
    print("\n========== MEDIAN NUMBER OF INTERACTIONS ==========")

    exclude = ['diagnostic feedback', 'remedial feedback', 'final test']

    # obtain the number of times each person interacted with Chip in each domain
    num_interactions_at = []
    num_interactions_sb = []
    perfect_training = []
    perfect_interactions_at_usernames = []
    for username in df_trials[df_trials.loop_condition == condition].username.unique():
        num_interactions_at_user = sum(~df_trials[(df_trials.domain == 'at') & (
                df_trials.loop_condition == condition) & (df_trials.username == username)].interaction_type.isin(exclude))
        num_interactions_sb_user = sum(~df_trials[(df_trials.domain == 'sb') & (
                df_trials.loop_condition == condition) & (df_trials.username == username)].interaction_type.isin(exclude))
        num_interactions_at.append(num_interactions_at_user)
        num_interactions_sb.append(num_interactions_sb_user)

        if num_interactions_at_user == 9 and num_interactions_sb_user == 14:
            perfect_training.append(username)
        if num_interactions_at_user == 9:
            perfect_interactions_at_usernames.append(username)

    median_interactions_at = np.median(num_interactions_at)
    median_interactions_sb = np.median(num_interactions_sb)
    print("Median number of closed-loop interactions for taxi: {}".format(median_interactions_at))
    print("Median number of closed-loop interactions for skateboard: {}".format(median_interactions_sb))

    # did anyone go through the training perfectly?
    print("Number of people who perfectly underwent taxi training: {}".format(np.sum(np.array(num_interactions_at) == 9)))
    print("Number of people who perfectly underwent skateboard training: {}".format(np.sum(np.array(num_interactions_sb) == 14)))
    print("People who perfectly went through both training: {}".format(perfect_training))

    # obtain the participants who saw the median number of interactions
    median_interactions_at_users = np.array(df_trials[df_trials.loop_condition == condition].username.unique())[np.array(num_interactions_at) == median_interactions_at]
    median_interactions_sb_users = np.array(df_trials[df_trials.loop_condition == condition].username.unique())[np.array(num_interactions_sb) == median_interactions_sb]
    median_training = []
    for at_user in median_interactions_at_users:
        if at_user in median_interactions_sb_users:
            median_training.append(at_user)
    print("People who went through both median training: {}".format(perfect_training))

def print_qualitative_feedback(df_trials, df_users, df_domain):
    print("\n========== QUALITATIVE FEEDBACK ==========")

    data = df_trials[df_trials['unpickled_improvement_short_answer'].map(
        lambda d: len(d) > 0)]
    data_domain = df_domain[df_domain['unpickled_engagement_short_answer'].map(
        lambda d: len(d) > 0)]
    data_users = df_users[df_users['unpickled_final_feedback'].map(
        lambda d: len(d) > 0)]

    data.style.set_properties(**{'text-align': 'left'})
    data_domain.style.set_properties(**{'text-align': 'left'})
    data_users.style.set_properties(**{'text-align': 'left'})

    pd.set_option('display.max_colwidth', None)

    width = max(data['unpickled_improvement_short_answer'].str.len().max(), data_domain['unpickled_engagement_short_answer'].str.len().max(), data_users['unpickled_final_feedback'].str.len().max())
    data2 = data.copy()
    data2['unpickled_improvement_short_answer'] = data['unpickled_improvement_short_answer'].str.ljust(width)
    data_domain2 = data_domain.copy()
    data_domain2['unpickled_engagement_short_answer'] = data_domain['unpickled_engagement_short_answer'].str.ljust(width)
    data_users2 = data_users.copy()
    data_users2['unpickled_final_feedback'] = data_users['unpickled_final_feedback'].str.ljust(width)

    for loop_condition in df_trials.loop_condition.unique():
        print("===================================== Loop condition: {} =====================================".format(
            loop_condition))
        if len(data_users2[data_users2.loop_condition == loop_condition].unpickled_final_feedback) > 0:
            print(data_users2[data_users2.loop_condition == loop_condition].unpickled_final_feedback)
        for domain in df_trials.domain.unique():
            print(
                "===================================== Domain condition: {} =====================================".format(
                    domain))

            if len(data2[(data2.loop_condition == loop_condition) & (data2.domain == domain)].unpickled_improvement_short_answer) > 0:
                print(data2[(data2.loop_condition == loop_condition) & (data2.domain == domain)].unpickled_improvement_short_answer)
            if len(data_domain2[(data_domain2.loop_condition == loop_condition) & (data_domain2.domain == domain)].unpickled_engagement_short_answer) > 0:
                print(data_domain2[(data_domain2.loop_condition == loop_condition) & (data_domain2.domain == domain)].unpickled_engagement_short_answer)

    # # by username
    # for username in df_trials.username.unique():
    #     print("Username: {}".format(username))
    #     if len(data2[data.username == username].unpickled_improvement_short_answer) > 0:
    #         print(data2[data.username == username].unpickled_improvement_short_answer)
    #     if len(data_domain[data_domain.username == username].unpickled_engagement_short_answer) > 0:
    #         print(data_domain[data_domain.username == username].unpickled_engagement_short_answer)
    #     if len(data_users[data_users.username == username].unpickled_final_feedback) > 0:
    #         print(data_users[data_users.username == username].unpickled_final_feedback)


def analyze_time_spent(df_trials):
    np.mean(df_trials[df_trials.interaction_type == 'final test'].duration_ms) / 1000

def analyze_reward_weights(df_trials):
    df_trials_reward_weights = df_trials[df_trials['unpickled_reward_ft_weights'].map(lambda d: (len(d) > 0) and len(d[1]) > 0)].copy()
    def normalize_reward_weights(weights):
        normalized_weights = np.array([[float(weights[0]), float(weights[1]), -1]])

        return normalized_weights / np.linalg.norm(normalized_weights[0, :], ord=2)

    df_trials_reward_weights['scaled_reward_ft_weights'] = df_trials_reward_weights['unpickled_reward_ft_weights'].apply(normalize_reward_weights)

    sb_gt_weights = np.array([[0.59565914, 0.3519804, -0.72201107]])
    at_gt_weights = np.array([[-0.63599873, 0.74199852, -0.21199958]])

    def correct_sign(data, iv, gt_weights):
        gt_sign = np.sign(gt_weights)
        for condition in np.unique(data[iv]):
            print(condition)
            incorrect_sign_ct, correct_sign_ct = 0, 0
            data_condition = data[data[iv] == condition]
            for i in range(len(data_condition)):
                if (np.sign(data_condition.iloc[i].scaled_reward_ft_weights) == gt_sign).all():
                    correct_sign_ct += 1
                else:
                    incorrect_sign_ct += 1

            print('correct sign: ', correct_sign_ct)
            print('incorrect sign: ', incorrect_sign_ct)

    print('at')
    correct_sign(df_trials_reward_weights[df_trials_reward_weights.domain == 'at'], 'loop_condition', at_gt_weights)
    print('sb')
    correct_sign(df_trials_reward_weights[df_trials_reward_weights.domain == 'sb'], 'loop_condition', sb_gt_weights)

    # if I want to see how many estimates belong in the BEC area
    # BEC_helpers.sample_human_models_uniform([np.array([[0, 0, -1]])], 50)
    at_BEC_constraints = [np.array([[1, 1, 0]]), np.array([[-1, 0, 2]]), np.array([[0, -1, -4]])]
    sb_BEC_constraints = [np.array([[5, 2, 5]]), np.array([[-6,  4, -3]]), np.array([[ 3, -3,  1]])]


# ---------------------------------- Running the Analysis ---------------------------------- #

if __name__ == '__main__':
    with open('dfs_f23_processed.pickle', 'rb') as f:
        df_users, df_trials, df_domain = pickle.load(f)

    # ------------------------ data selection ------------------------#
    # if I'm interested in only considering a subset of the full dataset
    # original user study conditions (cl, pl, open)
    df_users = df_users[(df_users.loop_condition == 'cl') | (df_users.loop_condition == 'pl') | (df_users.loop_condition == 'open')]
    df_trials = df_trials[(df_trials.loop_condition == 'cl') | (df_trials.loop_condition == 'pl') | (df_trials.loop_condition == 'open')]
    df_domain = df_domain[(df_domain.loop_condition == 'cl') | (df_domain.loop_condition == 'pl') | (df_domain.loop_condition == 'open')]

    # follow-up user study on direct reward explanations (cl, wt, wtcl)
    # df_users = df_users[(df_users.loop_condition == 'cl') | (df_users.loop_condition == 'wt') | (df_users.loop_condition == 'wtcl')]
    # df_trials = df_trials[(df_trials.loop_condition == 'cl') | (df_trials.loop_condition == 'wt') | (df_trials.loop_condition == 'wtcl')]
    # df_domain = df_domain[(df_domain.loop_condition == 'cl') | (df_domain.loop_condition == 'wt') | (df_domain.loop_condition == 'wtcl')]

    #------------------------ descriptive statistics ------------------------#
    # print_qualitative_feedback(df_trials, df_users, df_domain)

    # print_demographics(df_users)

    # ------------------------ primary analyses ------------------------#

    # compare effect of feedback and domain on performance (H1)
    # compare_feedback_domain_on_performance(df_trials)
    #
    # compare effect of feedback and domain on focused attn and perceived usability (H2)
    # compare_feedback_domain_on_engagement(df_domain, plot=False)

    # compare effect of feedback and domain on improvement (H3)
    compare_feedback_on_improvement(df_trials)

    # compare effect of feedback and domain on understanding (H4)
    # compare_feedback_domain_on_understanding(df_domain)

    # custom plots for original user study conditions (cl, pl, open)
    # plot regret and usability (latter only in the delivery domain)
    # plot_joint(df_trials, df_domain, between='reward_diff')
    # plot_joint_attn_improvement(df_trials, df_domain)

    # custom plots for follow-up user study conditions (cl, wt, wtcl)
    # plot_custom_followup(df_trials, df_domain, between='reward_diff')

    #------------------------ secondary analyses ------------------------#
    # estimating reward weights (IRL)
    # analyze_reward_weights(df_trials)