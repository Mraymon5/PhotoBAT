#%% Imports
import cv2
import time
import warnings
import os
import array
import numpy as np

warnings.filterwarnings("ignore", message="QObject::moveToThread", category=UserWarning, module=".*")
#warnings.filterwarnings("ignore", regex="QObject::moveToThread")
warnings.filterwarnings("ignore")

#%% Capture Function
def preview(mode = None):
    # Open a connection to the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    if mode is None:
        print("Possible Settings:")
        print("    [1]:  640 x  480, 120fps")
        print("    [2]:  320 x  240, 120fps")
        print("    [3]: 1280 x  720,  60fps")
        print("    [4]:  800 x  600,  60fps")
        print("    [5]: 1920 x 1080,  30fps")
        print("    [6]: 1280 x 1024,  30fps")
        print("    [7]: 1024 x  768,  30fps")

        get_Settings = input('Select Setting (default=1): ') or "1"
    else:
        get_Settings = str(mode)

    if get_Settings == "1":
        PixX, PixY, FPS = 640, 480, 120
    elif get_Settings == "2":
        PixX, PixY, FPS = 320, 240, 120
    elif get_Settings == "3":
        PixX, PixY, FPS = 1280, 720, 60
    elif get_Settings == "4":
        PixX, PixY, FPS = 800, 600, 60
    elif get_Settings == "5":
        PixX, PixY, FPS = 1920, 1080, 30
    elif get_Settings == "6":
        PixX, PixY, FPS = 1280, 1024, 30
    elif get_Settings == "7":
        PixX, PixY, FPS = 1024, 768, 30
    else:
        print("Invalid selection, using default.")
        PixX, PixY, FPS = 640, 480, 120
    
    print(f"Selected Resolution: {PixX}x{PixY}, {FPS}fps")
        

    #Enter Settings
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, PixX)   # Lower resolution to 640x480
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PixY)
    
    #Check Settings
    getFPS = cap.get(cv2.CAP_PROP_FPS)
    getPixX = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    getPixY = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Actual Resolution: {getPixX}x{getPixY}, {getFPS}fps")

        
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
    
        if not ret:
            print("Error: Failed to capture image.")
            break
    
        # Display the resulting frame
        cv2.imshow('Webcam Preview', frame)
    
        # Press 'q' to exit the preview
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()

#%% Capture Function with Brightness/Contrast/Gain/Exposure Sliders
def preview2(mode=None):
    def print_fps(state,extra):
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Current FPS: {fps}")
    # Open a connection to the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    if mode is None:
        print("Possible Settings:")
        print("    [1]:  640 x  480, 120fps")
        print("    [2]:  320 x  240, 120fps")
        print("    [3]: 1280 x  720,  60fps")
        print("    [4]:  800 x  600,  60fps")
        print("    [5]: 1920 x 1080,  30fps")
        print("    [6]: 1280 x 1024,  30fps")
        print("    [7]: 1024 x  768,  30fps")

        get_Settings = input('Select Setting (default=1): ') or "1"
    else:
        get_Settings = str(mode)

    if get_Settings == "1":
        PixX, PixY, FPS = 640, 480, 120
    elif get_Settings == "2":
        PixX, PixY, FPS = 320, 240, 120
    elif get_Settings == "3":
        PixX, PixY, FPS = 1280, 720, 60
    elif get_Settings == "4":
        PixX, PixY, FPS = 800, 600, 60
    elif get_Settings == "5":
        PixX, PixY, FPS = 1920, 1080, 30
    elif get_Settings == "6":
        PixX, PixY, FPS = 1280, 1024, 30
    elif get_Settings == "7":
        PixX, PixY, FPS = 1024, 768, 30
    else:
        print("Invalid selection, using default.")
        PixX, PixY, FPS = 640, 480, 120

    print(f"Selected Resolution: {PixX}x{PixY}, {FPS}fps")

    # Enter settings
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, PixX)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PixY)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)  # Enables manual exposure control

    # Check settings
    getFPS = cap.get(cv2.CAP_PROP_FPS)
    getPixX = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    getPixY = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Actual Resolution: {getPixX}x{getPixY}, {getFPS}fps")
    auto_exposure = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
    print(f"Auto Exposure: {auto_exposure}")

    # Create window for preview
    cv2.namedWindow('Webcam Preview')

    # Create sliders for brightness, contrast, gain, and exposure
    def nothing(x):
        pass

    # Brightness: usually 0 to 255 range
    cv2.createTrackbar('Brightness', 'Webcam Preview', 128, 255, nothing)
    # Contrast: usually 0 to 255 range
    cv2.createTrackbar('Contrast', 'Webcam Preview', 128, 255, nothing)
    # Gain: typically ranges from 0 to a max value depending on the camera
    cv2.createTrackbar('Gain', 'Webcam Preview', 0, 255, nothing)
    # Exposure: depending on the camera, the range might vary (note: some cameras might have exposure in negative values)
    cv2.createTrackbar('Exposure', 'Webcam Preview', 50, 255, nothing)
    # Get Settings Button
    cv2.createButton('Get_FPS', print_fps, None, cv2.QT_PUSH_BUTTON, 0)

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture image.")
            break

        # Get current positions of sliders
        brightness = cv2.getTrackbarPos('Brightness', 'Webcam Preview')
        contrast = cv2.getTrackbarPos('Contrast', 'Webcam Preview')
        gain = cv2.getTrackbarPos('Gain', 'Webcam Preview')
        exposure = cv2.getTrackbarPos('Exposure', 'Webcam Preview')
        exposure = cv2.getTrackbarPos('Exposure', 'Webcam Preview')
        
        # Apply brightness and contrast to the frame
        adjusted_frame = cv2.convertScaleAbs(frame, alpha=contrast / 128, beta=brightness - 128)

        # Set gain and exposure properties
        cap.set(cv2.CAP_PROP_GAIN, gain)
        cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

        # Display the resulting frame
        cv2.imshow('Webcam Preview', adjusted_frame)

        # Press 'q' to exit the preview
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()
#%% Trigger Capture Function
def triggerCapture(mode = None, duration = 10, title = "output", outputFolder = "./"):
    # Open a connection to the webcam (0 is usually the default camera)
    ZeroTime = time.time()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    print(f'Mark 1: {time.time()-ZeroTime} elapsed')
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    if mode is None:
        print("Possible Settings:")
        print("    [1]:  640 x  480, 120fps")
        print("    [2]:  320 x  240, 120fps")
        print("    [3]: 1280 x  720,  60fps")
        print("    [4]:  800 x  600,  60fps")
        print("    [5]: 1920 x 1080,  30fps")
        print("    [6]: 1280 x 1024,  30fps")
        print("    [7]: 1024 x  768,  30fps")
    
        get_Settings = str(1)
    else:
        get_Settings = str(mode)
    
    if get_Settings == "1":
        PixX, PixY, FPS = 640, 480, 120
    elif get_Settings == "2":
        PixX, PixY, FPS = 320, 240, 120
    elif get_Settings == "3":
        PixX, PixY, FPS = 1280, 720, 60
    elif get_Settings == "4":
        PixX, PixY, FPS = 800, 600, 60
    elif get_Settings == "5":
        PixX, PixY, FPS = 1920, 1080, 30
    elif get_Settings == "6":
        PixX, PixY, FPS = 1280, 1024, 30
    elif get_Settings == "7":
        PixX, PixY, FPS = 1024, 768, 30
    else:
        print("Invalid selection, using default.")
        PixX, PixY, FPS = 640, 480, 120
    
    print(f"Selected Resolution: {PixX}x{PixY}, {FPS}fps")
        

    #Enter Settings
    cap.set(cv2.CAP_PROP_FPS, FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, PixX)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PixY)
    
    #Check Settings
    getFPS = cap.get(cv2.CAP_PROP_FPS)
    getPixX = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    getPixY = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Actual Resolution: {getPixX}x{getPixY}, {getFPS}fps")
    print(f'Mark 2: {time.time()-ZeroTime} elapsed')

        
    # Define the codec and create VideoWriter object to save the video
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    outputFile = f'{outputFolder}/{title}.avi'
    out = cv2.VideoWriter(outputFile, fourcc, FPS, (PixX, PixY))
    
    print(f'Mark 3: {time.time()-ZeroTime} elapsed')
    # Start recording
    print(f"Recording for {duration} seconds...")
    start_time = time.time()

    while int((time.time() - start_time)) < duration:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break
        
        # Write the frame to the file
        out.write(frame)
    
    # Release everything when done
    print(f'Mark 4: {time.time()-ZeroTime} elapsed')
    cap.release()
    out.release()
    print("Recording complete and video saved.")
    print(f'Mark 5: {time.time()-ZeroTime} elapsed')

#%% Setup Fast Capture Functions
class FastCaptureFunctions():

    def __init__(self):
        pass
    
    def setupCapture(self, mode = None, autoExposure = False, exposure = 60):
        # Open a connection to the webcam (0 is usually the default camera)
        self.ZeroTime = time.time()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            exit()
    
        if mode is None:
            print("Possible Settings:")
            print("    [1]:  640 x  480, 120fps")
            print("    [2]:  320 x  240, 120fps")
            print("    [3]: 1280 x  720,  60fps")
            print("    [4]:  800 x  600,  60fps")
            print("    [5]: 1920 x 1080,  30fps")
            print("    [6]: 1280 x 1024,  30fps")
            print("    [7]: 1024 x  768,  30fps")
        
            get_Settings = str(1)
        else:
            get_Settings = str(mode)
        
        if get_Settings == "1":
            PixX, PixY, FPS = 640, 480, 120
        elif get_Settings == "2":
            PixX, PixY, FPS = 320, 240, 120
        elif get_Settings == "3":
            PixX, PixY, FPS = 1280, 720, 60
        elif get_Settings == "4":
            PixX, PixY, FPS = 800, 600, 60
        elif get_Settings == "5":
            PixX, PixY, FPS = 1920, 1080, 30
        elif get_Settings == "6":
            PixX, PixY, FPS = 1280, 1024, 30
        elif get_Settings == "7":
            PixX, PixY, FPS = 1024, 768, 30
        else:
            print("Invalid selection, using default.")
            PixX, PixY, FPS = 640, 480, 120
        
        print(f"Selected Resolution: {PixX}x{PixY}, {FPS}fps")
        
        if autoExposure==True:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3.0)  # Enables auto-exposure
        else:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)  # Enables manual exposure control
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
            
        self.PixX = PixX
        self.PixY = PixY
        self.FPS = FPS

        #Enter Settings
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, PixX)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PixY)

        #Check Settings
        getFPS = self.cap.get(cv2.CAP_PROP_FPS)
        getPixX = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        getPixY = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Actual Resolution: {getPixX}x{getPixY}, {getFPS}fps")
        getAutoExp = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)  # Enables manual exposure control
        getExp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        
        print(f'Auto Exposure is : {getAutoExp}, Exposure is {getExp}')
        print('Setup Complete')

            
    # Fast Capture Function
    def fastCapture(self, duration = 10, title = "output", outputFolder = "./"):
        # Define the codec and create VideoWriter object to save the video
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        outputFile = f'{outputFolder}/{title}.avi'
        out = cv2.VideoWriter(outputFile, fourcc, self.FPS, (self.PixX, self.PixY))
        
        print(f"Recording for {duration} seconds...")
        start_time = time.time()
        timeStamps = np.array([])
        
        while int((time.time() - start_time)) < duration:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                break
            
            # Write the frame to the file
            out.write(frame)
            
            # Save a timestamp
            timeStamps = np.append(timeStamps, (time.time() - start_time))
            
        # Release everything when done
        out.release()
        np.savetxt(f'{outputFolder}/{title}Timestamps.csv', timeStamps*1000)
        print("Recording complete and video saved.")
        
    # Close the camera
    def cleanup(self):
        self.cap.release()
    
    #%% Function Test
#preview2(mode=2)
#triggerCapture(mode=6,title='test')
os.getcwd()
os.chdir("/home/ramartin/Documents/Code/Python/CameraTest/")

capture = FastCaptureFunctions()
capture.setupCapture(mode=2, autoExposure= False, exposure=127)
capture.fastCapture(title="testA", duration = 5)
capture.fastCapture(title="testB", duration = 10)
capture.cleanup()
