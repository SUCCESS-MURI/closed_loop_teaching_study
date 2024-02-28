import itertools
import numpy as np
import random as rand
import sys
from environment import FEATURES
from collections import OrderedDict

N_BINS = 3
VALID_MODES = ['easy', 'hard']
VALID_BINS = ['1', '2', '3']
VALID_CLASSES = ['fill', 'color', 'number', 'shape']
FEATURE_TO_FEATURE_CLASS = {
	f: ('fill' if i == 0 else 'color' if i == 1 else 'number' if i == 2 else 'shape') for i,feats in enumerate(FEATURES) for f in feats
}

def easy_rule_to_string(bins):
  primary = 'Priority 1: '
  secondary = 'Priority 2: '
  for i,b in enumerate(bins):
    if type(b) == str:
      primary += f'{b} in Bin {i+1}'
    else:
      secondary += f'{" and ".join(b)} in Bin {i+1}, '
  secondary = secondary[:-2]  # Remove last comma and space
  return primary + '\n' + secondary

def hard_rule_to_string(bins):
  # primary = 'Primary Rule: '
  # secondary = 'Exception: '
  exception_string = ''
  regular_strings = ''
  rule_str = ''
  for i,b in enumerate(bins):
    if type(b) == list:
      # primary_str = b[0]
      # secondary += f'{b[1]} in Bin {i+1}'
      primary_class = FEATURE_TO_FEATURE_CLASS[b[0]]
      regular_strings += f'\"{b[0].capitalize()}\" cards go in Bin {i + 1}, ' 
      exception_string += f'\"{b[1].capitalize()}\" cards also go in Bin {i + 1} regardless of {primary_class} because they are an exception.'
    else:
      # primary_str = b
      regular_strings += f'\"{b.capitalize()}\" cards go in Bin {i + 1}, '
    # primary += f'{primary_str} in Bin {i+1}, '
  # primary = primary[:-2]  # Remove last comma and space
  regular_strings = regular_strings[:-2] + "."  # Remove last comma and space
  rule_str = regular_strings + '\n\n' + exception_string
  return rule_str
  # return primary + '\n' + secondary

def generate_rule(mode: str) -> str:
  if mode not in VALID_MODES:
    raise ValueError(f'Invalid mode: {mode}, expected one of: {VALID_MODES}')

  if mode == 'easy':
    bins = generate_easy_rules()
    rule_str = easy_rule_to_string(bins)
  elif mode == 'hard':
    bins = generate_hard_rules()
    rule_str = hard_rule_to_string(bins)
  return bins, rule_str

def generate_easy_rules():
	features = [['hollow', 'striped', 'solid'],
		    ['red', 'green', 'purple'],
		    ['one', 'two', 'three'],
		    ['ellipse', 'diamond', 'squiggle']]

	bins = [None] * 3
	bin_a = rand.randint(0, 2)

	prim_ft = rand.randint(0, len(features) - 1)
	bins[bin_a] = rand.choice(features[prim_ft])
	second_ft = rand.choice([f for f in features if f != features[prim_ft]])
	rand.shuffle(second_ft)

	remaining_bins = [r for r in range(3) if r != bin_a]
	rand.shuffle(remaining_bins)
	bins[remaining_bins[0]] = second_ft[:1]
	bins[remaining_bins[1]] = second_ft[1:]

	return bins

def generate_hard_rules():
	features = [['hollow', 'striped', 'solid'],
                    ['red', 'green', 'purple'],
                    ['one', 'two', 'three'],
                    ['ellipse', 'diamond', 'squiggle']]

	prim_ft = rand.randint(0, len(features) - 1)
	bins = features[prim_ft]
	rand.shuffle(bins)

	bin_a = rand.randint(0, 2)

	second_ft = rand.choice([f for f in features if f != features[prim_ft]])
	rand.shuffle(second_ft)

	bins[bin_a] = [bins[bin_a], second_ft[0]]

	return bins

def generate_hard_rule_constrained(rule, constrain_primary, constrain_exception):
	features = [['hollow', 'striped', 'solid'],
				['red', 'green', 'purple'],
				['one', 'two', 'three'],
				['ellipse', 'diamond', 'squiggle']]

	feature_classes = ['fill', 'color', 'number', 'shape']

	# Get components of rule 
	primary_class = None
	exception_class = None
	primary_features = []
	exception_features = []
	bin_a = -1
	for i,bin in enumerate(rule):
		if type(bin) == list:
			primary_class = FEATURE_TO_FEATURE_CLASS[bin[0]]
			exception_class = FEATURE_TO_FEATURE_CLASS[bin[1]]
			primary_features.append(bin[0])
			exception_features.append(bin[1])
			bin_a = i
		else:
			primary_features.append(bin)


	prim_ft = None
	bins = []
	if not constrain_primary:
		# Choose a primary feature that is not the original one
		orig_prim_ft = feature_classes.index(primary_class)
		exclusion_list = [orig_prim_ft]
		if constrain_exception:
			orig_excep_ft = feature_classes.index(exception_class)
			exclusion_list.append(orig_excep_ft)
		prim_ft = rand.choice([i for i in range(0, len(features) - 1) if i not in exclusion_list])
		bins = features[prim_ft]

	else: 
		prim_ft = feature_classes.index(primary_class)
		bins = primary_features

	if not constrain_exception:
		# Choose a random bin (although people likely won't notice/recall this as well)
		orig_bin_a = bin_a
		bin_a = rand.choice([i for i in range(0, 2) if i != orig_bin_a])

		orig_excep_ft = feature_classes.index(exception_class)
		second_ft_idx = rand.choice([i for i in range(0, len(features) - 1) if i not in [prim_ft, orig_excep_ft]])
		second_ft = features[second_ft_idx]
		rand.shuffle(second_ft)

		bins[bin_a] = [bins[bin_a], second_ft[0]]
	else:
		bins[bin_a] = [bins[bin_a], exception_features[0]]

	return hard_rule_to_string(bins)

def generate_all_easy_rules():
	rules = []
	for prim_ft_class in range(len(FEATURES)):
		for prim_ft in range(len(FEATURES[prim_ft_class])):
			for prim_bin in range(N_BINS):
				for second_ft_class in range(len(FEATURES)):
					if second_ft_class == prim_ft_class:
						continue
					for second_bins in itertools.permutations([b for b in range(N_BINS) if b != prim_bin]):
						for second_ft in FEATURES[second_ft_class]:
							rule = [None]*N_BINS
							rule[prim_bin] = FEATURES[prim_ft_class][prim_ft]
							rule[second_bins[0]] = [second_ft]
							rule[second_bins[1]] = [f for f in FEATURES[second_ft_class] if f != second_ft]
							rules.append(rule)
	return rules

def generate_all_hard_rules():
	rules = []
	for prim_ft_class in range(len(FEATURES)):
		for prim_ft in range(len(FEATURES[prim_ft_class])):
			for prim_bin in range(N_BINS):
				for second_ft_class in range(len(FEATURES)):
					if second_ft_class == prim_ft_class:
						continue
					for second_fts in itertools.permutations(FEATURES[second_ft_class]):
						rule = list(second_fts)
						rule[prim_bin] = [rule[prim_bin], FEATURES[prim_ft_class][prim_ft]]
						rules.append(rule)
	return rules


def generate_all_rules(mode):
	if mode == 'easy':
		return generate_all_easy_rules()
	elif mode == 'hard':
		return generate_all_hard_rules()
	else:
		raise ValueError(f'Unrecognized rule type: {mode}')


def easy_rule_to_semantic(rule):
	sem_rule = {}
	for i,bin in enumerate(rule):
		if type(bin) == str:
			sem_rule['p1_class'] = FEATURE_TO_FEATURE_CLASS[bin]
			sem_rule['p1_bin'] = i+1
			sem_rule['p1_val'] = bin
		else:
			sem_rule['p2_class'] = FEATURE_TO_FEATURE_CLASS[bin[0]]
			for feature in bin:
				sem_rule[f'p2_{feature}_bin'] = i+1
	return sem_rule


def hard_rule_to_semantic(rule):
	sem_rule = {}
	for i,bin in enumerate(rule):
		if type(bin) == list:
			sem_rule['primary_class'] = FEATURE_TO_FEATURE_CLASS[bin[0]]
			sem_rule['exception_class'] = FEATURE_TO_FEATURE_CLASS[bin[1]]
			sem_rule['exception_bin'] = i+1
			sem_rule['exception_val'] = bin[1]
			sem_rule[f'primary_bin{i+1}'] = bin[0]
		else:
			sem_rule[f'primary_bin{i+1}'] = bin
		
	return sem_rule


def rule_to_semantic(rule, mode):
	if mode == 'easy':
		return easy_rule_to_semantic(rule)
	elif mode == 'hard':
		return hard_rule_to_semantic(rule)
	else:
		raise ValueError(f'Unrecognized rule type: {mode}')


def build_semantic_distribution_easy():
	raise NotImplementedError('build_semantic_distribution_easy not implemented.')

def build_semantic_distribution_hard():
	semantic_dist = {}
	semantic_properties = [
		'primary_class', 'exception_class', 'exception_bin', 'exception_val', 'primary_bin1', 'primary_bin2', 'primary_bin3'
	]
	for prop in semantic_properties:
		semantic_dist[prop] = OrderedDict()
		if prop[-5:] == 'class':
			for c in VALID_CLASSES:
				semantic_dist[prop][c] = 0
		elif prop == 'exception_bin':
			for b in VALID_BINS:
				semantic_dist[prop][int(b)] = 0
		else:
			for f in [feat for feats in FEATURES for feat in feats]:
				semantic_dist[prop][f] = 0
	return semantic_dist

def build_semantic_distribution(mode):
	if mode == 'easy':
		return build_semantic_distribution_easy()
	elif mode == 'hard':
		return build_semantic_distribution_hard()
	else:
		raise ValueError(f'Unrecognized rule type: {mode}')

def main():
	mode = str(sys.argv[1])
	bins = None
	if mode == "easy":
		bins = generate_easy_rules()
	if mode == "hard":
		bins = generate_hard_rules()
	print(bins)

if __name__ == "__main__":
	main()
