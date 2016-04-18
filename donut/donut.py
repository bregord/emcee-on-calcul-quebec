import sys
import paramiko
import ConfigParser
import scp
import tarfile
import os


def help():
    print "flags:\n --init [SERVER NAME] \n \
--transfer-to [user] [SERVER NAME] file1.ext file2.ext ... \n \
--transfer-from [user] [SERVER NAME] file3.ext file2.ext ... \n \
Server Options: Guillimin, Briaree, Colosse. MP2, MS2, PSI not supported    "

config = ConfigParser.ConfigParser()
config.read('server.cfg')

#cluster = config.get("CLUSTER", "name")
#host = config.get('SSH', 'hostname') # returns 12.2
login = config.get('SSH', 'login')
path = config.get('SSH', 'pathToKey')

modules = config.items('MODULES')

firstTime = config.getboolean('CLUSTER', 'firstTime')

#find the cluster and log into it
ssh = paramiko.SSHClient()
ssh.load_host_keys(path)


def getHostname(args):
    host = args[2].lower()

    if(host == "guillimin"):
        return "guillimin.hpc.mcgill.ca"


    elif(host == "briaree"):
        return "briaree.calculquebec.ca"

    elif(host=="colosse"):
        return "colosse.calculquebec.ca"

    else:
        print "Server name not recognized. Enter guillimin or briaree or colosse"
        sys.exit()

def getFolder(args):
    folder = args[3].lower()

    if(folder == "programs:"):
        return "programs/"

    elif(folder == "data:"):
        return "data/"

    elif(folder == "workspace:"):
        return ""

    elif(folder == "jobs:"):
        return "jobs/"

    else:
        print "Folder not specified. defaulting to workspace"
        return ""


def transferFrom(arg, login, path):
    host = getHostname(arg)

    folder = getFolder(arg)

    try:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(path)
        ssh.connect(host, username=login)
        scps = scp.SCPClient(ssh.get_transport())


        files = ""

        for file in range(4,len(arg)):
            files = files + folder+arg[file] + " "

        ssh.exec_command('tar -zcvf transit.tar.gz ' +  files)

        scps.get('./workspace/'+ folder + 'transit.tar.gz')


        scps.close()
        ssh.close()


    except paramiko.AuthenticationException as e:
        print e

    except tarfile.TarError as e:
        print e
    #get error for tarfile


def transferTo(arg,login, path):

    host = getHostname(arg)
    folder = getFolder(arg)

    try:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(path)
        ssh.connect(host, username=login)
        scps = scp.SCPClient(ssh.get_transport())

        tar = tarfile.open("transit.tar.gz", "w")
        for file in range(4, len(arg)):
            if(arg[file][0] == "-" or (arg[file][0] == "-" and arg[file][1] == "-")):
                print arg[file] + " is not a valid flag"

            if(os.path.isfile(arg[file])):
                tar.add(arg[file])

            else:
                print "file " + arg[file] + " not found"
                sys.exit()

        print "sending tar file"

        scps.put('transit.tar.gz', './workspace/' + folder)

        print "unzipping tar file"
        ssh.exec_command('tar -xzvf ./workspace/data.tar.gz')

        scps.close()
        ssh.close()


    except paramiko.AuthenticationException as e:
        print e

    except tarfile.TarError as e:
        print e
    #get error for tarfile


def initServer(arg,login, path):

    hostname = getHostname(arg)

    print "test"

    try:
        ssh.connect(hostname, username=login)
        #check if stuff exists
        ssh.exec_command('mkdir workspace')
        ssh.exec_command('cd workspace')
        ssh.exec_command('mkdir programs')
        ssh.exec_command('mkdir jobs')
        ssh.exec_command('mkdir data')
        ssh.close()

    except paramiko.AuthenticationException as e:
        print e


def main():

    arg = sys.argv
    config = ConfigParser.ConfigParser()
    config.read('server.cfg')

#cluster = config.get("CLUSTER", "name")
#host = config.get('SSH', 'hostname') # returns 12.2
    login = config.get('SSH', 'login')
    path = config.get('SSH', 'pathToKey')

    if arg[1].lower() == "--transfer-to":
        transferTo(arg, login, path)


    elif arg[1].lower() == "--transfer-from":
        transferFrom(arg, login, path)

    elif arg[1].lower() == "--init":
        initServer(arg, login, path)

    elif arg[1].lower() == "--help" or arg[1].lower() == "--help" or arg[1].lower() == "--h":
        help()

    else:
        print "Command not recognized. use the --help or --h flag to print a list of available commands"



if __name__ == "__main__":
    main()
