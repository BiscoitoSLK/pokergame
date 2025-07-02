# gesture_cam.py
import cv2
import time
from collections import deque
import mediapipe as mp

# Map number of fingers to poker action
def gesture_to_action(fingers_up):
    mapping = {
        1: "fold",
        2: "call",
        3: "raise",
        4: "allin",
        5: "show"
    }
    return mapping.get(fingers_up, None)

def count_fingers(hand_landmarks, handedness):
    """
    Counts raised fingers given one hand's landmarks.
    Uses the classic tip vs pip/trip positions.
    """
    # Landmark indices for tips and pip/mcp joints:
    tips = [4, 8, 12, 16, 20]
    pip_or_mcp = {4: 2, 8: 6, 12:10, 16:14, 20:18}

    fingers = 0
    # Thumb: compare tip.x with IP.x depending on left/right
    if handedness.classification[0].label == 'Right':
        if hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[pip_or_mcp[tips[0]]].x:
            fingers += 1
    else:
        if hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[pip_or_mcp[tips[0]]].x:
            fingers += 1

    # Other four fingers: tip.y lower (up) than pip.y
    for tip_id in tips[1:]:
        if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[pip_or_mcp[tip_id]].y:
            fingers += 1

    return fingers

def gesture_cam(action_queue):
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hands:

        prev_count = None
        hold_start = None
        action_sent = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)  # mirror
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            fingers_up = 0
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                handedness = results.multi_handedness[0]
                fingers_up = count_fingers(hand_landmarks, handedness)

                # draw hand skeleton
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Timer logic
            now = time.time()
            if fingers_up != prev_count:
                prev_count = fingers_up
                hold_start = now
                action_sent = False
            elapsed = now - (hold_start or now)

            # Display finger count and timer
            cv2.putText(frame, f"Fingers Up: {fingers_up}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, f"Hold Time: {elapsed:.1f}s", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            # After 3 seconds of same count, send action once
            if elapsed >= 3.0 and not action_sent:
                action = gesture_to_action(fingers_up)
                if action:
                    action_queue.put(action)
                    action_sent = True
                    # feedback
                    cv2.putText(frame, f"Action: {action}", (10, 110),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)

            # Show the frame
            cv2.imshow('Gesture Control', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
