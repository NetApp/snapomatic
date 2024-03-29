import sys
sys.path.append(sys.path[0] + "/NTAPlib")
import os
import getOracleHome
import getOwner
import userio
import doSqlplus

class startOracleInstance:

    def __init__(self,sid,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.sid=None
        self.home=None
        self.base=None
        self.user=None
        self.start=None
        self.debug=0

        self.apibase=self.__class__.__name__
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        else:
            self.apicaller=''
        localapi='->'.join([self.apicaller,self.apibase])
    
        if 'debug' in kwargs.keys():
            self.debug=kwargs['debug']

        if self.debug & 1:
            userio.message('',service=localapi + ":INIT")
        
        if 'start' in kwargs.keys():
            self.start=kwargs['start']

        self.sid=sid
        
        home=getOracleHome.getOracleHome(sid=self.sid,apicaller=localapi,debug=self.debug)
        if not home.go():
            self.result=home.result
            self.reason=home.reason
            return
        else:
            self.home=home.home
            self.base=home.base
            self.user=home.user

    def go(self,**kwargs):

        if self.home == None or self.base == None:
            self.result=1
            return(False)

        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])

        delim=userio.randomtoken()


        if self.start is None:
            cmd='startup;'
        else:
            cmd='startup ' + self.start + ';'

        out=doSqlplus.doSqlplus(self.sid,cmd,user=self.user,home=self.home,base=self.base,debug=self.debug)
        if out.result > 0:
            self.result=1
            if out.reason is None:
                self.reason="SQLPLUS call failed"
            else:
                self.reason=out.reason
            self.stdout=out.stdout
            self.stderr=out.stderr
            return(False)
        else:
            for line in out.stdout:
                if line == 'Database opened.' and self.start is None:
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return(True)
                elif line == 'Database mounted.' and self.start=="mount":
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return(True)
                elif line[-24:] == 'ORACLE instance started.' and self.start=="nomount":
                    self.result=0
                    self.stdout=out.stdout
                    self.stderr=out.stderr
                    return(True)

            self.result=1
            self.reason="Unable to confirm instance startup"
            self.stdout=out.stdout
            self.stderr=out.stderr
            return(False)

    def showDebug(self):
        userio.debug(self)

