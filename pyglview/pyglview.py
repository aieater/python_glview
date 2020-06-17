#!/usr/bin/env python3
import logging
import os
import signal
import sys
import threading
import time

import numpy as np
from easydict import EasyDict as edict

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    import OpenGL.GLUT
    AVAILABLE_OPENGL = True
except Exception as e:
    print(e)
    print("Error: Does not exist OpenGL library")
    print("  > sudo apt install -y libxmu-dev libxi-dev # install before GPU driver")
    print("  > pip3 install PyOpenGL PyOpenGL-accelerate")
    AVAILABLE_OPENGL = False

logger = logging.getLogger(__name__)


def to_bool(s):
    return s in [1, 'True', 'TRUE', 'true', '1', 'yes', 'Yes', 'Y', 'y', 't']


def handler(signum, frame):
    exit(0)


signal.signal(signal.SIGINT, handler)

config = edict()
config.viewer = edict({"window_name": "Screen", "vsync": False, "double_buffer": False, "rgba_buffer": False, "fullscreen": False, "window_x": 100, "window_y": 100, "window_width": 1280, "window_height": 720, "cpu": False})


def get_config():
    return {section: dict(config[section]) for section in config.sections()}


class Viewer:
    def init(self, kargs):
        for k in kargs:
            setattr(self, k, kargs[k])

        def s_bool(s, k):
            setattr(s, k, to_bool(getattr(s, k)))

        def s_int(s, k):
            setattr(s, k, int(getattr(s, k)))

        s_bool(self, "vsync")
        s_bool(self, "double_buffer")
        s_bool(self, "rgba_buffer")
        s_bool(self, "fullscreen")
        s_int(self, "window_x")
        s_int(self, "window_y")
        s_int(self, "window_width")
        s_int(self, "window_height")
        s_bool(self, "cpu")
        logger.debug(f"Window:{self.window_width}")

    def __init__(self, **kargs):
        global config
        self.keyboard_listener = None
        self.cnt = 0
        self.tm = 0
        self.cnt2 = 0
        self.image_buffer = None
        self.destructor_function = None
        self.idle_function = None
        self.previous_time = time.time()
        cv = config.viewer
        for k in cv:
            setattr(self, k, cv[k])

        self.init(kargs)

    def set_window_name(self, name):
        self.window_name = name

    def set_image(self, img):
        self.image_buffer = img

    def set_loop(self, func):
        self.idle_function = func

    def set_destructor(self, func):
        self.destructor_function = func

    def enable_fullscreen(self):
        self.fullscreen = True

    def disable_fullscreen(self):
        self.fullscreen = True

    def enable_vsync(self):
        if "darwin" in sys.platform:
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
            logger.debug("Enabled vsync")
        except Exception as e:
            logger.warning("Unable to set vsync mode, using driver defaults: {}".format(e))

    def start(self, **kargs):
        global AVAILABLE_OPENGL
        self.init(kargs)

        window_type = "offscreen"
        if "linux" in sys.platform:
            if 'DISPLAY' in os.environ:
                logger.debug(f"DISPLAY: {os.environ['DISPLAY']}")
                if os.environ['DISPLAY'] == ':0':
                    window_type = "primary"
                else:
                    AVAILABLE_OPENGL = False
                    window_type = "virtual"
            else:
                AVAILABLE_OPENGL = False
        else:
            window_type = "primary"

        logger.debug(f"WindowType: {window_type}")
        logger.debug(f"Available OpenGL: {AVAILABLE_OPENGL}")
        logger.debug(f"GPU: {self.cpu is False}")

        if self.cpu is False and AVAILABLE_OPENGL:
            logger.info("")
            logger.info("---- Use GPU directly ----")
            logger.info("")
            args = []
            logger.debug(f"VSync: {self.vsync}")
            if self.vsync:
                args.append('-sync')
                self.enable_vsync()
            logger.debug(f"ARGS: {args}")
            w = self.window_width
            h = self.window_height
            x = self.window_x
            y = self.window_y
            glutInit(args)
            DB = GLUT_SINGLE
            CL = GLUT_RGB
            if self.double_buffer:
                DB = GLUT_DOUBLE
                logger.debug("Use double buffer")
            else:
                logger.debug("Use single buffer")

            if self.rgba_buffer:
                CL = GLUT_RGBA
                logger.debug("Use rgba buffer")
            else:
                logger.debug("Use rgb buffer")

            glutInitDisplayMode(CL | DB | GLUT_DEPTH)
            glutInitWindowSize(w, h)
            glutInitWindowPosition(x, y)
            glutCreateWindow(self.window_name)
            if self.fullscreen: glutFullScreen()
            glutDisplayFunc(self.__gl_draw)
            glutIdleFunc(self.__gl_draw)
            glutReshapeFunc(self.__gl_resize)
            glutKeyboardFunc(self.__gl_keyboard)
            glutSpecialFunc(self.__gl_keyboard)

            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_DEPTH_TEST)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(-1, 1, -1, 1, -1, 1)

            glutMainLoop()
        else:
            if window_type == "offscreen":
                #import cv2
                import imgcat
                import queue
                import multiprocessing

                def iterm2_renderer(q):
                    while True:
                        img = q.get()
                        print("\033[0;0f")
                        imgcat.imgcat(img)

                if True:
                    q = multiprocessing.Queue()
                    th = multiprocessing.Process(target=iterm2_renderer, args=(q, ), daemon=True)
                    th.start()
                else:
                    q = queue.Queue()
                    th = threading.Thread(target=iterm2_renderer, args=(q, ))
                    th.setDaemon(True)
                    th.start()

                logger.warning("@WARNING: No display.")
                logger.warning("---- No display: iTerm2 renderer will be used ----")
                while True:
                    if self.idle_function is not None:
                        try:
                            self.idle_function()
                        except Exception as e:
                            logger.error(e)
                            return
                    if self.image_buffer is not None:
                        try:
                            self.cnt += 1
                            #self.image_buffer = cv2.cvtColor(self.image_buffer,cv2.COLOR_BGR2RGB)
                            if time.time() - self.tm > 1.0:
                                #logger.info(f"\033[0KViewer[N/A]-FPS {self.cnt}\033[1A")
                                self.tm = time.time()
                                self.cnt = 0
                            if q.empty():
                                q.put(self.image_buffer)
                            #imgcat.imgcat(self.image_buffer)
                            time.sleep(0.008)
                        except Exception as e:
                            logger.error(e)
                            return
                        self.image_buffer = None
                    else:
                        time.sleep(0.008)
            else:
                import cv2
                if self.cpu is False: logger.warning("@WARNING: GPU or physical display is not available.")
                logger.warning("---- Use CPU(OpenCV) renderer ----")
                buffer = np.zeros(shape=(self.window_height, self.window_width, 3), dtype=np.uint8)
                if self.fullscreen:
                    cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                    # cv2.namedWindow(self.window_name, cv2.WINDOW_OPENGL)
                    cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                else:
                    cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_NORMAL)
                    # cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                    # pass
                    # cv2.namedWindow(self.window_name, cv2.WINDOW_GUI_NORMAL)

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
                            self.cnt += 1
                            self.image_buffer = cv2.cvtColor(self.image_buffer, cv2.COLOR_BGR2RGB)
                            buffer.fill(0)
                            w = self.window_width
                            h = self.window_height
                            iw = self.image_buffer.shape[1]
                            ih = self.image_buffer.shape[0]
                            img = self.image_buffer
                            r = w / h
                            ir = iw / ih
                            ratio = 1.0
                            if r > ir:
                                ratio = h / ih
                                img = cv2.resize(img, (int(img.shape[1] * ratio), int(img.shape[0] * ratio)))
                                hlf = int((w - img.shape[1]) / 2)
                                buffer[0:img.shape[0], hlf:img.shape[1] + hlf, ] = img
                            else:
                                ratio = w / iw
                                img = cv2.resize(img, (int(img.shape[1] * ratio), int(img.shape[0] * ratio)))
                                hlf = int((h - img.shape[0]) / 2)
                                buffer[hlf:img.shape[0] + hlf, 0:img.shape[1], ] = img
                            if time.time() - self.tm > 1.0:
                                logger.info(f"\033[0KViewer[CV2]-FPS {self.cnt}\033[1A")
                                self.tm = time.time()
                                self.cnt = 0
                            if self.fullscreen:
                                cv2.imshow(self.window_name, self.image_buffer)
                            else:
                                cv2.imshow(self.window_name, buffer)

                            if cv2.waitKey(8) & 0xFF == 27:
                                cv2.waitKey(1)
                                cv2.destroyAllWindows()
                                cv2.waitKey(1)
                                return
                        except Exception as e:
                            logger.warning(e)
                            cv2.waitKey(1)
                            cv2.destroyAllWindows()
                            cv2.waitKey(1)
                            return
                        self.image_buffer = None
                    else:
                        time.sleep(0.008)

    def __gl_resize(self, Width, Height):  # Retina problem.
        x, y, w, h = glGetIntegerv(GL_VIEWPORT)
        self.window_width = w
        self.window_height = h
        #glViewport(0, 0, w, h)
        # glViewport(0, 0, Width, Height)
        #glfwGetFramebufferSize(window, &width, &height);
        # glViewport(0, 0, int(self.window_width), int(self.window_height))

    def __gl_keyboard(self, key, x, y):
        if type(key) == bytes:
            key = ord(key)
        else:
            key = 0x0100 + key
        if self.keyboard_listener: self.keyboard_listener(key, x, y)
        if key == b'q' or key == b'\x1b' or key == b'\x03':
            if self.destructor_function is not None:
                logger.info("Call destructor function")
                self.destructor_function()
            exit(9)
            return

    def __gl_draw(self):
        self.cnt2 += 1
        if self.idle_function is not None: self.idle_function()
        if self.image_buffer is not None:
            try:
                self.cnt += 1
                if time.time() - self.tm > 1.0:
                    logger.info(f"\033[0KViewer[GPU]-FPS {self.cnt} Idle {self.cnt2}\033[1A")
                    self.tm = time.time()
                    self.cnt = 0
                    self.cnt2 = 0
                    for i in threading.enumerate():
                        if i.name == "MainThread":
                            if i.is_alive() is False:
                                exit(9)
                                return

                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glColor3f(1.0, 1.0, 1.0)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                glOrtho(-1, 1, -1, 1, -1, 1)
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.image_buffer.shape[1], self.image_buffer.shape[0], 0, GL_RGB, GL_UNSIGNED_BYTE, self.image_buffer)
                glEnable(GL_TEXTURE_2D)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glBegin(GL_QUADS)
                glTexCoord2d(0.0, 1.0)
                w = self.window_width
                h = self.window_height
                iw = self.image_buffer.shape[1]
                ih = self.image_buffer.shape[0]
                r = w / h
                ir = iw / ih
                x_ratio = 1.0
                y_ratio = 1.0
                if r > ir:
                    x_ratio = ir / r
                else:
                    y_ratio = r / ir
                glVertex3d(-x_ratio, -y_ratio, 0.0)
                glTexCoord2d(1.0, 1.0)
                glVertex3d(x_ratio, -y_ratio, 0.0)
                glTexCoord2d(1.0, 0.0)
                glVertex3d(x_ratio, y_ratio, 0.0)
                glTexCoord2d(0.0, 0.0)
                glVertex3d(-x_ratio, y_ratio, 0.0)
                glEnd()

                glFlush()
                if self.double_buffer:
                    glutSwapBuffers()
            except Exception as e:
                logger.error(e)
                exit(9)
                return
            self.image_buffer = None
        if time.time() - self.previous_time < 0.008:
            time.sleep(0.005)
        self.previous_time = time.time()


if __name__ == '__main__':
    import cv2
    import argparse

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(filename)s:%(lineno)d] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    import coloredlogs
    coloredlogs.install()

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('input', type=str, help='')
    parser.add_argument('--codec', type=str, default="libx265", help='')
    parser.add_argument('--quality', type=int, default=None, help='')
    parser.add_argument('--quality_adjust', type=int, default=None, help='+6=low, +3=middle, high=0')
    parser.add_argument('--quality_test', action='store_true')
    parser.add_argument('--resolution', type=int, default=0, help='0/1280/1920')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--animation', action='store_true')
    parser.add_argument('--volume', type=str, default=None, help='')
    parser.add_argument('--disable_two_pass', action='store_true')
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--disable_audio_normalize', action='store_true')
    args = parser.parse_args()

    viewer = Viewer(cpu=False, fullscreen=False)
    # viewer = Viewer(opengl_direct=False)
    # viewer = Viewer(window_width=512,window_height=512,fullscreen=True,opengl_direct=True)
    # viewer = Viewer(window_width=512,window_height=512,fullscreen=True,opengl_direct=False)
    cap = cv2.VideoCapture(os.path.expanduser(args.input))
    if cap is None:
        logger.debug("Could not detect capture fd")
        exit(9)

    def loop():
        check, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if check:
            viewer.set_image(frame)

    viewer.set_loop(loop)
    viewer.start()
    logger.debug("Main thread ended")
else:
    logger.addHandler(logging.NullHandler())
