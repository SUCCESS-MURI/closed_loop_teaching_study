from collections import OrderedDict
from scipy.special import rel_entr
from scipy.stats import entropy
import matplotlib.pyplot as plt
import numpy as np
import random as rand
import os

from generate_rules import generate_all_rules, easy_rule_to_string, hard_rule_to_string, rule_to_semantic, build_semantic_distribution
from environment import Environment, FEATURES

CARD_FEATURES = [
    [color, fill, shape, number] for color in ['red', 'green', 'purple'] for fill in ['hollow', 'striped', 'solid'] for shape in ['diamond', 'ellipse', 'squiggle'] for number in ['one', 'two', 'three']
]

class Learner:
  def __init__(self, mode: str, fb_type: str='no_feedback'):
    self._rules = generate_all_rules(mode)
    self._envs = []
    for rule in self._rules:
      self._envs.append(Environment(rule, mode))
    self._weights = np.ones(len(self._envs)) / len(self._envs)
    self._mode = mode
    self._n_observations = 0
    self._n_observations_to_learn_rule = None
    self._n_observations_at_first_termination = None
    self._observations = []
    self._n_hypotheses_remaining = []
    self._last_observed_card = None
    self._last_observed_distribution = self.get_semantic_distribution()
    self._fb_type = fb_type
    self._binary_pos_thresh = 0.95
    self._binary_neg_thresh = 0.05

  # def to_dict(self):
  #   d = {}
  #   d['mode'] = self._mode
  #   d['fb_type'] = self._fb_type
  #   d['envs'] = [env.to_dict() for env in self._envs]
  #   d['weights'] = self._weights.tolist()
  #   d['n_observations'] = self._n_observations
  #   d['n_observations_to_learn_rule'] = self._n_observations_to_learn_rule
  #   d['last_observed_card'] = self._last_observed_card
  #   d['last_observed_distribution'] = self._last_observed_distribution
  #   d['binary_pos_thresh'] = self._binary_pos_thresh
  #   d['binary_neg_thresh'] = self._binary_neg_thresh
  #   return d
  
  # def from_dict(d):
  #   learner = Learner(d['mode'], d['fb_type'])
  #   learner._envs = [Environment.from_dict(d) for d in d['envs']]
  #   learner._weights = np.array(d['weights'])
  #   learner._n_observations = d['n_observations']
  #   learner._n_observations_to_learn_rule = d['n_observations_to_learn_rule']
  #   learner._last_observed_card = d['last_observed_card']
  #   learner._last_observed_distribution = d['last_observed_distribution']
  #   learner._binary_pos_thresh = d['binary_pos_thresh']
  #   learner._binary_neg_thresh = d['binary_neg_thresh']
  #   return learner

  def describe_card(self, card):
    descriptor = ''
    for feature in card: 
      descriptor += f'{feature}, '
    descriptor = descriptor[:-2]
    return descriptor

  def get_n_valid_rules(self):
    return np.count_nonzero(self._weights)

  def get_bonus(self):
    if self._n_observations_at_first_termination is None:
      self._n_observations_at_first_termination = self._n_observations
    if self.get_n_valid_rules() == 1: 
      delta = abs(self._n_observations_at_first_termination - self._n_observations_to_learn_rule)
      if delta == 0:
        return '$1.00'
      elif delta == 1:
        return '$0.75'
      elif delta == 2: 
        return '$0.25'
      else:
        return '$0.00'
    return '$0.00'

  def get_most_confident_rule(self):
    return self._rules[np.argmax(self._weights)]

  def get_most_confident_rule_str(self):
    rule = self.get_most_confident_rule()
    if self._mode == 'easy':
      return(easy_rule_to_string(rule))
    elif self._mode == 'hard':
      return(hard_rule_to_string(rule))
    else:
      raise ValueError(f'Unrecognized mode: {self._mode}')

  def observe(self, card_features: list, bin: int):
    self._last_observed_distribution = self.get_semantic_distribution()
    self._n_observations += 1
    self._last_observed_card = card_features
    print('Observed ', self._last_observed_card)
    self._observations.append(card_features)
    for i,env in enumerate(self._envs):
      # Ignore any already pruned rules
      if self._weights[i] == 0:
        continue
      env_bin = env.get_bin_for_card(card_features)
      if env_bin != bin:
        # Prune invalidated rule
        self._weights[i] = 0

    # Renormalize weights
    self._weights = self._weights / (np.sum(self._weights))
    if np.count_nonzero(self._weights) == 1 and self._n_observations_to_learn_rule is None:
      self._n_observations_to_learn_rule = self._n_observations
    
    self._n_hypotheses_remaining.append(np.count_nonzero(self._weights))

  # def get_all_possible_feedback_bins(self, semantic_dist: OrderedDict, ver:str):
  #   semantic_dist_keys = list(semantic_dist.keys())
  #   semantic_dist_values = semantic_dist.values()

  #   target_entropy_loc = None
  #   target_entropy = float('inf') if (ver == 'least_entropy') else 0.0

  #   for idx, distr in enumerate(semantic_dist_values):
  #     curr_values = list(distr.values())
  #     prev_values = list(self._last_observed_distribution[semantic_dist_keys[idx]].values())
  #     curr_entropy = entropy(curr_values, prev_values) if (ver == 'max_kl_divergence') else entropy(curr_values)

  #     if curr_entropy == target_entropy:
  #       if target_entropy_loc is None: 
  #         target_entropy_loc = [idx]
  #       else:
  #         target_entropy_loc.append(idx)
  #     elif (curr_entropy < target_entropy and ver == 'least_entropy') or (curr_entropy > target_entropy and ver != 'least_entropy'):
  #       target_entropy = curr_entropy
  #       target_entropy_loc = [idx]

  #     return target_entropy, target_entropy_loc

  # def streamlined_get_feedback_bin(self, semantic_dist: OrderedDict, ver:str):
  #   semantic_dist_keys = list(semantic_dist.keys())

  #   curr_entropy, curr_locs = get_all_possible_feedback_bins(semantic_dist, ver)
  #   if curr_entropy == 0.0 and len(curr_locs) == len(semantic_dist_keys)

  #   if target_entropy == 0.0 and len(target_entropy_loc) == len(semantic_dist_keys):
  #     if ver != 'max_kl_divergence':
  #       return (None, None)

  #     target_entropy = 0.0
  #     target_entropy_loc = None
  #     for idx, distr in enumerate(semantic_dist_values):
  #       curr_values = list(distr.values())
  #       curr_entropy = entropy(curr_values)
  #       if curr_entropy == target_entropy:
  #         if target_entropy_loc is None: 
  #           target_entropy_loc = [idx]
  #         else:
  #           target_entropy_loc.append(idx)
  #       elif curr_entropy > target_entropy: 
  #         target_entropy = curr_entropy
  #         target_entropy_loc = [idx]

  #     if target_entropy == 0.0 and len(target_entropy_loc) == len(semantic_dist_keys):
  #       return (None, None)

  #   target_entropy_loc = rand.choice(target_entropy_loc)
  #   return (semantic_dist_keys[target_entropy_loc], target_entropy)
  
  def get_feedback_bin(self, semantic_dist: OrderedDict, ver: str):
    semantic_dist_keys = list(semantic_dist.keys())
    semantic_dist_values = semantic_dist.values()
    target_entropy_loc = None

    # For first version, just look at which of the keys has the ** lowest entropy **. 
    if ver == 'least_entropy':
      target_entropy = float('inf')
      for idx, distr in enumerate(semantic_dist_values):
        curr_values = list(distr.values())
        curr_entropy = entropy(curr_values)
        if curr_entropy == target_entropy:
          if target_entropy_loc is None: 
            target_entropy_loc = [idx]
          else:
            target_entropy_loc.append(idx)
        elif curr_entropy < target_entropy: 
          target_entropy = curr_entropy
          target_entropy_loc = [idx]

    elif ver == 'max_entropy':
      target_entropy = 0.0
      for idx, distr in enumerate(semantic_dist_values):
        curr_values = list(distr.values())
        curr_entropy = entropy(curr_values)
        if curr_entropy == target_entropy:
          if target_entropy_loc is None: 
            target_entropy_loc = [idx]
          else:
            target_entropy_loc.append(idx)
        elif curr_entropy > target_entropy: 
          target_entropy = curr_entropy
          target_entropy_loc = [idx]

    elif ver == 'max_kl_divergence':
      target_entropy = 0.0
      keys = list(semantic_dist.keys())
      for idx, distr in enumerate(semantic_dist_values):
        curr_values = list(distr.values())
        prev_values = list(self._last_observed_distribution[keys[idx]].values())
        curr_entropy = entropy(curr_values, prev_values)
        if curr_entropy == target_entropy:
          if target_entropy_loc is None: 
            target_entropy_loc = [idx]
          else:
            target_entropy_loc.append(idx)
        elif curr_entropy > target_entropy: 
          target_entropy = curr_entropy
          target_entropy_loc = [idx]

    # Second version can look at which of the keys has the greatest change in entropy. 
    # if self._last_observed_distribution is not None:
    if target_entropy == 0.0 and len(target_entropy_loc) == len(semantic_dist_keys):
      if ver != 'max_kl_divergence':
        return (None, None)

      # MAKE SURE THAT ALL THE OPTIONS HAVE 0 ENTROPY, EVEN IF THE REMAINING GRAPH HASN'T CHANGED ... MIGHT NOT BE CERTAIN.
      # Super hacky copy-pasted from above ... can I make these all lambda functions?
      target_entropy = 0.0
      target_entropy_loc = None
      for idx, distr in enumerate(semantic_dist_values):
        curr_values = list(distr.values())
        curr_entropy = entropy(curr_values)
        if curr_entropy == target_entropy:
          if target_entropy_loc is None: 
            target_entropy_loc = [idx]
          else:
            target_entropy_loc.append(idx)
        elif curr_entropy > target_entropy: 
          target_entropy = curr_entropy
          target_entropy_loc = [idx]

      if target_entropy == 0.0 and len(target_entropy_loc) == len(semantic_dist_keys):
        return (None, None)

    target_entropy_loc = rand.choice(target_entropy_loc)
    return (semantic_dist_keys[target_entropy_loc], target_entropy)

  def set_feedback_type(self, fb_type: str):
    self._fb_type = fb_type

  def get_feedback(self) -> str:
    if self._fb_type == 'no_feedback':
      return 'The robot will not be sharing any feedback during this game.'
    elif self._fb_type == 'credit_assignment':
      return self.get_feedback_credit_assignment()
    elif self._fb_type == 'preference':
      return self.get_feedback_preferences()
    elif self._fb_type.split('_')[0] == 'binary':
      return self.get_feedback_binary(self._fb_type.split('_')[1])
    elif self._fb_type == 'showing': 
      return self.get_feedback_showing()
    else:
      raise ValueError(f'Unrecognized feedback type: {self._fb_type}')

  def get_feedback_credit_assignment(self) -> str:
    semantic_dist = self.get_semantic_distribution()
    if self._last_observed_card is None or semantic_dist is None:
      return 'Unable to provide credit assignment feedback'

    # Assume that last observed card has been placed, and invalid environments have been pruned
    # Find a valid environment
    b = self._envs[np.argmax(self._weights)].get_bin_for_card(self._last_observed_card) + 1
    print(f'Last observed card: {self._last_observed_card}')
    features_list_flattened = [feat for feats in FEATURES for feat in feats]
    probs = []
    for f in self._last_observed_card: # TODO only iterate over last_observed_card features
      # For the hard rule, the probability of a card being placed in bin B due to feature F is:
      # p(B is exception)*p(F is exception_val) + p(B is not exception)*p(F is primary_bin B val)
      p_exception_bin = semantic_dist['exception_bin'][b]
      p_exception_val = semantic_dist['exception_val'][f]
      p_primary_bin_val = semantic_dist[f'primary_bin{b}'][f]
      p = p_exception_bin*p_exception_val + (1-p_exception_bin)*p_primary_bin_val
      print(f'Feature {f}, Bin {b}: {p}')
      probs.append(p)
    probs = np.array(probs)
    max_prob_idx = np.random.choice(np.flatnonzero(probs == probs.max()))
    return f'I think the {self.describe_card(self._last_observed_card)} card was placed into Bin {b} because it is a {self._last_observed_card[max_prob_idx]} card.'
    # return f'I think the {self._last_observed_card} card was placed into Bin {b} because it is {self._last_observed_card[max_prob_idx]}'

  def get_feedback_preferences(self) -> str:
    semantic_dist = self.get_semantic_distribution()
    if semantic_dist is None:
      return 'Unable to provide preference feedback'

    # For this version, we randomly pick any of the bins.
    # rand_key = rand.choice(list(semantic_dist.keys()))
    curr_key, entropy_val = self.get_feedback_bin(semantic_dist, 'max_kl_divergence')
    if entropy_val is None:
      # TODO: THIS WORKS FOR HARD RULES, NOT 'EASY' RULES. 
      # Find the bin that has two values associated with it, and give feedback about that pair. 
      exception_bin = max(semantic_dist['exception_bin'], key=semantic_dist['exception_bin'].get)
      exception_val = max(semantic_dist['exception_val'], key=semantic_dist['exception_val'].get)
      primary_bin = 'primary_bin' + str(exception_bin)
      primary_bin_val = max(semantic_dist[primary_bin], key=semantic_dist[primary_bin].get)
      return f"For Bin {exception_bin}, my first choice would be a {primary_bin_val} card. My second choice would be a {exception_val} card."

    # Top choice selection
    max_val = [keys for keys,values in semantic_dist[curr_key].items() if values == max(semantic_dist[curr_key].values())]
    if len(max_val) > 1:
      rand.shuffle(max_val)
      first_pref = max_val[0]
      second_pref = max_val[1]
    else: 
      second_max_val = []

    # First, we rearrange the dictionary based on the value as the key
    semantic_dist_by_value = {n:[k for k in semantic_dist[curr_key].keys() if semantic_dist[curr_key][k] == n] for n in set(semantic_dist[curr_key].values())}
    sorted_keys = sorted(semantic_dist_by_value) # NOT SURE IF WE NEED THIS
    max_val = semantic_dist_by_value[sorted_keys[-1]]

    # Get the maximal value, tie-break randomly
    if len(max_val) > 1:
      rand.shuffle(max_val)
      first_pref = max_val[0]
      second_pref = max_val[1]
    # If there are no max ties, repeat the process on the second highest valued keys
    else: 
      try:
        second_max_val = semantic_dist_by_value[sorted_keys[-2]]
        if len(second_max_val) > 1:
          rand.shuffle(second_max_val)
        first_pref = max_val[0]
        second_pref = second_max_val[0]
      except:
        first_pref = max_val[0]
        second_pref = "Unable to provide preference feedback."

    # FIST FRAMING
    # if curr_key is 'exception_bin':
    #   return f"For {curr_key}, my first choice would be Bin {first_pref}. My second choice would be Bin {second_pref}.""
    # f"For {curr_key}, my first choice would be a {first_pref} card. My second choice would be a {second_pref} card."
    dict_keys = list(semantic_dist.keys())
    print(dict_keys)

    # ['primary_class', 'exception_class', OK -- 'exception_bin', OK -- 'exception_val', 'primary_bin1', 'primary_bin2', 'primary_bin3']

    if curr_key == 'primary_class':
      curr_key = "how cards are primarily sorted"
    elif curr_key == 'exception_class':
      curr_key = "the exception"
    elif curr_key == 'exception_val':
      curr_key = "the exception"
    elif curr_key == 'exception_bin':
      return f"Between Bin {first_pref} and Bin {second_pref}, I think {first_pref} is more likely the bin where the exception is placed."
    else:
      if curr_key == 'primary_bin1':
        curr_key = "Bin 1"
      elif curr_key == 'primary_bin2':
        curr_key = "Bin 2"
      elif curr_key == 'primary_bin3':
        curr_key = "Bin 3"
      return f"Between {first_pref} cards and {second_pref} cards, I think {first_pref} is more likely the feature primarily associated with {curr_key}."
    return f"Between {first_pref} cards and {second_pref} cards, I think {first_pref} is more likely the feature associated with {curr_key}."

  def get_feedback_binary(self, fb_type: str='combined') -> str:
    semantic_dist = self.get_semantic_distribution()
    if fb_type != 'positive' and fb_type != 'negative' and fb_type != 'combined':
      return f'Invalid binary feedback type: {fb_type}'
    if semantic_dist is None:
      return f'Unable to provide binary {fb_type} feedback'

    # Top choice selection
    curr_key, _ = self.get_feedback_bin(semantic_dist, 'max_kl_divergence')
    if curr_key is None:
      # Learning has terminated
      curr_key = np.random.choice(list(semantic_dist.keys()))

    max_val = [keys for keys,values in semantic_dist[curr_key].items() if values == max(semantic_dist[curr_key].values())]
    min_val = [keys for keys,values in semantic_dist[curr_key].items() if values == min(semantic_dist[curr_key].values())]
    if fb_type == 'combined':
      choice_vals = []
      self._last_observed_distribution[curr_key]
      # First check if any positive feedback values crossed the threshold
      for val in max_val:
        if semantic_dist[curr_key][val] >= self._binary_pos_thresh and self._last_observed_distribution[curr_key][val] < self._binary_pos_thresh:
          choice_vals.append(val)
          fb_type = 'positive'
      if not choice_vals:
        # If no positive feedback values crossed the threshold, check if any negative feedback values crossed the threshold
        for val in min_val:
          if semantic_dist[curr_key][val] <= self._binary_neg_thresh and self._last_observed_distribution[curr_key][val] > self._binary_neg_thresh:
            choice_vals.append(val)
            fb_type = 'negative'
      if not choice_vals:
        # If neither positive nor negative feedback values crossed threshold, default to positive feedback values
        choice_vals = max_val
        fb_type = 'positive'
    else:
      choice_vals = max_val if fb_type == 'positive' else min_val

    if curr_key == 'primary_class':
      return f'I think that {np.random.choice(choice_vals)} {"is not" if fb_type == "negative" else "is"} how cards are primarily sorted.'
    elif curr_key == 'exception_class':
      return f'I think that {np.random.choice(choice_vals)} {"does not have to" if fb_type == "negative" else "has to"} do with the exception.'
    elif curr_key == 'exception_val':
      return f'I think that the feature \"{np.random.choice(choice_vals)}\" {"does not have to" if fb_type == "negative" else "has to"} do with the exception.'
    elif curr_key == 'exception_bin':
      return f'I think that Bin {np.random.choice(choice_vals)} {"is not" if fb_type == "negative" else "is"} where the exception is placed.'
    else:
      if curr_key == 'primary_bin1':
        curr_key = "Bin 1"
      elif curr_key == 'primary_bin2':
        curr_key = "Bin 2"
      elif curr_key == 'primary_bin3':
        curr_key = "Bin 3"
      return f'I think that {np.random.choice(choice_vals)} cards {"do not belong" if fb_type == "negative" else "belong"} in {curr_key}'
    # return f'I think that {np.random.choice(choice_vals)} {"does not belong" if fb_type == "negative" else "belongs"} in {curr_key}'

  ## TODO: Make this so that 'I wonder if' asks about minimums instead -- everything else the ball is in the learner court, here it's in the teacher's court.
  def get_feedback_showing(self) -> str:

    semantic_dist = self.get_semantic_distribution()
    if semantic_dist is None:
      return f'Unable to provide showing feedback'
    curr_key, entropy_val = self.get_feedback_bin(semantic_dist, 'max_kl_divergence')
    if curr_key is None:
      curr_key = rand.choice(list(semantic_dist.keys()))
    max_val_num = max(semantic_dist[curr_key].values())
    max_val = [keys for keys,values in semantic_dist[curr_key].items() if values == max(semantic_dist[curr_key].values())]
    if len(max_val) == 1:
      remove_extrema = [value for value in semantic_dist[curr_key].values() if value != max_val_num and value != 0]
      if len(remove_extrema) > 0:
        max_val = [keys for keys,values in semantic_dist[curr_key].items() if values == max(remove_extrema)]
    #min_val = [keys for keys,values in semantic_dist[curr_key].items() if values == min([value for value in semantic_dist[curr_key].values() if value != 0])]
    
    #2nd max value 
    if curr_key in ['primary_bin1', 'primary_bin2', 'primary_bin3']:
      return f'I am wondering where a {np.random.choice(max_val)} card would go.'
      # return f'I am wondering where a {np.random.choice(min_val)} card would go.'
      # return f'I think I know where a {np.random.choice(max_val)} card would go.'
    else:
      # if curr_key in ['primary_class', 'exception_class']:
      #   return f'I am wondering if {np.random.choice(max_val)} has something to do with the rule.'
      # elif curr_key == 'exception_bin':
      #   return f'I am wondering if Bin {np.random.choice(max_val)} has something to do with the rule.'
      if curr_key == 'primary_class':
        curr_key = "how cards are primarily sorted has to do with their "
      elif curr_key == 'exception_class':
        curr_key = "the exception has to do with "
      elif curr_key == 'exception_val':
        curr_key = "the exception has to do with the feature "
        return f'I am wondering if {curr_key} \"{np.random.choice(max_val)}\"'
      elif curr_key == 'exception_bin':
        curr_key = "the location of the exception could be Bin "
      return f'I am wondering if {curr_key} {np.random.choice(max_val)}'
      # return f'I am wondering if {curr_key} is {np.random.choice(min_val)}'
      # return f'I think that the {curr_key} is {np.random.choice(max_val)}'

  def get_semantic_distribution(self):
    try:
      # Only hard rule works for now
      semantic_dist = build_semantic_distribution(self._mode)
    except NotImplementedError:
      print(f'build_semantic_distribution not yet implemented for {self._mode}')
      return None

    for i,rule in enumerate(self._rules):
      # Ignore rules not in version space
      if self._weights[i] == 0:
        continue
      curr_rule_semantic = rule_to_semantic(rule, self._mode)
      for key in curr_rule_semantic:
        semantic_dist[key][curr_rule_semantic[key]] += 1

    # Normalize
    for key in semantic_dist:
      sum_vals = sum(semantic_dist[key].values())
      semantic_dist[key] = OrderedDict((k, semantic_dist[key][k] / sum_vals) for k in semantic_dist[key])
    return semantic_dist

  def get_metrics(self, true_rule):
    # Board similarity score based on how many cards would end up in the same bin as the correct rule
    board_similarity = 1.0
    least_board_similar_rule = ''
    # Semantic similarity score based on overlap of rule "properties"
    semantic_similarity = 1.0
    least_semantic_similar_rule = ''
    true_env = Environment(true_rule, self._mode)
    true_rule_semantic = rule_to_semantic(true_rule, self._mode)
    print(true_rule_semantic)

    for i,rule in enumerate(self._rules):
      # Ignore rules not in version space
      if self._weights[i] == 0:
        continue
      
      # Compute board similarity
      curr_board_similarity = 0.0
      for card in CARD_FEATURES:
        true_bin = true_env.get_bin_for_card(card)
        rule_bin = self._envs[i].get_bin_for_card(card)
        if true_bin == rule_bin and true_bin != -1:
          curr_board_similarity += 1.0 / len(CARD_FEATURES)
      if curr_board_similarity <= board_similarity:
        board_similarity = curr_board_similarity
        least_board_similar_rule = easy_rule_to_string(rule) if self._mode == 'easy' else hard_rule_to_string(rule)
      
      # Compute semantic similarity
      curr_semantic_similarity = 0.0
      curr_rule_semantic = rule_to_semantic(rule, self._mode)
      for key in curr_rule_semantic:
        if key in true_rule_semantic and true_rule_semantic[key] == curr_rule_semantic[key]:
          curr_semantic_similarity += 1.0
      curr_semantic_similarity /= len(curr_rule_semantic)
      if curr_semantic_similarity <= semantic_similarity:
        semantic_similarity = curr_semantic_similarity
        least_semantic_similar_rule = easy_rule_to_string(rule) if self._mode == 'easy' else hard_rule_to_string(rule)
    
    # Semantic distribution plotting
    semantic_dist = self.get_semantic_distribution()
    if semantic_dist is not None:
      fig = plt.figure(figsize=(9,9))
      n_cols = 3
      n_rows = int(np.ceil(len(semantic_dist) / n_cols))
      for i,key in enumerate(semantic_dist):
        ax = fig.add_subplot(n_rows, n_cols, i+1)
        ax.bar(np.arange(len(semantic_dist[key])), list(semantic_dist[key].values()))
        ax.set_xticks(np.arange(len(semantic_dist[key])), semantic_dist[key].keys(), rotation=90)
        ax.set_title(key)
      fig.tight_layout()
      plt.savefig('app/static/semantic_distribution.png')
    else:
      try:
        os.remove('app/static/semantic_distribution.png')
      except OSError:
        pass

    # Paraphrasing feedback
    original_fb_type = self._fb_type
    self.set_feedback_type('credit_assignment')
    credit_assignment_fb = self.get_feedback()
    self.set_feedback_type('preference')
    preference_fb = self.get_feedback()
    self.set_feedback_type('binary_positive')
    binary_fb_pos = self.get_feedback()
    self.set_feedback_type('binary_negative')
    binary_fb_neg = self.get_feedback()
    self.set_feedback_type('binary_combined')
    binary_fb_combined = self.get_feedback()
    self.set_feedback_type(original_fb_type)

    return {'board_similarity': board_similarity,
            'least_board_similar_rule': least_board_similar_rule,
            'semantic_similarity': semantic_similarity,
            'least_semantic_similar_rule': least_semantic_similar_rule,
            'n_observations': self._n_observations,
            'n_observations_to_learn_rule': self._n_observations_to_learn_rule,
            'preference_feedback': preference_fb,
            'credit_assignment_fb': credit_assignment_fb,
            'binary_negative_fb': binary_fb_neg,
            'binary_positive_fb': binary_fb_pos,
            'binary_combined_fb': binary_fb_combined
            }
