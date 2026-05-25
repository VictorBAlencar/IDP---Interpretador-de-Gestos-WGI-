function updateButtonStates(isTracking) {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');

    btnStart.disabled = isTracking;
    btnStop.disabled = !isTracking;

    if (isTracking) {
        btnStart.classList.remove('primary');
        btnStop.classList.add('primary');
    } else {
        btnStart.classList.add('primary');
        btnStop.classList.remove('primary');
    }
}

function setStatus(message) {
    document.getElementById('status').innerText = message;
}

document.getElementById('btn-start').addEventListener('click', () => {
    setStatus("Starting engine...");
    document.getElementById('btn-start').disabled = true;

    chrome.runtime.sendMessage({ action: "start_tracking" }, (res) => {
        if (res && res.error) {
            setStatus(res.message);
            updateButtonStates(false);
            return;
        }

        updateButtonStates(true);
    });
});

document.getElementById('btn-stop').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: "stop_tracking" });
    setStatus("Stopping engine...");
    updateButtonStates(false);
});

chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.message) {
        setStatus(msg.message);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    updateButtonStates(false);

    chrome.runtime.sendMessage({ action: "get_state" }, (response) => {
        if (chrome.runtime.lastError) return;

        if (response && response.is_tracking) {
            setStatus("Tracking Active");
            updateButtonStates(true);
        } else if (response && !response.error) {
            setStatus("Camera Stopped");
            updateButtonStates(false);
        } else if (response && response.error) {
            setStatus("Error: WGI Server offline");
            updateButtonStates(false);
        }
    });
});

const root = document.documentElement;
const mainPanel = document.getElementById('main-panel');
const wizardPanel = document.getElementById('wizard-panel');
const steps = document.querySelectorAll('.wizard-step');
let currentStep = 0;
let feedbackInterval;
let activeCalibrationGesture = null;
let advanceTimeout = null;

document.getElementById('theme-btn').addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
});

document.getElementById('btn-calibrate').addEventListener('click', () => {
    openWizard();
});

function resetWizardUi() {
    document.querySelectorAll('.btn-calibrate-action').forEach(button => {
        const label = getGestureLabel(button.dataset.gesture)
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        button.disabled = false;
        button.innerText = `Calibrate ${label}`;
    });

    document.querySelectorAll('.saved-values').forEach(value => {
        value.classList.remove('visible');
        value.innerText = "";
    });

    document.querySelectorAll('.live-feedback[data-target]').forEach(fb => {
        setFeedback(fb, "Ready. Press calibrate, then hold the pose.", null);
        delete fb.dataset.lockUntil;
    });

    document.querySelectorAll('.wizard-step').forEach(step => {
        delete step.dataset.completed;
    });

    const nextButtons = document.querySelectorAll('.wizard-step .btn-next');
    if (nextButtons[1]) nextButtons[1].innerText = "Next: Right Click";
    if (nextButtons[2]) nextButtons[2].innerText = "Next: Double Click";
    if (nextButtons[3]) nextButtons[3].innerText = "Finish Setup";
}

function openWizard() {
    mainPanel.classList.add('hidden');
    wizardPanel.classList.remove('hidden');
    resetWizardUi();

    chrome.runtime.sendMessage({ action: "set_wizard_mode", active: true });

    chrome.runtime.sendMessage({ action: "get_base_url" }, (res) => {
        if (res && res.base_url) {
            document.getElementById('video-feed').src = res.base_url + "/video_feed?" + new Date().getTime();
        }
    });

    showStep(0);
}

function closeWizard() {
    wizardPanel.classList.add('hidden');
    mainPanel.classList.remove('hidden');
    document.getElementById('video-feed').src = "";
    currentStep = 0;
    activeCalibrationGesture = null;
    clearInterval(feedbackInterval);
    clearTimeout(advanceTimeout);
    chrome.runtime.sendMessage({ action: "set_wizard_mode", active: false });
}

function showStep(index) {
    steps.forEach((step, i) => step.classList.toggle('active', i === index));
    clearTimeout(advanceTimeout);
    if (steps[index]?.querySelector('.btn-calibrate-action')) {
        startLiveFeedback();
    } else {
        clearInterval(feedbackInterval);
    }
}

document.querySelectorAll('.btn-next').forEach(btn => {
    btn.addEventListener('click', () => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            showStep(currentStep);
        } else {
            closeWizard();
        }
    });
});

document.querySelectorAll('.btn-calibrate-action').forEach(btn => {
    btn.addEventListener('click', (e) => {
        startCalibrationCapture(e.target.dataset.gesture, e.target);
    });
});

function setFeedback(fb, message, state, lockMs = 0) {
    fb.classList.remove('success', 'warning', 'error');
    if (state) fb.classList.add(state);
    fb.innerText = message;
    if (lockMs > 0) {
        fb.dataset.lockUntil = String(Date.now() + lockMs);
    } else {
        delete fb.dataset.lockUntil;
    }
}

function setStepComplete(step, gesture) {
    step.dataset.completed = "true";

    const button = step.querySelector('.btn-calibrate-action');
    if (button) {
        button.disabled = true;
        button.innerText = "OK - Calibrated";
    }

    const nextButton = step.querySelector('.btn-next');
    if (nextButton) {
        nextButton.innerText = currentStep < steps.length - 2 ? "Continuing..." : "Completing...";
    }

    advanceTimeout = setTimeout(() => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            showStep(currentStep);
        } else {
            closeWizard();
        }
    }, 1200);
}

function getGestureLabel(gesture) {
    return gesture.replace('_', ' ');
}

function formatSavedValues(gesture, config) {
    const values = config && config[gesture];
    if (!values) return "Saved, but the values could not be loaded.";

    const usefulKeys = {
        left_click: ["idx_angle_max", "mid_angle_min", "thumb_index_dist_min"],
        right_click: ["idx_angle_min", "mid_angle_max", "thumb_index_dist_min"],
        double_click: ["trigger_angle_max", "release_angle_min", "thumb_index_dist_min"]
    }[gesture] || Object.keys(values);

    return "Saved: " + usefulKeys
        .map(key => `${key}=${Number(values[key]).toFixed(1)}`)
        .join(", ");
}

function showSavedValues(gesture) {
    chrome.runtime.sendMessage({ action: "get_config" }, (config) => {
        const target = document.querySelector(`[data-values-for="${gesture}"]`);
        if (!target) return;

        target.innerText = formatSavedValues(gesture, config);
        target.classList.add('visible');
    });
}

function startCalibrationCapture(gesture, button) {
    const step = button.closest('.wizard-step');
    const fb = step.querySelector('.live-feedback');
    const saved = step.querySelector('.saved-values');

    chrome.runtime.sendMessage({ action: "get_state" }, (state) => {
        if (!state || state.error || !state.is_tracking) {
            setFeedback(fb, "Start Camera first, then run calibration.", 'error', 1800);
            return;
        }

        activeCalibrationGesture = gesture;
        button.disabled = true;
        if (saved) {
            saved.classList.remove('visible');
            saved.innerText = "";
        }
        setFeedback(fb, `Recording ${getGestureLabel(gesture)}. Hold still...`, 'warning');

        chrome.runtime.sendMessage({ action: "start_calibration", gesture: gesture }, (res) => {
            if (!res || res.error) {
                button.disabled = false;
                activeCalibrationGesture = null;
                setFeedback(fb, res?.message || "Could not start calibration. Is the WGI server running?", 'error');
            }
        });
    });
}

function startLiveFeedback() {
    clearInterval(feedbackInterval);
    feedbackInterval = setInterval(() => {
        chrome.runtime.sendMessage({ action: "get_state" }, (res) => {
            if (!res || !res.action) return;

            const step = steps[currentStep];
            const fb = step?.querySelector('.live-feedback');
            const button = step?.querySelector('.btn-calibrate-action');
            if (!fb) return;
            const calibration = res.calibration || {};
            const calibrationStatus = calibration.status;
            const calibrationGesture = calibration.gesture;

            if (calibrationStatus === "recording" && calibrationGesture === activeCalibrationGesture) {
                setFeedback(fb, "Recording. Keep the exact same pose...", 'warning');
                return;
            }

            if (calibrationStatus === "saved" && calibrationGesture === activeCalibrationGesture) {
                const gesture = activeCalibrationGesture;
                if (button) button.disabled = false;
                activeCalibrationGesture = null;
                setFeedback(fb, `OK - ${getGestureLabel(gesture)} calibrated.`, 'success');
                if (gesture) showSavedValues(gesture);
                setStepComplete(step, gesture);
                return;
            }

            if (calibrationStatus === "failed" && calibrationGesture === activeCalibrationGesture) {
                if (button) button.disabled = false;
                activeCalibrationGesture = null;
                setFeedback(fb, "Calibration rejected. Use the exact pose shown and try again.", 'error', 1800);
                return;
            }

            if (activeCalibrationGesture) return;
            if (step.dataset.completed === "true") return;
            if (Number(fb.dataset.lockUntil || 0) > Date.now()) return;

            const targetAction = fb.dataset.target;
            if (res.action === targetAction || (targetAction === 'left_click' && res.action === 'left_click_intent')) {
                setFeedback(fb, "Pose detected. You can recalibrate if it feels off.", 'success');
            } else {
                setFeedback(fb, "Ready. Press calibrate, then hold the pose.", null);
            }
        });
    }, 150);
}
