def send_signal(passed_test):
    if passed_test:
        return {"first":"yay!", "second":"you did it!!"}
    else:
        return {"first":"oh no", "second":"you didn't quite get it..."}
    
jsons = {
  "at": {
    "0": {
      "agent": {
        "x": 3,
        "y": 3,
        "has_passenger": 0
      },
      "walls": [
        {
          "x": 1,
          "y": 3
        },
        {
          "x": 1,
          "y": 2
        }
      ],
      "passengers": [
        {
          "x": 3,
          "y": 1,
          "dest_x": 1,
          "dest_y": 1,
          "in_taxi": 0
        }
      ],
      "tolls": [
        {
          "x": 3,
          "y": 2
        }
      ],
      "available_tolls": [
        {
          "x": 3,
          "y": 3
        },
        {
          "x": 2,
          "y": 2
        },
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 2
        },
        {
          "x": 3,
          "y": 1
        }
      ],
      "traffic": [],
      "fuel_station": [],
      "hotswap_station": [],
      "available_hotswap_stations": [
        {
          "x": 4,
          "y": 3
        }
      ],
      "width": 4,
      "height": 3,
      "gamma": 1,
      "env_code": [
        0,
        0,
        1,
        0,
        0,
        0
      ],
      "opt_actions": [
        "left",
        "down",
        "down",
        "right",
        "pickup",
        "left",
        "left",
        "dropoff"
      ],
      "opt_traj_length": 8,
      "opt_traj_reward": -1.695996608010176,
      "test_difficulty": "none",
      "tag": -1,
      "all_opt_actions": [
        [
          "left",
          "down",
          "down",
          "right",
          "pickup",
          "left",
          "left",
          "dropoff"
        ],
        [
          "right",
          "down",
          "down",
          "left",
          "pickup",
          "left",
          "left",
          "dropoff"
        ]
      ]
    },
    "1": {
      "agent": {
        "x": 3,
        "y": 3,
        "has_passenger": 0
      },
      "walls": [
        {
          "x": 1,
          "y": 3
        },
        {
          "x": 1,
          "y": 2
        }
      ],
      "passengers": [
        {
          "x": 4,
          "y": 1,
          "dest_x": 1,
          "dest_y": 1,
          "in_taxi": 0
        }
      ],
      "tolls": [
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 3,
          "y": 1
        }
      ],
      "available_tolls": [
        {
          "x": 3,
          "y": 3
        },
        {
          "x": 2,
          "y": 2
        },
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 2
        },
        {
          "x": 3,
          "y": 1
        }
      ],
      "traffic": [],
      "fuel_station": [],
      "hotswap_station": [],
      "available_hotswap_stations": [
        {
          "x": 4,
          "y": 3
        }
      ],
      "width": 4,
      "height": 3,
      "gamma": 1,
      "env_code": [
        0,
        0,
        1,
        0,
        1,
        0
      ],
      "opt_actions": [
        "right",
        "down",
        "down",
        "pickup",
        "left",
        "left",
        "left",
        "dropoff"
      ],
      "opt_traj_length": 8,
      "opt_traj_reward": -2.3319953360139922,
      "test_difficulty": "none",
      "tag": 0,
      "all_opt_actions": [
        [
          "right",
          "down",
          "down",
          "pickup",
          "left",
          "left",
          "left",
          "dropoff"
        ]
      ]
    }
  },
  "ct": {
    "0": {
      "agent": {
        "x": 3,
        "y": 1
      },
      "goal": {
        "x": 5,
        "y": 1
      },
      "walls": [],
      "A_tiles": [
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 1
        }
      ],
      "available_A_tiles": [
        {
          "x": 2,
          "y": 2
        },
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 2
        },
        {
          "x": 4,
          "y": 1
        }
      ],
      "B_tiles": [],
      "available_B_tiles": [
        {
          "x": 2,
          "y": 4
        },
        {
          "x": 3,
          "y": 4
        },
        {
          "x": 4,
          "y": 4
        },
        {
          "x": 5,
          "y": 4
        },
        {
          "x": 5,
          "y": 3
        }
      ],
      "width": 5,
      "height": 5,
      "gamma": 1,
      "env_code": [
        0,
        1,
        0,
        1,
        0,
        0,
        0,
        0,
        0
      ],
      "opt_actions": [
        "left",
        "up",
        "up",
        "right",
        "right",
        "down",
        "right",
        "down"
      ],
      "opt_traj_length": 8,
      "opt_traj_reward": -0.9506814576356905,
      "test_difficulty": "none",
      "tag": -1,
      "all_opt_actions": [
        [
          "left",
          "up",
          "up",
          "right",
          "right",
          "down",
          "right",
          "down"
        ],
        [
          "left",
          "up",
          "up",
          "right",
          "right",
          "right",
          "down",
          "down"
        ]
      ]
    },
    "1": {
      "agent": {
        "x": 3,
        "y": 1
      },
      "goal": {
        "x": 5,
        "y": 1
      },
      "walls": [],
      "A_tiles": [
        {
          "x": 2,
          "y": 2
        },
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 1
        }
      ],
      "available_A_tiles": [
        {
          "x": 2,
          "y": 2
        },
        {
          "x": 3,
          "y": 2
        },
        {
          "x": 4,
          "y": 2
        },
        {
          "x": 4,
          "y": 1
        }
      ],
      "B_tiles": [],
      "available_B_tiles": [
        {
          "x": 2,
          "y": 4
        },
        {
          "x": 3,
          "y": 4
        },
        {
          "x": 4,
          "y": 4
        },
        {
          "x": 5,
          "y": 4
        },
        {
          "x": 5,
          "y": 3
        }
      ],
      "width": 5,
      "height": 5,
      "gamma": 1,
      "env_code": [
        1,
        1,
        0,
        1,
        0,
        0,
        0,
        0,
        0
      ],
      "opt_actions": [
        "right",
        "right"
      ],
      "opt_traj_length": 2,
      "opt_traj_reward": -1.0100990487379211,
      "test_difficulty": "none",
      "tag": 0,
      "all_opt_actions": [
        [
          "right",
          "right"
        ]
      ]
    }
  },
  "sb": {
    "0": {
      "agent": {
        "x": 3,
        "y": 2,
        "has_skateboard": 0
      },
      "skateboard": [
        {
          "x": 1,
          "y": 1,
          "on_agent": 0
        }
      ],
      "goal": {
        "x": 6,
        "y": 4
      },
      "walls": [],
      "available_paths": [
        {
          "x": 1,
          "y": 1
        },
        {
          "x": 2,
          "y": 1
        },
        {
          "x": 3,
          "y": 1
        },
        {
          "x": 4,
          "y": 1
        },
        {
          "x": 5,
          "y": 1
        },
        {
          "x": 6,
          "y": 1
        },
        {
          "x": 6,
          "y": 2
        },
        {
          "x": 6,
          "y": 3
        }
      ],
      "paths": [],
      "width": 6,
      "height": 4,
      "gamma": 1,
      "env_code": [
        0,
        0,
        1
      ],
      "opt_actions": [
        "down",
        "left",
        "left",
        "pickup",
        "up",
        "up",
        "up",
        "right",
        "right",
        "right",
        "right",
        "right"
      ],
      "opt_traj_length": 12,
      "opt_traj_reward": -4.022949748984706,
      "test_difficulty": "none",
      "tag": -1,
      "all_opt_actions": [
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "up",
          "right",
          "right",
          "right",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "right",
          "up",
          "right",
          "right",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "right",
          "right",
          "up",
          "right",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "right",
          "right",
          "right",
          "up",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "right",
          "right",
          "right",
          "right",
          "up",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "up",
          "right",
          "right",
          "right",
          "right",
          "right",
          "up"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "right",
          "up",
          "up",
          "right",
          "right",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "right",
          "up",
          "right",
          "up",
          "right",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "right",
          "up",
          "right",
          "right",
          "up",
          "right",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "right",
          "up",
          "right",
          "right",
          "right",
          "up",
          "right"
        ],
        [
          "down",
          "left",
          "left",
          "pickup",
          "up",
          "right",
          "up",
          "right",
          "right",
          "right",
          "right",
          "up"
        ]
      ]
    },
    "1": {
      "agent": {
        "x": 3,
        "y": 2,
        "has_skateboard": 0
      },
      "skateboard": [
        {
          "x": 1,
          "y": 4,
          "on_agent": 0
        }
      ],
      "goal": {
        "x": 6,
        "y": 4
      },
      "walls": [],
      "available_paths": [
        {
          "x": 1,
          "y": 1
        },
        {
          "x": 2,
          "y": 1
        },
        {
          "x": 3,
          "y": 1
        },
        {
          "x": 4,
          "y": 1
        },
        {
          "x": 5,
          "y": 1
        },
        {
          "x": 6,
          "y": 1
        },
        {
          "x": 6,
          "y": 2
        },
        {
          "x": 6,
          "y": 3
        }
      ],
      "paths": [],
      "width": 6,
      "height": 4,
      "gamma": 1,
      "env_code": [
        0,
        0,
        1
      ],
      "opt_actions": [
        "up",
        "up",
        "right",
        "right",
        "right"
      ],
      "opt_traj_length": 5,
      "opt_traj_reward": -4.396666392333012,
      "test_difficulty": "none",
      "tag": 0,
      "all_opt_actions": [
        [
          "up",
          "up",
          "right",
          "right",
          "right"
        ],
        [
          "up",
          "right",
          "up",
          "right",
          "right"
        ],
        [
          "up",
          "right",
          "right",
          "up",
          "right"
        ],
        [
          "up",
          "right",
          "right",
          "right",
          "up"
        ],
        [
          "right",
          "up",
          "up",
          "right",
          "right"
        ],
        [
          "right",
          "up",
          "right",
          "up",
          "right"
        ],
        [
          "right",
          "up",
          "right",
          "right",
          "up"
        ],
        [
          "right",
          "right",
          "up",
          "up",
          "right"
        ],
        [
          "right",
          "right",
          "up",
          "right",
          "up"
        ],
        [
          "right",
          "right",
          "right",
          "up",
          "up"
        ]
      ]
    }
  }
}