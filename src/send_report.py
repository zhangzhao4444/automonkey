# -*- coding:utf-8 -*-

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import smtplib
import time
day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
from optparse import OptionParser

def sendmail(toMail, subject, content):
    smtpHost = 'postman.ops.pandatv.com'
    sslPort = '465'
    fromMail = 'qa@postman.ops.pandatv.com'
    username = 'qa@postman.ops.pandatv.com'
    password = '1PimRC6yvg2i'

    encoding = 'utf-8'
    mail = MIMEMultipart('alternative')
    mail = MIMEText(content.encode(encoding), 'html', encoding)
    mail['Subject'] = Header(subject, encoding)
    mail['From'] = fromMail
    mail['To'] = ','.join(toMail)
    mail['Date'] = day

    try:
        smtp = smtplib.SMTP_SSL(host=smtpHost, port=sslPort, timeout=10)
        smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(fromMail, toMail , mail.as_string())
        smtp.close()
        return 0
    except Exception as e:
        print('ERROR:unable to send mail',e)
        return 1

def sender(subject,email,url,tomail):
    _, api = url.split(':8080')
    url = 'http://10.31.131.43:8080' + api
    fromMail = 'qa@postman.ops.pandatv.com'
    toMail = ['zhangzhao@panda.tv', 'zhanglihui@panda.tv','libing@panda.tv']
    toMail.append(tomail)
    file = open(email,'r', encoding='UTF-8')
    html =''
    try:
        for line in file:
            html += line
    finally:
        file.close()
    html = html.replace('{jenkinshtmlreporturl}','"'+ url + '"')

    sendmail(toMail, subject , html)

if __name__ == '__main__':
    usage = ''
    cmd = OptionParser(usage)
    cmd.add_option("-t", "--title", type="string", dest="title")
    cmd.add_option("-f", "--file", type="string", dest="email")
    cmd.add_option("-a", "--url", type="string", dest="url")
    cmd.add_option("-p", "--tomail", type="string", dest="tomail")
    (options, args) = cmd.parse_args()
    sender(options.title,options.email,options.url,options.tomail)

#python sendtomail.py -t [自动化报告]Pandatv_uimonkeytest_android#56 -f D:\automock\result\2017_01_23_12_17_16\TestReprot.html -a baidul.com -p zhangzhao@panda.tv
