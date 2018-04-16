#https://github.com/TheHiddenGamer23 was a source for the server wrapper part of this


#for backup script
import os
import zipfile
import time #for the backup timestamp
import datetime


class library:
    def getDirSize(dir): #this gets the directory size
        folderSize = 0
        for root, dirs, files in os.walk(dir,followlinks=False): #goes through all the files and folders
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




class backup:
    def __init__(self):

        self.backupLocation = "./backups"
        self.backupDir = "."
        self.createbackupLocation()
        

    def createbackupLocation(self):
        if not os.path.exists(self.backupLocation):
            os.makedirs(self.backupLocation)
            self.createbackupLocation()


    def createBackup(self):
        if library.getDriveFree("./") > library.getDirSize("./world") and library.getDriveFree("./") - library.getDirSize("./world") > 1024*1024*1024:
            backupTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            backupTitle= "{0}/{1}.zip".format(self.backupLocation,backupTime)

            zf = zipfile.ZipFile(backupTitle, "w",compression=zipfile.ZIP_DEFLATED,allowZip64=True)
            os.chmod(backupTitle,0o755)
            for dirname, subdirs, files in os.walk(self.backupDir):
                #print(dirname)
                #add a loop to check for a list of excluded stuff
                if dirname != self.backupLocation:
                    zf.write(dirname)
                    for filename in files:
                        zf.write(os.path.join(dirname, filename))
            zf.close()


    def purgeBackups(self):
        current_time = time.time()

        for f in os.listdir(self.backupLocation):
            file = "{0}/{1}".format(self.backupLocation,f)
            creation_time = os.path.getmtime(file)
            if (current_time - creation_time) // (24*3600) >= 7:
                os.unlink(file)
                print('{} removed'.format(f))
        if library.getDriveFree("./") < library.getDirSize("./world") and (library.getDriveFree("./") - library.getDirSize("./world")) < 1024*1024*1024:
            os.unlink(library.findOldestFile(self.backupLocation))


#for server script
import subprocess, sys
from threading import Thread
import time
import os
class Server:
    def __init__(self):
        self.process = None
        self.ServerThread = None
        self.backup = backup()
        self.backupThread = Thread(target=self.backupScript,daemon=True) #start backup as a thread
        


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
                        self.backupThread = Thread(target=self.backupScript,daemon=True) #start backup as a thread
                        self.backupThread.start()
                    else:
                        print("Backup already occuring")
                else:
                    print("This is a placeholder for the help dialog")
            else:
                self._writeConsole(command)

    def backupScript(self):
        self._writeConsole("say Starting Backup")
        self._writeConsole("save-off")
        self._writeConsole("save-all")
        self.backup.createBackup()
        self._writeConsole("save-on")
        self._writeConsole("save-all")
        self.backup.purgeBackups()
        self._writeConsole("say Backup Complete")

s = Server()

s.main()