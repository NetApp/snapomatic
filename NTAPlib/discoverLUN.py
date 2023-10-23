import os
import doProcess
import userio

class discoverLUN:

    def __init__(self,path,**kwargs):
        self.result=None
        self.reason=None
        self.stdout=[]
        self.stderr=[]
        self.igroup=None
        self.svm=None
        self.path=path
        self.lunpath=None
        self.luntype=None
        self.lun=None
        self.volume=None
        self.size=None
        self.blocksize=None
        self.protocol=None
        self.debug=False

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
        
        if 'cache' in kwargs.keys():
            store=kwargs['cache']
            cache=True
        else:
            cache=False

        if not os.path.isfile('/usr/bin/sg_raw'):
            self.result=1
            self.reason="Cannot find /usr/bin/sg_raw"
            return

    def showDebug(self):
        userio.debug(self)

    def go(self,**kwargs):
    
        if 'apicaller' in kwargs.keys():
            self.apicaller=kwargs['apicaller']
        localapi='->'.join([self.apicaller,self.apibase + ".go"])
        
        if not os.path.isfile('/usr/bin/sg_raw'):
            self.result=1
            self.reason="Cannot find /usr/bin/sg_raw"
            if self.debug & 1:
                self.showDebug()
            return(False)
        
        sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.path + " 12 00 00 00 ff 00",debug=self.debug,encoding=None, binary=True)
    
        if sgcmd.result > 0:
            self.result=1
            self.reason="Cannot execute /usr/bin/sg_raw"
            self.stderr=sgcmd.stderr
            return(False)
        
        self.luntype=sgcmd.stdout[8:14]
    
        try:
            self.luntype=sgcmd.stdout[8:14].decode('utf8')
        except:
            self.reason="Cannot find LUN owner for " + self.path
            self.error=1
            self.stderr=sgcmd.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
    
        if self.luntype is None:
            self.reason="Unknown owner for " + self.path
            self.error=1
            self.stderr=sgcmd.stderr
            if self.debug & 1:
                self.showDebug()
            return(False)
    
        if self.luntype=='NETAPP':
            sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.path + " c0 00 02 0a 98 0a FF 10 00 00", debug=self.debug,encoding=None, binary=True)
            if sgcmd.result > 0:
                self.reason="Cannot execute /usr/bin/sg_raw"
                self.error=1
                self.stderr=sgcmd.stderr
                return(False)
    
            outstring=sgcmd.stdout
            startofblock=8
            while startofblock<len(outstring):
                pagecode=hex(outstring[startofblock])
                length=int.from_bytes(outstring[startofblock+2:startofblock+4],"big")
                if pagecode=='0x0':
                    self.svm=outstring[startofblock+4:startofblock+length].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x10':
                    self.lunpath=outstring[startofblock+4:startofblock+length].decode('utf-8').rstrip('\x00')
                    self.volume=self.lunpath.split('/')[2]
                elif pagecode == '0x11':
                    self.volname=outstring[startofblock+20:startofblock+length].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x16':
                    self.igroup=outstring[startofblock+8:startofblock+length].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x22':
                    self.ontapversion=outstring[startofblock+4:startofblock+22].decode('utf-8').rstrip('\x00')
                elif pagecode == '0x40':
                    self.protocol='ISCSI'
                startofblock=startofblock+(length)
            sgcmd=doProcess.doProcess("/usr/bin/sg_raw -r 4k -b " + self.path + " 9e 10 00 00 00 00 00 00 00 00 00 00 00 FF 00 00",debug=self.debug,encoding=None, binary=True)
            if sgcmd.result > 0:
                self.reason="Cannot execute /usr/bin/sg_raw"
                self.error=1
                self.stderr=sgcmd.stderr
                return(False)
    
            outstring=sgcmd.stdout
            totalblocks=int.from_bytes(outstring[0:8],"big")
            blocksize=int.from_bytes(outstring[9:12],"big")
            lunsize=totalblocks * blocksize
            self.size=int(lunsize)
            self.blocksize=blocksize
        else:
            self.reason="Cannot execute /usr/bin/sg_raw"
            self.error=1
            self.stderr=sgcmd.stderr
            return(False)

#        if self.cache:
#            store.cacheLUN(self.path,
#                           self.lunpath,
#                           self.igroup,
#                           self.svm,
#                           self.size,
#                           self.blocksize,
#                           self.protocol)
        
        if self.debug & 1:
            self.showDebug()
        self.result=0
        return(True)
    