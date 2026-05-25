import json
import os
import copy
import statistics
import sys

def get_runtime_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.getcwd()

DB_FILE = os.path.join(get_runtime_dir(), "calibration.json")

DEFAULT_CONFIG = {
    "right_click": {
        "mid_angle_max": 50,
        "idx_angle_min": 90,
        "thumb_index_dist_min": 50,
        "stability_std_max": 25
    },
    "left_click": {
        "idx_angle_max": 50,
        "mid_angle_min": 90,
        "idx_drag_angle_max": 110,
        "mid_drag_angle_min": 40,
        "thumb_index_dist_min": 50,
        "stability_std_max": 25
    },
    "double_click": {
        "trigger_angle_max": 50,
        "release_angle_min": 90,
        "thumb_index_dist_min": 50,
        "stability_std_max": 25
    },
    "scroll": {
        "idx_angle_min": 90,
        "mid_angle_min": 90,
        "ring_angle_max": 50,
        "pinky_angle_max": 50
    }
}

VALID_RANGES = {
    "right_click": {
        "mid_angle_max": (20, 95),
        "idx_angle_min": (65, 175),
        "thumb_index_dist_min": (25, 350),
        "stability_std_max": (8, 35)
    },
    "left_click": {
        "idx_angle_max": (20, 95),
        "mid_angle_min": (65, 175),
        "idx_drag_angle_max": (70, 130),
        "mid_drag_angle_min": (20, 80),
        "thumb_index_dist_min": (25, 350),
        "stability_std_max": (8, 35)
    },
    "double_click": {
        "trigger_angle_max": (20, 90),
        "release_angle_min": (65, 145),
        "thumb_index_dist_min": (25, 350),
        "stability_std_max": (8, 35)
    },
    "scroll": {
        "idx_angle_min": (65, 175),
        "mid_angle_min": (65, 175),
        "ring_angle_max": (20, 95),
        "pinky_angle_max": (20, 95),
        "stability_std_max": (8, 35)
    }
}

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def sanitize_config(raw_config):
    clean = copy.deepcopy(DEFAULT_CONFIG)

    if isinstance(raw_config, dict):
        for gesture_name, gesture_defaults in DEFAULT_CONFIG.items():
            raw_gesture = raw_config.get(gesture_name, {})
            if not isinstance(raw_gesture, dict):
                continue

            for key, default_value in gesture_defaults.items():
                value = raw_gesture.get(key, default_value)
                min_value, max_value = VALID_RANGES.get(gesture_name, {}).get(key, (None, None))

                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = default_value

                if min_value is not None and max_value is not None:
                    value = clamp(value, min_value, max_value)

                clean[gesture_name][key] = value

    return clean

def load_config():
    if not os.path.exists(DB_FILE):
        save_config(DEFAULT_CONFIG)
        return copy.deepcopy(DEFAULT_CONFIG)
        
    with open(DB_FILE, 'r') as f:
        try:
            loaded_config = json.load(f)
        except json.JSONDecodeError:
            return copy.deepcopy(DEFAULT_CONFIG)

    clean_config = sanitize_config(loaded_config)
    if clean_config != loaded_config:
        save_config(clean_config)
    return clean_config

def save_config(config_data):
    config_data = sanitize_config(config_data)
    with open(DB_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

def auto_calibrate(gesture_name, idx_raw_history, mid_raw_history, thumb_dist_history=None):
    global config

    if gesture_name not in DEFAULT_CONFIG:
        return False
    
    if gesture_name not in config:
        config[gesture_name] = {}
        
    idx_mean = statistics.median(idx_raw_history)
    mid_mean = statistics.median(mid_raw_history)
    
    BUFFER = 12
    
    if gesture_name == "left_click":
        if idx_mean > 110 or mid_mean < 60:
            return False
        config[gesture_name]["idx_angle_max"] = idx_mean + BUFFER
        config[gesture_name]["mid_angle_min"] = mid_mean - BUFFER
    elif gesture_name == "right_click":
        if idx_mean < 60 or mid_mean > 110:
            return False
        config[gesture_name]["idx_angle_min"] = idx_mean - BUFFER
        config[gesture_name]["mid_angle_max"] = mid_mean + BUFFER
    elif gesture_name == "double_click":
        if idx_mean > 110 or mid_mean > 110:
            return False
        config[gesture_name]["trigger_angle_max"] = max(idx_mean, mid_mean) + BUFFER
    elif gesture_name == "scroll":
        if idx_mean < 60 or mid_mean < 60:
            return False
        config[gesture_name]["idx_angle_min"] = idx_mean - BUFFER
        config[gesture_name]["mid_angle_min"] = mid_mean - BUFFER
        
    if thumb_dist_history and len(thumb_dist_history) > 0:
        thumb_mean = statistics.median(thumb_dist_history)
        config[gesture_name]["thumb_index_dist_min"] = thumb_mean - 20
        
    config = sanitize_config(config)
    save_config(config)
    return True

config = load_config()
