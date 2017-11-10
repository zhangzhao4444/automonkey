#!/usr/bin/evn python
# -*- coding:utf-8 -*-

import platform
import subprocess,signal
import re,time,os
import threading,traceback
from lxml import etree
import logger
logobj=logger.logobj

#Q adb devices not see any devices--http://jingyan.baidu.com/article/ce09321b5b76642bff858f31.html

def excepter(func):
    def execute(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            logobj.error(traceback.format_exc())
        return None
    return execute

class ADB():
    def __init__(self, id):
        self.deviceid = id
        self.system = platform.system()
        self.pagesource = ''
        self.installsucc = False
        self.needperf = True
        self.cpu = []
        self.mem = []
        self.totalmem = 0
        self.nettotal = []
        self.netrev = []
        self.netsnd = []
        self.mempercend = []
        self.anr = []
        self.crash = []
        self.tombstone = []
        self.oom = []
        if 'ANDROID_HOME' in os.environ:
            if self.system == 'Windows': self.command = os.path.join(os.environ['ANDROID_HOME'],'platform-tools','adb.exe')
            else: self.command = os.path.join(os.environ['ANDROID_HOME'],'platform-tools','adb')
        else: raise EnvironmentError('not found $ANDROID_HOME')
        if self.system == 'Windows': self.pipecmd = 'findstr'
        else : self.pipecmd = 'grep'

    def adb(self, args):
        start = time.time()
        process = subprocess.Popen('%s -s %s %s'%(self.command,self.deviceid,str(args)),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, error = process.communicate()
        out = []
        # if error:
        #     logobj.error(bytes.decode(error).replace('\r\r\n', '\n'))
        #     return []
        output = bytes.decode(output).replace('\r\r\n', '\n')
        for line in output.split('\n'):
            out.append(line.strip())
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
        try:
            process.kill()
        except OSError as e:
            logobj.error(e)
        return out

    def shell(self,args):
        process = subprocess.Popen('%s -s %s shell %s'%(self.command,self.deviceid,str(args)),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, error = process.communicate()
        out = []
        # if error:
        #     logobj.error(bytes.decode(error).replace('\r\r\n','\n'))
        #     return []
        output = bytes.decode(output).replace('\r\r\n','\n')
        for line in output.split('\n'):
            out.append(line.strip())
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
        try:
            process.kill()
        except OSError as e:
            logobj.error(e)
        return out

    @excepter
    def getdevicestate(self):
        for line in self.adb('get-state'):
            if line: return line

    @excepter
    def getdeviceid(self):
        for line in self.adb('get-serialno'):
            if line: return line

    @excepter
    def getandroidversion(self):
        for line in self.shell('getprop ro.build.version.release'):
            if line: return line

    @excepter
    def getsdkversion(self):
        for line in self.shell('getprop ro.build.version.sdk'):
            if line: return line

    @excepter
    def getdevicemodel(self):
        for line in self.shell('getprop ro.product.model'):
            if line: return line

    @excepter
    def getprocess(self,package):
        if self.system =='Windows': cmd = 'ps | %s %s'%(self.pipecmd,package)
        else : cmd = 'ps | %s -w %s'%(self.pipecmd,package)
        process = []
        for line in self.shell(cmd):
            if re.compile(package).findall(line): process.append(line)
        return process

    def getpid(self,package):
        processs = self.getprocess(package)
        ret = []
        for p in processs:
            pid = re.compile(' (\d+) ').findall(p)[0]
            process = re.compile(' ('+package+'\S*)').findall(p)[0]
            ret.append((process,pid))
        return ret

    @excepter
    def getuid(self,pid):
        for line in self.shell('cat /proc/%s/status'%pid):
            if line :
                if 'uid' in line.lower(): return line.split()[1]

    @excepter
    def killprocess(self,pid):
        # need root
        result = ''
        for line in self.shell('kill %s'%pid):
            if line : result = line.split(':')[-1].strip(' ')
        if not result : return 'kill success'
        return result

    @excepter
    def quitapp(self,package):
        for line in self.shell('am force-stop %s'%package):
            if line : return line

    @excepter
    def getfocusedactivity(self):
        for line in self.shell('dumpsys activity activities | %s mFocusedActivity'%self.pipecmd):
            if line : return line.strip().split(' ')[3]

    def getcurrentpackage(self):
        return self.getfocusedactivity().split('/')[0]

    def getcurrentactivity(self):
        return self.getfocusedactivity().split('/')[-1]

    @excepter
    def getappservers(self,package):
        list = []
        for line in self.shell('dumpsys activity services %s'%package):
            if 'intent' in line:
                server = line.split('=')[-1].split('}')[0].replace('(has extras)','').strip(' ')
                if server not in list: list.append(server)
        return list

    def getcurrentservers(self):
        return self.getappservers(self.getcurrentpackage())

    @excepter
    def getbatterylevel(self):
        for line in self.shell('dumpsys battery | %s level'%self.pipecmd):
            if line : return line.split(': ')[-1]

    @excepter
    def getbatterystatus(self):
        status = {1:'unknow',2:'charging',3:'discharging',4:'notcharging',5:'full'}
        for line in self.shell('dumpsys battery | %s status'%self.pipecmd):
            if line :
                s = line.split(': ')[-1]
                return status[int(s)]

    @excepter
    def getbatterytemp(self):
        for line in self.shell('dumpsys battery | %s temperature'%self.pipecmd):
            if line :return int(line.split(': ')[-1])/10.0

    @excepter
    def getscreenhw(self):
        for line in self.shell('dumpsys window displays | %s init'%self.pipecmd):
            if line:
                screen = re.compile('\d+').findall(line)
                return int(screen[0]),int(screen[1])
        return 0,0

    @excepter
    def reboot(self):
        self.adb('reboot')

    @excepter
    def fastboot(self):
        self.adb('reboot bootloader')

    @excepter
    def delfile(self):
        self.shell('rm /data/local/tmp/*.png' )

    @excepter
    def getsystemapps(self):
        list = []
        for line in self.shell('pm list packages -s'):
            app = line.split(':')[-1]
            if app not in list :list.append(app)
        return list

    @excepter
    def getuserapp(self):
        list = []
        for line in self.shell('pm list packages -3'):
            app = line.split(':')[-1]
            if app not in list :list.append(app)
        return list

    @excepter
    def getsearchapp(self,key):
        list = []
        for line in self.shell('pm list packages %s'%key):
            app = line.split(':')[-1]
            if app not in list :list.append(app)
        return list

    @excepter
    def getappstarttime(self,activity):
        #adb.getappstarttime('com.panda.videoliveplatform/com.panda.videoliveplatform.activity.WelcomeActivity')
        #https://www.zhihu.com/question/35487841?sort=created
        #如果只关心某个应用自身启动耗时，参考TotalTime；如果关心系统启动应用耗时，参考WaitTime；如果关心应用有界面Activity启动耗时，参考ThisTime。
        for line in self.shell('am start -W %s | %s TotalTime'%(activity,self.pipecmd)):
            if line : return line.split(': ')[-1]

    @excepter
    def installapp(self,apk):
        '''
        INSTALL_FAILED_ALREADY_EXISTS	应用已经存在，或卸载了但没卸载干净	adb install 时使用 -r 参数，或者先 adb uninstall <packagename> 再安装
        INSTALL_FAILED_INVALID_APK	无效的 APK 文件
        INSTALL_FAILED_INVALID_URI	无效的 APK 文件名	确保 APK 文件名里无中文
        INSTALL_FAILED_INSUFFICIENT_STORAGE	空间不足	清理空间
        INSTALL_FAILED_DUPLICATE_PACKAGE	已经存在同名程序
        INSTALL_FAILED_NO_SHARED_USER	请求的共享用户不存在
        INSTALL_FAILED_UPDATE_INCOMPATIBLE	以前安装过同名应用，但卸载时数据没有移除	先 adb uninstall <packagename> 再安装
        INSTALL_FAILED_SHARED_USER_INCOMPATIBLE	请求的共享用户存在但签名不一致
        INSTALL_FAILED_MISSING_SHARED_LIBRARY	安装包使用了设备上不可用的共享库
        INSTALL_FAILED_REPLACE_COULDNT_DELETE	替换时无法删除
        INSTALL_FAILED_DEXOPT	dex 优化验证失败或空间不足
        INSTALL_FAILED_OLDER_SDK	设备系统版本低于应用要求
        INSTALL_FAILED_CONFLICTING_PROVIDER	设备里已经存在与应用里同名的 content provider
        INSTALL_FAILED_NEWER_SDK	设备系统版本高于应用要求
        INSTALL_FAILED_TEST_ONLY	应用是 test-only 的，但安装时没有指定 -t 参数
        INSTALL_FAILED_CPU_ABI_INCOMPATIBLE	包含不兼容设备 CPU 应用程序二进制接口的 native code
        INSTALL_FAILED_MISSING_FEATURE	应用使用了设备不可用的功能
        INSTALL_FAILED_CONTAINER_ERROR	sdcard 访问失败	确认 sdcard 可用，或者安装到内置存储
        INSTALL_FAILED_INVALID_INSTALL_LOCATION	不能安装到指定位置	切换安装位置，添加或删除 -s 参数
        INSTALL_FAILED_MEDIA_UNAVAILABLE	安装位置不可用	一般为 sdcard，确认 sdcard 可用或安装到内置存储
        INSTALL_FAILED_VERIFICATION_TIMEOUT	验证安装包超时
        INSTALL_FAILED_VERIFICATION_FAILURE	验证安装包失败
        INSTALL_FAILED_PACKAGE_CHANGED	应用与调用程序期望的不一致
        INSTALL_FAILED_UID_CHANGED	以前安装过该应用，与本次分配的 UID 不一致	清除以前安装过的残留文件
        INSTALL_FAILED_VERSION_DOWNGRADE	已经安装了该应用更高版本	使用 -d 参数
        INSTALL_FAILED_PERMISSION_MODEL_DOWNGRADE	已安装 target SDK 支持运行时权限的同名应用，要安装的版本不支持运行时权限
        INSTALL_PARSE_FAILED_NOT_APK	指定路径不是文件，或不是以 .apk 结尾
        INSTALL_PARSE_FAILED_BAD_MANIFEST	无法解析的 AndroidManifest.xml 文件
        INSTALL_PARSE_FAILED_UNEXPECTED_EXCEPTION	解析器遇到异常
        INSTALL_PARSE_FAILED_NO_CERTIFICATES	安装包没有签名
        INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES	已安装该应用，且签名与 APK 文件不一致	先卸载设备上的该应用，再安装
        INSTALL_PARSE_FAILED_CERTIFICATE_ENCODING	解析 APK 文件时遇到 CertificateEncodingException
        INSTALL_PARSE_FAILED_BAD_PACKAGE_NAME	manifest 文件里没有或者使用了无效的包名
        INSTALL_PARSE_FAILED_BAD_SHARED_USER_ID	manifest 文件里指定了无效的共享用户 ID
        INSTALL_PARSE_FAILED_MANIFEST_MALFORMED	解析 manifest 文件时遇到结构性错误
        INSTALL_PARSE_FAILED_MANIFEST_EMPTY	在 manifest 文件里找不到找可操作标签（instrumentation 或 application）
        INSTALL_FAILED_INTERNAL_ERROR	因系统问题安装失败
        INSTALL_FAILED_USER_RESTRICTED	用户被限制安装应用
        INSTALL_FAILED_DUPLICATE_PERMISSION	应用尝试定义一个已经存在的权限名称
        INSTALL_FAILED_NO_MATCHING_ABIS	应用包含设备的应用程序二进制接口不支持的 native code
        INSTALL_CANCELED_BY_USER	应用安装需要在设备上确认，但未操作设备或点了取消	在设备上同意安装
        INSTALL_FAILED_ACWF_INCOMPATIBLE	应用程序与设备不兼容
        does not contain AndroidManifest.xml	无效的 APK 文件
        is not a valid zip file	无效的 APK 文件
        Offline	设备未连接成功	先将设备与 adb 连接成功
        unauthorized	设备未授权允许调试
        error: device not found	没有连接成功的设备	先将设备与 adb 连接成功
        protocol failure	设备已断开连接	先将设备与 adb 连接成功
        Unknown option: -s	Android 2.2 以下不支持安装到 sdcard	不使用 -s 参数
        No space left on devicerm	空间不足	清理空间
        Permission denied ... sdcard ...	sdcard 不可用
        '''
        s = ''
        for line in self.adb('install -r %s' % apk):
            if line : s = s+ ' '+ str(line)
        return s

    def isinstall(self,package):
        if self.getsearchapp(package): return True
        return False

    @excepter
    def uninstallapp(self,package):
        s = ''
        for line in self.adb('uninstall %s'%package):
            if line: s = s + ' ' + str(line)
        return s

    @excepter
    def clearappdata(self,package,**kw):
        for line in self.shell('pm clear %s'%package):
            if line : return line

    @excepter
    def startactivity(self,activity,**kw):
        for line in self.shell('am start -n %s'%activity):
            if line : return line

    def resetcurrentapp(self,package,activity,**kw):
        self.clearappdata(package)
        return self.startactivity(activity)

    @excepter
    def startwebpage(self,url):
        for line in self.shell('am start -a android.intent.action.VIEW -d %s'%url):
            if line :return line

    @excepter
    def callphone(self,number):
        for line in self.shell('am start -a android.intent.action.CALL -d tel:%s'%number):
            if line:return line

    @excepter
    def event(self,key):
        return self.shell('input keyevent %s'%key)

    @excepter
    def longpresseventkey(self,key):
        return self.shell('input keyevent --longpress %s'%key)

    @excepter
    def touch(self,x,y):
        w,h = self.getscreenhw()
        if 0<x<w: x*=w
        if 0<y<h: y*=h
        for line in self.shell('input tap %s %s'%(x,y)):
            if line : return line

    @excepter
    def getpagesource(self,path):
        file = '%s_'%self.deviceid + time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        #ret = self.shell('uiautomator dump /data/local/tmp/{}.xml'.format(file)).read().strip().decode()
        for line in self.shell('uiautomator dump /data/local/tmp/dump.xml'):
            if line : ret = line
        #self.pagesource = path+'\\'+file+'.xml'
        self.pagesource = path + os.path.sep + file + '.xml'
        #return self.adb('pull /data/local/tmp/{}.xml %s'.format(file) %self.pagesource).read().strip().decode()
        return self.adb('pull /data/local/tmp/dump.xml %s'% self.pagesource)

    @excepter
    def xpathtolist(self,xpath, pagesource):
        nlist = []
        Root = etree.XML(bytes(bytearray(pagesource, encoding='utf-8')))
        Tree = etree.ElementTree(Root)
        for node in etree.XPath(xpath)(Root):
            nodemap = {}
            nodemap['tag'] = node.tag
            nodemap['xpath'] = Tree.getpath(node)
            nodemap[node.tag] = node.text
            for k, v in node.attrib.items():
                nodemap[k] = v
            if 'resource-id' not in nodemap and 'name' not in nodemap:
                nodemap['name'] = ''
                nodemap['value'] = ''
                nodemap['label'] = ''
            if 'resource-id' in nodemap: nodemap['name'] = nodemap['resource-id'].split('/')[-1]
            if 'text' in nodemap: nodemap['value'] = nodemap['text']
            if 'content-desc' in nodemap: nodemap['label'] = nodemap['content-desc']
            nodemap['xpath'] and nlist.append(nodemap)
        return nlist

    @excepter
    def findinstallerbutton(self):
        blist = []
        blist.append("//*[@resource-id='android:id/button2']")
        blist.append("//*[@resource-id='com.miui.securitycenter:id/allow_button']")
        blist.append("//*[@text='确定' and @package='com.htc.htcappopsguarddog']")
        blist.append("//*[@resource-id='android:id/button1']")
        blist.append("//*[@resource-id='com.sonymobile.cta:id/btn_ok']")
        #blist.append("//*[@content-desc='更多选项' and @class='android.widget.ImageButton']")
        blist.append("//*[@resource-id='com.android.packageinstaller:id/ok_button']")
        blist.append("//*[@resource-id='com.android.packageinstaller:id/btn_allow_once']")
        blist.append("//*[@resource-id='com.android.packageinstaller:id/bottom_button_two']")
        blist.append("//*[@resource-id='com.android.packageinstaller:id/btn_continue_install']")
        #blist.append("//*[@resource-id='android:id/button1']")
        blist.append("//*[@resource-id='vivo:id/vivo_adb_install_ok_button']")
        blist.append("//*[@resource-id='com.android.packageinstaller:id/confirm_button']")
        blist.append("//*[@resource-id='com.qihoo360.mobilesafe:id/c1']")
        #self.getpagesource('D:\\automonkey\\tmp\\dump')
        self.getpagesource('%s%stmp%sdump'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep))
        if not self.pagesource or not os.path.exists(self.pagesource):
            return None,None
        else:
            dom = open(self.pagesource, 'rb').read().decode('utf-8')
        for xpath in blist:
            for node in self.xpathtolist(xpath,dom):
                bounds = re.compile('\d+').findall(node['bounds'])
                x = int(bounds[0])+((int(bounds[2])-int(bounds[0]))/2)
                y = int(bounds[1])+((int(bounds[3])-int(bounds[1]))/2)
                return x,y
        return None,None

    def clickinstallerbutton(self,**kw):
        while True:
            time.sleep(3)
            if self.installsucc: break
            x,y = self.findinstallerbutton()
            if x and y :
                logobj.debug('find element=(%s,%s)'%(x,y))
                self.click((x,y))
            else:
                logobj.debug('not find')

    @excepter
    def findlanucherbutton(self):
        blist = []
        blist.append("//*[@resource-id='flyme:id/accept']")
        blist.append("//*[@resource-id='com.lbe.security.miui:id/accept']")
        self.getpagesource('%s%stmp%sdump' % (os.path.split(os.path.realpath(__file__))[0], os.path.sep, os.path.sep))
        if not self.pagesource or not os.path.exists(self.pagesource):
            return None, None
        else:
            dom = open(self.pagesource, 'rb').read().decode('utf-8')
        for xpath in blist:
            for node in self.xpathtolist(xpath, dom):
                bounds = re.compile('\d+').findall(node['bounds'])
                x = int(bounds[0]) + ((int(bounds[2]) - int(bounds[0])) / 2)
                y = int(bounds[1]) + ((int(bounds[3]) - int(bounds[1])) / 2)
                return x, y
        return None, None

    def clicklanucherbutton(self,t,**kw):
        t0 = time.time()
        while True:
            time.sleep(3)
            t1 = time.time()
            if t1-t0 > t:break
            x, y = self.findlanucherbutton()
            if x and y:
                logobj.debug('%s,find element=(%s,%s)' % (self.deviceid, x, y))
                self.click((x, y))
            else:
                logobj.debug('%s,not find' % self.deviceid)

    def install(self,package,apk,**kw):
        self.quitapp('com.android.packageinstaller')
        if not self.installsucc:
            if self.isinstall(package): self.uninstallapp(package)
            retry = 0
            while retry < 5:
                logobj.debug('%s app install:'%apk)
                ret = self.installapp(apk)
                logobj.debug(ret)
                if self.isinstall(package) :
                    self.installsucc = True
                    logobj.debug('install thread quit.')
                    break
                else :
                    logobj.debug('install failed ,retry')
                    retry += 1
            self.quitapp('com.android.packageinstaller')

    def startinstall(self,package,apk):
        checkthread = threading.Thread(target = self.clickinstallerbutton,args=())
        installthread = threading.Thread(target = self.install,args=(package,apk))
        for t in [checkthread,installthread]:
            t.start()
        for t in [checkthread,installthread]:
            t.join()

    @excepter
    def click(self,element):
        return self.shell('input tap %s %s'%(element[0],element[1]))

    @excepter
    def swipeptp(self,startx,starty,endx,endy,duration=' '):
        return self.shell('input swipe %s %s %s %s %s'%(startx,starty,endx,endy,duration))

    @excepter
    def swipe(self,a='',b='',sx='',sy='',ex='',ey='',duration = ' '):
        w,h = self.getscreenhw()
        if a :
            sx=a[0]
            sy=a[1]
        if b:
            ex=b[0]
            ey=b[1]
        if 0<sx<1:sx*=w
        if 0<sy<1:sy*=h
        if 0<ex<1:ex*=w
        if 0<ey<1:ey*=h
        return self.shell('input swipe %s %s %s %s %s'%(sx,sy,ex,ey,duration))

    @excepter
    def swipeto(self,direction):
        if direction not in ['left', 'right', 'up', 'down']: return 0
        move = {
            'left': lambda: self.swipe('','', '0.9', '0.5', '0.1', '0.5'),
            'right': lambda: self.swipe('','', '0.1', '0.5', '0.9', '0.5'),
            'up': lambda: self.swipe('','', '0.5', '0.8', '0.5', '0.2'),
            'down': lambda: self.swipe('','', '0.5', '0.2', '0.5', '0.8'),
        }
        return move[direction]()

    def longpresspoint(self,e='',x=0,y=0):
        return self.swipe(e,e,str(x),str(y),str(x),str(y),str(2000))

    @excepter
    def sendtext(self,s):
        for i in re.sub('\s+(?!$)',' ',s).split(' '):
            self.shell('input text %s' % i)
            time.sleep(1)

    @excepter
    def savescreen(self,path):
        file = '%s_' % self.deviceid + time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        self.shell('/system/bin/screencap -p /data/local/tmp/{}.png'.format(file))
        return self.adb('pull /data/local/tmp/{}.png %s'.format(file) % path)

    @excepter
    def getcurrentappversion(self):
        for line in self.shell('dumpsys package %s'%self.getcurrentpackage()):
            if 'versionName' in line: return line.split('=',2)[1]

    @excepter
    def getappversion(self,package):
        for line in self.shell('dumpsys package %s'%package):
            if 'versionName' in line: return line.split('=',2)[1]

    @excepter
    def getcurrentappversioncode(self):
        for line in self.shell('dumpsys package %s'%self.getcurrentpackage()):
            if 'versionCode' in line: return line.split('=',2)[1].split(' ',2)[0]

    @excepter
    def getcurrentappfirstinstalltime(self):
        for line in self.shell('dumpsys package %s'%self.getcurrentpackage()):
            if 'firstInstallTime' in line: return line.split('=',2)[1]

    @excepter
    def getcurrentapplastupdatetime(self):
        for line in self.shell('dumpsys package %s'%self.getcurrentpackage()):
            if 'lastUpdateTime' in line: return line.split('=',2)[1]

    @excepter
    def getcpu(self,package):
        for line in self.shell('top -n 1 -d 0.5 | %s %s'%(self.pipecmd,package)):
            if package in line:
                print(line)
                #return line.split(' ')[5].split('%',1)[0]
                return int(re.compile('(\d+)%').findall(line)[0])

    # @excepter
    # def getmempss(self,package):
    #     for line in self.shell('top -n 1 -d 0.5 | %s %s'%(self.pipecmd,package)):
    #         if package in line:
    #             print(line)
    #             #return '%.2f'%(int(line.split(' ')[12].split('K')[0])/1024)
    #             return int(re.compile('(\d+)K').findall(line)[1])/1024

    @excepter
    def getcpupss(self,package):
        for line in self.shell('top -n 1 -d 0.5 | %s %s'%(self.pipecmd,package)):
            if package in line:
                print(line)
                return int(re.compile('(\d+)%').findall(line)[0]),int(re.compile('(\d+)K').findall(line)[1])/1024

    def getmempss(self,package):
        #pid = self.getpid(package)
        for line in self.shell('dumpsys meminfo %s'%package):
            if 'TOTAL' in line:
                print(line)
                return int(re.compile('(\d+)').findall(line)[0])/1024

    @excepter
    def getmemtotal(self):
        for line in self.shell('cat proc/meminfo'):
            if 'MemTotal' in line:
                return int(re.compile('(\d+) kB').findall(line)[0])/1024

    @excepter
    def getmem(self,package):
        pss = self.getmempss(package)
        if pss:
            return '%.2f'%(float(pss)/float(self.getmemtotal())*100)+'%'
        return None

    @excepter
    def isroot(self):
        return 'not found' not in self.shell('su')

    @excepter
    def filldisk(self):
        return self.shell('dd if=/dev/zero of=/mnt/sdcard/bigfile')

    @excepter
    def backupapk(self,package,path):
        file = '%s_' % self.deviceid + time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        self.adb('backup -apk %s -f /data/local/tmp/{}.ab'.format(file) %package)
        return self.adb('pull /data/local/tmp/{}.ab %s'.format(file) % path)

    @excepter
    def pull(self,source,target):
        #拉
        return self.adb('pull %s %s'%(source,target))

    @excepter
    def push(self,source,target):
        #pc推phone
        return self.adb('push %s %s'%(source,target))

    @excepter
    def unlock(self):
        #https: // testerhome.com / topics / 8707
        return self.shell('am start -n io.appium.unlock/.Unlock')

    @excepter
    def restoreapk(self,path):
        file = os.path.basename(path)
        if '.ab' in file:
            ab = '/data/local/tmp/%s'%file
            self.push(path,ab)
            return self.adb('restore %s'%ab)

    @excepter
    def getcrashlogcat(self,file):
        #to do
        return self.adb('logcat -v time -d| %s AndroidRuntime >%s&'%(self.pipecmd,file))

    @excepter
    def getcpuversion(self):
        for line in self.shell("getprop ro.product.cpu.abi"):
            if line:return line

    @excepter
    def getdisk(self):
        '''
        :return used,free:
        '''
        for line in self.shell('df'):
            if '/mnt/shell/emulated' in line or '/storage/sdcard0' in line or '/data' in line or '/storage/emulated' in line:
                disk = re.compile('([\.\d]+)G').findall(line)
                if len(disk) >2: return disk[1],disk[2]

    @excepter
    def getwifi(self):
        for line in self.shell('dumpsys wifi'):
            if 'mWifiInfo' in line:
                wifi = re.compile('SSID:([^"]+), BSSID').findall(line)
                if wifi: return wifi[0].strip()
                return None

    @excepter
    def getwifistate(self):
        for line in self.shell('dumpsys wifi|%s ^Wi-Fi' % self.pipecmd):
            if line: return 'enabled' in line

    @excepter
    def getdataconnectstate(self):
        for line in self.shell('dumpsys telephony.registry|%s mDataConnectionState' % self.pipecmd):
            if line: return '2' in line

    @excepter
    def getnetworkstate(self):
        for line in self.shell('ping -w 1 www.baidu.com'):
            if line: return 'unknown host' not in line

    @excepter
    def getmacaddress(self):
        for line in self.shell('cat /sys/class/net/wlan0/address'):
            if line :return line

    @excepter
    def getipaddress(self):
        if self.getwifistate() or self.getdataconnectstate():
            for line in self.shell('ip addr | %s global'%self.pipecmd):
                if line :return re.compile('\d+\.\d+\.\d+\.\d+').findall(line)[0]

    @excepter
    def getcpuinfo(self):
        for line in self.shell('cat /proc/cpuinfo'):
            if line :return line.split(':')[-1].strip()

    @excepter
    def getimei(self):
        if int(self.getsdkversion()) < 21:
            for line in self.shell('dumpsys iphonesubinfo'):
                if line : return re.compile('[0-9]{15}').findall(line)[0]
        imei = []
        for line in self.shell('service call iphonesubinfo 1'):
            for i in re.compile('(\d+)\.').findall(line):
                imei.append(i)
        return ''.join(imei)

    def checksimcard(self):
        return len(self.getdeviceoperators()) > 2

    @excepter
    def getdeviceoperators(self):
        return self.shell('getprop | %s gsm.operator.alpha'%self.pipecmd)[-1]

    @excepter
    def getscreenstate(self):
        for line in self.shell('dumpsys power'):
            if 'mScreenOn=' in line: return line.split[-1] == 'mScreenOn=true'
            if 'Display Power' in line:return 'ON' in line.split('=')[-1].upper()

    @excepter
    def getinteriorsdcard(self):
        return self.shell('df | %s \/mnt\/shell\/emulated'%self.pipecmd)

    @excepter
    def getexternalsdcard(self):
        return self.shell('df | %s \/storage'%self.pipecmd)

    @excepter
    def getnetflow(self,uid):
        '''
        :param uid:
        :return: total,rcv,snd   M
        '''
        rx = []
        tx = []
        try:
            for line in self.shell('cat /proc/net/xt_qtaguid/stats|%s %s' % (self.pipecmd, uid)):
                if line:
                    rx.append(int(line.strip().split(' ')[5]))
                    tx.append(int(line.strip().split(' ')[7]))
            total = round((sum(rx) + sum(tx)) / 1024.0 / 1024.0, 4)
            rcv = round(sum(rx) / 1024.0 / 1024.0, 4)
            snd = round(sum(tx) / 1024.0 / 1024.0, 4)
            return total, rcv, snd
        except Exception as e:
            return 0,0,0

    @excepter
    def setrotationscreen(self,on_off):
        '''
        :param on_off: 0-禁止 1可自旋
        :return:
        '''
        return self.shell('/system/bin/content insert --uri content://settings/system'
                          ' --bind name:s:accelerometer_rotation --bind value:i:%s'%on_off)

    @excepter
    def rcvbroadcast(self,cmd):
        # https://testerhome.com/topics/6970
        # ios rcv msg : adb shell dumpsys activity broadcasts | grep senderName = | awk - F 'message=|senderName=|testerhome=' '{print $2}' | grep - oE '[0-9]{4,}'
        return self.shell('dumpsys activity broadcasts |%s'%cmd)

    @excepter
    def monkey(self,parm,path):
        '''
        #http://developer.android.com/guide/developing/tools/monkey.html
        #http://www.jianshu.com/p/2ce1b267ec72
        :param parm:
        # time >6hour
        # -p com.panda.videoliveplatform --throttle 1000 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -s 1000  -v -v -v 90000
        :param report:
        :return:
        '''
        file = '%s_' % self.deviceid + time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        return self.shell('monkey %s >%s\\{}.log'.format(file) %(parm,path))

    def netmonitor(self,package,internal,**kw):
        uid = self.getuid(self.getpid(package))
        while True:
            time.sleep(internal+1)
            if not self.needperf: break
            total,rev,snd = self.getnetflow(uid)
            if total :
                logobj.debug('total:%s,rev:%s,snd:%s'%(total,rev,snd))
                t = time.time()
                self.nettotal.append((t,total))
                self.netrev.append((t,rev))
                self.netsnd.append((t,snd))

    def cpumonitor(self,package,internal,**kw):
        while True:
            time.sleep(internal)
            if not self.needperf: break
            cpu = self.getcpu(package)
            if cpu :
                logobj.debug('cpu=%s'%cpu)
                t = time.time()
                self.cpu.append((t,cpu))

    def memmonitor(self,package,internal,**kw):
        if not self.totalmem :
            try:
                self.totalmem = self.getmemtotal()
            except:
                logobj.error('total mem calc error')
                self.totalmem = 1890
        while True:
            time.sleep(internal+0.5)
            if not self.needperf: break
            pss = self.getmempss(package)
            logobj.debug('pss=%s'%pss)
            t = time.time()
            if pss :
                self.mempercend.append((t,pss/self.totalmem))
                self.mem.append((t,pss))

    @excepter
    def logcat(self):
        logcatcmd = 'logcat -v time -f /sdcard/logcat.txt'
        return subprocess.check_output('adb -s %s '%self.deviceid + logcatcmd, shell=True)
        # kw = {}
        # if 'Windows' in platform.system():
        #     kw['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        # process = subprocess.Popen('%s -s %s %s' % (self.command, self.deviceid, logcatcmd), shell=True,
        #                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
        # while process.poll() is None:
        #     time.sleep(0.1)
        #     now = time.time()
        #     if now - start > 15:
        #         try:
        #             if 'Windows' in platform.system(): process.send_signal(signal.CTRL_BREAK_EVENT)
        #             process.terminate()
        #         except Exception as e:
        #             logobj.error(e)
        # try:
        #     if 'Windows' in platform.system(): process.send_signal(signal.CTRL_BREAK_EVENT)
        #     process.terminate()
        # except OSError as e:
        #     logobj.error(e)
        #     return None
        # return True

    @excepter
    def getanr(self,path):
        return self.pull('/data/anr/traces.txt', path)

    @excepter
    def getlogcat(self, path):
        self.pull('/sdcard/logcat.txt', path)
        time.sleep(10)
        self.shell('rm /sdcard/logcat.txt')

    @excepter
    def clearlogcat(self):
        return self.adb('logcat -c')

    def linereader(self, file):
        f = open(file,'rb')
        line = f.readline()
        while line:
            yield line
            line = f.readline()
        f.close()
        yield None

    def logcattosave(self,udid):
        logcat_info = subprocess.check_output('adb -s %s logcat -d' % (udid,), shell=True)
        logobj.info('%s logcat | start:'%time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time())))
        logobj.info(logcat_info)
        logobj.info('%s logcat | end!')
        subprocess.call('adb -s %s logcat -c' % (udid,), shell=True)

    def findcrashinsplashscreen(self, udid, pkg):
        wininfo = subprocess.check_output('adb -s %s shell dumpsys window windows' % (udid,), shell=True)
        launched = False
        for l in wininfo.splitlines():
            l = l.decode()
            if 'mCurrentFocus' in l and 'Application Error' in l:
                launched = False
                break
            if 'mCurrentFocus' in l or 'mFocusedApp' in l:
                launched = launched or pkg in l
        return launched

    def analyzecrash(self,time,string,package):
        def formatlog(s):
            def dash(obj):
                return '<br/>' + obj.group(0)
            v = str(s)
            v = v.replace('\r\r\n', '<br/>')
            v = v.replace('\t', '    ')
            if '<br/>' not in v:
                pattern = re.compile(r'\w+-\w+ \w+:\w+:\w+.\w+ ')
                v = re.sub(pattern, dash, v)
            return v
        anr = 'ANR'
        crash = 'E/AndroidRuntime'
        forcestop = 'Force stopping'
        tombstone = 'Build fingerprint'
        oom = 'OutOfMemoryError'
        html = formatlog(string)
        lines = html.split('<br/>')
        if anr in string:
            if ' ANR in %s' % package not in string: return
            self.anr.append((time,string))
            self.getanr('%s%stmp%slogcat%s'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep,os.path.sep))
        if (crash in string and oom not in string) or forcestop in string:
            if 'java.lang.IllegalStateException: UiAutomationService' in string: return
            if 'com.android.uiautomator' in string:return
            if package not in string:return
            for line in lines:
                if 'Force stopping' in line and package in line and ('uninstall pkg' in line or 'pkg removed' in line or 'update pkg' in line):return
                if 'Force stopping' in line and package not in line: return
                if 'Force stopping' in line and package in line and 'from pid' in line: return
                if 'AndroidRuntime' in line and package not in line: return
            self.crash.append((time,string))
        if tombstone in string:
            if package not in string: return
            self.tombstone.append((time,string))
            #self.pull('/data/tombstones/tombstones*','tmp\\logcat\\')
        if oom in string:
            if 'com.android.commands.monkey.ape' in string:return
            self.oom.append((time,string))

    def analyzelogcat(self, file, package):
        log = {}
        time = None
        for line in self.linereader(file):
            if line:
                line = line.decode('gbk','replace')
                time = re.compile('(\d{2}-\d{2} \d{2}:\d{2}:\d)\d.').findall(line)
                if time :
                    if time[0] in log:
                        tmp = log[time[0]]
                        del log[time[0]]
                        tmp += line
                        log[time[0]] = tmp
                    else:
                        log[time[0]] = line
        for k,v in log.items():
            self.analyzecrash(k,v,package)

    # def calccrash(self):
    #     #logfile = 'D:\\automonkey\\tmp\\logcat\\logcat.txt'
    #     logfile = '%s%stmp%slogcat%slogcat.txt'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep,os.path.sep)
    #
    #     if not os.path.exists(logfile):return
    #     self.analyzelogcat(logfile,'panda')
    #     logobj.info('crash =%s' % len(self.crash))
    #     for i in self.crash:
    #         _, log = i
    #         logobj.info(log)
    #         logobj.info('\n')
    #     logobj.info('oom =%s' % len(self.oom))
    #     for i in self.oom:
    #         _, log = i
    #         logobj.info(log)
    #         logobj.info('\n')
    #     logobj.info('anr =%s' % len(self.anr))
    #     for i in self.anr:
    #         _, log = i
    #         logobj.info(log)
    #         logobj.info('\n')
    #     logobj.info('native crash =%s' % len(self.tombstone))
    #     for i in self.tombstone:
    #         _, log = i
    #         logobj.info(log)
    #         logobj.info('\n')
    #     print(self.crash)
    #     print(self.anr)
    #     print(self.tombstone)
    #     print(self.oom)

    @excepter
    def GTstart(self):
        return self.shell('am start -W -n com.tencent.wstt.gt/com.tencent.wstt.gt.activity.GTMainActivity')

    def GTsettest(self,package):
        return self.shell('am broadcast -a com.tencent.wstt.gt.baseCommand.startTest --es pkgName "%s"'%package)

    def GTstartsampling(self,it):
        return self.shell('am broadcast -a com.tencent.wstt.gt.baseCommand.sampleData --ei %s 1' %it)

    def GTstopsampling(self,it):
        return self.shell('am broadcast -a com.tencent.wstt.gt.baseCommand.sampleData --ei %s 0' %it)

    def GTstartSM(self,package):
        # mustbe root
        # adb shell am broadcast -a com.tencent.wstt.gt.plugin.sm.modify        对应UI上的“更改”，一次执行除非执行逆操作“恢复”,会一直有效
        # adb shell am broadcast -a com.tencent.wstt.gt.plugin.sm.resume        对应UI上的“恢复”，测试完毕时执行一次，如手机长期用于流畅度测试可以一直不用恢复
        # adb shell am broadcast -a com.tencent.wstt.gt.plugin.sm.restart        对应UI上的“重启”，重启手机使“更改”或“恢复”生效
        return self.shell('am broadcast -a com.tencent.wstt.gt.plugin.sm.startTest --es procName "%s"' % package)

    def GTstopSM(self):
        return self.shell('am broadcast -a com.tencent.wstt.gt.plugin.sm.endTest')

    def GTsavetest(self,udid,timestamp,desc):
        #adb shell am broadcast -a com.tencent.wstt.gt.baseCommand.endTest --es saveFolderName "普通导航测试"  --es desc "腾讯地图_6.0.1_普通导航_1"
        return self.shell('am broadcast -a com.tencent.wstt.gt.baseCommand.endTest --es saveFolderName "%s_%s"  --es desc "%s" '%(udid,timestamp,desc))

    def GTexit(self):
        return self.shell('am broadcast -a com.tencent.wstt.gt.baseCommand.exitGT')

    def startgttest(self,package):
        try:
            # mustbe start app
            self.GTstart()
            self.GTsettest(package)
            self.GTstartsampling('cpu')
            #self.GTstartsampling('jif')
            self.GTstartsampling('pss')
            #self.GTstartsampling('pri')
            #self.GTstartsampling('net')
            #self.GTstartsampling('fps')
            # switch app
            return 1
        except Exception as e:
            return 0

    def startgttestnogui(self,package):
        try:
            # mustbe start app
            #self.GTstart()
            self.GTsettest(package)
            self.GTstartsampling('cpu')
            #self.GTstartsampling('jif')
            self.GTstartsampling('pss')
            #self.GTstartsampling('pri')
            #self.GTstartsampling('net')
            #self.GTstartsampling('fps')
            # switch app
            return 1
        except Exception as e:
            return 0

    def stopandsavegttest(self,package,udid,timestamp,desc,target):
        try:
            self.GTstopsampling('cpu')
            #self.GTstopsampling('jif')
            self.GTstopsampling('pss')
            #self.GTstopsampling('pri')
            #self.GTstopsampling('net')
            #self.GTstopsampling('fps')
            self.GTsavetest(udid,timestamp ,desc)
            self.GTexit()
            source = '/sdcard/gt/GW/%s/unknow/%s_%s' % (package, udid,timestamp)
            self.pull(source, target)
            return 1
        except Exception as e:
            print(e)
            return 0



class KeyCode:
    KEYCODE_CALL = 5  # 拨号键
    KEYCODE_ENDCALL = 6  # 挂机键
    KEYCODE_HOME = 3  # Home键
    KEYCODE_MENU = 82  # 菜单键
    KEYCODE_BACK = 4  # 返回键
    KEYCODE_SEARCH = 84  # 搜索键
    KEYCODE_CAMERA = 27  # 拍照键
    KEYCODE_FOCUS = 80  # 对焦键
    KEYCODE_POWER = 26  # 电源键
    KEYCODE_NOTIFICATION = 83  # 通知键
    KEYCODE_MUTE = 91  # 话筒静音键
    KEYCODE_VOLUME_MUTE = 164  # 扬声器静音键
    KEYCODE_VOLUME_UP = 24  # 音量+键
    KEYCODE_VOLUME_DOWN = 25  # 音量-键
    KEYCODE_ENTER = 66  # 回车键
    KEYCODE_ESCAPE = 111  # ESC键
    KEYCODE_DPAD_CENTER = 23  # 导航键 >> 确定键
    KEYCODE_DPAD_UP = 19  # 导航键 >> 向上
    KEYCODE_DPAD_DOWN = 20  # 导航键 >> 向下
    KEYCODE_DPAD_LEFT = 21  # 导航键 >> 向左
    KEYCODE_DPAD_RIGHT = 22  # 导航键 >> 向右
    KEYCODE_MOVE_HOME = 122  # 光标移动到开始键
    KEYCODE_MOVE_END = 123  # 光标移动到末尾键
    KEYCODE_PAGE_UP = 92  # 向上翻页键
    KEYCODE_PAGE_DOWN = 93  # 向下翻页键
    KEYCODE_DEL = 67  # 退格键
    KEYCODE_FORWARD_DEL = 112  # 删除键
    KEYCODE_INSERT = 124  # 插入键
    KEYCODE_TAB = 61  # Tab键
    KEYCODE_NUM_LOCK = 143  # 小键盘锁
    KEYCODE_CAPS_LOCK = 115  # 大写锁定键
    KEYCODE_BREAK = 121  # Break / Pause键
    KEYCODE_SCROLL_LOCK = 116  # 滚动锁定键
    KEYCODE_ZOOM_IN = 168  # 放大键
    KEYCODE_ZOOM_OUT = 169  # 缩小键
    KEYCODE_0 = 7
    KEYCODE_1 = 8
    KEYCODE_2 = 9
    KEYCODE_3 = 10
    KEYCODE_4 = 11
    KEYCODE_5 = 12
    KEYCODE_6 = 13
    KEYCODE_7 = 14
    KEYCODE_8 = 15
    KEYCODE_9 = 16
    KEYCODE_A = 29
    KEYCODE_B = 30
    KEYCODE_C = 31
    KEYCODE_D = 32
    KEYCODE_E = 33
    KEYCODE_F = 34
    KEYCODE_G = 35
    KEYCODE_H = 36
    KEYCODE_I = 37
    KEYCODE_J = 38
    KEYCODE_K = 39
    KEYCODE_L = 40
    KEYCODE_M = 41
    KEYCODE_N = 42
    KEYCODE_O = 43
    KEYCODE_P = 44
    KEYCODE_Q = 45
    KEYCODE_R = 46
    KEYCODE_S = 47
    KEYCODE_T = 48
    KEYCODE_U = 49
    KEYCODE_V = 50
    KEYCODE_W = 51
    KEYCODE_X = 52
    KEYCODE_Y = 53
    KEYCODE_Z = 54
    KEYCODE_PLUS = 81  # +
    KEYCODE_MINUS = 69  # -
    KEYCODE_STAR = 17  # *
    KEYCODE_SLASH = 76  # /
    KEYCODE_EQUALS = 70  # =
    KEYCODE_AT = 77  # @
    KEYCODE_POUND = 18  # #
    KEYCODE_APOSTROPHE = 75  # '
    KEYCODE_BACKSLASH = 73  # \
    KEYCODE_COMMA = 55  # ,
    KEYCODE_PERIOD = 56  # .
    KEYCODE_LEFT_BRACKET = 71  # [
    KEYCODE_RIGHT_BRACKET = 72  # ]
    KEYCODE_SEMICOLON = 74  # ;
    KEYCODE_GRAVE = 68  # `
    KEYCODE_SPACE = 62  # 空格键
    KEYCODE_MEDIA_PLAY = 126  # 多媒体键 >> 播放
    KEYCODE_MEDIA_STOP = 86  # 多媒体键 >> 停止
    KEYCODE_MEDIA_PAUSE = 127  # 多媒体键 >> 暂停
    KEYCODE_MEDIA_PLAY_PAUSE = 85  # 多媒体键 >> 播放 / 暂停
    KEYCODE_MEDIA_FAST_FORWARD = 90  # 多媒体键 >> 快进
    KEYCODE_MEDIA_REWIND = 89  # 多媒体键 >> 快退
    KEYCODE_MEDIA_NEXT = 87  # 多媒体键 >> 下一首
    KEYCODE_MEDIA_PREVIOUS = 88  # 多媒体键 >> 上一首
    KEYCODE_MEDIA_CLOSE = 128  # 多媒体键 >> 关闭
    KEYCODE_MEDIA_EJECT = 129  # 多媒体键 >> 弹出
    KEYCODE_MEDIA_RECORD = 130  # 多媒体键 >> 录音

if __name__ == "__main__":
    #test
    adb = ADB('04157df40b50c41b')

    # crash = adb.findcrashinsplashscreen('04157df40b50c41b','com.panda.videoliveplatform')
    # print(crash)
    # test!
    # print(adb.getdevicestate())
    # adb.startgttest('com.panda.videoliveplatform')
    # timestamp = time.time()
    # time.sleep(30)
    # adb.stopandsavegttest('com.panda.videoliveplatform', '96e73657', timestamp, 'panda_gt', 'D:\\automonkey\\result\\2017_06_08_12_57_33')
    # print(adb.getandroidversion())
    # print(adb.getsdkversion())
    # print(adb.getdevicemodel())
    # print(adb.getprocess('com.panda.videoliveplatform'))
    # print(adb.getpid('com.panda.videoliveplatform'))
    # _,pid = adb.getpid('com.panda.videoliveplatform')[0]
    # print(pid)
    # print(adb.getuid(pid))
    #print(adb.killprocess(pid))
    # print(adb.quitapp('com.panda.videoliveplatform'))
    # print(adb.getfocusedactivity())
    # print(adb.getcurrentpackage())
    # print(adb.getcurrentactivity())
    # print(adb.getappservers('com.panda.videoliveplatform'))
    # print(adb.getcurrentservers())
    # print(adb.getbatterylevel())
    # print(adb.getbatterystatus())
    # print(adb.getbatterytemp())
    # print(adb.getscreenhw())
    # print(adb.getsystemapps())
    # print(adb.getuserapp())
    # print(adb.getsearchapp('panda'))
    # print(adb.getappstarttime('com.panda.videoliveplatform/.activity.WelcomeActivity'))
    # print(adb.installapp('d:\\automonkey\\conf\\pandalive.apk'))
    # print(adb.installapp('%s%sconf%spandalive.apk'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep)))
    # print(adb.isinstall('com.panda.videoliveplatform'))
    # print(adb.uninstallapp('com.panda.videoliveplatform'))
    # print(adb.clearappdata('com.panda.videoliveplatform'))
    # print(adb.startactivity('com.panda.videoliveplatform/.activity.WelcomeActivity'))
    # print(adb.startwebpage('http://www.baidu.com'))
    # print(adb.callphone('114'))
    # print(adb.event(4))
    # print(adb.longpresseventkey(4))
    # print(adb.touch(0.3,0.5))
    # print(adb.click((500,550)))
    # print(adb.sendtext('hi'))
    # print(adb.getcurrentappversion())
    # print(adb.getappversion('com.panda.videoliveplatform'))
    # print(adb.getcurrentappversioncode())
    # print(adb.getcurrentappfirstinstalltime())
    # print(adb.getcpu('com.panda.videoliveplatform'))
    # print(adb.getmempss('com.panda.videoliveplatform'))
    # print(adb.getmemtotal())
    # print(adb.getcpuversion())
    # print(adb.getdisk())
    # print(adb.getwifi())
    # print(adb.getwifistate())
    # print(adb.getdataconnectstate())
    # print(adb.getnetworkstate())
    # print(adb.getmacaddress())
    # print(adb.getipaddress())
    # print(adb.getcpuinfo())
    # print(adb.getimei())
    # print(adb.checksimcard())
    # print(adb.getdeviceoperators())
    # print(adb.getscreenstate())
    # print(adb.getexternalsdcard())
    # uid = adb.getuid(pid)
    # print(uid)
    # print(adb.getnetflow(uid))

    # adb.startinstall('com.panda.videoliveplatform','d:\\automonkey\\conf\\pandalive.apk')
    # print(adb.getpagesource('d:\\automonkey\\conf\\'))
    # print(adb.getpagesource('%s%sconf'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep)))

    #performance test
    # t0 = time.time()
    # print(adb.getcpupss('com.panda.videoliveplatform'))
    # t1 = time.time()
    # print(t1-t0)
    #
    # print(adb.getmempss('com.panda.videoliveplatform'))
    # t2 = time.time()
    # print(t2-t1)

    # t3 = time.time()
    # adb.logcat('D:\\automonkey\\tmp\\logcat\\logcat.txt')
    # adb.logcat('%s%stmp%slogcat%slogcat.txt'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep,os.path.sep))
    # adb.calccrash()
    # t4 = time.time()
    # print(t4-t3)

    # adb.monkey('-p com.wan.leopard.dmol --throttle 1000 --ignore-crashes --ignore-timeouts '
    #            '--ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -s 1000  '
    #            '-v -v -v 7200','D:\\automonkey\\tmp\\logcat')


