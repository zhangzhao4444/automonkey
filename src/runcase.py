#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20170301
# @version: 1.0.0.1001

import sys,os
sys.path.append('..')

# https://pypi.python.org/pypi/html-testRunner/1.0.3
# pip install --index-url=http://pypi.python.org/simple/ --trusted-host pypi.python.org html_testRunner-1.0.3-py2.py3-none-any.whl
import unittest
import time,re
#from nose.tools import *
import functools
import selenium
import traceback
import util
import appiumdriver
import logger
import HTMLTestRunner
import monkey
from optparse import OptionParser
from selenium.webdriver.common.by import By
logobj=logger.logobj

class GEB(monkey.Crawler):
    def __init__(self,cmd):
        super().__init__(cmd)
        logobj.info('GEB class init')

def screensnap(funname,ret):
    if not os.path.exists(Geb.resultdir): os.makedirs(Geb.resultdir)
    timestamp = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    png = Geb.resultdir + os.path.sep + '%s_%s' %(funname,timestamp) + '.png'
    appiumdriver.screenshot(driver, png)
    try:
        if isinstance(ret, list):
            element = ret[0]
        else:
            element = ret
        x = element.location['x']
        y = element.location['y']
        h = element.size['height']
        w = element.size['width']
        util.addmarker(png, x, y, h, w)
    except:
        logobj.info('not WebElement Object')
    return png

def teststep(func):
    @functools.wraps(func)
    def wrapper(funcation,*args, **kwargs):
        string = str(funcation)
        result = re.compile('function (\w+) at').findall(string) or re.compile('method (TestCase.\w+) of').findall(string)
        functionname = result[0]
        line = sys._getframe().f_back.f_lineno
        if 'TestCase' in functionname:
            key = ','.join(args)
        else:
            key = args[1]
            if 'resource-id' in key:
                x = re.compile(r"@resource-id='(\S+)'").findall(key)[0].split('/')[-1]
                key = x
            elif 'name' in key:
                x = re.compile(r"@name='(\S+)'").findall(key)[0]
                key = x
            elif '/' in key:
                key = key.split('/')[-1]
        logobj.info('\t--> %s,%s,%s' % (line, functionname, args[1]))
        parentfunc = sys._getframe().f_back.f_back.f_locals['args'][0]._testMethodName
        png = '%s-%s-%s-%s-' % (parentfunc, line, functionname, key)
        ret = None
        try:
            ret = func(funcation,*args, **kwargs)
            if ret or (not ret and 'TestCase' in functionname):
                png += 'pass-'
                return ret
            else:
                png += 'fail-'
                logobj.info('\t<-- %s,%s,%s Fail' % (line, functionname, args[1]))
                raise AssertionError
        except selenium.common.exceptions.WebDriverException:
            png += 'error-'
            logobj.info('\t<-- %s,%s,%s Error' %(line,functionname, args[1]))
            raise selenium.common.exceptions.WebDriverException
        except AssertionError:
            if 'TestCase' in functionname:
                png += 'fail-'
                logobj.info('\t<-- %s,%s,%s Fail' % (line, functionname, args[1]))
            raise AssertionError
        finally:
            screensnap(png,ret)
    return wrapper

@teststep
def do(func,*args,**kw):
    ret = func(*args,**kw)
    return ret

def testcase(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logobj.info('--> %s'%func.__qualname__)
            ret = func(*args, **kwargs)
            logobj.info('<-- %s, %s\n'%(func.__qualname__, 'Success'))
            return ret
        except selenium.common.exceptions.WebDriverException:
            logobj.info('<-- %s, %s\n'%(func.__qualname__, 'Error'))
            raise selenium.common.exceptions.WebDriverException
        except AssertionError:
            logobj.info('<-- %s, %s\n'%(func.__qualname__, 'Fail'))
            raise AssertionError
        except:
            logobj.error(traceback.format_exc())
    return wrapper


class TestCase(unittest.TestCase):

    @classmethod
    def setUp(self):
        Geb.startclient()
        global firstrun
        global secrun
        if firstrun:
            appiumdriver.asynctask(Geb.dialogmonitor, timeout=3)
            firstrun = 0
            time.sleep(15)
        else:
            secrun = 1
        global driver
        driver = Geb.driver
        appiumdriver.back(Geb.driver)
        Geb.maybedialog = False
        time.sleep(5)
        if secrun:
            appiumdriver.whenfindclick(Geb.driver, By.XPATH, Obj.FollowRecommendActivity.tv_skip)

    @classmethod
    def tearDown(self):
        driver.quit()

    @testcase
    def test_case_01(self):
        index = 0
        #key = "com.panda.videoliveplatform:id/main_user_btn"
        key = Obj.MainFragmentActivity.main_user_btn
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)

        appiumdriver.swipeto(driver,'down')

        #key = "点击登录"
        key = Obj.MainFragmentActivity.tv_click2login
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)
        time.sleep(3)

        key = Obj.WebLoginActivity.toolbar_title
        do(appiumdriver.see, driver, key)
        elements = appiumdriver.find(driver,By.XPATH,key)
        do(self.assertEqual,appiumdriver.getelementtext(elements[0]),'登录')

        key = Obj.WebLoginActivity.phone
        phone = '13488723896'
        do(appiumdriver.send, driver, key, phone)

        key = Obj.WebLoginActivity.password
        password = '123456'
        do(appiumdriver.send, driver, key, password)

        key = "//*[@content-desc='登录' and @class='android.view.View' and @clickable='true']"
        do(appiumdriver.tapkey, driver, key, index)

        key = Obj.MyFollowActivity.tv_name
        do(appiumdriver.see, driver, key)
        elements = appiumdriver.find(driver, By.XPATH, key)
        do(self.assertEqual, appiumdriver.getelementtext(elements[0]), 'niuyihan0603')

    @testcase
    def test_case_02(self):
        index = 0
        key = Obj.MainActivity.main_column_live_btn
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)

        key = Obj.MainActivity.iv_pic
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)

        key = Obj.LiveRoomActivity.layout_video_label
        do(appiumdriver.see, driver, key)

        key = Obj.LiveRoomActivity.messageEditText
        do(appiumdriver.see, driver, key)
        message = '666'
        do(appiumdriver.send, driver, key, message)

        key = Obj.LiveRoomActivity.sendButton
        do(appiumdriver.tapkey, driver, key, index)

        time.sleep(1)
        key = Obj.LiveRoomActivity.textTextView
        elements = appiumdriver.find(driver, By.XPATH, key)
        do(appiumdriver.elementsishavevalue,elements,'text',message)
        time.sleep(1)

    @testcase
    def test_case_03(self):
        index = 0
        key = Obj.MainActivity.main_column_live_btn
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)

        key = Obj.MainActivity.iv_pic
        do(appiumdriver.see, driver, key)
        do(appiumdriver.tapkey, driver, key, index)

        keyA = Obj.LiveRoomActivity.layout_video_label
        key = Obj.LiveRoomActivity.iv_player_enlarge
        appiumdriver.whennotfindAclickB(driver,key,keyA)
        do(appiumdriver.tapkey, driver, key, index)

        key = Obj.LiveRoomActivity.textview_full_control_text_msg
        appiumdriver.whennotfindclickxy(driver, key, 500,500)
        message = '2333'
        do(appiumdriver.send, driver, key, message)
        elements = appiumdriver.find(driver, By.XPATH, key)
        do(self.assertEqual, appiumdriver.getelementtext(elements[0]), message)

        #key = Obj.LiveRoomActivity.button_full_control_danmu_send
        #do(appiumdriver.tapkey, driver, key, index)
        x = 0.7
        y = 0.95
        w, h = Geb.adb.getscreenhw()
        appiumdriver.tappoint(driver, h*x, w*y)

        appiumdriver.whennotfindclickxy(driver, key, 500, 500)
        elements = appiumdriver.find(driver, By.XPATH, key)
        do(self.assertEqual, appiumdriver.getelementtext(elements[0]), '输入聊天内容')
        time.sleep(5)

if __name__ == '__main__':
    cmd = monkey.cmd()

    #debug
    appname = cmd['config'].split(os.path.sep)[-1].split('.')[0]
    #debug

    #cmd
    #appname = cmd.config.split(os.path.sep)[-1].split('.')[0]
    #cmd
    file = '%s%sconf%s%s_pageobject.yml' % (
    os.path.split(os.path.realpath(__file__))[0], os.path.sep, os.path.sep, appname)
    if os.path.exists(file):
        pageobjects = util.readyml(file)
        Obj = util.obj(pageobjects)

    Geb = GEB(cmd)
    Geb.registctrlc()
    Geb.startadbinstall()
    Geb.startserver()
    time.sleep(25)
    print(Geb.resultdir)
    if not os.path.exists(Geb.resultdir): os.makedirs(Geb.resultdir)
    file = open(Geb.resultdir+ os.path.sep +'testreport.html','wb')
    firstrun = 1
    secrun = 0
    tmp = sys.argv[0]
    sys.argv =[]
    sys.argv.append(tmp)
    unittest.main(testRunner = HTMLTestRunner.HTMLTestRunner(stream=file, title='%s_自动化CASE测试报告'%os.path.basename(Geb.apppath), description='用例执行情况：',resultdir=Geb.resultdir))