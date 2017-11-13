# -*- coding:utf-8 -*-

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import smtplib
import time
day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
from optparse import OptionParser

def sendmail(toMail, subject, content):
    smtpHost = 'xx.pandatv.com'
    sslPort = 'x'
    fromMail = 'qa@xx.pandatv.com'
    username = 'qa@xx.pandatv.com'
    password = '1'

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
    url = 'http://xx:8080' + api
    fromMail = 'qa@xx.pandatv.com'
    toMail = ['xx@panda.tv']
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

