# pyglview (Python OpenGL viewer library)

## Description
OpenCV3 renderer is too slow due to cv2.waitKey(1).
If you want to more performance, you should use OpenCV4+ or 'pyglview' package.

This package is supported fastest OpenGL direct viewer and OpenCV renderer both.
If your environment was not supported OpenGL, it will be switched to CPU renderer(OpenCV) automatically and also available remote desktop(Xserver) like VNC.



pyglview is useful library instead of OpenCV imshow/waitKey API.





## Getting Started

##### AMD Radeon GPU driver on Ubuntu

```
curl -sL http://install.aieater.com/setup_rocm | bash -
```

##### NVIDIA GPU driver on Ubuntu

```
curl -sL http://install.aieater.com/setup_nvidia_with_cuda10 | sudo bash -
```

##### Desktop package (optional)

If you installed OS as Ubuntu Server, you need to install desktop environment.
```
sudo apt update
sudo apt install -y ubuntu-desktop
```

For remote desktop.
```
sudo apt install -y gnome-panel gnome-settings-daemon metacity nautilus gnome-terminal vnc4server
```
Also see xstartup template script => http://install.aieater.com/xstartup




### Install OpenGL packages

Install OpenGL native packages, (Ubuntu16/18)
```
# Full OpenGL packages.
sudo apt install -y build-essential
sudo apt install -y libgtkglext1 libgtkglext1-dev
sudo apt install -y libgl1-mesa-dev libglu1-mesa-dev mesa-utils
sudo apt install -y freeglut3-dev libglew1.10 libglew-dev libgl1-mesa-glx libxmu-dev
sudo apt install -y libglew-dev libsdl2-dev libsdl2-image-dev libglm-dev libfreetype6-dev
```


Install python packages (Linux/MacOSX/Windows)
```
pip3 install PyOpenGL PyOpenGL_accelerate
```




##### Python package dependencies
|  Version  |  Library  | installation  |
| ---- | ---- | ---- |
|  v3.x/v4.x  |  OpenCV  | pip3 install opencv-python  |
|  v1.1x.x  |  numpy  | pip3 install numpy  |
|  v3.1.x  |  PyOpenGL  | pip3 install PyOpenGL  |
|  v3.7.x  |  configparser  | pip3 install configparser  |


#### Finally, install pyglview.

```
pip3 install pyglview
```

-----

### Examples

```
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
```

If you got something warning message, it is not using GPU.

### Message type

```
Use GPU directly
```
This message is successful to use GPU.


```
@WARNING: No display.
```
No display message meaning is there is no available display.
This message will be appeared, when you have executed program in ssh console.


```
@WARNING: GPU or physical display is not available. Use CPU renderer.
```
This message will be appeared, when there was no GPU or GPU driver, or remote logged in like VNC.
You have to make sure GPU driver and PyOpenGL packages and use physical display.




#### Also see 'acapture' package

If you want to more performance and non-blocking API for camera and video, acapture package is  very useful.

#### acapture + pyglview + webcamera example.
```
import cv2
import acapture
import pyglview
viewer = pyglview.Viewer()
cap = acapture.open(0) # Camera 0,  /dev/video0
def loop():
    check,frame = cap.read() # non-blocking
    frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    if check:
        viewer.set_image(frame)
viewer.set_loop(loop)
viewer.start()
```
Logicool C922 1280x720(HD) is supported 60FPS.
This camera device and OpenGL direct renderer is best practice.
Logicool BRIO 90FPS camera is also good!, but little bit expensive.



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
