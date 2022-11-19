import time
import cv2
from datetime import datetime
import threading
import queue
import subprocess
import os
from cloudstorage import CloudStorage

_CCTV_SOURCE_LIST = {
    "cam1":'rtsp://admin:Torrzz_cctv_30@100.66.148.93:8000/live/ch00_1',
    "cam2":'rtsp://admin:Torrzz_cctv_30@100.66.148.93:8001/live/ch00_1',
    "cam3":'rtsp://admin:Torrzz_cctv_30@100.66.148.93:8002/live/ch00_1',
    "cam4":'rtsp://admin:Torrzz_cctv_30@100.66.148.93:8003/live/ch00_1',
}
_DURATION_IN_SEC = 10 # 10 SECONDS
_MAX_SIZE_IN_MB = 9 # 9 MB
_CURRENT_SIZE_IN_MB = 0
_FPS = 10
_FILE_NAME = queue.Queue()
_LOCK = threading.Lock() 
_READY = []
_READY_LOCK = threading.Lock()
_STORAGE = CloudStorage()

def onReadStorage():
    global _MAX_SIZE_IN_MB , _CURRENT_SIZE_IN_MB
    while True:
        isOnMaxSize = _CURRENT_SIZE_IN_MB >= _MAX_SIZE_IN_MB

        if isOnMaxSize:
            print("\n--- MAX Size ---\n")
            with _LOCK:
                fileName = _FILE_NAME.get()
                isFileExist = os.path.exists(fileName)
                if isFileExist:
                    size = round(os.stat(fileName).st_size / (1024 * 1024),2)
                    _CURRENT_SIZE_IN_MB -= size
                    os.remove(fileName)
                    _STORAGE.delete(fileName)

        time.sleep(0.2)

class HomeCamera:
    def __init__(self,source):
        self.source = source
        self.queue = queue.Queue()

    def initialize (self):
        self.cctv = cv2.VideoCapture(self.source)
        startStoring = threading.Thread(target=self.storeFrame)
        startStoring.start()
        
    def storeFrame(self):
        while(True):
            # Capture frame-by-frame
            ret, frame = self.cctv.read()
            if ret:
                # update the frame
                self.queue.put(frame)
            else:
                time.sleep(0.2)
         
    def startRecording (self,cameraName,dateTime):
        global _READY

        # Wait Other Camera to connect in cctv
        if len(_READY) < 4:
            isReady = False
            print(cameraName + " is ready")
            _READY.append(cameraName)
            with _READY_LOCK:
                while not isReady:
                    isReady = len(_READY) == 4
                    time.sleep(0.2)

        # Return if Queue is empty
        isQeueuEmpty = self.queue.empty()
        if isQeueuEmpty:
            time.sleep(5)
            return

        # Start Recording
        self.name = cameraName
        uid = cameraName + "_" + dateTime +".avi"
        print(self.name + " recording")

        size = (640, 360)
        vidoeCodec = cv2.VideoWriter_fourcc(*'XVID')
        self.result = cv2.VideoWriter(uid,vidoeCodec,_FPS,size)
        resultFrame = 0

        while True:
            isQeueuEmpty = self.queue.empty()

            if not isQeueuEmpty:
                frame = self.queue.get()
                frame = cv2.resize(frame,size,fx=0,fy=0,interpolation=cv2.INTER_CUBIC)
                self.result.write(frame)
                resultFrame += 1
                
                isDone = resultFrame == (_DURATION_IN_SEC*_FPS)
                if isDone:
                    self.result.release()
                    onCompress = threading.Thread(target=self.compress,args=(uid,))
                    onCompress.start()
                    break
                else:
                    time.sleep(1/10)


    def compress(self,pathName):
        global _CURRENT_SIZE_IN_MB,_LOCK
        with open(pathName) as f:
            output = pathName[0:-4] + "-f"+ ".mp4"
            input = pathName
            subprocess.run('ffmpeg -i ' + input + ' -vcodec libx264 ' + output , shell=True, 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)
            size = 0 
            while size == 0:
                try:
                    size = round(os.stat(output).st_size / (1024 * 1024),2) # video size in mb
                except Exception as e:
                    print(self.name + " " + str(e))
                finally:
                    time.sleep(1)
            
        with _LOCK:
            _FILE_NAME.put(output)
            _CURRENT_SIZE_IN_MB += size

        os.remove(input)
        _STORAGE.upload(output)
        print(output + " saved\n")
        # Save to Cloud
    
    def generateName(self):
        dateTime = datetime.now().date()
        now = datetime.now().time()
        hour = now.hour
        minute = now.minute
        second = now.second
        date = str(dateTime) + f"{hour:02}" + f"{minute:02}" + f"{second:02}"
        return date


def getCamName(my_dict, val):
    return list(my_dict.keys()) [list(my_dict.values()).index(val)]

def main():
    def cameraRecord(source: str):
        cctv = HomeCamera(source)
        cameraName = getCamName(_CCTV_SOURCE_LIST,source)
        print(cameraName + " starting")
        cctv.initialize()

        while True:
            dateTime = cctv.generateName()
            cctv.startRecording(cameraName,dateTime)
        
        
    cam1 = threading.Thread(target=cameraRecord,args=(_CCTV_SOURCE_LIST["cam1"],))
    cam2 = threading.Thread(target=cameraRecord,args=(_CCTV_SOURCE_LIST["cam2"],))
    cam3 = threading.Thread(target=cameraRecord,args=(_CCTV_SOURCE_LIST["cam3"],))
    cam4 = threading.Thread(target=cameraRecord,args=(_CCTV_SOURCE_LIST["cam4"],))

    cam1.start()
    cam2.start()
    cam3.start()
    cam4.start()

    onReadStorage()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)

