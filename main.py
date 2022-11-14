import cv2
from datetime import datetime
import threading
import queue
import subprocess
import os


class HomeCamera:
    def __init__(self,source,fps,duration):
        self.source = source
        self.fps = fps
        self.queue = queue.Queue()
        self.duration = duration

    def initialize (self):
        self.cctv = cv2.VideoCapture(self.source)
        self.startStoring = threading.Thread(target=self.storeFrame)
        self.startStoring.start()
        
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

        print(uid + " recording")
        size = (640, 360)
        print(size)
        vidoeCodec = cv2.VideoWriter_fourcc(*'XVID')
        self.result = cv2.VideoWriter(uid,vidoeCodec,self.fps,size)
        resultFrame = 0

        while True:
            isQeueuEmpty = self.queue.empty()
            isDone = resultFrame == (self.duration*self.fps)

            if not isQeueuEmpty:
                frame = self.queue.get()
                frame = cv2.resize(frame,size,fx=0,fy=0,interpolation=cv2.INTER_CUBIC)
                self.result.write(frame)
                resultFrame += 1

            if isDone:
                self.result.release()
                print(self.name + " recording saved "+" filename: "+ uid)
                break

        def finishing(name):
            with open(uid) as f:
                # content = f.read()
                output = uid[0:-4] + "-f"+ ".mp4"
                # subprocess.run('ffmpeg -i '+ uid + ' -c:v libx264 -crf 19 -preset slow -c:a libfdk_aac -b:a 192k -ac 2 ' + output)
                subprocess.run('ffmpeg -i ' + name + ' -vcodec libx264 ' + output)
            
            # Remove raw file
            os.remove(name)

        finish = threading.Thread(target=finishing,args=(uid,))
        finish.start()

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
    cctvSource = {
        "cam1":'rtsp://admin:Torrzz_cctv_30@192.168.0.102/live/ch00_1',
        "cam2":'rtsp://admin:Torrzz_cctv_30@192.168.0.103/live/ch00_1',
        "cam3":'rtsp://admin:Torrzz_cctv_30@192.168.0.104/live/ch00_1',
        "cam4":'rtsp://admin:Torrzz_cctv_30@192.168.0.105/live/ch00_1',
        }

    duration = 10 * 60
    fps = 10
    
    def cameraRecord(source: str):
        cctv = HomeCamera(source, fps,duration)
        cameraName = getCamName(cctvSource,source)
        cctv.initialize()
        print(cameraName + " Starting")

        # while (True):
        #     dateTime = cctv.generateName()
        #     cctv.initialize(dateTime,cameraName)
        #     cctv.startRecording(duration)

        # while True:
        #     dateTime = cctv.generateName()
        #     cctv.startRecording(cameraName,dateTime)

        dateTime = cctv.generateName()
        cctv.startRecording(cameraName,dateTime)


    cam1 = threading.Thread(target=cameraRecord,args=(cctvSource["cam1"],))
    cam2 = threading.Thread(target=cameraRecord,args=(cctvSource["cam2"],))
    cam3 = threading.Thread(target=cameraRecord,args=(cctvSource["cam3"],))
    cam4 = threading.Thread(target=cameraRecord,args=(cctvSource["cam4"],))

    cam1.start()
    cam2.start()
    cam3.start()
    cam4.start()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)



