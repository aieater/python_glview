#!/usr/bin/env python3
from __future__ import print_function
import os
def to_bool(s): return s in [1,'True','TRUE','true','1','yes','Yes','Y','y','t']
USE_CONFIG = "PYGLVIEW_CONFIG" in os.environ
AVAILABLE_OPENGL = True
DEBUG = False
if "DEBUG" in os.environ and to_bool(os.environ["DEBUG"]):
    DEBUG = True
    try: import __builtin__
    except ImportError: import builtins as __builtin__
    import inspect
    def lpad(s,c): return s[0:c].ljust(c)
    def rpad(s,c):
        if len(s) > c: return s[len(s)-c:]
        else: return s.rjust(c)
    def print(*args, **kwargs):
        s = inspect.stack()
        __builtin__.print("\033[47m%s@%s(%s):\033[0m "%(rpad(s[1][1],20), lpad(str(s[1][3]),10), rpad(str(s[1][2]),4)),end="")
        return __builtin__.print(*args, **kwargs)
try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    import OpenGL.GLUT

except:
    print("Error: Does not exist OpenGL library")
    print("  > sudo apt install -y libxmu-dev libxi-dev # install before GPU driver")
    print("  > pip3 install PyOpenGL")
    AVAILABLE_OPENGL = False
import sys
import time
import traceback
import threading
import platform

import configparser
config = configparser.ConfigParser()
ini_file_name = os.path.basename(__file__.split(".")[0]+".ini")
if os.path.exists(ini_file_name) and USE_CONFIG:
    config.read(ini_file_name)
else:
    config["Viewer"] = {"window_name":"Screen","xsync":True,"vsync":True,"double_buffer":True,"rgba_buffer":False,"fullscreen":False,"x":100,"y":100,"width":1280,"height":720,"opengl_direct":True}
    if USE_CONFIG: config.write(open(ini_file_name,"w"))

def get_config(): return {section: dict(config[section]) for section in config.sections()}

class Viewer:
    def __init__(self,**kwargs):
        self.cnt = 0
        self.tm = 0
        self.cnt2 = 0
        self.destructor_function = None
        self.image_buffer = None
        self.idle_function = None
        self.window_width = 0
        self.window_height = 0
        self.window_name = config["Viewer"]["window_name"]
        self.fullscreen = to_bool(config["Viewer"]["fullscreen"])
        self.opengl_direct = to_bool(config["Viewer"]["opengl_direct"])
        self.previous_time = time.time()
        if "window_name" in kwargs:
            self.window_name = kwargs["window_name"]
        if "fullscreen" in kwargs:
            self.fullscreen = to_bool(kwargs["fullscreen"])
        if "opengl_direct" in kwargs:
            self.opengl_direct = to_bool(kwargs["opengl_direct"])
    def set_window_name(self,name): self.window_name = name
    def set_image(self,img): self.image_buffer = img
    def set_loop(self,func): self.idle_function = func
    def set_destructor(self,func): self.destructor_function = func
    def enable_fullscreen(self): self.fullscreen = True
    def disable_fullscreen(self): self.fullscreen = True

    def enable_vsync(self):
        if sys.platform != 'darwin':
            return
        try:
            import ctypes
            import ctypes.util
            ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))
            v = ctypes.c_int(1)

            ogl.CGLGetCurrentContext.argtypes = []
            ogl.CGLGetCurrentContext.restype = ctypes.c_void_p

            ogl.CGLSetParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
            ogl.CGLSetParameter.restype = ctypes.c_int

            context = ogl.CGLGetCurrentContext()

            ogl.CGLSetParameter(context, 222, ctypes.pointer(v))
        except Exception as e:
            print("Unable to set vsync mode, using driver defaults: {}".format(e))


    def start(self,x=int(config["Viewer"]["x"]),y=int(config["Viewer"]["y"]),w=int(config["Viewer"]["width"]),h=int(config["Viewer"]["height"])):
        global AVAILABLE_OPENGL
        self.window_width = w
        self.window_height = h


        window_type = "offscreen"

        if platform.uname()[0] == "Linux":
            if 'DISPLAY' in os.environ:
                if DEBUG: print("DISPLAY:",os.environ['DISPLAY'])
                if os.environ['DISPLAY'] == ':0':
                    window_type = "primary"
                else:
                    AVAILABLE_OPENGL = False
                    window_type = "virtual"
            else:
                AVAILABLE_OPENGL = False
        else:
            window_type = "primary"

        if DEBUG:
            print("WindowType:",window_type)
            print("Available OpenGL:",AVAILABLE_OPENGL)
            print("Direct:",self.opengl_direct)

        if self.opengl_direct and AVAILABLE_OPENGL:
            print("Use GPU directly")
            args = []
            if to_bool(config["Viewer"]["xsync"]):
                args.append('-sync')
                self.enable_vsync()
            if DEBUG: print("ARGS:",args)
            glutInit(args)
            DB = GLUT_SINGLE
            CL = GLUT_RGB
            if to_bool(config["Viewer"]["double_buffer"]):
                DB = GLUT_DOUBLE
                if DEBUG: print("Use double buffer")
            else:
                if DEBUG: print("Use single buffer")

            if to_bool(config["Viewer"]["rgba_buffer"]):
                CL = GLUT_RGBA
                if DEBUG: print("Use rgba buffer")
            else:
                if DEBUG: print("Use rgb buffer")

            glutInitDisplayMode(CL | DB | GLUT_DEPTH)
            glutInitWindowSize(w, h)
            glutInitWindowPosition(x, y)
            glutCreateWindow(self.window_name)
            if self.fullscreen: glutFullScreen()
            glutDisplayFunc(self.__gl_draw)
            glutIdleFunc(self.__gl_draw)
            glutReshapeFunc(self.__gl_resize)
            glutKeyboardFunc(self.__gl_keyboard)


            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_DEPTH_TEST)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(-1,1,-1,1,-1,1)

            glutMainLoop()
            glutLeaveMainLoop()
        else:
            if window_type == "offscreen":
                import cv2
                print("@WARNING: No display.")
                while True:
                    if self.idle_function is not None:
                        try:
                            self.idle_function()
                        except:
                            return
                    if self.image_buffer is not None:
                        try:
                            self.cnt+=1
                            self.image_buffer = cv2.cvtColor(self.image_buffer,cv2.COLOR_BGR2RGB)
                            if time.time() - self.tm > 1.0:
                                if DEBUG: print("PyOpenGLView[N/A]-FPS",self.cnt)
                                self.tm = time.time()
                                self.cnt = 0
                            time.sleep(0.008)
                        except:
                            traceback.print_exc()
                            return
                        self.image_buffer = None
                    else:
                        time.sleep(0.008)
            else:
                import cv2
                print("@WARNING: GPU or physical display is not available. Use CPU renderer.")
                # cv2.namedWindow(self.window_name, cv2.WINDOW_OPENGL)
                # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                if self.fullscreen:
                    cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

                while True:

                    if self.idle_function is not None:
                        try:
                            self.idle_function()
                        except:
                            cv2.waitKey(1)
                            cv2.destroyAllWindows()
                            cv2.waitKey(1)
                            return
                    if self.image_buffer is not None:
                        try:
                            self.cnt+=1
                            self.image_buffer = cv2.cvtColor(self.image_buffer,cv2.COLOR_BGR2RGB)
                            if time.time() - self.tm > 1.0:
                                if DEBUG: print("PyOpenGLView[CV]-FPS",self.cnt)
                                self.tm = time.time()
                                self.cnt = 0
                            cv2.imshow(self.window_name,self.image_buffer)
                            if cv2.waitKey(8) & 0xFF == 27:
                                cv2.waitKey(1)
                                cv2.destroyAllWindows()
                                cv2.waitKey(1)
                                return
                        except:
                            traceback.print_exc()
                            cv2.waitKey(1)
                            cv2.destroyAllWindows()
                            cv2.waitKey(1)
                            return
                        self.image_buffer = None
                    else:
                        time.sleep(0.008)


    def __gl_resize(self,Width, Height):
        self.window_width = Width
        self.window_height = Height
        glViewport(0, 0, Width, Height)

    def __gl_keyboard(self,key, x, y):
        if key == b'q' or key == b'\x1b' or  key == b'\x03':
            if self.destructor_function is not None:
                print("Call destructor function")
                self.destructor_function()
            exit(0)

    def __gl_draw(self):
        self.cnt2 += 1
        if self.idle_function is not None: self.idle_function()
        if self.image_buffer is not None:
            try:
                self.cnt+=1
                if time.time() - self.tm > 1.0:
                    if DEBUG: print("PyOpenGLView[GL]-FPS",self.cnt,"Idle",self.cnt2)
                    self.tm = time.time()
                    self.cnt = 0
                    self.cnt2 = 0
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glColor3f(1.0, 1.0, 1.0)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                glOrtho(-1,1,-1,1,-1,1)
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.image_buffer.shape[1], self.image_buffer.shape[0], 0, GL_RGB, GL_UNSIGNED_BYTE, self.image_buffer)
                glEnable(GL_TEXTURE_2D)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glBegin(GL_QUADS)
                glTexCoord2d(0.0, 1.0)
                glVertex3d(-1.0, -1.0,  0.0)
                glTexCoord2d(1.0, 1.0)
                glVertex3d( 1.0, -1.0,  0.0)
                glTexCoord2d(1.0, 0.0)
                glVertex3d( 1.0,  1.0,  0.0)
                glTexCoord2d(0.0, 0.0)
                glVertex3d(-1.0,  1.0,  0.0)
                glEnd()

                glFlush()
                glutSwapBuffers()
            except:
                traceback.print_exc()
                exit(9)
            self.image_buffer = None
            if time.time()-self.previous_time<0.008:
                time.sleep(0.008)
            self.previous_time = time.time()

if __name__ == '__main__':
    import cv2
    import pyglview
    viewer = pyglview.Viewer()
    cap = cv2.VideoCapture(os.path.join(os.path.expanduser('~'),"test.mp4"))
    def loop():
        check,frame = cap.read()
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        if check:
            viewer.set_image(frame)
    viewer.set_loop(loop)
    viewer.start()
    print("Main thread ended")
