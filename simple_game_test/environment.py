import numpy as np

FEATURES = [
  ['hollow', 'striped', 'solid'],
  ['red', 'green', 'purple'],
  ['one', 'two', 'three'],
  ['ellipse', 'diamond', 'squiggle']
]

class Environment:
  def __init__(self, bins, mode):
    # Create mappings from certain features to bins, in order of priority
    self.bins = bins
    self.mode = mode
    self.priority1 = {}
    self.priority2 = {}
    if mode == 'easy':
      for i,b in enumerate(bins):
        if type(b) == str:
          self.priority1[b] = i
        else:
          for feature in b:
            self.priority2[feature] = i
    elif mode == 'hard':
      for i,b in enumerate(bins):
        if type(b) == list:
          # Assume second item is the exception
          self.priority2[b[0]] = i
          self.priority1[b[1]] = i
        else:
          self.priority2[b] = i
    else:
      raise ValueError(f'Unrecognized mode: {mode}')

    self.cards_used = np.zeros((3,3,3,3)).astype(bool)
    self.feature_to_idx = {}
    for i,f_list in enumerate(FEATURES):
      for f in f_list:
        self.feature_to_idx[f] = i

  def to_dict(self):
    d = {}
    d['bins'] = self.bins
    d['mode'] = self.mode
    d['cards_used'] = self.cards_used.tolist()
    return d    

  def from_dict(d):
    env = Environment(d['bins'], d['mode'])
    env.cards_used = np.array(d['cards_used'])
    return env

  def cards_remaining(self):
    return np.size(self.cards_used) - np.count_nonzero(self.cards_used)

  def get_bins(self):
    return self.bins

  def get_bin_for_card(self, card_features) -> int:
    # Identify correct bin and return bin index
    # Returns -1 if cannot identify correct bin (i.e. if card_features are invalid)
    bin = -1
    for key in self.priority1:
      if key in card_features:
        bin = self.priority1[key]
        break
    if bin == -1:
      for key in self.priority2:
        if key in card_features:
          bin = self.priority2[key]
          break
    return bin

  def place_card(self, card_features):
    '''
    Place card into the appropriate bin
    Return: index of bin the card was placed into. If the card was not placed into any bin (e.g. card already used), return -1
    '''

    # Identify correct bin
    bin = self.get_bin_for_card(card_features)
    card_feature_idx = [-1]*4
    for cf in card_features:
      if cf not in self.feature_to_idx:
        raise KeyError(f'Unrecognized feature: {cf}')
      i = self.feature_to_idx[cf]
      card_feature_idx[i] = FEATURES[i].index(cf)
    if self.cards_used[tuple(card_feature_idx)]:
      outcome_str = f'Card with features {card_features} has already been used.'
      return -1, outcome_str
    else:
      outcome_str = f'Successfully placed card with features {card_features} into Bin {bin+1}'
      self.cards_used[tuple(card_feature_idx)] = True
    return bin, outcome_str