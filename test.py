#!/usr/bin/env python3
import os
import pyglview
import cv2

cap = cv2.VideoCapture(os.path.join(os.path.expanduser('~'),"test.mp4"))
viewer = pyglview.Viewer(window_width=512,window_height=512,fullscreen=False,opengl_direct=True)
# viewer = pyglview.Viewer(window_width=512,window_height=512,fullscreen=False,opengl_direct=False)
def loop():
    check,frame = cap.read()
    if check:
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        viewer.set_image(frame)
    pass
viewer.set_loop(loop)
viewer.start()
print("Main thread ended")
