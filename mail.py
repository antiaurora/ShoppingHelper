#coding:utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def send(status,words):        
    # 第三方 SMTP 服务

    mail_host="smtp.qq.com"       #设置服务器:这个是qq邮箱服务器，直接复制就可以
    mail_pass="xxxxxxxxxxxxxxxx"           #刚才我们获取的授权码
    sender = 'xxxxxxxxx@qq.com'      #你的邮箱地址 
    receivers = ['xxxxxxxx@xxxxxxxx']  # 收件人的邮箱地址，可设置为你的QQ邮箱或者其他邮箱，可多个   

    content = words
    message = MIMEText(content, 'plain', 'utf-8')

    message['From'] = Header("xxx", 'utf-8')  
    message['To'] =  Header("管理员", 'utf-8')
        
    subject = status  #发送的主题，可自由填写
    message['Subject'] = Header(subject, 'utf-8') 
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465) 
        smtpObj.login(sender,mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string())
        smtpObj.quit()
        print('邮件发送成功')
    except smtplib.SMTPException as e:
        print('邮件发送失败')


if  __name__ == '__main__':
    send()