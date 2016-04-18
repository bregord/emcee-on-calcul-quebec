import scp
import ConfigParser
import paramiko


def transferData():

    config = ConfigParser.ConfigParser()
    config.read('server.cfg')
    a = config.get('SSH', 'hostname') # returns 12.2

    cluster = config.get("CLUSTER", "name")
    host = config.get('SSH', 'hostname') # returns 12.2
    login = config.get('SSH', 'login')
    path = config.get('SSH', 'pathToKey')

    try:

        ssh = paramiko.SSHClient()
        ssh.load_host_keys(path)

        ssh.connect(host, username=login)
        scps = scp.SCPClient(ssh.get_transport())

        print "sending tar file"
        scps.put('data.tar.gz', './workspace/')
        scps.put('build.sh', '.')

        scps.put('detectorModel.py', './workspace/')
        #scps.put('test', '.')
        #scp.get('test2.txt')
        print "unzipping tar file"
        ssh.exec_command('tar -xzvf ./workspace/data.tar.gz')

        scps.close()
        ssh.close()


    except paramiko.AuthenticationException as e:
        print e

transferData()
