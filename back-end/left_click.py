import calculo_distancia as util
import collections
import statistics
import calibration_manager as calibration_manager
import cursor_movement as cursor_movement

HISTORY_LENGTH = 3
idx_history = collections.deque(maxlen=HISTORY_LENGTH)
mid_history = collections.deque(maxlen=HISTORY_LENGTH)

def reset_state():
    idx_history.clear()
    mid_history.clear()

def is_left_click(landmark_list, thumb_index_dist, is_dragging=False):
    idx_angle_raw = util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8])
    mid_angle_raw = util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12])
    
    idx_history.append(idx_angle_raw)
    mid_history.append(mid_angle_raw)
    
    if len(idx_history) < HISTORY_LENGTH:
        return False
        
    idx_angle = statistics.mean(idx_history)
    mid_angle = statistics.mean(mid_history)
    
    idx_std = statistics.stdev(idx_history)
    mid_std = statistics.stdev(mid_history)
    
    cfg = calibration_manager.config.get("left_click", {})
    
    is_stable = idx_std < cfg.get("stability_std_max", 35) and mid_std < cfg.get("stability_std_max", 35)
    is_frozen = cursor_movement.is_frozen(landmark_list)
    thumb_gate_open = thumb_index_dist > cfg.get("thumb_index_dist_min", 50) or is_frozen
    
    if is_dragging:
        return (not is_frozen and
                idx_angle < cfg.get("idx_drag_angle_max", 110) and 
                mid_angle > cfg.get("mid_drag_angle_min", 40))
    else:
        return (is_stable and 
                idx_angle < cfg.get("idx_angle_max", 50) and 
                mid_angle > cfg.get("mid_angle_min", 90) and 
                thumb_gate_open)
