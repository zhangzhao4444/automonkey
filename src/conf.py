#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161005
# @version: 1.0.0.1009

import yaml
import os,platform

def dictinsertdict(dicta,dictb):
    for k, v in dicta.items():
        x = dictb.get(k)
        if not x:
            dictb[k] = v
        else:
            if isinstance(v,dict):
                dictinsertdict(v, x)
            else:
                dictb[k] = v

class Conf():
    def __init__(self):
        self.conf = {}
        self.conf['pluginlist'] = []
        self.conf['saveScreen'] = True
        self.conf['pageobject'] = False
        self.conf['reportTitle'] = ''
        self.conf['screenshotTimeout'] = 20
        self.conf['currentDriver'] = 'Android'
        self.conf['tagLimitMax'] = 6
        self.conf['tagLimit'] = []
        self.conf['showCancel'] = False
        self.conf['maxTime'] = 3600*3
        #win
        if 'Windows' in platform.system():self.conf['resultDir'] = '%s%sresult' % (os.path.split(os.path.realpath(__file__))[0], os.path.sep)
        #linux jenkins
        else: self.conf['resultDir'] = '/home/zhangzhao/work/test/job/workspace/Pandatv_uimonkeytest_android'
        self.conf['gt'] = False
        capability = {}
        capability['app'] = ''
        capability['udid'] = ''
        capability['noRest'] = False
        capability['autoWebview'] = False
        capability['autoLaunch'] = True
        capability['unicodeKeyboard'] = True
        capability['resetKeyboard'] = True
        self.conf['capability'] = capability
        androidcapability = {}
        androidcapability['platformName'] = 'android'
        androidcapability['deviceName'] = 'android'
        androidcapability['appPackage'] = ''
        androidcapability['appActivity'] = ''
        androidcapability['appWaitActivity'] = ''
        androidcapability['mainActivity'] = 'com.panda.videoliveplatform.MainFragmentActivity'
        self.conf['androidCapability'] = androidcapability
        ioscapability = {}
        ioscapability['automationName'] = 'XCUITest'
        ioscapability['bundleID'] = ''
        ioscapability['autoAcceptAlerts'] = True
        ioscapability['platformVersion'] = '10.2.1'
        ioscapability['platformName'] = 'iOS'
        ioscapability['deviceName'] = 'iPhone 6'
        self.conf['iosCapability'] = ioscapability
        self.conf['xpathAttributes'] = ['name','label','value','resource-id','content-desc','index','text']
        self.conf['defineUrl'] = []
        self.conf['baseUrl'] = []
        self.conf['appWhiteList'] = []
        self.conf['maxDepth'] = 6
        self.conf['headFirst'] = True
        self.conf['enterWebView'] = True
        self.conf['urlBlackList'] = []
        self.conf['urlWhiteList'] = []
        self.conf['defaultBackAction'] = []
        self.conf['backButton'] = []
        self.conf['firstList'] = []
        self.conf['selectedList'] = ["//*[contains(name(), 'Text')]",
                                     "//*[contains(name(), 'Image')]",
                                     "//*[contains(name(), 'Button')]",
                                     "//*[contains(name(), 'CheckBox')]"]
        self.conf['lastList'] = []
        self.conf['blackList'] = []
        self.conf['extrablackList'] = []
        self.conf['elementActions'] = []
        self.conf['startupActions'] = ["time.sleep(3)",
                                       "swipeto(driver,\"left\")",
                                       "swipeto(driver,\"left\")",
                                       "swipeto(driver,\"left\")",
                                       "swipeto(driver,\"left\")",
                                       "swipeto(driver,\"left\")"]
        self.conf['beforeElementAction'] = []
        self.conf['afterElementAction'] = []
        self.conf['afterUrlFinished'] = []
        self.conf['monkeyEvents'] = []
        self.conf['monkeyRunTimeSeconds'] =30
        self.conf['schemaBlackList'] = []
        self.conf['beforeRefreshpageAction'] = []
        self.conf['randomselect'] = 1
        self.conf['startupClosePopenSysmenu'] = []
        self.conf['elementActionsInanyURLwilldo'] = []

    def load(self,path):
        file = open(path,encoding='gbk')
        yamlconf = yaml.load(file)
        dictinsertdict(yamlconf,self.conf)
        return self.conf

def test():
    ymlpath = '%s%sconf%spanda.yml'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep)
    config = Conf()
    config.load(ymlpath)
    print(config.conf)

if __name__ == "__main__":
    test()

