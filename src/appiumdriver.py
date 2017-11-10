#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161005
# @version: 1.0.0.1009

import time,threading,traceback,re,subprocess,platform
import urllib.request
from xml.sax.saxutils import *
import logger
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from lxml import etree
import requests
#windows
#pip install wheel
#down http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
#pip install xxx.whl

logobj=logger.logobj

class Webelement:
    def __init__(self,location,size):
        self.location = location
        self.size = size

def exception(func):
    def execute(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except selenium.common.exceptions.TimeoutException:
            logobj.error('selenium.common.exceptions.TimeoutException,element not find')
        except urllib.request.URLError:
            logobj.error('urllib.error.URLError: 由于连接方在一段时间后没有正确答复或连接的主机没有反应，连接尝试失败,func=%s'%func.__name__)
        except KeyError:
            logobj.error('appium session over')
        except selenium.common.exceptions.WebDriverException as e:
            # # if 'An unknown server-side error occurred' \
            # #         in str(e).strip() and func.func_name == 'swipe':
            # #     return True
            # else:
            logobj.error('selenium.common.exceptions.WebDriverException: Message: An unknown server-side error occurred while processing the command,func=%s'%func.__name__)
        except ConnectionResetError:
            logobj.error('ConnectionResetError: [WinError 10054] 远程主机强迫关闭了一个现有的连接')
            time.sleep(181)
        except:
            logobj.error(traceback.format_exc())
        return None
    return execute

class workthread(threading.Thread):
    def __init__(self, func, *args, **kw):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kw = kw
        self.result = None
        self.done = False
    @exception
    def run(self):
        self.result = self.func(*self.args, **self.kw)
        self.done = True
    def getresult(self):
        return self.result
    def isdone(self):
        return self.done

def startwt(func,*args,**kw):
    wt = workthread(func,*args,**kw)
    wt.setDaemon(True)
    wt.start()
    return wt

def calctimeout(func,*args,**kw):
    timeout = kw.get('timeout')
    interval = 0.1
    if not timeout: timeout = 30  # 30 SECONDS
    result = None
    while timeout > 0:
        t = time.time()
        result = func()
        if result and not isinstance(result, Exception):
            break
        time.sleep(interval)
        elapsedtime = time.time() - t
        timeout -= elapsedtime
    return result

def asynctask(func,*args,**kw):
    wt = startwt(func,*args,**kw)
    if not calctimeout(wt.isdone,*args,**kw):
        return 0
    return wt.getresult()

###### webdriver miniappium ######
#crawler

def isrunning(url):
    response = ''
    try:
        response = requests.get(url,timeout=0.01)
        if str(response.status_code) == '502':
            logobj.debug('502')
            return False
        if re.compile('valid JSONWP resource').findall(response.text):
            logobj.debug('404')
            return True
        logobj.debug(response.text)
        return False
    except requests.exceptions.ConnectionError: return False
    except requests.exceptions.ReadTimeout : return False
    except requests.packages.urllib3.exceptions.ReadTimeoutError : return False
    finally:
        if response:response.close()

def isusing(port):
    system = platform.system()
    if system == 'Windows':
        cmd = 'netstat -an | findstr %s'%port
    else:
        cmd = 'netstat -an | grep %s'%port
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.stdout.readlines():return True
    else:return False

def getfreeports(port,count=1):
    ports = []
    port = int(port)
    while True:
        if len(ports) == count: break
        if not isusing(port) and port not in ports: ports.append(port)
        else:port+=5
    return ports

def startappiumserver(port,timeout):
    ports = getfreeports(port)
    if ports : port = ports[0]
    system = platform.system()
    if system == 'Windows':
        cmd = 'C:\\Program Files (x86)\\Appium\\node.exe ' + "--max-old-space-size=2047 --gc-global " + r'"C:\\Program Files (x86)\\Appium\\node_modules\\appium\\lib\\server\\main.js"' + " --address 127.0.0.1 --port %s --bootstrap-port %s --platform-name Android --platform-version 23 --automation-name Appium" %(port,int(port)+1)
        asynctask(subprocess.Popen, cmd, timeout)
    else:
        cmd ='/usr/local/bin/node' + " --max-old-space-size=2047 --gc-global " +\
        '/usr/local/lib/node_modules/appium/build/lib/main.js' + " " + \
        "--address 127.0.0.1 --port %s --bootstrap-port %s --platform-name Android --platform-version 23 --automation-name Appium"%(port,int(port)+1)
        asynctask(subprocess.Popen, cmd, timeout,shell=True)
    return port

def startappiumclient(url, caps):
    driver = webdriver.Remote(url, caps)
    #driver.implicitly_wait(30)
    return driver

def startapp(port , udid , apk , autolaunch=True, package='' ,activity='' ,waitactivity=''):
    caps = {}
    caps['app'] = os.path.realpath(apk)
    caps['autoLaunch'] = autolaunch
    caps['deviceName'] = 'Android'
    caps['platformName'] = 'Android'
    caps['udid'] = udid
    caps['unicodeKeyboard'] = True
    caps['resetKeyboard'] = True
    caps['autoAcceptAlerts'] = True #ios
    #caps['automationName'] = 'Selendroid'
    if package:
        caps['appPackage'] = package
    if activity:
        caps['appActivity'] = activity
    if waitactivity:
        caps['appWaitActivity'] = waitactivity
    url = 'http://127.0.0.1:%s/wd/hub' % port
    return webdriver.Remote(url, caps)

# def toxml(raw):
#     #str = re.sub(r'[\\x00-\\x1F]','',raw)
#     #str = str.replace("&#",escape("&#"))
#     return raw

def getpagesource(*args,**kw):
    # source = asynctask(getpagesource, driver, timeout=60)
    #0.36299991607666016 --0.4630000591278076
    (driver,) = args
    v = ''
    source = ''
    for x in range(3):
        v = driver.page_source
        if v:
            source = v
            break
    return source

def keytoxpath(key):
    def bstr(v, op):
        xpath = ''
        klist = ['@text', '@resource-id', '@content-desc', '@name', '@label', '@value', 'name()']
        for k in klist:
            xpath += op + "(" + k + ",'" + v + "') or "
        return xpath[:-3]
    if key[0] == '/' or key[0] == '(':
        xpath = key
        return xpath
    elif key[0] == '^':
        xpath = "//*[" + bstr(key, 'matches') + "]"
    else:
        xpath = "//*[" + bstr(key, 'contains') + "]"
    return xpath

def xpathtolist(xpath,pagesource):
    nlist = []
    #print(pagesource)
    if not pagesource: return nlist
    Root = etree.XML(bytes(bytearray(pagesource, encoding='utf-8')))
    Tree = etree.ElementTree(Root)
    for node in etree.XPath(xpath)(Root):
        nodemap = {}
        nodemap['tag'] = node.tag
        nodemap['xpath'] = Tree.getpath(node)
        nodemap[node.tag] = node.text
        for k,v in node.attrib.items():
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

def tree(driver, key = "//*", index = 0):
    # e=tree(driver, key, index=0)
    # print(e['xpath'])
    node={}
    nodes = xpathtolist(keytoxpath(key), asynctask(getpagesource, driver, timeout=60))
    if nodes:
        return nodes[index]
    node['xpath']=''
    return node

@exception
def find(driver, X = By.XPATH, v='//*',timeout = 10):
    if v=='': return 0
    WebDriverWait(driver,timeout,poll_frequency=0.5).until(expected_conditions.presence_of_all_elements_located((X,v)))
    #http://selenium-python.readthedocs.io/waits.html#implicit-waits
    elements = driver.find_elements(X, v)
    return elements

def whenfindclick(driver,X = By.XPATH, v='//*',timeout = 1):
    elements = ''
    elements = find(driver,X,v,timeout = 1)
    if elements:
        click(elements)
        return True
    return False

def whennotfindAclickB(driver,A,B,XA = By.XPATH,XB =By.XPATH,timeout=1):
    Aelements = find(driver, XA, A, timeout=1)
    if not Aelements:
        Belements = find(driver, XB, B, timeout=1)
        if Belements:
            click(Belements)
            return True
    return False

def whennotfindclickxy(driver,key,x,y,X=By.XPATH,timeout=1):
    elements = find(driver, X, key, timeout=1)
    if not elements:
        tappoint(driver, x, y)
        return True
    return False



def findSysmenu(driver,startupClosePopenSysmenu):
    # if not startupClosePopenSysmenu:
    #     startupClosePopenSysmenu.append("//*[@resource-id='android:id/button1' and @text='允许']")
    for xpath in startupClosePopenSysmenu:
        elements = find(driver,By.XPATH,xpath,timeout=1)
        if elements :
            logobj.info('find system button =%s'%xpath)
            click(elements)
            return True
    logobj.debug('not find')
    return False

# def clickstartupsysmenu(driver,startupClosePopenSysmenu,**kw):
#     keep = 3
#     while keep:
#         time.sleep(1)
#         findSysmenu(driver,startupClosePopenSysmenu)
#         keep -= 1
#     logobj.debug('findsysmenu thread quit.')

def wait(driver, key):
    #elements = wait(driver, text)
    isfound = False
    elements = None
    xpath = keytoxpath(key)
    for x in range(10):
        if not isfound:
            elements = driver.find_elements_by_xpath(xpath)
            if len(elements) > 0:
                isfound = True
            else:
                time.sleep(0.5)
    return elements

def see(driver, key):
    return wait(driver, key)

def event(driver, keycode):
    return driver.press_keycode(keycode)

def click(elements):
    def do():
        elements[0].click()
        time.sleep(1)
    return do()

def tapkey(driver, key, index = 0,**kw):
    elements = find(driver, By.XPATH, tree(driver, key, index)['xpath'])
    if not elements:
        print('notfind')
        return 0
    location ={}
    size = {}
    location['x'] = elements[0].location['x']
    location['y'] = elements[0].location['y']
    size['height'] = elements[0].size['height']
    size['width'] = elements[0].size['width']
    webelement = Webelement(location,size)
    click(elements)
    return webelement

def tappoint(driver, x, y, time=100):
    # h,w = getscreenhw(driver)
    # tappoint(driver,h/2, w/2)
    return driver.tap([(x, y)], time)

def tapelement(driver, element):
    action = TouchAction(driver)
    return action.tap(element).perform()

def send(driver, key, text, index=0,X = By.XPATH):
    # key = "android.widget.EditText"
    # send(driver, key, '中文',0)
    elements = find(driver,X=By.XPATH,v=key,timeout=10)
    click(elements)
    elements[0].send_keys(text)
    return elements[0]

def sendkeys(element,text):
    element.send_keys(text)
    return element

def swipe(driver, startX= 0.9, endX= 0.1, startY=0.9, endY= 0.1):
    h,w,=getscreenhw(driver)
    return driver.swipe(int(w * startX),int(h * startY),int(w * endX),int(h * endY),1000)

def swipeto(driver, direction,**kw):
    # swipeto(driver,'up')
    # time.sleep(5)
    # swipeto(driver, 'down')
    if direction not in ['left','right','up','down']:return 0
    move = {
        'left': lambda: swipe(driver, 0.9, 0.1, 0.5, 0.5),
        'right': lambda: swipe(driver, 0.1, 0.9, 0.5, 0.5),
        'up': lambda: swipe(driver, 0.5, 0.5, 0.9, 0.1),
        'down': lambda: swipe(driver, 0.5, 0.5, 0.2, 0.9),
    }
    return move[direction]()

def getscreenhw(driver):
    size = driver.get_window_size()
    return (size['height'],size['width'])

def screenshot(driver,img):
    #todo minicap
    # http://blog.csdn.net/itfootball/article/details/47658171
    return asynctask(driver.get_screenshot_as_file,img)

def screenshot64(driver):
    return asynctask(driver.get_screenshot_as_base64)

def screenshotpng(driver):
    return asynctask(driver.get_screenshot_as_png)

def back(driver):
    # todo driver.navigate().back()
    return event(driver,4)

def iosback(driver):
    return driver.back()

# def backapp(driver):
#     # todo
#     # event(driver,4)
#     # time.sleep(1)
#     # event(driver,66)
#     back(driver)

def backapp(driver,package,activity):
    driver.start_activity(package,activity)

@exception
def dsl(driver,command,**kw):
    return eval(command)

def getcurrentactivity(*args,**kw):
    # driver.current_activity
    # 0.22600007057189941
    (driver,) = args
    return driver.current_activity

def hidekeyboard(driver,key_name=None,key=None,strategy=None):
    return driver.hide_keyboard(key_name,key,strategy)

#other api
def tapxy(x,y):
    os.popen("adb shell input tap "+str(x)+" "+str(y))

def findtoast(driver,message,timeout=10,interval=1):
    # https://testerhome.com/topics/2715,https://testerhome.com/topics/2346
    # test failed; todo
    element = WebDriverWait(driver,timeout,interval).\
        until(expected_conditions.presence_of_element_located((By.PARTIAL_LINK_TEXT,message)))
    return element

def asyncclick(driver,key,timeout):
    asynctask(tapkey, driver, key, timeout)

def getcontexts(driver):
    return driver.contexts

def getcurrcontext(driver):
    return driver.current_context

def switchcontext(driver,webview):
    return driver.switch_to.context(webview)

def scroll(driver, origin, destination):
    return driver.scroll(origin,destination)

def draganddrop(driver, e1, e2):
    return driver.drag_and_drop(e1, e2)

def flick(driver,startx,starty,endx,endy):
    return driver.flick(startx,starty,endx,endy)

def pinch(driver,element,percent=200,steps=50):
    return driver.pinch(element,percent,steps)

def zoom(driver,element,percent=200,steps=50):
    return driver.zoom(element,percent,steps)

def reset(driver):
    return driver.reset()

# def hidekeyboard(driver,key_name=None, key=None, strategy=None):
#     return driver.hide_keyboard(key_name,key,strategy)

def longpress(self, element, duration):
    action = TouchAction(self.driver).press(element).wait(duration).release()
    action.perform()
    return True

def presshome(self):
    self.driver.press_keycode(3)

def getcurractivity(driver):
    return driver.current_activity

def waitactivity(driver,activity,timeout=5,interval=1):
    return driver.wait_activity(activity,timeout,interval)

def runinbackgroud(driver,time):
    return driver.background_app(time)

def isappinstalled(driver,package):
    return driver.is_app_installed(package)

def installapp(driver,path):
    return driver.install_app(path)

def uninstallapp(driver,package):
    if isappinstalled(driver,package):
        return driver.remove_app(package)

def launchapp(driver):
    return driver.launch_app()

def closeapp(driver):
    return driver.close_app()

def startactivity(driver,package,activity,**kw):
    #only android
    return driver.start_activity(package,activity,**kw)

def lock(driver,time):
    #only ios
    return driver.lock(time)

# def shake(driver):
#     return driver.shake()

def opennotifications(driver):
    # android api>18
    return driver.open_notifications()

def getnetworkstate(driver):
    return driver.network_connection

def setnetworkstate(driver, state):
    # NO_CONNECTION = 0
    # AIRPLANE_MODE = 1
    # WIFI_ONLY = 2
    # DATA_ONLY = 4
    # ALL_NETWORK_ON = 6
    # from appium.webdriver.connectiontype import ConnectionType
    driver.set_network_connection(state)
    asyncclick(driver, '允许', 10)
    return True

def openlocation(driver):
    # only android
    return driver.toggle_location_services()

def setlocation(driver,latitude,longitude,altitude):
    #latitude -90 90
    #longitude -180 180
    return driver.set_location(latitude,longitude,altitude)

def getelementclasename(element):
    return element.tag_name()

def getelementtext(element):
    return element.text

def elementclearinput(element):
    return element.clear()

def getattr(element,attr):
    #https://testerhome.com/topics/2606
    #attr: name,text,classname,resourceid
    return element.get_attribute(attr)

def elementsishavevalue(elements,attr,value):
    try:
        for element in elements:
            v = getattr(element, attr)
            if value in v :return 1
        return 0
    except Exception:
        return 0

def isselected(element):
    #checkbox or radio is selected
    return element.is_selected()

def isenabled(element):
    return element.is_enabled()

def isvisible(element):
    return element.is_displayed()

def getelementsize(element):
    return element.size

def getelementxy(element):
    return element.location

# def getelementrect(element):
#     return element.rect

def execjs(driver,js,*args):
    #execjs(driver,'document.title')
    #test -not yet implement!!
    return driver.execute_script(js,*args)

def asyncexecjs(driver,js,*args):
    #test -not yet implement!!
    return driver.execute_async_script(js,*args)

def getcurrurl(driver):
    # test -not yet implement!!
    return driver.current_url

def close(driver):
    #test -not yet implement!!
    return driver.close()

def quit(driver):
    return driver.quit()

if __name__ == "__main__":
    source = '''<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation="0"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1440,2560]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1440,2560]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/action_bar_root" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="android:id/content" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/activity_live" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/live_room_viewpager" class="android.support.v4.view.ViewPager" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="1" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/videoview" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="true" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="" class="tv.danmaku.ijk.media.player.widget.media.TextureRenderView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]" /></node><node index="1" text="" resource-id="com.panda.videoliveplatform:id/clearScreenLayout" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/canvas_texture_view" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/loading_view" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/loading_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[596,784][844,1160]" /><node index="1" text="正在加载中..." resource-id="com.panda.videoliveplatform:id/loading_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[530,1160][909,1495]" /></node><node index="2" text="" resource-id="com.panda.videoliveplatform:id/clear_container" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/layout_gift_content" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/layout_gift_combo_parent" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/ll_combo_item_parent" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/layout_experience_item" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1640][1440,2560]" /></node></node><node index="1" text="" resource-id="com.panda.videoliveplatform:id/layout_user_info" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,124][1440,423]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,124][1440,423]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,124][1408,255]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/llt_host_info" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,124][387,255]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,124][163,255]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/img_host_avatar" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[36,128][159,251]" /><node index="1" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[103,199][163,255]" /><node index="2" text="5" resource-id="com.panda.videoliveplatform:id/txt_host_level_number" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[103,199][163,255]" /></node><node index="1" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[176,142][344,236]"><node index="0" text="熊猫甜儿" resource-id="com.panda.videoliveplatform:id/txt_host_nickName" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[176,142][344,194]" /><node index="1" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[176,194][234,236]"><node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[176,205][201,225]" /><node index="1" text="0" resource-id="com.panda.videoliveplatform:id/txt_room_person_num" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[214,194][234,236]" /></node></node></node><node index="1" text="" resource-id="com.panda.videoliveplatform:id/button_show" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[448,124][1408,255]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[448,124][1239,255]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/rcv_room_user" class="android.support.v7.widget.RecyclerView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[448,124][1239,255]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[448,124][576,255]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[448,124][576,255]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_room_user_avatar" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[454,132][569,247]" /><node index="1" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[512,191][576,255]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/img_rome_user_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[520,194][568,247]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/vw_padding" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[512,247][576,255]" /></node></node></node><node index="1" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[584,124][712,255]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[584,124][712,255]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_room_user_avatar" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[590,132][705,247]" /><node index="1" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[648,191][712,255]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/img_rome_user_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[656,194][704,247]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/vw_padding" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[648,247][712,255]" /></node></node></node></node></node><node NAF="true" index="2" text="" resource-id="com.panda.videoliveplatform:id/layout_user_list" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1263,132][1408,247]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1299,179][1372,199]"><node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1299,179][1318,199]" /><node index="1" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1326,179][1345,199]" /><node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1353,179][1372,199]" /></node></node></node></node><node index="1" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,271][610,423]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,271][405,423]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/xy_lv_roundprogress_bar" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,285][405,409]" /><node index="1" text="40428" resource-id="com.panda.videoliveplatform:id/txt_host_star_val" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,305][385,389]" /></node><node NAF="true" index="1" text="" resource-id="com.panda.videoliveplatform:id/iv_guard" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[458,285][610,409]" /></node></node></node><node index="2" text="" resource-id="com.panda.videoliveplatform:id/gift_marquee_layout" class="android.widget.HorizontalScrollView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" bounds="[0,396][1440,660]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,396][1440,660]" /></node><node NAF="true" index="3" text="" resource-id="com.panda.videoliveplatform:id/img_week_rank" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,447][413,531]" /><node index="4" text="" resource-id="com.panda.videoliveplatform:id/layout_room_activity" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,821]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,821]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/cbr_activity_img" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,821]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,821]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,821]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/cbLoopViewPager" class="android.support.v4.view.ViewPager" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,795]"><node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,582][303,795]" /></node></node></node></node></node></node><node index="5" text="" resource-id="com.panda.videoliveplatform:id/special_marquee_layout" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1624][1440,1748]" /><node index="6" text="" resource-id="com.panda.videoliveplatform:id/chat_msg_layout" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1768][1200,2344]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/chat_msg_list_recyclerview" class="android.support.v7.widget.RecyclerView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" bounds="[0,1768][1200,2328]"><node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1768][1200,1844]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,1768][144,1822]" /><node index="1" text="笨兔兔爱的傻摆摆：您能火&#128293;" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,1768][866,1844]" /></node><node index="1" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1844][1200,1940]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,1862][144,1918]" /><node index="1" text="笨兔兔爱的傻摆摆：我老了" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,1844][800,1940]" /></node><node index="2" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1940][1200,2036]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,1958][144,2014]" /><node index="1" text="笨兔兔爱的傻摆摆：跑不动了" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,1940][853,2036]" /></node><node index="3" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,2036][1200,2132]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,2054][144,2110]" /><node index="1" text="笨兔兔爱的傻摆摆：拜拜" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,2036][747,2132]" /></node><node index="4" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,2132][1200,2228]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,2150][144,2206]" /><node index="1" text="xmidqc4ohvflm2 关注了主播" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,2132][865,2228]" /></node><node index="5" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,2228][1200,2328]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/msg_avatar_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,2246][144,2302]" /><node index="1" text="xy_ic_fang宇宙无敌萌贱帅来了" resource-id="com.panda.videoliveplatform:id/msg_content_tv" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[164,2228][713,2328]" /></node></node></node><node index="8" text="" resource-id="com.panda.videoliveplatform:id/bottom_bar" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[32,2344][1408,2520]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/send_cmt_btn" class="android.widget.ImageButton" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[32,2381][171,2520]" /><node NAF="true" index="1" text="" resource-id="com.panda.videoliveplatform:id/share_btn" class="android.widget.ImageButton" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1104,2381][1243,2520]" /></node></node><node index="3" text="" resource-id="com.panda.videoliveplatform:id/end_view" class="android.widget.ScrollView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/ll_live_end_anchor_info" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,172][1440,1063]"><node index="0" text="直播已结束" resource-id="" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[530,172][910,279]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/live_end_host_portrait" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[586,315][854,583]" /><node index="2" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[561,623][878,693]"><node index="0" text="熊猫甜儿" resource-id="com.panda.videoliveplatform:id/live_end_anchor_name" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[561,623][757,693]" /><node index="1" text="" resource-id="com.panda.videoliveplatform:id/img_end_host_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[770,623][878,678]" /></node><node index="3" text="星颜ID：7199720" resource-id="com.panda.videoliveplatform:id/txt_end_xid" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[534,724][905,789]" /><node index="4" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[166,822][1274,918]"><node index="0" text="粉丝：194" resource-id="com.panda.videoliveplatform:id/txt_end_fans_num" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[166,822][489,918]" /><node index="1" text="" resource-id="" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[489,850][490,890]" /><node index="2" text="星值：4万" resource-id="com.panda.videoliveplatform:id/txt_end_star_val" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[490,822][805,918]" /><node index="3" text="" resource-id="" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[805,850][806,890]" /><node index="4" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[806,822][1053,918]"><node index="0" text="排行榜" resource-id="com.panda.videoliveplatform:id/txt_end_score_rank" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[806,822][1053,918]" /></node><node index="5" text="" resource-id="" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1053,822][1274,918]"><node index="0" text="英雄" resource-id="com.panda.videoliveplatform:id/txt_end_hero" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1053,822][1274,918]" /></node></node><node NAF="true" index="5" text="" resource-id="com.panda.videoliveplatform:id/btn_live_end_follow" class="android.widget.Button" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[586,971][854,1063]" /></node><node index="1" text="" resource-id="com.panda.videoliveplatform:id/ll_live_end_recommend" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1119][1440,1178]"><node index="0" text="" resource-id="" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,1148][574,1149]" /><node index="1" text="精彩推荐" resource-id="" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[642,1119][810,1178]" /><node index="2" text="" resource-id="" class="android.view.View" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[866,1148][1440,1149]" /></node><node index="2" text="" resource-id="com.panda.videoliveplatform:id/rl_live_end_room_parent" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1254][1344,2502]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1254][688,1846]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1254][688,1846]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_fengmian" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1254][688,1846]" /><node index="1" text="镇江市" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_position" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[498,1278][668,1337]" /><node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1585][688,1846]" /><node index="3" text="我叫十三幺" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_name" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[112,1775][322,1834]" /><node index="4" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[334,1775][442,1830]" /><node index="5" text="9927人" resource-id="com.panda.videoliveplatform:id/tv_live_end_number_of_people" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[522,1775][664,1834]" /></node></node><node index="1" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1254][1344,1846]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1254][1344,1846]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_fengmian" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1254][1344,1846]" /><node index="1" text="滨州市" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_position" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1154,1278][1324,1337]" /><node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1585][1344,1846]" /><node index="3" text="水水是个谜" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_name" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[768,1775][978,1834]" /><node index="4" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[990,1775][1098,1830]" /><node index="5" text="17888人" resource-id="com.panda.videoliveplatform:id/tv_live_end_number_of_people" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1153,1775][1320,1834]" /></node></node><node index="2" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1910][688,2502]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1910][688,2502]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_fengmian" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,1910][688,2502]" /><node index="1" text="延边朝鲜族自治州" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_position" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[288,1934][668,1993]" /><node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[96,2241][688,2502]" /><node index="3" text="护食的艺文baby" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_name" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[112,2431][372,2490]" /><node index="4" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[384,2431][492,2486]" /><node index="5" text="5688人" resource-id="com.panda.videoliveplatform:id/tv_live_end_number_of_people" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[522,2431][664,2490]" /></node></node><node index="3" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1910][1344,2502]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1910][1344,2502]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_fengmian" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,1910][1344,2502]" /><node index="1" text="上海市" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_position" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1154,1934][1324,1993]" /><node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[752,2241][1344,2502]" /><node index="3" text="胸前有炸弹" resource-id="com.panda.videoliveplatform:id/tv_live_end_item_anchor_name" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[768,2431][978,2490]" /><node index="4" text="" resource-id="com.panda.videoliveplatform:id/img_live_end_item_anchor_level" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[990,2431][1098,2486]" /><node index="5" text="6187人" resource-id="com.panda.videoliveplatform:id/tv_live_end_number_of_people" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1178,2431][1320,2490]" /></node></node></node></node></node><node index="4" text="" resource-id="com.panda.videoliveplatform:id/layout_finger_guessing_begin" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,2560]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,96][1440,1166]" /></node><node index="5" text="7199720" resource-id="com.panda.videoliveplatform:id/txt_room_xid" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" bounds="[1192,320][1408,428]" /><node NAF="true" index="6" text="" resource-id="com.panda.videoliveplatform:id/xy_screen_shot_entry_layout" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1269,1941][1408,2080]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1269,1941][1408,2080]"><node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1269,1941][1408,2080]" /><node index="1" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1302,1970][1375,2050]" /></node></node><node index="7" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[36,2120][1404,2520]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/llt_finger_guessing_parent" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[136,2230][733,2520]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/llt_finger_guessing" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[136,2230][733,2520]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/txt_finger_guessing_entry" class="android.widget.TextView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[365,2381][504,2520]" /></node></node><node NAF="true" index="1" text="" resource-id="com.panda.videoliveplatform:id/gift_btn" class="android.widget.ImageButton" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[650,2380][790,2520]" /><node NAF="true" index="2" text="" resource-id="com.panda.videoliveplatform:id/xy_secret_chat_entry" class="android.widget.LinearLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[942,2381][1081,2520]"><node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[942,2381][1081,2520]"><node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[942,2381][1081,2520]" /></node></node></node><node index="8" text="" resource-id="com.panda.videoliveplatform:id/bamboo_layout" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[876,2101][1408,2240]"><node index="0" text="" resource-id="" class="android.widget.RelativeLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[876,2101][1408,2240]"><node index="0" text="" resource-id="com.panda.videoliveplatform:id/bamboo_lay" class="android.widget.FrameLayout" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1269,2101][1408,2240]"><node NAF="true" index="0" text="" resource-id="com.panda.videoliveplatform:id/bamboo_iv" class="android.widget.ImageView" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="true" bounds="[1269,2101][1408,2240]" /></node></node></node><node NAF="true" index="9" text="" resource-id="com.panda.videoliveplatform:id/close_btn" class="android.widget.ImageButton" package="com.panda.videoliveplatform" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[1269,2381][1408,2520]" /></node></node></node></node></node></node></node></node></node></hierarchy>'''
    nlist = xpathtolist('//*',source)
    print(nlist)
    # startappiumserver(4723,3)
    # time.sleep(15)
    # #test
    # #apk = 'D:\\automonkey\\conf\\pandalive.apk'
    # apk = '%s%sconf%spandalive.apk'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep)
    #
    # #deviceid = re.findall(r'^\w*\b', list(os.popen('adb devices').readlines())[1])[0]
    # #deviceversion = re.findall(r'^\w*\b',list(os.popen('adb shell getprop ro.build.version.release').readlines())[0])[0]
    # #package = re.findall(r'\'com\w*.*?\'', list(os.popen('aapt dump badging ' + apk ).readlines())[0])[0]
    #
    # t0 = time.time()
    # package='com.panda.videoliveplatform'
    # activity='com.panda.videoliveplatform.activity.WelcomeActivity'
    # driver = startapp(4723,'22c41bc',apk ,True,package,activity,activity)
    # #driver.implicitly_wait(30)
    #
    # t1 = time.time()
    # key = "//*[@resource-id='com.panda.videoliveplatform:id/main_column_live_btn']"
    # text = "com.panda.videoliveplatform:id/main_column_live_btn"
    # print(t1 - t0)
    #
    # elements = wait(driver,key)
    # t2 = time.time()
    # print(t2 - t1)
    #
    # print('gogo')
    # time.sleep(30)
    # source = asynctask(getpagesource, driver, timeout=60)
    # t3 = time.time()
    # print(t3 - t2)
    # print(source)

    # #back(driver)
    # #logobj.info(source)
    # key = "//*[@content-desc='登录' and @class='android.view.View' and @clickable='true']"
    # elements = find(driver,By.XPATH,key)
    # print(elements)
    # elements[0].click()
    # img = 'd:\\test.png'
    # screenshot(driver, img)
    # t4 = time.time()
    # print(t4 - t3)
    #
    # index=0
    # key = "com.panda.videoliveplatform:id/main_user_btn"
    # see(driver,key)
    # t5 = time.time()
    # print(t5 - t4)
    #
    # tapkey(driver,key,index)
    # t6 = time.time()
    # print(t6 - t5)
    #
    # key = "点击登录"
    # see(driver, key)
    # t7 = time.time()
    # print(t7 - t6)
    #
    # tapkey(driver, key, index)
    # t8 = time.time()
    # print(t8 - t7)
    #
    # # key = "登录"
    # # see(driver, key)
    # # elements = wait(driver, key)
    # # key = "android.widget.EditText"
    # # send(driver, key, '中文',0)
    # time.sleep(1)
    #
    # # dom = ''
    # # xpath = "//UIANavigationBar/UIAButton[2]"
    # # dom = open('D:\\automonkey\\tmp\\test.dom','rb').read().decode('utf-8')
    # # list = xpathtolist(xpath,dom)
    # # print(list)