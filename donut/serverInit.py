import ConfigParser
import paramiko

config = ConfigParser.ConfigParser()
config.read('server.cfg')
a = config.get('SSH', 'hostname') # returns 12.2

cluster = config.get("CLUSTER", "name")
host = config.get('SSH', 'hostname') # returns 12.2
login = config.get('SSH', 'login')
path = config.get('SSH', 'pathToKey')

modules = config.items('MODULES')

firstTime = config.getboolean('CLUSTER', 'firstTime')

#find the cluster and log into it
ssh = paramiko.SSHClient()
ssh.load_host_keys(path)

if cluster == 'guillim':
    print "Logging into guillim"

    try:
        ssh.connect(host, username=login)
        if firstTime:
            print "First time connecting. Initializing server"
            ssh.exec_command('echo -e "# .bash_profile" > .bash_profile')
            ssh.exec_command('echo -e "# Get the aliases and functions\n" >> .bash_profile')
            ssh.exec_command('echo -e "if [ -f ~/.bashrc ]; then\n    . ~/.bashrc\n    fi\n" >> .bash_profile')
            ssh.exec_command('echo -e "PATH=$PATH:$HOME/bin\n" >> .bash_profile')
# User specific environment and startup programs


            for el in modules:
                ssh.exec_command('echo -e "' + el[1] +'\n" >> .bash_profile')


            config.set('CLUSTER', 'firstTime', 'False')
        else:
            print "already initialized"

    except paramiko.AuthenticationException as e:
        print e

else:
    print "ERROR. CLUSTER NOT FOUND"
