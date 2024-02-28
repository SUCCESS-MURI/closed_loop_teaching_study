DEBUG_MODE = False

CONDITIONS = [
(('EASY', 'NONVERBAL'), ('DIFFICULT', 'NONVERBAL')), 
(('EASY', 'NEUTRAL'), ('DIFFICULT', 'NEUTRAL')), 
(('DIFFICULT', 'NONVERBAL'), ('EASY', 'NONVERBAL')), 
(('DIFFICULT', 'NEUTRAL'), ('EASY', 'NEUTRAL')), 
(('EASY', 'NEUTRAL'), ('DIFFICULT', 'NONVERBAL')), 
(('EASY', 'NONVERBAL'), ('DIFFICULT', 'NEUTRAL')), 
(('DIFFICULT', 'NEUTRAL'), ('EASY', 'NONVERBAL')), 
(('DIFFICULT', 'NONVERBAL'), ('EASY', 'NEUTRAL')),
]

ONLINE_CONDITIONS = [ 
    ["no_feedback", "showing"], 
    ["no_feedback", "preference"],
    ["no_feedback", "binary_combined"],
    ["no_feedback", "credit_assignment"],
    ["showing", "no_feedback"],
    ["preference", "no_feedback"],
    ["binary_combined", "no_feedback"],
    ["credit_assignment", "no_feedback"]
]

IN_PERSON_CONDITIONS = [
	["showing", "preference", "binary_combined", "credit_assignment", "any"],
    ["preference", "credit_assignment", "showing", "binary_combined", "any"], 
    ["credit_assignment", "binary_combined", "preference", "showing", "any"], 
    ["binary_combined", "showing", "credit_assignment", "preference", "any"]
]

RULE_PROPS = {'EASY': {'rule': 'diamonds on left, all others on right', 'demo_cards': [54, 60], 'cards': [48, 47, 10, 58, 14, 18, 57, 32], 'demo_answers': [0, 1], 'answers': [1, 0, 0, 1, 1, 0, 1, 1]},
            'DIFFICULT': {'rule': 'green-one, red/purple on left, green two/three on right', 'demo_cards': [61, 34], 'cards': [33, 32, 42, 17, 68, 29, 26, 45],'demo_answers': [0, 1], 'answers': [0, 1, 0, 0, 0, 1, 0, 0]}}

FEEDBACK = {
    'NEUTRAL': {'CORRECT-RIGHT': ['neutral_correct_right_1', 'neutral_correct_right_2'], 'INCORRECT-RIGHT': ['neutral_incorrect_right_1', 'neutral_incorrect_right_2', ],'CORRECT-LEFT': ['neutral_correct_left_1', 'neutral_correct_left_2'], 'INCORRECT-LEFT': ['neutral_incorrect_left_1', 'neutral_incorrect_left_2']},
    'NONVERBAL': {'CORRECT-RIGHT': ['nonverbal_correct_right_1', 'nonverbal_correct_right_2', 'nonverbal_correct_right_3', 'nonverbal_correct_right_4'], 'INCORRECT-RIGHT': ['nonverbal_incorrect_right_1', 'nonverbal_incorrect_right_2', 'nonverbal_incorrect_right_3', 'nonverbal_incorrect_right_4'],'CORRECT-LEFT': ['nonverbal_correct_left_1', 'nonverbal_correct_left_2', 'nonverbal_correct_left_3', 'nonverbal_correct_left_4'], 'INCORRECT-LEFT': ['nonverbal_incorrect_left_1', 'nonverbal_incorrect_left_2', 'nonverbal_incorrect_left_3', 'nonverbal_incorrect_left_4']}
}

NEUTRAL = ['neutral_long_1', 'neutral_long_2', 'neutral_long_3']

VIDEO_LIST = ['neutral_long_1', 'neutral_long_2', 'neutral_long_3', 'neutral_correct_right_1', 'neutral_correct_right_2', 'neutral_incorrect_right_1', 'neutral_incorrect_right_2', 'neutral_correct_left_1', 'neutral_correct_left_2', 'neutral_incorrect_left_1', 'neutral_incorrect_left_2', 'nonverbal_correct_right_1', 'nonverbal_correct_right_2', 'nonverbal_correct_right_3', 'nonverbal_correct_right_4', 'nonverbal_incorrect_right_1', 'nonverbal_incorrect_right_2', 'nonverbal_incorrect_right_3', 'nonverbal_incorrect_right_4', 'nonverbal_correct_left_1', 'nonverbal_correct_left_2', 'nonverbal_correct_left_3', 'nonverbal_correct_left_4', 'nonverbal_incorrect_left_1', 'nonverbal_incorrect_left_2', 'nonverbal_incorrect_left_3', 'nonverbal_incorrect_left_4']