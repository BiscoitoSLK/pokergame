import threading
from gesture_cam    import gesture_cam
from rules_window   import run_rules_window
from poker_game     import run_poker_game

if __name__ == '__main__':
    # Shared queue for gesture actions
    action_queue = __import__('multiprocessing').Queue()

    # 1) Launch gesture recognition in a background thread
    gest_thr = threading.Thread(
        target=gesture_cam,
        args=(action_queue,),
    )
    gest_thr.daemon = True
    gest_thr.start()

    # 2) Launch rules window in background
    rules_thr = threading.Thread(
        target=run_rules_window
    )
    rules_thr.daemon = True
    rules_thr.start()

    # 3) Run poker GUI (blocks here)
    run_poker_game(action_queue)

    # (threads are daemons so they’ll die when the main GUI closes)
