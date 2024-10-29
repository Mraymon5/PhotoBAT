#%% Imports
import cv2
import time
import os
import numpy as np
import argparse
import threading

import array
import warnings

#warnings.filterwarnings("ignore", message="QObject::moveToThread", category=UserWarning, module=".*")
#warnings.filterwarnings("ignore", regex="QObject::moveToThread")
#warnings.filterwarnings("ignore")

#TODO : Make a capture version that has 3 call phases; phase 1 sets up the camera connection, phase 2 starts recording into a 5-sec rolling buffer, and phase 3 saves the buffer and starts recording for an additional x time

#%% Capture Function with Brightness/Contrast/Gain/Exposure Sliders
def preview(mode=None):
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
        print("    [5]: 1920 x 1080,  30fps (universal)")
        print("    [6]: 1280 x 1024,  30fps")
        print("    [7]: 1024 x  768,  30fps")
        print("    [8]:  640 x  480,  30fps (universal)")

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
    elif get_Settings == "8":
        PixX, PixY, FPS = 640, 480, 30
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
        getFPS = round(self.cap.get(cv2.CAP_PROP_FPS),2)
        getPixX = round(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        getPixY = round(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
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

#%% 3-stage camera function
#TODO this is the code to iron out
class TriggerCaptureFunctions():

    def __init__(self):
        self.buffer = []
        self.stop_buffer = threading.Event()

    def setupCapture(self, mode = None, autoExposure = False, exposure = 31, gain = None, buffer_duration = 5, zeroTime = None, verbose = False):
        # Open a connection to the webcam (0 is usually the default camera)
        if zeroTime is None:
            self.ZeroTime = time.time()
        else:
            self.ZeroTime = zeroTime
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.buffer_duration = buffer_duration # Seconds for rolling buffer

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
        
        if verbose: print(f"Selected Resolution: {PixX}x{PixY}, {FPS}fps")
        
        if autoExposure==True:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3.0)  # Enables auto-exposure
        else:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)  # Enables manual exposure control
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

        if gain is not None:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
            self.cap.set(cv2.CAP_PROP_GAIN, gain)

        self.PixX = PixX
        self.PixY = PixY
        self.FPS = FPS

        #Enter Settings
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, PixX)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PixY)

        #Check Settings
        getFPS = round(self.cap.get(cv2.CAP_PROP_FPS),2)
        getPixX = round(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        getPixY = round(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if verbose: print(f"Actual Resolution: {getPixX}x{getPixY}, {getFPS}fps")
        getAutoExp = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)  # Enables manual exposure control
        getExp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        
        if verbose: print(f'Auto Exposure is : {getAutoExp}, Exposure is {getExp}')
        if verbose: print('Setup Complete')

    def startBuffer(self):
        print("Starting rolling buffer...")
        self.buffer.clear()  # Resets self.buffer to an empty list
        self.stop_buffer.clear()
        self.buffer_thread = threading.Thread(target=self._bufferLoop)
        self.buffer_thread.start()

    def _bufferLoop(self):
        #buffer_time = time.time()
        while not self.stop_buffer.is_set():
            ret, frame = self.cap.read()
            if ret:
                # Add frame to buffer with timestamp
                self.buffer.append((frame, time.time()))
                # Keep only the last 'buffer_duration' seconds in the buffer
                if (time.time() - self.buffer[0][1]) > self.buffer_duration:
                    self.buffer.pop(0)
        print("Camera: Buffer loop closed")

    def saveBufferAndCapture(self, start_time = None, duration=10, title="output", outputFolder="./"):
        print("Camera: Closing buffer and starting recording")
        self.stop_buffer.set()  # Stop the buffer loop
    
        # Wait for the buffer thread to finish
        if self.buffer_thread.is_alive():
            self.buffer_thread.join()
    
        # Create a VideoWriter object to save the buffer + additional capture
        fourcc = cv2.VideoWriter_fourcc(*'MJPG') 
        outputFile = f'{outputFolder}/{title}.avi'
        out = cv2.VideoWriter(outputFile, fourcc, self.FPS, (self.PixX, self.PixY))
    
        # Save the buffer frames
        #for frame, _ in self.buffer:
        #    out.write(frame)
    
        # Now define a function to continue capturing additional frames
        def capture_additional_frames():
            nonlocal start_time
            if not self.cap.isOpened():
                print("Camera: Capture object was released or closed unexpectedly.")
            if start_time is None: start_time = time.time()
            while int((time.time() - start_time)) < duration:
                ret, frame = self.cap.read()
                if ret:
                    self.buffer.append((frame, time.time()))
                    #out.write(frame)
                else:
                    print("Camera: No Frame")
                    time.sleep(1)
                    
            #Save frames and release VideoWriter when done
            timeStamps = np.array([])
            for frame, stamp in self.buffer:
                out.write(frame)
                timeStamps = np.append(timeStamps, stamp)
            out.release()
            np.savetxt(f'{outputFolder}/{title}Timestamps.csv', (timeStamps-start_time)*1000)
            print(f"Camera: Recording complete, video saved as {outputFile}.")

            # Clear frames from the internal buffer
            while self.cap.grab():
                pass

        # Start saving additional frames in a new thread
        self.save_thread = threading.Thread(target=capture_additional_frames)
        self.save_thread.start()

    def cleanup(self):
        if not self.stop_buffer.is_set():
            self.stop_buffer.set()  # Stop the buffer loop
        self.cap.release()


#%% Function call for running the script from Terminal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Script for controlling cameras via python')
    parser.add_argument('Mode', nargs='?', help = 'Mode for camera frame rate and resolution', default=2)
    args = parser.parse_args()
    preview(mode=args.Mode)
    

#%% Function Test
if 0:
    #preview(mode=2)
    #triggerCapture(mode=6,title='test')
    os.getcwd()
    os.chdir("/home/ramartin/Documents/Code/Python/CameraTest/")
    
    capture = FastCaptureFunctions()
    capture.setupCapture(mode=2, autoExposure= False, exposure=31)
    capture.fastCapture(title="testA", duration = 5)
    capture.fastCapture(title="testB", duration = 10)
    capture.cleanup()
