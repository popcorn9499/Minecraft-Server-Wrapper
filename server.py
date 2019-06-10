#https://github.com/TheHiddenGamer23 was a source for the server wrapper part of this


#for backup script
import os
import zipfile
import time #for the backup timestamp
import datetime


class library:
    def getDirSize(dir,ignoreDir=[]): #this gets the directory size
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
                #print("Delete: {0}".format(oldestFile))
        return oldestFile

    def fileHumanReadable(num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def file_size(fname):
        return os.path.getsize(fname)





class backup:
    def __init__(self,Server):
        self.server = Server
        self.backupLocation = "./backups"
        self.backupDir = "."
        self.createbackupLocation()
        self.oldestBackups = 7
        self.compressionLevel = 9
        #/title @a actionbar ["",{"text":"This is an example actionbar","color":"dark_purple"}]
        #reminder for later
        
    def backupScript(self):
        self.server._writeConsole("say Starting Backup")
        self.server._writeConsole("save-off")
        self.server._writeConsole("save-all")
        size = self.createBackup()
        size = library.fileHumanReadable(size)
        self.server._writeConsole("save-on")
        self.server._writeConsole("save-all")
        self.purgeBackups()
        self.server._writeConsole("say Backup Complete {0}".format(size))

    def createbackupLocation(self):
        if not os.path.exists(self.backupLocation):
            os.makedirs(self.backupLocation)
            self.createbackupLocation()

    def createBackup(self):
        spaceForBackup = library.getDriveFree(self.backupLocation) > library.getDirSize("./world")
        extraSpaceForBackup = library.getDriveFree(self.backupLocation) - library.getDirSize("./world") > 1024*1024*1024

        if spaceForBackup and extraSpaceForBackup:
            
            backupTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            backupTitle= "{0}/{1}.zip".format(self.backupLocation,backupTime)
            zf = zipfile.ZipFile(backupTitle, "w",compression=zipfile.ZIP_DEFLATED,compresslevel=self.compressionLevel,allowZip64=True)
            os.chmod(backupTitle,0o755)

            worldSize = library.getDirSize(self.backupDir,[self.backupLocation])
            print(worldSize)
            currentSize = 0
            lastTime = time.time()

            for dirname, subdirs, files in os.walk(self.backupDir):
                #print(dirname)
                #add a loop to check for a list of excluded stuff
                if dirname != self.backupLocation:
                    zf.write(dirname)
                    for filename in files:
                        currentTime = time.time() 
                        currentSize = currentSize + library.file_size(os.path.join(dirname, filename))
                        if currentTime - lastTime >=5:
                            lastTime=currentTime
                            #/title @a actionbar ["",{"text":"This is an example actionbar","color":"dark_purple"}]
                            self.server._writeConsole("say {0}".format(percentage))
                        
                        self.server._writeConsole("say {0}".format(percentage))
                        zf.write(os.path.join(dirname, filename))
            print(currentSize)
            zf.close()
            size = library.file_size(backupTitle)
            return size


    def purgeBackups(self):
        current_time = time.time()

        for f in os.listdir(self.backupLocation): #checks if any backups are older than x.
            file = "{0}/{1}".format(self.backupLocation,f)
            creation_time = os.path.getmtime(file)
            if (current_time - creation_time) // (24*3600) >= self.oldestBackups:
                os.unlink(file)
                print('{} removed'.format(f))

        freeBackupLessThanWorldSize = library.getDriveFree(self.backupLocation) < library.getDirSize("./world")
        lessThanGBFree = (library.getDriveFree(self.backupLocation) - library.getDirSize("./world")) < 1024*1024*1024

        if freeBackupLessThanWorldSize and lessThanGBFree:
            os.unlink(library.findOldestFile(self.backupLocation)) #removes the oldest backup if


#for server script
import subprocess, sys
from threading import Thread
import time
import os
class Server:
    def __init__(self):
        self.process = None
        self.ServerThread = None
        self.backup = backup(self)
        self.backupThread = Thread(target=self.backup.backupScript,daemon=True) #start backup as a thread
        


    def _listen(self):
        while True:
            line = self.process.stdout.readline()
            process = self.process.poll()
            if not line and process is not None:
                break
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
            if command.lower().startswith("!"):
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

    

s = Server()

s.main()