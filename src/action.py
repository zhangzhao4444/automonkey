#!/usr/bin/evn python
# -*- coding:utf-8 -*-
# @author: zhangzhao_lenovo@126.com
# @date: 20161201
# @version: 1.0.0.1001

import time,os,sys
sys.path.append('..')
from optparse import OptionParser
import util
import appiumdriver
import logger
import monkey
from selenium.webdriver.common.by import By
logobj=logger.logobj

class Action(monkey.Crawler):
    def __init__(self,cmd):
        super().__init__(cmd)
        logobj.info('action class init')
        self.closepopup = 0

    def action(self):
        self.maybedialog = False
        # U can do it
        key = "//*[@resource-id='com.panda.videoliveplatform:id/iv_pic']"
        elements = appiumdriver.wait(self.driver,key)
        appiumdriver.click(elements)
        time.sleep(3)
        appiumdriver.back(self.driver)
        if not self.closepopup:
            closekey = "//*[@resource-id='com.panda.videoliveplatform:id/forget']"
            ret = appiumdriver.whenfindclick(self.driver, By.XPATH, closekey, timeout=2)
            if ret: self.closepopup = 1
        time.sleep(1)

    def makereport(self):
        if not self.report: self.report = self.resultdir+os.path.sep+'testreport.html'
        util.report(self.report, 'Action性能基准测试', self.baseinfo, self.coverageinfo, self.crashinfo, self.anrinfo, self.tombinfo, self.oominfo, self.perfinfo)

    def stop(self, signum, frame):
        self.running = False
        logobj.info('test finished!')
        if not os.path.exists(self.resultdir): os.makedirs(self.resultdir)
        self.calccrash()
        self.calcperformation()
        self.makereport()
        sys.exit()

    def start(self):
        self.registctrlc()
        self.startadbinstall()
        self.startserver()
        time.sleep(30)
        self.startclient()
        appiumdriver.asynctask(self.dialogmonitor, timeout=3)
        appiumdriver.back(self.driver)
        time.sleep(2)
        self.perfmonitor(2)
        self.screenheight,self.screenwigth = appiumdriver.getscreenhw(self.driver)

        keep = 10

        while keep:
            try:
                self.action()
                keep -= 1
            except Exception as e:
                logobj.error(e)
                keep = False
        self.stop(None,None)

if __name__ == "__main__":
    Ac = Action(monkey.cmd())
    Ac.start()