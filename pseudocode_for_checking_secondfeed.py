to_save_listA
to_save_listB
firstValidateflag = False
secondValidateflag = False
timer = 0
timerthreadFlag = False ##when breaking timer thread loop
def videochecker:
    if firstValidateflag == False:
        ValidateFirstFeed = ValidateFirstFeed
    else if firstValidateflag == True
        if timer not start:
            timer.start(2) #(separate thread)
                while timer < 2 seconds
                    ValidateSecondFeed = ValidateSecondFeed
                    if ValidateSecondFeed == True
                        timer.stop
                        timer=0
                        timerthreadFlag = True
                        break
        if timer < 2 or timerthreadFlag == False:
            pass
        if ValidateSecondFeed == False:
            alert("Please scan item again")
            to_save_listA = None
            to_save_listB = None
            firstValidateflag = False
            secondValidateflag = False
        else:
            store data
            post on info header

def ValidateFirstFeed:
    checkfeed
    to_save_listA/B = events
    
    if to_save_list is not None:
        firstValidateflag = True
        return True
    else:
        firstValidateflag = False
        return False
def ValidateSecondFeed:
    checkfeed
    to_save_listA    


---------
to_save_listA = None
to_save_listB = None
firstValidateflag = False
secondValidateflag = False
timer = 0
timerthreadFlag = False ##when breaking timer thread loop


self.WorkerCamera.SignalFeedEvents.connect(self.ValidateVideoFeed) 

self.threadValidation = QThread()
self.threadValidation.started.connect(self.ValidateSecondFeed)
self.SignalValidation = pyqtSignal(tuple)



def ValidateVideofeed(events):
    if firstValidateflag == False:
        ValidateFirstFeed = ValidateFirstFeed(events)
    elif firstValidateflag == True:
        if threadValidation.isRunning() == False:
            self.threadValidation.start()
        self.SignalValidation.emit(events)

def ValidateFirstFeed(events):
    if events[0][0]["list"] is not None:
        to_save_listA = events[0][0]["list"] 
        firstValidateflag = True
    if events[1][0]["list"] is not None:
        to_save_listB = events[1][0]["list"]
        firstValidateflag = True

def ValidateSecondFeed(events):

------------
self.WorkerCamera.SignalFeedEvents.connect(self.VideoSignalFeedEvents) 
self.WorkerCamera.SignalFeedEvents.connect(self.)


----
# thread
self.threadValidation = QThread()
self.threadValidation.started.connect(self.ValidateFeed.validate)
# global variables
to_save_listA = None
to_save_listB = None
list_to_validate = None #input A or B to check which list to check
flag_list_saved = False #If true, stop validation


self.ValidateFeed.SignalValidation.connect(self.ValidateConfirm)
self.ValidateFeed.SignalStopThread.connect(self.StopValidateFeed)

def store_lists(self,events):
    event_list_A = events[0][0]
    event_list_B = events[1][0]
    if (to_save_listA is None) and (event_list_A["list"] is not None):
        self.to_save_listA = event_list_A
    if (to_save_listB is None) and (event_list_B["list"] is not None):
        self.to_save_listB = event_list_B
    if (self.to_save_listA is not None) and (self.to_save_listB is None):
        list_to_validate = "B"
        if not self.threadValidation.isRunning():
            self.threadValidation.start()
    elif (self.to_save_listA is None ) and (self.to_save_listB is not None):
        list_to_validate = "A"
        if not self.threadValidation.isRunning():
            self.threadValidation.start()
    elif (self.to_save_listA is not None )and (self.to_save_listB is not None):
        list_save(self.to_save_listA, self.to_save_listB)   
        flag_list_saved = True    
        if self.threadValidation.isRunning():            
            self.StopValidateFeed()
        # printtoGUI("Item Recorded")
        self.to_save_listA = None
        self.to_save_listB = None
        self.list_to_validate = None
        print("Item Recorded")
def ValidateConfirm(self, result):
    if not result:
        # printtoGUI("Please try again")
        # reset all values, including CT
        objectIDA = None
        objectIDB = None
        for objectID in list(to_save_listA.keys()):
            objectIDA = objectID
        for objectIDB in list(to_save_listB.keys()):
            objectIDB = objectID
        self.to_save_listA["centroid"].reset(objectIDA)
        self.to_save_listB["centroid"].reset(objectIDB)
        self.to_save_listA = None
        self.to_save_listB = None
        self.list_to_validate = None
        self.flag_list_saved = False
        self.StopValidateFeed()
        print("Please Try Again")
    else:
        if not flag_list_saved and (self.to_save_listA is not None and self.to_save_listB is not None):
            list_save(self.to_save_listA, self.to_save_listB)   
            self.StopValidateFeed()
            self.flag_list_saved = False
            self.to_save_listA = None
            self.to_save_listB = None
            self.list_to_validate = None
            # reset all values, don't include ct
            # printtoGUI("ItemRecorded")
            print("Item Recorded")
def StopValidateFeed(self, stop=False):
    self.ValidateFeed.stop()
    self.threadValidation.quit()
    self.threadValidation.exit()
class ValidateFeed(QObject, MainWindow):
    SignalValidation = pyqtSignal(bool)
    SignalStopThread = pyqtSignal(bool)
    def __init__(self):
        super(ValidateFeed, self).__init__()
    
    def validate(self):
        time.sleep(2)
        if flag_list_saved:
            self.SignalStopThread.emit(True)
            # self.stop()
        else:
            checklist = None
            if list_to_validate == "A":
                checklist = self.to_save_listA
            elif list_to_validate == "B":
                checklist = self.to_save_listB
            if checklist is None:
                self.SignalValidation.emit(False)
            else:
                self.SignalValidation.emit(True)
    def stop(self):
        self.quit()
        self.exit()