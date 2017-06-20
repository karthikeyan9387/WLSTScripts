##################################################
# This script is used to check the status of all WL instances including the admin
# Send proactive alert message when server state goes to warning state
# Send Proactive alert when stuck threads are about to occur
# @author : Karthikeyan Ulaganthan
###########################################################

def conn():
    UCF='/u01/configfile.secure'
    UKF='/u01/keyfile.secure'
    admurl = "t3://localhost:7001"

    try:
        connect(userConfigFile=UCF, userKeyFile=UKF, url=admurl)
    except ConnectionException,e:
        print '\033[1;31m Unable to find admin server...\033[0m'
        exit()

def ServrState():
    print 'Fetching state of every WebLogic instance'
    for name in serverNames:
        try:
            cd("/ServerLifeCycleRuntimes/" + name.getName())
            serverState = cmo.getState()
            if serverState != "RUNNING":
                alertmsg = 'Production Server ' + name.getName() + ' is ' + serverState + ' state '
                serverName = name.getName()
                sendMail(alertmsg,serverState,serverName)
        except WLSTException,e:
            pass
    for name in serverNames:
        try:
            cd("/ServerRuntimes/" + name.getName())
            serverHealthState = cmo.getOverallHealthState()
            # print name.getName(),"Server health State" , serverHealthState
            if str(serverHealthState).find("HEALTH_OK") == -1:
                serverStateMsg = str(serverHealthState).split(",")
                alertmsg = 'Production Server ' + name.getName() + ' is in ' + serverStateMsg[1]
                serverName = name.getName()
                sendMail(alertmsg,serverStateMsg[1],serverName)
        except WLSTException,e:
            pass

def alertStuckThreads():
    for name in serverNames:
        try:
            cd("/ServerRuntimes/" + name.getName() + "/ThreadPoolRuntime/ThreadPoolRuntime")
            executeTTC=cmo.getExecuteThreadTotalCount()
            hoggerTC=cmo.getHoggingThreadCount()
            print 'Execute Threads '+ name.getName() + ': ', executeTTC
            print 'Hogger Thread Count ' + name.getName() + ': ', hoggerTC
            if hoggerTC != 0:
                ratio=(executeTTC/hoggerTC)
                print "Ratio" , ratio
                if ratio <= 2:
                    alertmsg = "!!!! ALERT !!!! Stuck Threads are on its way....." + "on server" + name.getName() + "\n" + "Execute Threads "+ name.getName() + ": " +  str(executeTTC) + "\n" +"Hogger Thread Count " + name.getName() + ": " + str(hoggerTC)
                    stuckState = "might be in stuck state!"
                    serverName = name.getName()
                    sendMail(alertmsg,stuckState,serverName)
                    print "Starting to take ThreadDumps..."
                    for counter in range(0,6):
                        java.lang.Thread.sleep(5000)
                        fileName = '/u01/ThreadDumps/dump' + str(name.getName()) + '_' + str(java.util.Calendar.getInstance().getTimeInMillis()) + '.dmp'
                        serverName = str(name.getName())
                        threadDump('true',fileName,serverName)
        except WLSTException,e:
            pass

def quit():
    disconnect()
    exit()

def sendMail(alertmsg,serverStatemsg,serverName):
    sendmail_location = "/usr/sbin/sendmail" # sendmail location
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write("From: %s\n" % "no-reply@example.com")
    p.write("To: %s\n" % "karthikeyan.ulaganathan@example.com")
    p.write("Subject: Alert! - Production Server "+ str(serverName) + " " + serverStatemsg +"\n")
    p.write("\n") # blank line separating headers from body
    p.write(alertmsg)
    status = p.close()
    if status != 0:
           print "Sendmail exit status", status

if __name__== "main":
    #redirect('./logs/Server.log', 'false')
    conn()
    serverNames = cmo.getServers()
    domainRuntime()
    ServrState()
    alertStuckThreads()
    quit()
