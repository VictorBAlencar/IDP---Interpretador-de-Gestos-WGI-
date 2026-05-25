import calculo_distancia as util
import collections
import statistics
import calibration_manager as calibration_manager
import cursor_movement as cursor_movement

is_double_holding = False

HISTORY_LENGTH = 3
idx_history = collections.deque(maxlen=HISTORY_LENGTH)
mid_history = collections.deque(maxlen=HISTORY_LENGTH)

def reset_state():
    global is_double_holding
    idx_history.clear()
    mid_history.clear()
    is_double_holding = False

def is_double_click(landmark_list, thumb_index_dist):
    global is_double_holding
    
    idx_angle_raw = util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8])
    mid_angle_raw = util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12])
    
    idx_history.append(idx_angle_raw)
    mid_history.append(mid_angle_raw)
    
    if len(idx_history) < HISTORY_LENGTH:
        return is_double_holding
        
    idx_angle = statistics.mean(idx_history)
    mid_angle = statistics.mean(mid_history)
    
    idx_std = statistics.stdev(idx_history)
    mid_std = statistics.stdev(mid_history)
    
    cfg = calibration_manager.config.get("double_click", {})
    
    is_stable = idx_std < cfg.get("stability_std_max", 35) and mid_std < cfg.get("stability_std_max", 35)
    is_frozen = cursor_movement.is_frozen(landmark_list)
    
    TRIGGER_ANGLE = cfg.get("trigger_angle_max", 50)
    RELEASE_ANGLE = cfg.get("release_angle_min", 90)  
    THUMB_DIST = cfg.get("thumb_index_dist_min", 50)
    
    if is_double_holding:
        if idx_angle > RELEASE_ANGLE or mid_angle > RELEASE_ANGLE:
            is_double_holding = False
    else:
        if (is_stable and 
            idx_angle < TRIGGER_ANGLE and 
            mid_angle < TRIGGER_ANGLE and 
            (thumb_index_dist > THUMB_DIST or is_frozen)):
            is_double_holding = True
            
    return is_double_holding
