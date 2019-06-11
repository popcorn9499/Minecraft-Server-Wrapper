#https://github.com/TheHiddenGamer23 was a source for the server wrapper part of this


#for backup script
import os
import zipfile
import time #for the backup timestamp
import datetime
import math
import json

class library:
    def getDirSize(dir,ignoreDir=[""]): #this gets the directory size
        folderSize = 0
        for root, dirs, files in os.walk(dir,followlinks=False): #goes through all the files and folders
            for ignore in ignoreDir:
                if root != ignore:
                    for x in files:
                        if os.path.islink("{0}/{1}".format(root,x)) == False and os.path.isfile("{0}/{1}".format(root,x)): #checks if its a link or not
                            folderSize = folderSize + os.path.getsize("{0}/{1}".format(root,x)) #gets the file size of the file and adds it to the total size
        return folderSize

    def getDriveFree(dir): #gets the drive space free
        statvfs = os.statvfs("./")
        spaceFree= statvfs.f_frsize * statvfs.f_bavail
        return spaceFree

    def creationTime(current_time,file):
        if file != "":
            creation_time = os.path.getmtime(file)
            return (current_time - creation_time)
        else:
            return 0

    def findOldestFile(dir):
        oldestFile = ""
        current_time = time.time()
        for f in os.listdir(dir):
            file = "{0}/{1}".format(dir,f)
            if library.creationTime(current_time,file) > library.creationTime(current_time,oldestFile):
                oldestFile=file
        return oldestFile

    def fileHumanReadable(num, suffix='B'):
        try:
            for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
                if abs(num) < 1024.0:
                    return "%3.1f%s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f%s%s" % (num, 'Yi', suffix)
        except:
            return num

    def file_size(fname):
        return os.path.getsize(fname)

    #file load and save stuff
    def fileSave(fileName,config):
        f = open(fileName, 'w') #opens the file your saving to with write permissions
        f.write(json.dumps(config,sort_keys=True, indent=4 ) + "\n") #writes the string to a file
        f.close() #closes the file io

    def fileLoad(fileName):#loads files
        with open(fileName, 'r') as handle:#loads the json file
            config = json.load(handle) 
        return config

    def loadConf(file):
        file = library.fileLoad(file.format(os.sep))
        return file

    def checkFolder(folderPath,folderName):
        if os.path.isdir(folderPath) == False:
            print("{0} Folder Does Not Exist".format(folderName))
            print("Creating...")
            os.makedirs(folderPath)

    def checkFile(examplePath,filePath,fileName):
        if (os.path.isfile(filePath) == False):
            print("{0} File Does Not Exist".format(fileName))
            print("Creating...")
            data = fileLoad(examplePath)
            library.fileSave(filePath,data)


class backup:
    def __init__(self,Server,config):
        
        self.backupLocation = config["backupLocation"]
        self.backupDir = config["backupDir"]
        self.oldestBackups = config["oldestBackups"]
        self.compressionLevel = config["compressionLevel"]
        self.titleBars = config["titleBars"]
        self.compressionMethod = config["compressionMethod"] # supports "pigz" "gzip" "zip" other methods are easy to add however
        self.compressionThreads = config["compressionThreads"] #limits compression threads on multi threaded compression tools
        self.createbackupLocation()
        self.server = Server

        self.process = None
        self.processThread = None
               
    def backupScript(self):
        print("Starting Server Backup")
        if self.titleBars:
            self.server._writeConsole('title @a actionbar ["",{"text":"Starting Server Backup","color":"dark_purple"}]')
        else:
            self.server._writeConsole("say Starting Server Backup")
        self.server._writeConsole("save-off")
        self.server._writeConsole("save-all")
        time.sleep(1)
        size = self.createBackup()
        size = library.fileHumanReadable(size)
        self.server._writeConsole("save-on")
        self.server._writeConsole("save-all")
        self.purgeBackups()
        if self.titleBars:
            self.server._writeConsole('title @a actionbar ["",{"text":"Server Backup Completed '+ str(size) +'","color":"dark_purple"}]')
        else:
            self.server._writeConsole("say Server Backup Complete {0}".format(size))

    def createbackupLocation(self):
        if not os.path.exists(self.backupLocation):
            os.makedirs(self.backupLocation)
            self.createbackupLocation()

    def createBackup(self):
        spaceForBackup = library.getDriveFree(self.backupLocation) > library.getDirSize("./world")
        extraSpaceForBackup = library.getDriveFree(self.backupLocation) - library.getDirSize("./world") > 1024*1024*1024
        if spaceForBackup and extraSpaceForBackup:
            backupTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            backupTitle= "{0}/{1}".format(self.backupLocation,backupTime)
           
            
            self.worldSize = library.getDirSize(self.backupDir,[self.backupLocation])
            self.currentSize = 0
            lastTime = time.time()
            if self.compressionMethod == "zip":
                backupTime= backupTime + ".zip"
                zf = zipfile.ZipFile(backupTitle, "w",compression=zipfile.ZIP_DEFLATED,compresslevel=self.compressionLevel,allowZip64=True)
                for dirname, subdirs, files in os.walk(self.backupDir):
                    if dirname != self.backupLocation:
                        zf.write(dirname)
                        for filename in files:
                            currentTime = time.time() 
                            self.currentSize = self.currentSize + library.file_size(os.path.join(dirname, filename))
                            if currentTime - lastTime >=2: #waits until 2 seconds since the last time this section was executed have passed
                                lastTime=currentTime
                                percentage = math.floor((self.currentSize / self.worldSize) * 100)
                                print("Server Backup " + str(percentage) + "%")
                                if self.titleBars:
                                    self.server._writeConsole('title @a actionbar ["",{"text":"Server Backup ' + str(percentage) + '%","color":"dark_purple"}]')
                            zf.write(os.path.join(dirname, filename))
                zf.close()
            elif self.compressionMethod == "gzip":
                backupTitle = backupTitle + ".tar.gz"
                args="nice -n 19 tar --exclude='{1}' -cvf - '{0}'  | gzip -{2} > '{3}'".format(self.backupDir,self.backupLocation,self.compressionLevel,backupTitle)
                print(args)
                self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True) #starts the server process
                #self.processThread = Thread(target=self._listen, daemon=True).start() #daemon thread in the background.
                self._listen()
            elif self.compressionMethod == "pigz":
                backupTitle = backupTitle + ".tar.gz"
                args="nice -n 19 tar --exclude='{1}' -cvf - '{0}'  | pigz -{2} -p {4} > '{3}'".format(self.backupDir,self.backupLocation,self.compressionLevel,backupTitle,self.compressionThreads)
                print(args)
                self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,shell=True) #starts the server process
                #self.processThread = Thread(target=self._listen, daemon=True).start() #daemon thread in the background.
                self._listen()
                
            os.chmod(backupTitle,0o755)
            size = library.file_size(backupTitle)
            return size

    def _listen(self):
        lastTime = time.time()
        print("Backing up")
        while True:
            line = self.process.stdout.readline()
            process = self.process.poll()
            if not line and process is not None:
                break
            try:
                self.currentSize = self.currentSize + library.file_size(line.decode().strip())
            except:
                pass
            currentTime = time.time() 
            if currentTime - lastTime >=2: #waits until 2 seconds since the last time this section was executed have passed
                lastTime=currentTime
                percentage = math.floor((self.currentSize / self.worldSize) * 100)
                print("Server Backup " + str(percentage) + "%")
                if self.titleBars:
                    self.server._writeConsole('title @a actionbar ["",{"text":"Server Backup ' + str(percentage) + '%","color":"dark_purple"}]')
        print("BACKUP COMPLETE")
            #print('', end='', flush=True)# end='' so that it doesn't go to a new line, to finish input on this line.
        
    def purgeBackups(self): #purges old backups either for more space or due to too many backups
        current_time = time.time()

        for f in os.listdir(self.backupLocation): #checks if any backups are older than x.
            file = "{0}/{1}".format(self.backupLocation,f)
            creation_time = os.path.getmtime(file)
            if (current_time - creation_time) // (24*3600) >= self.oldestBackups:
                os.unlink(file)
                print('{} removed'.format(f))

        freeBackupLessThanWorldSize = library.getDriveFree(self.backupLocation) < 3*library.getDirSize("./world") #we multiply world size by 3 to allow us to have some free space after the backup for another backup
        lessThanGBFree = (library.getDriveFree(self.backupLocation) - library.getDirSize("./world")) < 1024*1024*1024

        if freeBackupLessThanWorldSize and lessThanGBFree:
            os.unlink(library.findOldestFile(self.backupLocation)) #removes the oldest backup if


#for server script
import subprocess, sys
from threading import Thread
import time
import os
class Server:
    def __init__(self,configName):
        self.process = None
        self.ServerThread = None
        config = library.fileLoad(configName)
        self.backup = backup(self,config)
        self.backupThread = Thread(target=self.backup.backupScript,daemon=True) #start backup as a thread
        self.cmdAllowedList = config["cmdAllowedUserList"]
        
    def listenCommands(self,message):#listens for commands executed by users on the server
        for user in self.cmdAllowedList:
            if -1 != message.find("{0} issued server command: /Backup".format(user)):
                if self.backupThread.isAlive() == False:
                    self.backupThread = Thread(target=self.backup.backupScript,daemon=True) #start backup as a thread
                    self.backupThread.start()
                else:
                    self._writeConsole("msg {0} Backup Already Occuring".format(user))
                    print("Backup already occuring")


    def _listen(self):
        while True:
            line = self.process.stdout.readline()
            process = self.process.poll()
            if not line and process is not None:
                break
            self.listenCommands(line.decode().strip())
            print('\r'+line.decode().strip())
            #print('', end='', flush=True)# end='' so that it doesn't go to a new line, to finish input on this line.
        print('\rServer Closed with code: {}'.format(self.process.poll())) #line feed to return to the start of the line, will be processed on the flush with the next line
        os._exit(1)#kills the process entirely

    def _writeConsole(self,console):
        self.process.stdin.write((console+"\r\n").encode())
        self.process.stdin.flush()

    def main(self):
        args = sys.argv
        args.pop(0)

        print(args)
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) #starts the server process
        self.ServerThread = Thread(target=self._listen, daemon=True).start() #daemon thread in the background.
        while True:
            command=input()
            if command.lower().startswith("!"): #listens for the commands in the console
                if command.lower() == "!backup":
                    if self.backupThread.isAlive() == False:
                        self.backupThread = Thread(target=self.backup.backupScript,daemon=True) #start backup as a thread
                        self.backupThread.start()
                    else:
                        print("Backup already occuring")
                else:
                    print("This is a placeholder for the help dialog")
            else:
                self._writeConsole(command)

config = "wrapperConfig.json"
if (os.path.isfile(config) == False):#checks if the config exists or not
    configContents = {"backupLocation": "./backups", "backupDir": ".", "oldestBackups": 7, "compressionLevel": 9, "cmdAllowedUserList": [],"titleBars": True,"compressionMethod": "zip","compressionThreads": "4"}
    library.fileSave(config,configContents)



s = Server(config)

s.main()