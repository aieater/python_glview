import os
import pyglview
import cv2

viewer = pyglview.Viewer()
cap = cv2.VideoCapture(os.path.join(os.path.expanduser('~'),"test.mp4"))
def loop():
    check,frame = cap.read()
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    if check:
        viewer.set_image(frame)
    pass
viewer.set_loop(loop)
viewer.start()
print("Main thread ended")
