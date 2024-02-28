import numpy as np

from app.params import *


cur_rule = [
            [
                ['purple'], ['open', 'solid'], ['oval'], ['one', ]
            ],
            [
                ['red', 'green'], ['open', 'striped'], ['diamond', 'squiggle'], ['one', 'two']
            ]
        ]

perc_correct = np.zeros(len(CARD_ORDER))

for card_num, card in enumerate(CARD_ORDER):

    #Choose
    bin_count = np.zeros(2)
    for rule in range(4):
        if CARD_PROPERTIES[card][rule] in cur_rule[0][rule] and not (CARD_PROPERTIES[card][rule] in cur_rule[1][rule]):
            bin_count[0] += 1
        if CARD_PROPERTIES[card][rule] in cur_rule[1][rule] and not (CARD_PROPERTIES[card][rule] in cur_rule[0][rule]):
            bin_count[1] += 1

    bin_count = bin_count/sum(bin_count)

    correct_bin = ANSWER[card_num].index(1)
    perc_correct[card_num] = bin_count[correct_bin]
    
    #Update rule
    for rule in range(4):
        if not CARD_PROPERTIES[card][rule] in cur_rule[correct_bin][rule]:
            cur_rule[correct_bin][rule].append(CARD_PROPERTIES[card][rule])

print(perc_correct)