from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, TrialForm, DemoForm, ConsentForm, AttentionCheckForm, FinalForm, TrainingForm, FeedbackSurveyForm, NoFeedbackSurveyForm, InformativenessForm
from app.models import User, Trial, Demo, OnlineCondition, InPersonCondition, Survey, Domain
from app.params import *
from utils import rules_to_str, str_to_rules
import numpy as np
import random as rand
import json
from datetime import datetime
from generate_rules import generate_rule, generate_hard_rule_constrained
from environment import Environment
from learner import Learner

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'augmented_taxi'))
from .augmented_taxi.policy_summarization.flask_user_study_utils import normalize_trajectories, obtain_constraint
from .augmented_taxi.policy_summarization.BEC import obtain_remedial_demonstrations
from .augmented_taxi import params
from .augmented_taxi.policy_summarization import BEC_helpers
from .augmented_taxi.policy_summarization import particle_filter as pf
from .augmented_taxi.policy_summarization import BEC_visualization as BEC_viz

from app.backend_test import send_signal
from app import socketio
from flask_socketio import join_room, leave_room
import pickle
from multiprocessing import Pool
import copy

# change to the directory of this file
os.chdir(os.path.join(os.path.dirname(__file__)))

with open('user_study_dict.json', 'r') as f:
    jsons = json.load(f)

# rule_str = None
# TODO need a proper solution instead of global variables, i.e. per-user environment
# https://stackoverflow.com/questions/27611216/how-to-pass-a-variable-between-flask-pages
learners = {}
MODE = 'hard'
IS_IN_PERSON = False

CARD_ID_TO_FEATURES = [
    [color, fill, shape, number] for color in ['red', 'green', 'purple'] for fill in ['hollow', 'striped', 'solid'] for shape in ['diamond', 'ellipse', 'squiggle'] for number in ['one', 'two', 'three']
]

# todo: Mike uncomment for remedial demos and tests
# background variables needed for remedial demonstrations and tests
domain_background_vars = {}
def load_background_vars(data_loc):
    with open('models/' + data_loc + '/base_constraints.pickle', 'rb') as f:
        policy_constraints, min_subset_constraints_record, env_record, traj_record, traj_features_record, reward_record, mdp_features_record, consistent_state_count = pickle.load(
            f)
    background_vars = (
    policy_constraints, min_subset_constraints_record, env_record, traj_record, traj_features_record, reward_record,
    mdp_features_record, consistent_state_count)

    return background_vars

# todo: double check if this code is run for each new person
args = ['augmented_taxi2', 'colored_tiles', 'skateboard2']

for domain in args:
    domain_background_vars[domain] = load_background_vars(domain)

pool = Pool(os.cpu_count())

# HOW TO PREVENT RULE / STATE CHANGE ON RELOAD???

@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    # global rule_str
        # if rule_str is None:
    global learners
    start_time = datetime.now().utcnow().isoformat()
    # num_completed_trials = db.session.query(Trial).filter_by(user_id=current_user.id, round_num=round).count()
    # condition_id = current_user.condition_id
    # current_condition = db.session.query(Condition).get(condition_id)

    # if num_completed_trials == len(cards):
    # flash("You have seen all the trials in this round!")
    #     return redirect(url_for("survey", round=round))

    # if check_previous_demos < len(RULE_PROPS[check_rule_name]['demo_cards']):
    #     return redirect(url_for("consent"))
    print("trial id")
    print(current_user.id)

    bins, rule_str = generate_rule(MODE)
    env = Environment(bins, MODE)
    learners[current_user.username] = Learner(MODE)
    session['rule_str'] = rule_str
    session['rule_str_as_bin'] = bins
    session['env'] = env.to_dict()
    session['start_time_s'] = datetime.now().timestamp()
    # session['learner'] = learner.to_dict()
    db.session.commit()

    if IS_IN_PERSON:
        in_person_condition_id = current_user.in_person_condition_id
        current_condition = db.session.query(InPersonCondition).get(in_person_condition_id)
    else:
        online_condition_id = current_user.online_condition_id
        current_condition = db.session.query(OnlineCondition).get(online_condition_id)

    if current_user.num_trials_completed == len(current_condition.trials):
        return redirect(url_for("survey"))

    if current_user.training != 1:
        tutorial_mode = True
        feedback_condition = 'no_feedback'
        round_num = "0 (Tutorial)"
    else:
        tutorial_mode = False
        feedback_condition = current_condition.trials[current_user.num_trials_completed]
        round_num = current_user.num_trials_completed + 1
    learners[current_user.username].set_feedback_type(feedback_condition)
    return render_template("test.html",
        title="Robot Sorting Game, Round ",
        round_num=round_num,
        rule_str=rule_str,
        tutorial_mode=tutorial_mode,
        feedback_condition=feedback_condition,
        vid_name="neutral_long_1",
        debug=True)

@app.route("/place_card", methods=["GET", "POST"])
def place_card():
    global learners
    learner = learners[current_user.username]
    if 'env' in session:
        env = Environment.from_dict(session['env'])
    else:
        print('No ENV found in session')
        return {}
    # if 'learner' in session:
    #     learner = Learner.from_dict(session['learner'])
    # else:
    #     print(session)
    #     print('No LEARNER found in session')
    #     return {}
    card_id_str = request.args.get("card_id")
    card_id = int(card_id_str.split("-")[-1])
    card_features = CARD_ID_TO_FEATURES[card_id]
    print('Placing card with features: ', card_features)
    bin, outcome_str = env.place_card(card_features)
    print(outcome_str)
    if 'rule_str' in session:
        print(session['rule_str'])
    else:
        print('No RULE_STR found in session')
    # Update learner observation
    if bin != -1:
        learner.observe(card_features, bin)
        print(f'Learner\'s belief now contains {learner.get_n_valid_rules()} valid rule(s)')
    # fb_str = learner.get_feedback()
    # Update session variables
    session['env'] = env.to_dict()
    learned = 1 if learner.get_n_valid_rules() == 1 else 0
    # session['learner'] = learner.to_dict()
    return {'bin': bin+1, 'outcome_str': outcome_str, 'card_id': card_id, 'status': learned}

@app.route("/get_feedback", methods=["GET", "POST"])
def get_feedback():
    global learners
    learner = learners[current_user.username]
    fb_str = learner.get_feedback()
    print(f'User {current_user.username} got feedback: {fb_str}')
    return {'fb_str': fb_str}

def jsonStrToList(str):
    if len(str) > 2:
        return [int(val) for val in str[1:-1].split(',')]
    else:
        return []

@app.route("/trial_completed", methods=["GET", "POST"])
def trial_completed():
    global learners
    learner = learners[current_user.username]

    if IS_IN_PERSON:
        in_person_condition_id = current_user.in_person_condition_id
        current_condition = db.session.query(InPersonCondition).get(in_person_condition_id)
    else:
        online_condition_id = current_user.online_condition_id
        current_condition = db.session.query(OnlineCondition).get(online_condition_id)
    current_user.set_browser(request.args.get("browser"))
    trial_duration_ms = 1000 * (datetime.now().timestamp() - session['start_time_s'])
    feedback_confidences = jsonStrToList(request.args.get("feedback_confidences"))
    terminate_confidences = jsonStrToList(request.args.get("termination_confidences"))
    terminate_record = jsonStrToList(request.args.get("termination_record"))
    card_select_times = jsonStrToList(request.args.get("card_select_times"))
    feedback_strings = request.args.get("feedback_strings")
    if len(feedback_strings) > 2:
        feedback_strings = feedback_strings.split('","')
        feedback_strings[-1] = feedback_strings[-1][:-2]
        feedback_strings[0] = feedback_strings[0][2:]
    else:
        feedback_strings = []
    trial = Trial(
        user_id=current_user.id,
        trial_num=current_user.num_trials_completed + 1,
        duration_ms=trial_duration_ms,
        rule_str=session['rule_str'],
        fb_type=learner._fb_type,
        cards_played=learner._observations,
        n_cards=learner._n_observations,
        n_cards_to_learn_rule=learner._n_observations_to_learn_rule,
        card_select_times=card_select_times,
        n_hypotheses_remaining=learner._n_hypotheses_remaining,
        n_failed_terminations=request.args.get("n_failed_terminations"),
        terminate_confidences=terminate_confidences,
        feedback_confidences=feedback_confidences,
        terminate_record=terminate_record,
        bonus_value=request.args.get("bonus_value"),
        feedback_strings=feedback_strings
    )
    db.session.add(trial)
    db.session.commit()
    # if updated_num_trials_completed < len(current_condition.trials):
    #     return {"url":url_for("test", round=current_user.num_trials_completed)}

    # Remove learner from global dictionary
    print(learners.keys())
    del learners[current_user.username]
    print(learners.keys())
    return {"url":url_for("survey")}

@app.route("/check_termination_condition", methods=["GET", "POST"])
def check_termination_condition():
    global learners
    learner = learners[current_user.username]
    print(learner.get_n_valid_rules)
    has_learned = 1 if learner.get_n_valid_rules() == 1 else 0
    bonus = learner.get_bonus()
    print(learner.get_n_valid_rules)
    print(bonus)
    return {'has_learned': has_learned, 'bonus': bonus}


@app.route("/hover_card", methods=["GET", "POST"])
def hover_card():
    if 'env' in session:
        env = Environment.from_dict(session['env'])
    else:
        print('No ENV found in session')
        return {}
    card_id_str = request.args.get("card_id")
    card_id = int(card_id_str.split("-")[-1])
    card_features = CARD_ID_TO_FEATURES[card_id]
    bin = env.get_bin_for_card(card_features)
    return {"bin": bin+1}

@app.route("/terminate_learning", methods=["GET", "POST"])
def terminate_learning():
    global learners
    learner = learners[current_user.username]
    if 'env' in session:
        env = Environment.from_dict(session['env'])
    else:
        print('No ENV found in session')
        return {}
    # if 'learner' in session:
    #     learner = Learner.from_dict(session['learner'])
    # else:
    #     print('No LEARNER found in session')
    #     return {}

    debug = (request.args.get("debug") == "True")
    if not debug:
        return {'dialog_str': ''}
        return {'redirect_str': '/survey/999'}
    print('Terminating Learning.')
    dialog_str = "Learning terminated."
    if learner.get_n_valid_rules() == 1:
        dialog_str += f' Learner successfully identified the rule:\n\n{learner.get_most_confident_rule_str()}'
    else:
        dialog_str += f' Learner\'s belief contains {learner.get_n_valid_rules()} valid rules.'
    dialog_str += f'\n\nMetrics:'

    learner_metrics = learner.get_metrics(env.bins)
    for key in learner_metrics:
        dialog_str += f'\n- {key}: {learner_metrics[key]}'

    return {'dialog_str': dialog_str}

@app.route("/set_fb_type", methods=["GET", "POST"])
def set_fb_type():
    global learners
    learner = learners[current_user.username]
    # if 'learner' in session:
    #     learner = Learner.from_dict(session['learner'])
    # else:
    #     print('No LEARNER found in session')
    #     return "nothing"

    fb_type = request.args.get("fb_type")
    learner.set_feedback_type(fb_type)

    # session['learner'] = learner.to_dict()
    return "nothing"

# @app.route("/attn_check", methods=["GET", "POST"])
# @login_required
# def attn_check():
#     form = AttentionCheckForm()

#     true_rule = session['rule_str']
#     print(f"the true rule is {true_rule}")

#     # because exception_val is hard to identify, lets consider (primary class, exception class)
#     # the true rule is (TP, TP)
#     rules = [true_rule]
#     # so we generate (TP, FP)
#     rules.append(generate_hard_rule_constrained(session['rule_str_as_bin'], True, False))
#     # as well as (FP, TP)
#     rules.append(generate_hard_rule_constrained(session['rule_str_as_bin'], False, True))
#     # and, finally, (FP, FP)
#     rules.append(generate_hard_rule_constrained(session['rule_str_as_bin'], False, False))
#     rand.shuffle(rules)

#     if 'attention_check_rules' in session:
#         print(f"The attention check rules already exist, and are: {session['attention_check_rules']}")

#     else:
#         print(f"Defining attention check rules to be {rules}")
#         session['attention_check_rules'] = rules

#     # print (session['attention_check_rules'])
#     if form.validate_on_submit():
#         attention_check_val = 1 if (int(form.prev_rule.data) == session['attention_check_rules'].index(session['rule_str'])) else 0
#         print(f"Attention Check value is: {attention_check_val}")
#         print(f"Form.prev_rule.data was {form.prev_rule.data}")
#         print(f"Rules is {session['attention_check_rules']}")
#         print(f"And the location we indexed into was {session['attention_check_rules'].index(true_rule)}")

#         current_user.set_attention_check(attention_check_val)

#         # Clear this variable -- for some reason was not clearing on its own.
#         session.pop('attention_check_rules', None)

#         db.session.commit()
#         redirect(url_for("test"))

#     online_condition_id = current_user.online_condition_id
#     current_condition = db.session.query(OnlineCondition).get(online_condition_id)

#     # We only provide an attention check after the first survey
#     completed_survey = db.session.query(Survey).filter_by(user_id=current_user.id, round_num=1).count()

#     # Make sure previous step (survey after first game) has been completed
#     # if current_user.num_trials_completed == len(current_condition.trials) and current_user.study_completed == 0:
#     #     return redirect(url_for("survey"))
#     if completed_survey == 0:
#         return redirect(url_for("survey"))

#     # Only complete the attention check once
#     if current_user.attention_check != -1:
#         if current_user.num_trials_completed < len(current_condition.trials):
#             return redirect(url_for("test"))
#         else:
#             return redirect(url_for("survey"))

#     return render_template("attention_check.html",
#                             title="Attention Check",
#                             rule_1=session['attention_check_rules'][0],
#                             rule_2=session['attention_check_rules'][1],
#                             rule_3=session['attention_check_rules'][2],
#                             rule_4=session['attention_check_rules'][3],
#                             form=form)

@app.route("/training/<string:page>", methods=["GET", "POST"])
@login_required
def training(page):
    form = TrainingForm()
    if form.validate_on_submit():
        current_user.training = 1
        db.session.commit()
        redirect(url_for("test"))
    if current_user.training:
        # flash("Training already completed!")
        return redirect(url_for("test"))
    elif not current_user.consent:
        # flash("Consent not yet completed!")
        return redirect(url_for("consent"))
    else:
        if not IS_IN_PERSON:
            study_format = "Let's go over the format of the study. You will be teaching the robot in two separate games, with two separate rules. In one of these games, you will not receive any feedback from the robot at all and in the other, you will receive feedback from the robot after every card you play."
            compensation_info = "Then, you will receive a random code to enter into Prolific so that you can be compensated for completing this study."
        else:
            study_format = "Let's go over the format of the study. You will be teaching the robot in five separate games, with five separate rules. In all of these games, you will receive some form of feedback from the robot after every card you play."
            compensation_info = "At the conclusion of the study, you will be compensated for your time."
        url = "/training/" + page + ".html"
        return render_template(url, title="Training", form=form, study_format=study_format, compensation_info=compensation_info)

# @app.route("/", methods=["GET", "POST"])
# @app.route("/index/", methods=["GET", "POST"])
# def index():
#     start_time = datetime.now().utcnow().isoformat()
#     form = TrialForm(start_time=start_time)

#     num_completed_trials = 0 #db.session.query(Trial).filter_by(user_id=current_user.id, round_num=round).count()

#     # condition_id = current_user.condition_id
#     # current_condition = db.session.query(Condition).get(condition_id)
#     round = 0
#     rule_name = 'EASY' # current_condition.difficulty[round]
#     rule = RULE_PROPS[rule_name]['rule']
#     demo_cards = RULE_PROPS[rule_name]['demo_cards']
#     cards = RULE_PROPS[rule_name]['cards']
#     answers = RULE_PROPS[rule_name]['answers']
#     demo_answers = RULE_PROPS[rule_name]['demo_answers']

#     previous_cards = [[], []]
#     for ii in range(len(demo_cards)):
#         if demo_answers[ii] == 0:
#             previous_cards[0].append(demo_cards[ii])
#         if demo_answers[ii] == 1:
#             previous_cards[1].append(demo_cards[ii])

#     for ii in range(num_completed_trials):
#         if answers[ii] == 0:
#             previous_cards[0].append(cards[ii])
#         if answers[ii] == 1:
#             previous_cards[1].append(cards[ii])

#     if form.validate_on_submit():
#         chosen_bin = int(form.chosen_bin.data[3])
#         feedback_chosen = form.feedback_chosen.data
#         trial = Trial(author=current_user,
#                       trial_num=num_completed_trials + 1,
#                       card_num=cards[num_completed_trials],
#                       round_num=round,
#                       correct_bin=answers[num_completed_trials],
#                       chosen_bin=chosen_bin,
#                       feedback=feedback_chosen,
#                       rule_set=rule,
#                       switches=int(form.switches.data))
#         db.session.add(trial)

#         feedback_counts = current_user.feedback_counts
#         new_feedback_counts = {}
#         for new_vid_name in VIDEO_LIST:
#             if new_vid_name == feedback_chosen:
#                 new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name] + 1
#             else:
#                 new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name]

#         current_user.feedback_counts = new_feedback_counts
#         db.session.commit()
#         return redirect(url_for('trials', round=round))

#     if num_completed_trials == len(cards):
#         # flash("You have seen all the trials in this round!")
#         return redirect(url_for("survey", round=round))

#     #Check if previous thing is done, previous demos must be done
#     check_rule_name = rule_name# current_condition.difficulty[round]
#     check_previous_demos = db.session.query(Demo).filter_by(user_id=current_user.id, round_num=round).count()
#     if check_previous_demos < len(RULE_PROPS[check_rule_name]['demo_cards']):
#         return redirect(url_for("consent"))

#     #Pick the video to play
#     feedback_counts = current_user.feedback_counts
#     cur_names = []
#     cur_counts = []
#     for vid_name in NEUTRAL:
#         cur_names.append(vid_name)
#         cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         p = np.ones_like(cur_counts)/np.sum(np.ones_like(cur_counts))
#     else:
#         p= 1 - cur_counts/np.sum(cur_counts)
#     for ii in range(len(p)):
#         if p[ii] < 0.05:
#             p[ii] = 0.05
#     p = p / np.sum(p)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p= p)
#     neutral_vid_name = cur_names[vid_choice]

#     new_feedback_counts = {}
#     for new_vid_name in VIDEO_LIST:
#         if new_vid_name == vid_name:
#             new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name] + 1
#         else:
#             new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name]

#     current_user.feedback_counts = new_feedback_counts
#     db.session.commit()

#     if answers[num_completed_trials] == 0:
#         correct_bin = 'bin0'
#     else:
#         correct_bin = 'bin1'


#     #Choose correct video
#     current_nonverbal = 'NONVERBAL' # current_condition.nonverbal[round]
#     cur_names = []
#     cur_counts = []
#     if correct_bin == 'bin0':
#         for vid_name in FEEDBACK[current_nonverbal]['CORRECT-LEFT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     else:
#         for vid_name in FEEDBACK[current_nonverbal]['CORRECT-RIGHT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         cur_counts = np.ones_like(cur_counts)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p=cur_counts/np.sum(cur_counts))
#     correct_vid_name = cur_names[vid_choice]

#     #Choose incorrect video
#     cur_names = []
#     cur_counts = []
#     if correct_bin == 'bin0':
#         for vid_name in FEEDBACK[current_nonverbal]['INCORRECT-LEFT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     else:
#         for vid_name in FEEDBACK[current_nonverbal]['INCORRECT-RIGHT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         cur_counts = np.ones_like(cur_counts)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p=cur_counts/np.sum(cur_counts))
#     incorrect_vid_name = cur_names[vid_choice]

    # return render_template("trials.html",
    #     title="Trials",
    #     form=form,
    #     num_bins=len(rule),
    #     card=cards[num_completed_trials],
    #     correct_bin=correct_bin,
    #     num_completed_trials=num_completed_trials + 1,
    #     num_trials=len(cards),
    #     previous_cards=previous_cards,
    #     round=round,
    #     vid_name=neutral_vid_name,
    #     correct_vid_name = correct_vid_name,
    #     incorrect_vid_name = incorrect_vid_name)

@app.route("/", methods=["GET", "POST"])
# @app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    # condition_id = current_user.condition_id
    # print(condition_id)
    # current_condition = db.session.query(OnlineCondition).get(condition_id)
    # num_rounds = len(current_condition.difficulty)

    # completed = []
    # for round in range(num_rounds):
    #     completed.append([])
    #     rule_name = current_condition.difficulty[round]

    #     demo_cards = RULE_PROPS[rule_name]['demo_cards']
    #     num_completed_demos = db.session.query(Demo).filter_by(user_id=current_user.id, round_num=round).count()
    #     if num_completed_demos < len(demo_cards):
    #         completed[round].append(False)
    #     else:
    #         completed[round].append(True)

    #     cards = RULE_PROPS[rule_name]['cards']
    #     num_completed_trials = db.session.query(Trial).filter_by(user_id=current_user.id, round_num=round).count()
    #     if num_completed_trials < len(cards):
    #         completed[round].append(False)
    #     else:
    #         completed[round].append(True)

    #     num_completed_surveys = db.session.query(Survey).filter_by(user_id=current_user.id, round_num=round).count()
    #     if num_completed_surveys < 1:
    #         completed[round].append(False)
    #     else:
    #         completed[round].append(True)
    online_condition_id = current_user.online_condition_id
    current_condition = db.session.query(OnlineCondition).get(online_condition_id)

    completed = True if current_user.study_completed == 1 else False

    loop_conditions = ["cl"]  # cl, pl, open, wt, wtcl
    # rand.shuffle(loop_conditions)
    # domains = ["at", "ct", "sb"]
    domains = ["at", "sb"]
    # domains = ["sb", "at"]
    # rand.shuffle(domains)

    current_user.loop_condition = loop_conditions[0]
    current_user.domain_1 = domains[0]
    current_user.domain_2 = domains[1]
    # current_user.domain_3 = domains[2]
    current_user.final_test_condition = 0
    db.session.commit()

    return render_template("index.html",
                           title="Home Page",
                           completed=completed,
                           code=current_user.code)

@app.route("/introduction", methods=["GET", "POST"])
@login_required
def introduction():
    return render_template("mike/intro.html")

@app.route("/overview", methods=["GET", "POST"])
@login_required
def overview():
    return render_template("mike/overview.html")

@app.route("/sandbox_introduction", methods=["GET", "POST"])
@login_required
def sandbox_introduction():
    return render_template("mike/sandbox_introduction.html")

@socketio.on('make sandbox')
def make_sandbox(data):
    version = data['version']
    print(request.sid)
    print("I am getting called with version: " + str(version))
    # print('received message: ' + data['version'])
    # session_id = request.sid
    # print('session_id is: ' + session_id)
    # print(request.sid)
    if version == 1:
        current_user.set_curr_progress("sandbox_1")
    elif version == 2:
        current_user.set_curr_progress("sandbox_2")
    db.session.commit()
    print("current user progress is: " + current_user.curr_progress)
    socketio.emit('made sandbox', to=request.sid)
    # current_user.set_test_column(812)
    # db.session.commit()
    # curr_room = ""
    # if len(current_user.username) % 2 == 0:
    #     curr_room = "room1"
    # else:
    #     curr_room = "room2"
    # join_room(curr_room)
    # socketio.emit('join event', {"test":current_user.username + "just joined!"}, to=curr_room)

@socketio.on("connect")
def handle_connect():
    print(request.sid + " connected?")

@socketio.on("sandbox settings")
def sandbox_settings(data):
    print(request.sid)
    version = data["version"]
    if version == 1:
        params = {
            'agent': {'x': 4, 'y': 3, 'has_passenger': 0},
            'walls': [{'x': 2, 'y': 3}, {'x': 2, 'y': 2}, {'x': 3, 'y': 2}, {'x': 4, 'y': 2}],
            'passengers': [{'x': 4, 'y': 1, 'dest_x': 1, 'dest_y': 4, 'in_taxi': 0}],
            'hotswap_station': [{'x': 1, 'y': 2}],
            'width': 4,
            'height': 4,
        }
        continue_condition = "free_play"
    elif version == 2:
        params = {
            'agent': {'x': 4, 'y': 1, 'has_passenger': 0},
            'walls': [{'x': 1, 'y': 3}, {'x': 2, 'y': 3}, {'x': 3, 'y': 3}],
            'passengers': [{'x': 1, 'y': 2, 'dest_x': 1, 'dest_y': 4, 'in_taxi': 0}],
            'hotswap_station': [{'x': 2, 'y': 1}],
            'width': 4,
            'height': 4,
        }
        continue_condition = "optimal_traj_1"
    socketio.emit("sandbox configured", {"params": params, "continue_condition": continue_condition}, to=request.sid)


@app.route("/sandbox", methods=["GET", "POST"])
@login_required
def sandbox():
    version = current_user.curr_progress
    print(version)
    if version == "sandbox_1":
        preamble = ("<h1>Free play</h1> <hr/> " + "<h4>A subset of the keys in the table below will be available to control Chip in each game.<br>All game instances that you decide how Chip behaves in will be marked with a <font color='blue'>blue border</font>, like below.</h4><br>" +
        "<h4>Feel free to play around in the game below and get used to the controls.</h4>" +
        "<h4>If you accidentally take a wrong action, you may reset the simulation and start over by pressing 'r'.</h4><br>" +
        "<h4>You can click the continue button whenever you feel ready to move on.</h4><br>" +
        "<h5> As a reminder this game consists of a <b>location</b> (e.g. <img src = 'static/img/star.png' width=\"20\" height=auto />), <b>an object that you can grab and drop</b> (e.g. <img src = 'static/img/pentagon.png' width=\"20\" height=auto />), <b>an object that you can absorb by moving through</b> (e.g. <img src = 'static/img/diamond.png' width=\"20\" height=auto />), and <b>walls </b>that you can't move through (<img src = 'static/img/wall.png' width=\"20\" height=auto />).</h5>")
        # params = {
        #     'agent': {'x': 4, 'y': 3, 'has_passenger': 0},
        #     'walls': [{'x': 2, 'y': 3}, {'x': 2, 'y': 2}, {'x': 3, 'y': 2}, {'x': 4, 'y': 2}],
        #     'passengers': [{'x': 4, 'y': 1, 'dest_x': 1, 'dest_y': 4, 'in_taxi': 0}],
        #     'hotswap_station': [{'x': 1, 'y': 2}],
        #     'width': 4,
        #     'height': 4,
        # }
        legend = ""
        # continue_condition = "free_play"
    elif version == "sandbox_2":
        preamble = ("<h1>Practice game</h1> <hr/> " +
        "<h4>As previously mentioned, the task in this practice game is the following: </h4> <br>" +
        "<table class=\"center\"><tr><th>Task</th><th>Sample sequence</th></tr><tr><td>Dropping off the green pentagon at the purple star</td><td><img src = 'static/img/sandbox_dropoff1.png' width=\"75\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/sandbox_dropoff2.png' width=\"75\" height=auto /></td></tr></table> <br>" +
        "<h4>Each game will consist of <b>actions that change your energy level</b> differently. In this game, the following actions affect your energy:</h4> <br>" +
        "<table class=\"center\"><tr><th>Action</th><th>Sample sequence</th><th>Energy change</th></tr>" +
        "<tr><td>Moving through the orange diamond</td><td><img src = 'static/img/sandbox_diamond1.png' width=\"225\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/sandbox_diamond2.png' width=\"225\" height=auto /> <img src='static/img/arrow.png' width=\"30\" height=auto /><img src ='static/img/sandbox_diamond3.png' width=\"225\" height=auto/> <td><h3><b>+ 3%</b></h3></td></tr>" +
        "<tr><td>Any action that you take (e.g. moving right)</td><td><img src = 'static/img/right1.png' width=\"150\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/right2.png' width=\"150\" height=auto /><td><h3><b>- 1%</b></h3></td></tr></table> <br>" +
        "<h4><b>Grab the green pentagon</b> and <b>drop it off at the purple star</b> with the <b>maximum possible energy remaining</b>. </h4> " +
        "<h5>You should end with 89% energy left (you won't be able to move if energy falls to 0%, but you can reset by pressing 'r'). <u>You will need to successfully complete this practice game to continue on with the study!</u></h5>" +
        "<h5>Note: Since this is practice, we have revealed each actions's effect on Chip's energy and also provide a running counter of Chip's current energy level below.</h5> <br>")
        # params = {
        #     'agent': {'x': 4, 'y': 1, 'has_passenger': 0},
        #     'walls': [{'x': 1, 'y': 3}, {'x': 2, 'y': 3}, {'x': 3, 'y': 3}],
        #     'passengers': [{'x': 1, 'y': 2, 'dest_x': 1, 'dest_y': 4, 'in_taxi': 0}],
        #     'hotswap_station': [{'x': 2, 'y': 1}],
        #     'width': 4,
        #     'height': 4,
        # }
        legend = "<br><br><br><table class=\"center\"><tr><th>Key</th><th>Action</th></tr><tr><td>up/down/left/right arrow keys</td><td>corresponding movement</td></tr><tr><td>g</td><td>grab</td></tr><tr><td>d</td><td>drop</td></tr><tr><td>r</td><td>reset simulation</td></tr></table><br>"
        # continue_condition = "optimal_traj_1"
    # stimulus = '<iframe id = "ifrm" style="border:none;" src="' + source + '" height="550" width="950" title="Iframe Example"></iframe>    '
    res = render_template("mike/sandbox.html", preamble=preamble, legend=legend)
    # print(res)
    return res

@socketio.on("attention check")
def attention_check(data):
    if data["passed"]:
        socketio.emit("attention checked", {"passed": True}, to=request.sid)
        current_user.set_attention_check(1)

        db.session.commit()

@app.route("/post_practice", methods=["GET", "POST"])
@login_required
def post_practice():
    print("I'm in post practice")
    current_user.set_curr_progress("post practice")
    print(current_user.curr_progress)
    db.session.commit()
    # energy change is hidden
    # cl
    # preamble = ("<br><br><h3>Good job on completing the practice game! Let's now head over to the <b>two main games</b> and <b>begin the real study</b>.</h3><br>" +
    #         "<h3>In these games, you will <b>not</b> be told how each action changes Chip's energy level.</h3><br>" +
    #         "For example, note the '???' in the Energy Change column below. <table class=\"center\"><tr><th>Action</th><th>Sample sequence</th><th>Energy change</th></tr><tr><td>Any action that you take (e.g. moving right)</td><td><img src = 'static/img/right1.png' width=\"150\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/right2.png' width=\"150\" height=auto /><td>???</td></tr></table> <br>" +
    #         "<h3>Instead, you will have to <u>figure that out</u> and subsequently the best strategy for completing the task while minimizing Chip's energy loss <u>by observing Chip's demonstrations</u> and <u>testing your knowledge of Chip's behavior!</u></h3><br>" +
    #             "<h3>If you incorrectly predict Chip's behavior on check-in tests in between demonstrations, <u>Chip will give you corrective feedback and provide additional demonstrations and tests</u> to help you learn!</h3><br>" +
    #         "<h4>Finally, <u>you may navigate back to previous interactions</u> (e.g. demonstrations, feedback, etc) to refresh your memory <u>when you're not being tested!</u></h4>")
    # pl, open
    preamble = ("<br><br><h3>Good job on completing the practice game! Let's now head over to the <b>two main games</b> and <b>begin the real study</b>.</h3><br>" +
            "<h3>In these games, you will <b>not</b> be told how each action changes Chip's energy level.</h3><br>" +
            "For example, note the '???' in the Energy Change column below. <table class=\"center\"><tr><th>Action</th><th>Sample sequence</th><th>Energy change</th></tr><tr><td>Any action that you take (e.g. moving right)</td><td><img src = 'static/img/right1.png' width=\"150\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/right2.png' width=\"150\" height=auto /><td>???</td></tr></table> <br>" +
            "<h3>Instead, you will have to <u>figure that out</u> and subsequently the best strategy for completing the task while minimizing Chip's energy loss <u>by observing Chip's demonstrations!</u></h3><br>" +
                "<h4>In between demonstrations, Chip may test your understanding by asking you to predict the best strategy and giving you corrective feedback to help you learn!</h4><br>" +
            "<h4>Finally, <u>you may navigate back to previous interactions</u> (e.g. demonstrations) to refresh your memory <u>when you're not being tested!</u></h4>")

    # energy change is given
    # wtcl
    # preamble = ("<br><br><h3>Good job on completing the practice game! Let's now head over to the <b>two main games</b> and <b>begin the real study</b>.</h3><br>" +
    #         "<h3>In these games, you will be told how each action changes Chip's energy level</h3><br>" +
    #         "For example, note the '- 1%' in the Energy Change column below. <table class=\"center\"><tr><th>Action</th><th>Sample sequence</th><th>Energy change</th></tr><tr><td>Any action that you take (e.g. moving right)</td><td><img src = 'static/img/right1.png' width=\"150\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/right2.png' width=\"150\" height=auto /><td>- 1%</td></tr></table> <br>" +
    #         "<h3>and <u>also be shown demonstrations</u> of the best strategy for completing the task while minimizing Chip's energy loss.</h3><br>" +
    #             "<h3>And if you incorrectly predict Chip's behavior on check-in tests in between demonstrations, <u>Chip will give you corrective feedback and provide additional demonstrations and tests</u> to help you learn!</h3><br>" +
    #         "<h4>Finally, <u>you may navigate back to previous interactions</u> (e.g. demonstrations, feedback, etc) to refresh your memory <u>when you're not being tested!</u></h4>")
    # wt
    # preamble = ("<br><br><h3>Good job on completing the practice game! Let's now head over to the <b>two main games</b> and <b>begin the real study</b>.</h3><br>" +
    #         "<h3>For each of these games, Chip will let you know each action changes Chip's energy level.</h3><br>" +
    #         "For example, note the '- 1%' in the Energy Change column below. <table class=\"center\"><tr><th>Action</th><th>Sample sequence</th><th>Energy change</th></tr><tr><td>Any action that you take (e.g. moving right)</td><td><img src = 'static/img/right1.png' width=\"150\" height=auto /><img src = 'static/img/arrow.png' width=\"30\" height=auto /><img src = 'static/img/right2.png' width=\"150\" height=auto /><td>- 1%</td></tr></table> <br>" +
    #         "<h3>Then you will answer some questions about Chip's teaching and then test your understanding on a number of game instances.</h3><br>")

    return render_template("mike/post_practice.html", preamble=preamble)

@socketio.on("next domain")
def next_domain(data):
    # save any remaining data (from final test) before moving on to the next domain
    if len(data) > 0:
        if data["interaction type"] == "final test":
            # no need to save the pf model during the final tests
            update_pf_model_positions = []
            update_pf_model_weights = []
        else:
            update_pf_model_positions = copy.deepcopy(current_user.pf_model.positions)
            update_pf_model_weights = copy.deepcopy(current_user.pf_model.weights)
        trial = Trial(
            user_id=current_user.id,
            domain=data["domain"],
            interaction_type=data["interaction type"],
            iteration=data["iteration"],
            subiteration=data["subiteration"],
            likert=int(data["survey"]),
            moves=data["user input"]["moves"],
            coordinates=data["user input"]["agent_history_nonoffset"],
            is_opt_response=data["user input"]["opt_response"],
            mdp_parameters=data["user input"]["mdp_parameters"],
            duration_ms=data["user input"]["simulation_rt"],
            human_model_pf_pos=update_pf_model_positions,
            human_model_pf_weights=update_pf_model_weights,
            improvement_short_answer=data["improvement short answer"],
            reward_ft_weights=data["reward_ft_weights"]
        )
        db.session.add(trial)

    print("yassss")
    current_user.interaction_type = "demo"
    current_user.iteration = -1
    current_user.subiteration = 0
    current_user.control_stack = []
    current_user.params_stack = []
    current_user.visited_env_traj_idxs_stack = []
    current_user.final_test_rand_idxs = []
    current_user.pf_model = None
    print(current_user.curr_progress)
    if len(data) > 0:
        print("reward_ft_weights (if relevant): ")
        print(data["reward_ft_weights"])

    if current_user.curr_progress == "post practice":
        print("slayyy")
        current_user.set_curr_progress("domain 1")
        socketio.emit("next domain is", {"domain": current_user.domain_1}, to=request.sid)
    elif current_user.curr_progress == "domain 1":
        current_user.set_curr_progress("domain 2")
        socketio.emit("next domain is", {"domain": current_user.domain_2}, to=request.sid)
    # elif current_user.curr_progress == "domain 2":
    #     current_user.set_curr_progress("domain 3")
    #     socketio.emit("next domain is", {"domain": current_user.domain_3}, to=request.sid)
    # elif current_user.curr_progress == "domain 3":
    #     current_user.set_curr_progress("final survey")
    #     socketio.emit("next domain is", {"domain": "final survey"}, to=request.sid)
    elif current_user.curr_progress == "domain 2":
        current_user.set_curr_progress("final survey")
        socketio.emit("next domain is", {"domain": "final survey"}, to=request.sid)

    db.session.commit()

@app.route("/at_intro", methods=["GET", "POST"])
@login_required
def at_intro():
    return render_template("mike/augmented_taxi2_introduction.html")

@app.route("/at", methods=["GET", "POST"])
@login_required
def at():
    # form = InformativenessForm()
    # if form.validate_on_submit():
    #     # do something, this might not be the best way to structure this lol
    #     db.session.commit()
    return render_template("mike/augmented_taxi2.html")

@app.route("/ct_intro", methods=["GET", "POST"])
@login_required
def ct_intro():
    return render_template("mike/colored_tiles_introduction.html")

@app.route("/ct", methods=["GET", "POST"])
@login_required
def ct():
    return render_template("mike/colored_tiles.html")

@app.route("/sb_intro", methods=["GET", "POST"])
@login_required
def sb_intro():
    return render_template("mike/skateboard2_introduction.html")

@app.route("/sb", methods=["GET", "POST"])
@login_required
def sb():
    return render_template("mike/skateboard2.html")

# takes in state, including user input etc
# and returns params for next state
@socketio.on("settings")
def settings(data):
    loop_cond = current_user.loop_condition
    curr_domain = current_user.curr_progress[-1]
    # print(curr_domain)
    print(current_user.curr_progress)
    domain = ""
    if curr_domain == "1":
        domain = current_user.domain_1
    elif curr_domain == "2":
        domain = current_user.domain_2
    # elif curr_domain == "3":
    #     domain = current_user.domain_3
    it = current_user.interaction_type
    print("CURRENT interaction: {}".format(it))
    iter = current_user.iteration
    subiter = current_user.subiteration
    response = {}

    # hardcoded progressions for all loop conditions
    # REQUIRES: the params to be in a demo array, diagnostic test array, and final test array
    # indexable, and in the order of presentation to the user

    progression = {
        "debug": {
            "at": [["demo", -1], ["demo", 0],
                   ["final test",  0], ["final test", 1]],
            "ct": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1]],
            "sb": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1]]
            # "at": [["demo", -1], ["demo", 0], ["survey", 0]],
            # "ct": [["demo", -1], ["demo", 0], ["survey", 0]],
            # "sb": [["demo", -1], ["demo", 0], ["survey", 0]]
            # "at": [["demo", -1], ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
            #        ["final test", 5]],
            # "ct": [["demo", -1], ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
            #        ["final test", 5]],
            # "sb": [["demo", -1], ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
            #        ["final test", 5]]
        },
        "open": {
            "at": [["demo", -1], ["demo", 0], ["demo", 1], ["demo", 2], ["demo", 3], ["demo", 4], ["demo", 5], ["demo", 6], ["demo", 7], ["demo", 8], ["demo", 9],
                   ["demo", 10],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "ct": [["demo", -1], ["demo", 0], ["demo", 1], ["demo", 2], ["demo", 3], ["demo", 4],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "sb": [["demo", -1], ["demo", 0], ["demo", 1], ["demo", 2], ["demo", 3], ["demo", 4], ["demo", 5], ["demo", 6], ["demo", 7], ["demo", 8], ["demo", 9],
                   ["demo", 10], ["demo", 11], ["demo", 12], ["demo", 13], ["demo", 14], ["demo", 15], ["demo", 16], ["demo", 17], ["demo", 18], ["demo", 19], ["demo", 20], ["demo", 21],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]]
        },
        "pl": {
            "at": [["demo", -1], ["demo", 0], ["demo", 1], ["diagnostic test", 0], ["diagnostic feedback", 0],
                   ["demo", 2], ["demo", 3], ["demo", 4], ["diagnostic test", 1], ["diagnostic feedback", 1], ["diagnostic test", 2], ["diagnostic feedback", 2],
                   ["demo", 5], ["demo", 6], ["diagnostic test", 3], ["diagnostic feedback", 3],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "ct": [["demo", -1], ["demo", 0], ["demo", 1], ["diagnostic test", 0], ["diagnostic feedback", 0], ["diagnostic test", 1], ["diagnostic feedback", 1],
                   ["demo", 2], ["demo", 3], ["diagnostic test", 2], ["diagnostic feedback", 2], ["diagnostic test", 3], ["diagnostic feedback", 3],
                   ["demo", 4], ["diagnostic test", 4], ["diagnostic feedback", 4],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "sb": [["demo", -1], ["demo", 0], ["demo", 1], ["demo", 2], ["demo", 3], ["diagnostic test", 0], ["diagnostic feedback", 0], ["diagnostic test", 1], ["diagnostic feedback", 1],
                   ["demo", 4], ["demo", 5], ["demo", 6], ["demo", 7], ["diagnostic test", 2], ["diagnostic feedback", 2], ["diagnostic test", 3], ["diagnostic feedback", 3],
                   ["demo", 8], ["demo", 9], ["demo", 10], ["demo", 11], ["demo", 12], ["demo", 13], ["demo", 14], ["diagnostic test", 4], ["diagnostic feedback", 4], ["diagnostic test", 5], ["diagnostic feedback", 5], ["diagnostic test", 6], ["diagnostic feedback", 6],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]]
        },
        "cl": {
            "at": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1], ["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["demo", 4],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "ct": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1],["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["demo", 4],
                   ["diagnostic test", 4], ["diagnostic feedback", 4], ["remedial demo", 4],
                   ["remedial test", 4, 0], ["remedial feedback", 4, 0],
                   ["remedial test", 4, 1], ["remedial feedback", 4, 1],
                   ["remedial test", 4, 2], ["remedial feedback", 4, 2],
                   ["remedial test", 4, 3], ["remedial feedback", 4, 3],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]],
            "sb": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1], ["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["demo", 4], ["demo", 5], ["demo", 6],
                   ["diagnostic test", 4], ["diagnostic feedback", 4], ["remedial demo", 4],
                   ["remedial test", 4, 0], ["remedial feedback", 4, 0],
                   ["remedial test", 4, 1], ["remedial feedback", 4, 1],
                   ["remedial test", 4, 2], ["remedial feedback", 4, 2],
                   ["remedial test", 4, 3], ["remedial feedback", 4, 3],
                   ["diagnostic test", 5], ["diagnostic feedback", 5], ["remedial demo", 5],
                   ["remedial test", 5, 0], ["remedial feedback", 5, 0],
                   ["remedial test", 5, 1], ["remedial feedback", 5, 1],
                   ["remedial test", 5, 2], ["remedial feedback", 5, 2],
                   ["remedial test", 5, 3], ["remedial feedback", 5, 3],
                   ["diagnostic test", 6], ["diagnostic feedback", 6], ["remedial demo", 6],
                   ["remedial test", 6, 0], ["remedial feedback", 6, 0],
                   ["remedial test", 6, 1], ["remedial feedback", 6, 1],
                   ["remedial test", 6, 2], ["remedial feedback", 6, 2],
                   ["remedial test", 6, 3], ["remedial feedback", 6, 3],
                   ["survey", 0],
                   ["final test",  0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4], ["final test", 5]]
        },
        "wtcl": {
            "at": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1], ["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["demo", 4],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]],
            "ct": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1], ["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["demo", 4],
                   ["diagnostic test", 4], ["diagnostic feedback", 4], ["remedial demo", 4],
                   ["remedial test", 4, 0], ["remedial feedback", 4, 0],
                   ["remedial test", 4, 1], ["remedial feedback", 4, 1],
                   ["remedial test", 4, 2], ["remedial feedback", 4, 2],
                   ["remedial test", 4, 3], ["remedial feedback", 4, 3],
                   ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]],
            "sb": [["demo", -1], ["demo", 0], ["demo", 1],
                   ["diagnostic test", 0], ["diagnostic feedback", 0], ["remedial demo", 0],
                   ["remedial test", 0, 0], ["remedial feedback", 0, 0],
                   ["remedial test", 0, 1], ["remedial feedback", 0, 1],
                   ["remedial test", 0, 2], ["remedial feedback", 0, 2],
                   ["remedial test", 0, 3], ["remedial feedback", 0, 3],
                   ["diagnostic test", 1], ["diagnostic feedback", 1], ["remedial demo", 1],
                   ["remedial test", 1, 0], ["remedial feedback", 1, 0],
                   ["remedial test", 1, 1], ["remedial feedback", 1, 1],
                   ["remedial test", 1, 2], ["remedial feedback", 1, 2],
                   ["remedial test", 1, 3], ["remedial feedback", 1, 3],
                   ["demo", 2], ["demo", 3],
                   ["diagnostic test", 2], ["diagnostic feedback", 2], ["remedial demo", 2],
                   ["remedial test", 2, 0], ["remedial feedback", 2, 0],
                   ["remedial test", 2, 1], ["remedial feedback", 2, 1],
                   ["remedial test", 2, 2], ["remedial feedback", 2, 2],
                   ["remedial test", 2, 3], ["remedial feedback", 2, 3],
                   ["diagnostic test", 3], ["diagnostic feedback", 3], ["remedial demo", 3],
                   ["remedial test", 3, 0], ["remedial feedback", 3, 0],
                   ["remedial test", 3, 1], ["remedial feedback", 3, 1],
                   ["remedial test", 3, 2], ["remedial feedback", 3, 2],
                   ["remedial test", 3, 3], ["remedial feedback", 3, 3],
                   ["demo", 4], ["demo", 5], ["demo", 6],
                   ["diagnostic test", 4], ["diagnostic feedback", 4], ["remedial demo", 4],
                   ["remedial test", 4, 0], ["remedial feedback", 4, 0],
                   ["remedial test", 4, 1], ["remedial feedback", 4, 1],
                   ["remedial test", 4, 2], ["remedial feedback", 4, 2],
                   ["remedial test", 4, 3], ["remedial feedback", 4, 3],
                   ["diagnostic test", 5], ["diagnostic feedback", 5], ["remedial demo", 5],
                   ["remedial test", 5, 0], ["remedial feedback", 5, 0],
                   ["remedial test", 5, 1], ["remedial feedback", 5, 1],
                   ["remedial test", 5, 2], ["remedial feedback", 5, 2],
                   ["remedial test", 5, 3], ["remedial feedback", 5, 3],
                   ["diagnostic test", 6], ["diagnostic feedback", 6], ["remedial demo", 6],
                   ["remedial test", 6, 0], ["remedial feedback", 6, 0],
                   ["remedial test", 6, 1], ["remedial feedback", 6, 1],
                   ["remedial test", 6, 2], ["remedial feedback", 6, 2],
                   ["remedial test", 6, 3], ["remedial feedback", 6, 3],
                   ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]]
        },
        "wt": {
            "at": [["demo", -1], ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]],
            "ct": [["demo", -1], ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]],
            "sb": [["demo", -1], ["survey", 0],
                   ["final test", 0], ["final test", 1], ["final test", 2], ["final test", 3], ["final test", 4],
                   ["final test", 5]]
        }
    }
    print(loop_cond)
    print(domain)

    if domain == "at":
        domain_key = "augmented_taxi2"
    elif domain == "ct":
        domain_key = "colored_tiles"
    else:
        domain_key = "skateboard2"

    constraints = []
    prev_already_completed = data["already completed"]

    # save interaction data from the most recent page and consider updating the particle filter human model
    # only consider updating the particle filter following the first interaction, if it's a new page, and the person didn't go backward to a previous interaction
    if it == "survey":
        dom = Domain(
            user_id=current_user.id,
            domain=domain,
            attn1=int(data["attn1"]),
            attn2=int(data["attn2"]),
            attn3=int(data["attn3"]),
            use1=int(data["use1"]),
            use2=int(data["use2"]),
            use3=int(data["use3"]),
            understanding=int(data["understanding"]),
            engagement_short_answer=data["engagement short answer"]
        )
        db.session.add(dom)
        print(data["attn1"])
        print(data["attn2"])
        print(data["attn3"])
        print(data["use1"])
        print(data["use2"])
        print(data["use3"])
        print(data["understanding"])
        print(data["engagement short answer"])
    elif iter != -1 and prev_already_completed == "false" and data['movement'] != 'prev':
        # update particle filter
        update_pf = False

        if ('demo' in it):
            update_pf = True
            constraints = [np.array(c) for c in data["user input"]["mdp_parameters"]["constraints"]]
        elif ('test' in it) and ('final' not in it):
            update_pf = True
            if data["user input"]["opt_response"]:
                # person got the test right
                constraints = [np.array(c) for c in data["user input"]["mdp_parameters"]["constraints"]]
            else:
                # person got the test wrong
                # todo: Mike uncomment for remedial demos and tests
                policy_constraints, min_subset_constraints_record, env_record, traj_record, traj_features_record, reward_record, mdp_features_record, consistent_state_count = domain_background_vars[domain_key]
                prev_mdp_parameters = data['user input']['mdp_parameters']

                # store the moves input by the human in previous game
                prev_mdp_parameters['human_actions'] = data["user input"]["moves"]

                best_env_idx, best_traj_idx = prev_mdp_parameters['env_traj_idxs']
                opt_traj = traj_record[best_env_idx][best_traj_idx]
                opt_traj_features = traj_features_record[best_env_idx][best_traj_idx]

                # obtain the constraint that the participant failed to demonstrate
                constraint = obtain_constraint(domain_key, prev_mdp_parameters, opt_traj, opt_traj_features)
                constraints = [-constraint]
                # constraints = [np.array([[0, 0, -1]])] # dummy constraint
        # todo: Mike uncomment for remedial demos and tests
        if update_pf:
            if current_user.pf_model is None:
                particle_positions = BEC_helpers.sample_human_models_uniform([], params.BEC['n_particles'])
                particles = pf.Particles(particle_positions)
                particles.update(params.prior)
                particles.update(constraints)
                current_user.pf_model = particles
                # BEC_viz.visualize_pf_transition(constraints, particles, domain_key)
            else:
                particles = current_user.pf_model
                particles.update(constraints)
                current_user.pf_model = particles
                # BEC_viz.visualize_pf_transition(constraints, particles, domain_key)

            print("Updated PF with constraints: {}".format(constraints))

            # update the visited_env_traj_idxs_stack with the env_traj indices of the most recent interaction
            current_user.visited_env_traj_idxs_stack.append(data['user input']['mdp_parameters']['env_traj_idxs'])

        if data["interaction type"] == "final test":
            # no need to save the pf model during the final tests
            update_pf_model_positions = []
            update_pf_model_weights = []
        else:
            update_pf_model_positions = copy.deepcopy(current_user.pf_model.positions)
            update_pf_model_weights = copy.deepcopy(current_user.pf_model.weights)

        trial = Trial(
            user_id = current_user.id,
            domain = domain,
            interaction_type = it,
            iteration = iter,
            subiteration = subiter,
            likert = int(data["survey"]),
            moves = data["user input"]["moves"],
            coordinates = data["user input"]["agent_history_nonoffset"],
            is_opt_response = data["user input"]["opt_response"],
            mdp_parameters = data["user input"]["mdp_parameters"],
            duration_ms = data["user input"]["simulation_rt"],
            human_model_pf_pos = update_pf_model_positions,
            human_model_pf_weights = update_pf_model_weights,
            improvement_short_answer = data["improvement short answer"],
            reward_ft_weights=data["reward_ft_weights"]
        )
        print("improvement: ")
        print(data["improvement short answer"])
        db.session.add(trial)

        # pop the params from the params_stack once you've saved it
        current_user.params_stack.pop()
        print("popped from params stack")

    # need some cases
    # if survey completed, then push to the stack
    # if movement is prev,
        # if key in ctrl stack, then get the prev idx
        # if not, then get the -1 idx item
    # if movement is next,
        # search ctrl stack for the current key,

    key = [it, iter, subiter]
    last_test = False

    if key not in current_user.control_stack:
        current_user.stack_push(key)

    # determine which params to provide to the next page
    if data["movement"] == "prev":
        # if the user pressed prev, you can simply use params that was previously saved
        old_idx = current_user.control_stack.index(key)
        new_idx = old_idx - 1
        current_user.interaction_type = current_user.control_stack[new_idx][0]
        current_user.iteration = current_user.control_stack[new_idx][1]
        current_user.subiteration = current_user.control_stack[new_idx][2]
        current_user.curr_trial_idx = new_idx
        old_trials = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                        domain=domain,
                                                        interaction_type=current_user.interaction_type,
                                                        iteration=current_user.iteration,
                                                        subiteration=current_user.subiteration).all()
        params_list = [trial.mdp_parameters for trial in old_trials]
        response["params"] = params_list[0]
    elif data["movement"] == "next":
        # if the user pressed next, you'll have to determined whether you can still use previously saved params or generate new ones

        arr = progression[loop_cond][domain]
        if (it == "remedial test") or (it == "remedial feedback"):
            idx = arr.index([it, iter, subiter])
        else:
            idx = arr.index([it, iter])

        # taking care of next progs
        # here is a nice little jump table
        if idx == len(arr) - 2:
            last_test = True

        # a) get new control key
        control_stack_idx = current_user.control_stack.index([it, iter, subiter])
        if control_stack_idx < len(current_user.control_stack) - 1:
            # if there's a key ahead of you, use it
            current_user.interaction_type = current_user.control_stack[control_stack_idx + 1][0]
            current_user.iteration = current_user.control_stack[control_stack_idx + 1][1]
            current_user.subiteration = current_user.control_stack[control_stack_idx + 1][2]
        else:
            # otherwise, find the next key

            # REQUIRES: domain and loop condition are the same throughout this function
            # it, iter, and subiter are the old versions
            # current_user.{interaction_type, iteration, subiteration} are the new versions
            if loop_cond == "open" or loop_cond == "debug" or loop_cond == "wt":
                current_user.interaction_type = arr[idx + 1][0]
                current_user.iteration = arr[idx + 1][1]
            elif loop_cond == "pl":
                # skip the remedial demos and tests if the human answers correctly or if it's a rerun of a test (i.e. tag = -1)
                if it == "diagnostic test" and data["user input"]["opt_response"] and (data["user input"]["mdp_parameters"]['tag'] != -1):
                    current_user.interaction_type = arr[idx + 2][0]
                    current_user.iteration = arr[idx + 2][1]
                else:
                    current_user.interaction_type = arr[idx + 1][0]
                    current_user.iteration = arr[idx + 1][1]
            elif loop_cond == "cl" or loop_cond == "wtcl":
                # skip the remedial demos and tests if the human answers correctly or if it's a rerun of a test (i.e. tag = -1)
                if it == "diagnostic test" and data["user input"]["opt_response"] and (data["user input"]["mdp_parameters"]['tag'] != -1):
                    # move to next demo from next unit
                    current_user.interaction_type = arr[idx + 11][0]
                    current_user.iteration = arr[idx + 11][1]
                elif it == "remedial test" and data["user input"]["opt_response"] and (data["user input"]["mdp_parameters"]['tag'] != -1):
                    # move to next demo from next unit
                    jump = 2 * (4 - subiter)
                    current_user.interaction_type = arr[idx + jump][0]
                    current_user.iteration = arr[idx + jump][1]
                    current_user.subiteration = 0
                else:
                    # move to remedial feedback
                    current_user.interaction_type = arr[idx + 1][0]
                    current_user.iteration = arr[idx + 1][1]
                    if current_user.interaction_type == "remedial test" or current_user.interaction_type == "remedial feedback":
                        current_user.subiteration = arr[idx + 1][2]
                    else:
                        current_user.subiteration = 0

        # b) get new params
        num_times_completed = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                                domain=domain,
                                                                interaction_type=current_user.interaction_type,
                                                                iteration=current_user.iteration,
                                                                subiteration=current_user.subiteration).count()
        num_times_unfinished = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                                 domain=domain,
                                                                 interaction_type=current_user.interaction_type,
                                                                 iteration=current_user.iteration,
                                                                 subiteration=current_user.subiteration,
                                                                 likert=-1).count()
        num_times_finished = num_times_completed - num_times_unfinished
        print("num of times finished: {}".format(num_times_finished))

        if num_times_finished > 0:
            # if you've seen this page before, simply get the associated params from the database
            old_trials = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                           domain=domain,
                                                           interaction_type=current_user.interaction_type,
                                                           iteration=current_user.iteration,
                                                           subiteration=current_user.subiteration).all()
            params_list = [trial.mdp_parameters for trial in old_trials]
            response["params"] = params_list[0]
        else:
            if len(current_user.params_stack) > 0:
                # if there's still params on the stack (which hasn't been committed to the database yet), use it
                print("pulling from params stack")
                response["params"] = current_user.params_stack[-1]
            else:
                # otherwise, you'll have to obtain new params
                print("getting new params")
                response["params"] = {}

                print(current_user.interaction_type)
                print(current_user.iteration)
                if loop_cond != "debug":
                    if current_user.interaction_type == "final test":
                        # randomize the order of the tests (todo: potentially account for train_test_set (currently only using the first set))
                        if len(current_user.final_test_rand_idxs) == 0:
                            current_user.final_test_rand_idxs = list(np.arange(6))
                            np.random.shuffle(current_user.final_test_rand_idxs)
                            final_test_idx = current_user.final_test_rand_idxs.pop()
                        else:
                            final_test_idx = current_user.final_test_rand_idxs.pop()
                        print("final_text_idx: {}".format(final_test_idx))
                        if final_test_idx < 2:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["low"][current_user.final_test_condition][final_test_idx]
                        elif final_test_idx < 4:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["medium"][current_user.final_test_condition][final_test_idx - 2]
                        else:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["high"][current_user.final_test_condition][final_test_idx - 4]
                    elif current_user.interaction_type == "diagnostic feedback" or current_user.interaction_type == "remedial feedback":
                        # normalize the actions of the optimal and (incorrect) human trajectory such that they're the same length
                        # (by causing the longer trajectory to wait at overlapping states)
                        opt_actions = data['user input']['mdp_parameters']['opt_actions']
                        opt_locations = data['user input']['mdp_parameters']['opt_locations']
                        opt_locations_tuple = [tuple(opt_location) for opt_location in opt_locations]

                        human_actions = data["user input"]["moves"]
                        human_locations = data["user input"]["agent_history_nonoffset"]
                        if domain == 'at':
                            human_locations_tuple = [(human_location[0], human_location[1], int(human_location[2])) for
                                                     human_location in human_locations]
                        else:
                            human_locations_tuple = [(human_location[0], human_location[1]) for
                                                     human_location in human_locations]

                        normalized_opt_actions, normalized_human_actions = normalize_trajectories(opt_locations_tuple, opt_actions, human_locations_tuple, human_actions)
                        print(normalized_opt_actions)
                        print(normalized_human_actions)

                        # update the relevant mdp_parameter with the normalized versions of the trajectories
                        updated_data = data['user input']['mdp_parameters'].copy()
                        updated_data['normalized_opt_actions'] = normalized_opt_actions
                        updated_data['normalized_human_actions'] = normalized_human_actions
                        updated_data['tag'] = -2 # indicate that this is trajectory visualization
                        updated_data['human_actions'] = human_actions
                        response["params"] = updated_data
                    elif current_user.interaction_type == "remedial demo" or current_user.interaction_type == "remedial test":
                        # todo: Mike uncomment for remedial demos and tests
                        policy_constraints, min_subset_constraints_record, env_record, traj_record, traj_features_record, reward_record, mdp_features_record, consistent_state_count = domain_background_vars[domain_key]
                        prev_mdp_parameters = data['user input']['mdp_parameters']
                        # print(prev_mdp_parameters)
                        variable_filter = np.array(prev_mdp_parameters['variable_filter'])

                        if current_user.interaction_type == "remedial test" and current_user.subiteration == 0:
                            # the first remedial test will follow a remedial demonstration, which can piggyback off the remedial demonstration's constraint
                            constraint = np.array(data['user input']['mdp_parameters']['constraints'][0])
                        else:
                            best_env_idx, best_traj_idx = prev_mdp_parameters['env_traj_idxs']
                            opt_traj = traj_record[best_env_idx][best_traj_idx]
                            opt_traj_features = traj_features_record[best_env_idx][best_traj_idx]

                            # obtain the constraint that the participant failed to demonstrate
                            constraint = obtain_constraint(domain_key, prev_mdp_parameters, opt_traj, opt_traj_features)
                        print("this constraint: {}".format(constraint))

                        if current_user.interaction_type == "remedial demo": type = 'training'
                        else: type = 'testing'

                        particles = current_user.pf_model

                        # send in a copy of the visited_env_traj_idxs_stack so that it doesn't get modified
                        remedial_mdp_dict, visited_env_traj_idxs = obtain_remedial_demonstrations(domain_key, pool, particles, params.BEC['n_human_models'], constraint,
                        min_subset_constraints_record, env_record, traj_record, traj_features_record, [], current_user.visited_env_traj_idxs_stack.copy(), variable_filter, mdp_features_record, consistent_state_count, [],
                        params.step_cost_flag, type=type, n_human_models_precomputed=params.BEC['n_human_models_precomputed'], web_based=True)

                        response["params"] = remedial_mdp_dict

                        # dummy params
                        # if current_user.interaction_type == "remedial demo": response["params"] = jsons[domain_key]['demo'][str(0)]
                        # else: response["params"] = jsons[domain_key]['diagnostic test'][str(0)]
                    elif current_user.interaction_type != "survey":
                        if current_user.interaction_type == "demo":
                            if loop_cond == "open":
                                response["params"] = jsons["open"][domain_key][current_user.interaction_type][
                                    str(current_user.iteration)]
                            elif loop_cond == "pl":
                                response["params"] = jsons["pl"][domain_key][current_user.interaction_type][
                                    str(current_user.iteration)]
                            else:
                                response["params"] = jsons[domain_key][current_user.interaction_type][
                                    str(current_user.iteration)]
                        else:
                            response["params"] = jsons[domain_key][current_user.interaction_type][
                                str(current_user.iteration)]
                else:
                    # the code below is for debugging
                    if "test" in current_user.interaction_type:
                        if len(current_user.final_test_rand_idxs) == 0:
                            current_user.final_test_rand_idxs = list(np.arange(6))
                            np.random.shuffle(current_user.final_test_rand_idxs)
                            final_test_idx = current_user.final_test_rand_idxs.pop()
                        else:
                            final_test_idx = current_user.final_test_rand_idxs.pop()
                        print("final_text_idx: {}".format(final_test_idx))
                        if final_test_idx < 2:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["low"][current_user.final_test_condition][
                                final_test_idx]
                        elif final_test_idx < 4:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["medium"][current_user.final_test_condition][
                                final_test_idx - 2]
                        else:
                            response["params"] = jsons[domain_key][current_user.interaction_type]["high"][current_user.final_test_condition][
                                final_test_idx - 4]
                    else:
                        response["params"] = jsons[domain_key]["demo"]["0"]

                if current_user.interaction_type != "survey":
                    # add the newly obtained params to the stack (in case the user goes back to another page before committing it to the database)
                    current_user.params_stack.append(response["params"])
                    print("adding to params stack")

    already_completed = "false"

    if current_user.interaction_type != "survey":
        num_times_completed = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                            domain=domain,
                                                            interaction_type=current_user.interaction_type,
                                                            iteration=current_user.iteration,
                                                            subiteration=current_user.subiteration).count()
        num_times_unfinished = db.session.query(Trial).filter_by(user_id=current_user.id,
                                                            domain=domain,
                                                            interaction_type=current_user.interaction_type,
                                                            iteration=current_user.iteration,
                                                            subiteration=current_user.subiteration,
                                                            likert=-1).count()
        num_times_finished = num_times_completed - num_times_unfinished

        print("num of times finished: {}".format(num_times_finished))
        if num_times_finished > 0:
            already_completed = "true"
            if 'test' in current_user.interaction_type:
                # if you've already been to this test page, you should simply show the optimal trajectory
                response["params"]["tag"] = -1

    go_prev = "true"
    # cl, pl, open, wtcl
    if (current_user.iteration == 0 and current_user.interaction_type == "demo") or ("test" in current_user.interaction_type and already_completed == "false"):
        go_prev = "false"

    # wt
    # if (current_user.iteration == 0 and current_user.interaction_type == "demo") or ("test" in current_user.interaction_type and already_completed == "false") or current_user.interaction_type == "survey":
    #     go_prev = "false"

    # debug_string = f"domain={domain}, interaction type={current_user.interaction_type}, iteration={current_user.iteration}, subiteration={current_user.subiteration}"
    debug_string = ''
    response["debug string"] = debug_string
    response["username"] = current_user.username
    response["last test"] = last_test
    response["interaction type"] = current_user.interaction_type
    response["already completed"] = already_completed
    response["go prev"] = go_prev
    response["domain"] = domain
    response["iteration"] = current_user.iteration
    response["subiteration"] = current_user.subiteration
    if domain == "at":
        if loop_cond == "open":
            response["demo total"] = 11
        elif loop_cond == "pl":
            response["demo total"] = 7
        else:
            response["demo total"] = 5
    elif domain == "sb":
        if loop_cond == "open":
            response["demo total"] = 22
        elif loop_cond == "pl":
            response["demo total"] = 15
        else:
            response["demo total"] = 7
    else:
        # for colored tiles
        response["demo total"] = 5
    db.session.commit()
    socketio.emit("settings configured", response, to=request.sid)






# # takes in state, including interaction type and user input etc
# # and returns params for next state
# @socketio.on("settings")
# def settings(data):
    # # first we want to case on our interaction type
    # response = {}
    # it = data["interaction type"]
    # if it == "demo":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["0"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["0"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["0"]

    # elif it == "diagnostic test":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["1"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["1"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["1"]

    # elif it == "diagnostic feedback":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["0"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["0"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["0"]

    # elif it == "remedial demo":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["0"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["0"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["0"]

    # elif it == "remedial test":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["1"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["1"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["1"]

    # elif it == "remedial feedback":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["0"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["0"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["0"]

    # elif it == "final test":
    #     if data["domain"] == "at":
    #         response["params"] = jsons["augmented_taxi2"]["1"]
    #     elif data["domain"] == "ct":
    #         response["params"] = jsons["colored_tiles"]["1"]
    #     elif data["domain"] == "sb":
    #         response["params"] = jsons["skateboard2"]["1"]

    # socketio.emit("settings configured", response, to=request.sid)

@app.route("/sign_consent", methods=["GET", "POST"])
@login_required
def sign_consent():
    current_user.consent = 1
    db.session.commit()
    # need to return json since this function is called on button press
    # which replaces the current url with new url
    # sorry trying to work within existing infra
    return {"url":url_for("introduction")}

@app.route("/pass_trajectories", methods=["GET", "POST"])
@login_required
def pass_trajectories():
    final_data = request.get_json()
    print(final_data)
    return json.dumps(send_signal(final_data["opt_response"]))

@socketio.on('join room')
def handle_message():
    # print('received message: ' + data['data'])
    # session_id = request.sid
    # print('session_id is: ' + session_id)
    print(request.sid)
    if current_user.username[0] == "a":
        current_user.group = "room1"
    else:
        current_user.group = "room2"
    # socketio.emit('ping event', {'test': 'sending to client'}, to=request.sid)
    # current_user.set_test_column(812)

    # curr_room = ""
    # if len(current_user.username) % 2 == 0:
    #     curr_room = "room1"
    # else:
    #     curr_room = "room2"
    join_room(current_user.group)
    db.session.commit()
    # socketio.emit('join event', {"test":current_user.username + "just joined!"}, to=curr_room)

@socketio.on("group comm")
def group_comm(data):
    data["user"] = current_user.username
    socketio.emit("incoming group data", data, to=current_user.group, include_self=False)

@app.route("/intro", methods=["GET", "POST"])
@login_required
def intro():
    print(send_signal(True))
    # form = LoginForm()
    # if form.validate_on_submit():
    #     user = User.query.filter_by(username=form.username.data).first()
    #
    #     if user is None:
    #         user = User(username=form.username.data)
    #         user.set_num_trials_completed(0)
    #         user.set_completion(0)
    #         user.set_attention_check(-1)
    #
    #         # Change depending on the study type.
    #         cond = user.set_condition("in_person" if IS_IN_PERSON else "online")
    #         code = user.set_code()
    #
    #         db.session.add(user)
    #
    #         cond.users.append(user)
    #         cond.count += 1
    #
    #         db.session.commit()
    #
    #     login_user(user)
    #     next_page = request.args.get("next")
    #     if not next_page or url_parse(next_page).netloc != "":
    #         next_page = url_for("index")
    #     return redirect(next_page)
    #
    # render_template("login.html", title="Sign In", form=form)

    # just testing out my code
    # return render_template("intro.html")
    return render_template("augmented_taxi2.html")


@app.route("/consent", methods=["GET", "POST"])
@login_required
def consent():
    form = ConsentForm()
    # if current_user.consent:
    #     # flash("Consent completed!")
    #     online_condition_id = current_user.online_condition_id
    #     current_condition = db.session.query(OnlineCondition).get(online_condition_id)

    #     if current_user.num_trials_completed < (len(current_condition.trials)):
    #         return redirect(url_for("intro")) # verifying url_for and displaying training/testing simulations
    #         # return redirect(url_for("test"))
    #     return redirect(url_for("survey"))

    # else:
    if IS_IN_PERSON:
        procedure = "This study may take up to 90 minutes, and audio/screen recordings will be collected."
    else:
        procedure = "Most people complete the study within 30 minutes."
    return render_template("consent.html", title="Consent", form=form, procedure=procedure)

# @app.route("/training", methods=["GET", "POST"])
# @login_required
# def training():
#     form = TrainingForm()
#     if form.validate_on_submit():
#         current_user.training = 1
#         db.session.commit()
#         redirect(url_for("demos", round=0))
#     if current_user.training:
#         # flash("Training already completed!")
#         return redirect(url_for("demos", round=0))
#     elif not current_user.consent:
#         # flash("Consent not yet completed!")
#         return redirect(url_for("consent"))
#     else:
#         return render_template("training.html", title="Training", form=form)

# @app.route("/demos/<int:round>", methods=["GET", "POST"])
# @login_required
# def demos(round):
#     # form = DemoForm()

#     # num_completed_demos = db.session.query(Demo).filter_by(user_id=current_user.id, round_num=round).count()

#     # condition_id = current_user.condition_id
#     # current_condition = db.session.query(Condition).get(condition_id)
#     # rule_name = current_condition.difficulty[round]
#     # rule = RULE_PROPS[rule_name]['rule']
#     # demo_cards = RULE_PROPS[rule_name]['demo_cards']
#     # demo_answers = RULE_PROPS[rule_name]['demo_answers']

#     # previous_cards = [[], []]
#     # for ii in range(num_completed_demos):
#     #     if demo_answers[ii] == 0:
#     #         previous_cards[0].append(demo_cards[ii])
#     #     if demo_answers[ii] == 1:
#     #         previous_cards[1].append(demo_cards[ii])

#     # if form.validate_on_submit():
#     #     demo = Demo(author=current_user,
#     #                 demo_num=num_completed_demos + 1,
#     #                 round_num=round,
#     #                 card_num=demo_cards[num_completed_demos],
#     #                 correct_bin=demo_answers[num_completed_demos],
#     #                 rule_set=rule)
#     #     db.session.add(demo)
#     #     db.session.commit()
#     #     return redirect(url_for('demos', round=round))

#     # if num_completed_demos == len(demo_cards):
#     #     return redirect(url_for("trials",round=round))

#     #Check if previous thing is done

#     #If first round, training must be done
#     # if (round == 0) and (not current_user.training):
#         return redirect(url_for("consent"))

#     #If not first round, previous survey must be done
#     # if round > 0:
#     #     check_previous_surveys = db.session.query(Survey).filter_by(user_id=current_user.id, round_num=round-1).count()
#     #     if check_previous_surveys < 1:
#     #         return redirect(url_for("consent"))

#     #Pick the video to play
#     # feedback_counts = current_user.feedback_counts
#     # cur_names = []
#     # cur_counts = []
#     # for vid_name in NEUTRAL:
#     #     cur_names.append(vid_name)
#     #     cur_counts.append(feedback_counts[vid_name])
#     # cur_counts = np.array(cur_counts)
#     # if np.sum(cur_counts) == 0:
#     #     p = np.ones_like(cur_counts)/np.sum(np.ones_like(cur_counts))
#     # else:
#     #     p= 1 - cur_counts/np.sum(cur_counts)
#     # for ii in range(len(p)):
#     #     if p[ii] < 0.05:
#     #         p[ii] = 0.05
#     # p = p / np.sum(p)
#     # vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p= p)
#     # vid_name = cur_names[vid_choice]

#     # new_feedback_counts = {}
#     # for new_vid_name in VIDEO_LIST:
#     #     if new_vid_name == vid_name:
#     #         new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name] + 1
#     #     else:
#     #         new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name]

#     # current_user.feedback_counts = new_feedback_counts
#     # db.session.commit()

#     #Render the next demonstration
#     return render_template("demos.html",
#         title="Demonstrations",
#         form=form,
#         num_bins=len(rule),
#         card=demo_cards[num_completed_demos],
#         correct_bin=demo_answers[num_completed_demos],
#         num_completed_demos=num_completed_demos + 1,
#         num_demos=len(demo_cards),
#         previous_cards=previous_cards,
#         round=round,
#         vid_name=vid_name)

# @app.route("/trials/<int:round>", methods=["GET", "POST"])
# @login_required
# def trials(round):
#     start_time = datetime.now().utcnow().isoformat()
#     form = TrialForm(start_time=start_time)

#     num_completed_trials = db.session.query(Trial).filter_by(user_id=current_user.id, round_num=round).count()

#     condition_id = current_user.condition_id
#     current_condition = db.session.query(Condition).get(condition_id)
#     rule_name = current_condition.difficulty[round]
#     rule = RULE_PROPS[rule_name]['rule']
#     demo_cards = RULE_PROPS[rule_name]['demo_cards']
#     cards = RULE_PROPS[rule_name]['cards']
#     answers = RULE_PROPS[rule_name]['answers']
#     demo_answers = RULE_PROPS[rule_name]['demo_answers']

#     previous_cards = [[], []]
#     for ii in range(len(demo_cards)):
#         if demo_answers[ii] == 0:
#             previous_cards[0].append(demo_cards[ii])
#         if demo_answers[ii] == 1:
#             previous_cards[1].append(demo_cards[ii])

#     for ii in range(num_completed_trials):
#         if answers[ii] == 0:
#             previous_cards[0].append(cards[ii])
#         if answers[ii] == 1:
#             previous_cards[1].append(cards[ii])

#     if form.validate_on_submit():
#         chosen_bin = int(form.chosen_bin.data[3])
#         feedback_chosen = form.feedback_chosen.data
#         trial = Trial(author=current_user,
#                       trial_num=num_completed_trials + 1,
#                       card_num=cards[num_completed_trials],
#                       round_num=round,
#                       correct_bin=answers[num_completed_trials],
#                       chosen_bin=chosen_bin,
#                       feedback=feedback_chosen,
#                       rule_set=rule,
#                       switches=int(form.switches.data))
#         db.session.add(trial)

#         feedback_counts = current_user.feedback_counts
#         new_feedback_counts = {}
#         for new_vid_name in VIDEO_LIST:
#             if new_vid_name == feedback_chosen:
#                 new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name] + 1
#             else:
#                 new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name]

#         current_user.feedback_counts = new_feedback_counts
#         db.session.commit()
#         return redirect(url_for('trials', round=round))

#     if num_completed_trials == len(cards):
#         # flash("You have seen all the trials in this round!")
#         return redirect(url_for("survey", round=round))

#     #Check if previous thing is done, previous demos must be done
#     check_rule_name = current_condition.difficulty[round]
#     check_previous_demos = db.session.query(Demo).filter_by(user_id=current_user.id, round_num=round).count()
#     if check_previous_demos < len(RULE_PROPS[check_rule_name]['demo_cards']):
#         return redirect(url_for("consent"))

#     #Pick the video to play
#     feedback_counts = current_user.feedback_counts
#     cur_names = []
#     cur_counts = []
#     for vid_name in NEUTRAL:
#         cur_names.append(vid_name)
#         cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         p = np.ones_like(cur_counts)/np.sum(np.ones_like(cur_counts))
#     else:
#         p= 1 - cur_counts/np.sum(cur_counts)
#     for ii in range(len(p)):
#         if p[ii] < 0.05:
#             p[ii] = 0.05
#     p = p / np.sum(p)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p= p)
#     neutral_vid_name = cur_names[vid_choice]

#     new_feedback_counts = {}
#     for new_vid_name in VIDEO_LIST:
#         if new_vid_name == vid_name:
#             new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name] + 1
#         else:
#             new_feedback_counts[new_vid_name] = feedback_counts[new_vid_name]

#     current_user.feedback_counts = new_feedback_counts
#     db.session.commit()

#     if answers[num_completed_trials] == 0:
#         correct_bin = 'bin0'
#     else:
#         correct_bin = 'bin1'


#     #Choose correct video
#     current_nonverbal = current_condition.nonverbal[round]
#     cur_names = []
#     cur_counts = []
#     if correct_bin == 'bin0':
#         for vid_name in FEEDBACK[current_nonverbal]['CORRECT-LEFT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     else:
#         for vid_name in FEEDBACK[current_nonverbal]['CORRECT-RIGHT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         cur_counts = np.ones_like(cur_counts)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p=cur_counts/np.sum(cur_counts))
#     correct_vid_name = cur_names[vid_choice]

#     #Choose incorrect video
#     cur_names = []
#     cur_counts = []
#     if correct_bin == 'bin0':
#         for vid_name in FEEDBACK[current_nonverbal]['INCORRECT-LEFT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     else:
#         for vid_name in FEEDBACK[current_nonverbal]['INCORRECT-RIGHT']:
#             cur_names.append(vid_name)
#             cur_counts.append(feedback_counts[vid_name])
#     cur_counts = np.array(cur_counts)
#     if np.sum(cur_counts) == 0:
#         cur_counts = np.ones_like(cur_counts)
#     vid_choice = np.random.choice(np.arange(cur_counts.shape[0]), p=cur_counts/np.sum(cur_counts))
#     incorrect_vid_name = cur_names[vid_choice]

#     return render_template("trials.html",
#         title="Trials",
#         form=form,
#         num_bins=len(rule),
#         card=cards[num_completed_trials],
#         correct_bin=correct_bin,
#         num_completed_trials=num_completed_trials + 1,
#         num_trials=len(cards),
#         previous_cards=previous_cards,
#         round=round,
#         vid_name=neutral_vid_name,
#         correct_vid_name = correct_vid_name,
#         incorrect_vid_name = incorrect_vid_name)

@app.route("/final_survey", methods=["GET", "POST"])
@login_required
def final_survey():
    online_condition_id = current_user.online_condition_id
    current_condition = db.session.query(OnlineCondition).get(online_condition_id)

    (form, template) = (FinalForm(), "final_survey.html")

    # todo: maybe support being able to pick up where you left off, in case people frequently end up timing out of the study
    #  fwiw, people shouldn't be timing out around this portion of the study though
    if form.validate_on_submit():
        current_user.age = form.age.data
        current_user.gender = form.gender.data
        current_user.ethnicity = form.ethnicity.data
        current_user.education = form.education.data
        current_user.final_feedback = form.opt_text.data
        current_user.set_completion(1)

        print(form.ethnicity.data)
        db.session.commit()


        # They are complete and can receive their payment code
        return redirect(url_for("index"))

    return render_template(template,
                            methods=["GET", "POST"],
                            form=form,
                            round=round)

@app.route("/survey_old", methods=["GET", "POST"])
@login_required
def survey_old():
    if IS_IN_PERSON:
        in_person_condition_id = current_user.in_person_condition_id
        current_condition = db.session.query(InPersonCondition).get(in_person_condition_id)
    else:
        online_condition_id = current_user.online_condition_id
        current_condition = db.session.query(OnlineCondition).get(online_condition_id)

    round = (current_user.num_trials_completed + 1)
    if current_user.num_trials_completed >= len(current_condition.trials):
        # If they already completed the final form, they are done.
        check_final_survey_completion = db.session.query(Survey).filter_by(user_id=current_user.id, round_num=round).count()
        if check_final_survey_completion == 1:
            return redirect(url_for("index"))
        (form, template) = (FinalForm(), "final_survey.html")

    else:
        (form, template) = (NoFeedbackSurveyForm(), "survey.html") if current_condition.trials[current_user.num_trials_completed] == 'no_feedback' else (FeedbackSurveyForm(), "feedback_survey.html")


    if form.validate_on_submit():
        if current_user.num_trials_completed >= len(current_condition.trials):
            current_user.age = form.age.data
            current_user.gender = form.gender.data
            current_user.ethnicity = form.ethnicity.data
            current_user.education = form.education.data
            current_user.robot = form.robot.data
            current_user.final_robot_choice = form.robot_choice.data
            current_user.final_feedback = form.opt_text.data
            current_user.set_completion(1)

            print(form.ethnicity.data)
            db.session.commit()

        elif current_condition.trials[current_user.num_trials_completed] == 'no_feedback':
            survey = Survey(author=current_user,
                            round_num=round,
                            frustration = form.frustration.data,
                            ease_of_teaching = form.ease_of_teaching.data,
                            opt_text = form.opt_text.data)
            db.session.add(survey)

        else:
            survey = Survey(author=current_user,
                            round_num=round,
                            frustration = form.frustration.data,
                            utility_of_feedback = form.utility_of_feedback.data,
                            ease_of_teaching = form.ease_of_teaching.data,
                            opt_text = form.opt_text.data)
            db.session.add(survey)

        updated_num_trials_completed = current_user.num_trials_completed + 1
        current_user.set_num_trials_completed(updated_num_trials_completed)

        db.session.commit()

        # If the user submits the form, and they stil have more trials to do, we take them to the next game
        if current_user.num_trials_completed < len(current_condition.trials):
            if current_user.study_type == 'online' and current_user.num_trials_completed == 1:
                # with an attention check intermission if they are online participants
                return redirect(url_for("attn_check"))
            return redirect(url_for("test"))
        # If they have completed all the trials, but haven't completed the study, they still have the final survey to do
        elif current_user.num_trials_completed == len(current_condition.trials) and current_user.study_completed == 0:
            return redirect(url_for("survey"))
        # Otherwise, they are complete and can receive their payment code
        else:
            return redirect(url_for("index"))

    # If the survey corresponding to the current trial number has already been completed, they either need to
    # complete the next game or move on to the final round
    check_previous_surveys = db.session.query(Survey).filter_by(user_id=current_user.id, round_num=round).count()
    if check_previous_surveys == 1:
        if current_user.num_trials_completed < len(current_condition.trials):
            print("or this?")
            return redirect(url_for("test"))
        elif current_user.study_completed == 0:
            return redirect(url_for("survey"))
        else:
            return redirect(url_for("index"))

    # If they have not completed the previous game, they must do that
    completed_game = db.session.query(Trial).filter_by(user_id=current_user.id).count()
    print(current_user.id)
    print(completed_game)
    print(db.session.query(Trial).filter_by(user_id=current_user.id))
    if completed_game == 0 and round <= len(current_condition.trials):
        print("is this where we are?")
        print(round)
        print(completed_game)
        return redirect(url_for("test"))
    # if current_user.num_trials_completed < round - 1:
    #     return redirect(url_for("consent"))
    # TODO add an appropriate check back in
    # check_rule_name = current_condition.difficulty[round]
    # check_previous_trials = db.session.query(Trial).filter_by(user_id=current_user.id, round_num=round).count()
    # if check_previous_trials < len(RULE_PROPS[check_rule_name]['cards']):
    #     return redirect(url_for("consent"))
    return render_template(template,
                            methods=["GET", "POST"],
                            form=form,
                            round=round)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None:
            user = User(username=form.username.data)
            user.control_stack = []
            user.set_num_trials_completed(0)
            user.set_completion(0)
            user.set_attention_check(-1)

            # Change depending on the study type.
            cond = user.set_condition("in_person" if IS_IN_PERSON else "online")
            code = user.set_code()

            db.session.add(user)

            cond.users.append(user)
            cond.count += 1

            db.session.commit()

        login_user(user)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)

    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    # Clear this variable -- for some reason was not clearing on its own.
    session.pop("attention_check_rules", None)
    logout_user()
    return {"url":url_for("index")}
    # return redirect(url_for("index"))

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if current_user.is_authenticated:
#         # return redirect(url_for("test"))
#         return redirect(url_for("index"))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data)
#         user.set_password(form.password.data)
#         user.set_num_trials_completed(0)
#         user.set_completion(0)
#         user.set_attention_check(-1)

#         # Change depending on the study type.
#         cond = user.set_condition("online")
#         code = user.set_code()


#         db.session.add(user)

#         cond.users.append(user)
#         cond.count += 1

#         feedback = {}
#         for vid in VIDEO_LIST:
#             feedback[vid] = 0

#         user.feedback_counts = feedback

#         db.session.commit()
#         flash("Congratulations, you are now a registered user!")
#         return redirect(url_for("login"))
#     return render_template("register.html", title="Register", form=form)