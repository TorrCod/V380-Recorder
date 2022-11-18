import time
import cv2
from datetime import datetime
import threading
import queue
import subprocess
import os

_CCTVSOURCELIST = {
    "cam1":'rtsp://admin:Torrzz_cctv_30@192.168.0.102/live/ch00_1',
    "cam2":'rtsp://admin:Torrzz_cctv_30@192.168.0.103/live/ch00_1',
    "cam3":'rtsp://admin:Torrzz_cctv_30@192.168.0.104/live/ch00_1',
    "cam4":'rtsp://admin:Torrzz_cctv_30@192.168.0.105/live/ch00_1',
}
_DURATIONINSEC = 10
_FPS = 10
_STORAGEMAXSIZEINMB = 3
_STORAGECURRENTSIZEINMB = 0
_FILENAME = queue.Queue()
_LOCK = threading.Lock()

def onReadStorage():
    global _STORAGEMAXSIZEINMB , _STORAGECURRENTSIZEINMB
    while True:
        isOnMaxSize = _STORAGECURRENTSIZEINMB >= _STORAGEMAXSIZEINMB

        if isOnMaxSize:
            with _LOCK:
                fileName = _FILENAME.get()
                isFileExist = os.path.exists(fileName)
                if isFileExist:
                    size = round(os.stat(fileName).st_size / (1024 * 1024),2)
                    _STORAGECURRENTSIZEINMB -= size
                    os.remove(fileName)

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
         
    def startRecording (self,cameraName,dateTime):
        self.name = cameraName
        uid = cameraName + "_" + dateTime +".avi"

        size = (640, 360)
        vidoeCodec = cv2.VideoWriter_fourcc(*'XVID')
        self.result = cv2.VideoWriter(uid,vidoeCodec,_FPS,size)
        resultFrame = 0

        while True:
            isQeueuEmpty = self.queue.empty()
            isDone = resultFrame == (_DURATIONINSEC*_FPS)

            if not isQeueuEmpty:
                frame = self.queue.get()
                frame = cv2.resize(frame,size,fx=0,fy=0,interpolation=cv2.INTER_CUBIC)
                self.result.write(frame)
                resultFrame += 1

            if isDone:
                self.result.release()
                break

        onCompress = threading.Thread(target=self.compress,args=(uid,))
        onCompress.start()

    def compress(self,pathName):
        global _STORAGECURRENTSIZEINMB,_LOCK
        with open(pathName) as f:
            output = pathName[0:-4] + "-f"+ ".mp4"
            input = pathName
            subprocess.run('ffmpeg -i ' + input + ' -vcodec libx264 ' + output , shell=True, 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)
            size = round(os.stat(output).st_size / (1024 * 1024),2) # video size in mb
            
            with _LOCK:
                _FILENAME.put(output)
                _STORAGECURRENTSIZEINMB += size

        os.remove(input)
    
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
        cameraName = getCamName(_CCTVSOURCELIST,source)
        cctv.initialize()

        while True:
            dateTime = cctv.generateName()
            cctv.startRecording(cameraName,dateTime)

    cam1 = threading.Thread(target=cameraRecord,args=(_CCTVSOURCELIST["cam1"],))
    cam2 = threading.Thread(target=cameraRecord,args=(_CCTVSOURCELIST["cam2"],))
    cam3 = threading.Thread(target=cameraRecord,args=(_CCTVSOURCELIST["cam3"],))
    cam4 = threading.Thread(target=cameraRecord,args=(_CCTVSOURCELIST["cam4"],))

    cam1.start()
    cam2.start()
    # cam3.start()
    # cam4.start()

    onReadStorage()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)

