# coding:utf-8
import logging
import re
import time
import mail
from flask import Flask, current_app, redirect, url_for,request
from pymysql import NULL
import WXBizMsgCrypt3 
import sql

log_data=time.strftime("%Y-%m-%d", time.localtime())
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(filename='./log/'+log_data+'.log', level=logging.INFO, format=LOG_FORMAT)

# 创建Flask的应用程序
# __name__表示当前的模块名字
#           模块名，flask以这个模块所在的目录为总目录，默认这个目录中的static为静态目录，templates为模板目录
app = Flask(__name__)

# 通过method限定访问方式
@app.route("/", methods=["GET","POST"])
def function():
    sToken = "xxxxxxxxxxxxxxxxxxx"
    sEncodingAESKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    sCorpID = "wwxxxxxxxxxxxxxxxx"
    
    #接收信息区
    msg_signature=request.args.get("msg_signature")
    timestamp=request.args.get("timestamp")
    nonce=request.args.get("nonce")
    
    #实例化一个加解码对象
    sb=WXBizMsgCrypt3.WXBizMsgCrypt(sToken,sEncodingAESKey,sCorpID)
    
    #解码区
        #验证URL有效性
    if(request.method=="GET"):
        echostr=request.args.get("echostr")
        ret,sEchoStr=sb.VerifyURL(msg_signature,timestamp,nonce,echostr)
        print("接收到的值是:",sEchoStr)
        if(ret!=0):
            print("故障码:",ret)
            return("故障码",ret)
        return (sEchoStr)
    
        #回调函数
    if(request.method=="POST"):  
        #接收数据  
        body_data=request.data
        ret,sMsg=sb.DecryptMsg(body_data, msg_signature, timestamp, nonce)
        if( ret!=0 ):
            print("故障码:",ret)
            return("故障码",ret)
        
        #定位匹配，5s一次的定位信息滚蛋
        rx_msg_location=re.findall("<Event><!\[CDATA\[LOCATION\]\]>",sMsg.decode("utf-8"))
        if rx_msg_location!=[]:
            return sMsg

        print("接收到的用户发送的全数据是:",sMsg.decode("utf-8"))

        #用户账户匹配
        rx_msg_staff=re.findall("<FromUserName><!\[CDATA\[(.*?)\]",sMsg.decode("utf-8"))
        db_s=sql.sql_real()
        staff_table=db_s.sql_staff(rx_msg_staff[0])
        staff_real_name=staff_table[1]
        db_s.close
        #用户进入匹配
        rx_msg_agent=re.findall("<!\[CDATA\[enter_agent\]\]>",sMsg.decode("utf-8"))
        if rx_msg_agent!=[]:
            #数据拼接
            db_s=sql.sql_real()
            staff_table=db_s.sql_staff(rx_msg_staff[0])
            if staff_table==None:
                db_words="还不认识你呢，请找管理员添加一下哦"
            else:
                staff_real_name=staff_table[1]
                db_words="哈喽，可以随时叫我名字哦"
            db_s.close()
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''            
            #加个log
            logging.info("用户："+staff_real_name+"进入会话")
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #文字内容匹配
        #<Content><![CDATA[ABCDEFGHIJKLMN]]>
        rx_msg=re.findall("<Content><!\[CDATA\[(.*?)\]",sMsg.decode("utf-8"))
        # print("用户发送的数据是:",rx_msg[0])
        
        if rx_msg==[]:
    #         body_data = '''<xml>
    # <MsgType><![CDATA[text]]></MsgType>
    # <Content><![CDATA['''+"暂时解析不了别的消息哦"+''']]></Content>
    # </xml>'''
    #         ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
    #         if( ret!=0 ):
    #             print("故障码:",ret)
    #             return("故障码",ret)
            return "内容异常"


        #返回数据
            #防注入
        hack=[';' , "and" , "insert" , "update","updata"]
        for i in hack:
            if i in str(rx_msg[0]):
                print("注入检验命中")
                db_words="不要试图让我系统错乱哦~"
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg


        #帮助
        if rx_msg[0] in ["帮助","help"] :
            #数据拼接
            db_s=sql.sql_real()
            help_table=db_s.all_help()
            db_words="请问有什么可以为您服务的呢？"
            try:
                for i in range(0,100):
                    db_words = db_words + "\r\n"+str(help_table[i][0])+"、"+help_table[i][1]
            except:
                print("退出帮助信息循环")

            db_s.close()
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''      
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")      
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #我的积分
        if rx_msg[0] in ["积分","我的积分"] :
            #数据拼接
            db_s=sql.sql_real()
            staff_table=db_s.sql_staff(rx_msg_staff[0])
            if staff_table==None:
                db_words="还不认识你呢，请找管理员添加一下哦"
            else:
                db_words=""+staff_table[1]+"您好，您有"+str(staff_table[3])+"点x分。抓紧上车兑换礼品!"
            db_s.close()
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''  
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")          
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #我的商城
        if rx_msg[0] in ["商店","商城","打开商店","打开商城","积分兑换","积分商城","积分商店","商品列表","积分兑换","兑换","兑换表","兑换商城","兑换商店","购买商品","商品购买","兑换商品","商品兑换"]:
            #数据拼接
            db_s=sql.sql_real()
            commodity_table=db_s.all_commodity()
            print(commodity_table)
            db_words="请选择你要兑换的商品: "
            try:
                for i in range(0,100):
                    db_words = db_words+"\r\n\r\n【商品"+str(commodity_table[i][0])+"】\r\n "+str(commodity_table[i][1])+"\r\n需要"+str(commodity_table[i][3])+"点积分\r\n现有库存"+str(commodity_table[i][4])+"。"
            except:
                print("退出商品列表循环")
            db_s.close()
            
            db_words = db_words + "\r\n\r\n选好了吗？回复商品编号哦，例如:兑换商品2"
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>''' 
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")           
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #我的订单
        if rx_msg[0] in ["我的订单","历史订单","订单记录","订单记录","全部订单"]:
            #数据拼接
            db_s=sql.sql_real()
            order_table=db_s.all_order(rx_msg_staff[0])
            if order_table==():
                db_words="您还没有历史订单哦~抓紧兑换礼品!"
            else:
                db_words="您的历史订单如下:"
                try:
                    for i in range(0,100):
                        db_words = db_words+"\r\n\r\n【订单"+str(order_table[i][0])+"】\r\n商品:"+str(order_table[i][2])+"\r\n状态: "+str(order_table[i][4])+"\r\n时间: "+str(order_table[i][5])
                except:
                    print("退出订单循环")
            db_s.close()
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''            
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")   
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #查询某订单
        order_flag1=re.findall("查询订单(.*?)",rx_msg[0])
        order_flag2=re.findall("查找订单(.*?)",rx_msg[0])
        if order_flag1!=[] or order_flag2!=[] :
            order_num=rx_msg[0][4:]
            #非订单编号，进行提醒
            try:
                order_id=(int)(order_num)
            except:
                db_words="请输入正确的订单号哦~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''            
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")   
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            
            db_s=sql.sql_real()
            order_msg=db_s.one_order(order_id)
            print(order_msg)
            if order_msg==None:
                db_words="很抱歉，订单不存在哦~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''       
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")        
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            else:
                staff_msg=db_s.sql_staff(rx_msg_staff[0])
                staff_name=staff_msg[1]
                if order_msg[1]!=staff_name:
                    db_words="对不起，您没有权限查看他人订单哦~"
                    #设置回复内容
                    body_data = '''<xml>
                    <MsgType><![CDATA[text]]></MsgType>
                    <Content><![CDATA['''+db_words+''']]></Content>
                    </xml>''' 
                    #加个log
                    logging.info("用户"+staff_real_name+"："+rx_msg[0])
                    logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")              
                    #加密返回
                    ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                    if( ret!=0 ):
                        print("故障码:",ret)
                        return("故障码",ret)
                    return sMsg
                

            #查找订单成功
            db_words="【订单编号】"+str(order_msg[0])+"\r\n【兑换用户】"+order_msg[1]+"\r\n【商品名称】"+order_msg[2]+"\r\n【订单状态】"+order_msg[4]+"\r\n【订单时间】"+order_msg[5]
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''     
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")          
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #签到
        if rx_msg[0] in ["签到","每日签到","打卡","每日打卡"]:

            db_s=sql.sql_real()

            db_words=db_s.check_in(rx_msg_staff[0])

            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''  
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")             
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg

        
        #我的签到记录
        if rx_msg[0] in ["签到记录","历史签到","签到表","历史签到记录","我的签到"]:
            #数据拼接
            db_s=sql.sql_real()
            check_in_list=db_s.all_check_in(rx_msg_staff[0])
            if check_in_list==():
                db_words="您还没有签到过哦~快来签到吧!"
            else:
                db_words="您的签到记录如下:"
                try:
                    for i in range(0,1000):
                        db_words = db_words+"\r\n\r\n"+check_in_list[i][2]+"-"+check_in_list[i][3]
                except:
                    print("退出签到表循环")
            db_s.close()
            
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''  
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")             
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #建立订单
        commodity_flag1=re.findall("购买商品(.*?)",rx_msg[0])
        commodity_flag2=re.findall("兑换商品(.*?)",rx_msg[0])
        if commodity_flag1!=[] or commodity_flag2!=[]:
            commodity_num=rx_msg[0][4:]
            #非商品编号，进行提醒
            try:
                commodity_id=(int)(commodity_num)
            except:
                db_words="请输入正确的商品编号哦~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")               
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg

            db_s=sql.sql_real()
            staff_msg=db_s.sql_staff(rx_msg_staff[0])
            staff_point=staff_msg[3]
            commodity_msg=db_s.sql_commodity(commodity_id)
            #查找商品失败
            if commodity_msg == None:
                db_words="很抱歉，商品已售罄或商品不存在~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>''' 
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")              
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            #商品存在，拿数据
            staff_name=staff_msg[1]
            commodity_point=commodity_msg[3]
            commodity_rest=commodity_msg[4]
            commodity_name=commodity_msg[1]
            #积分不足失败
            if staff_point < commodity_point :
                db_words="哎呀，x分不足，无法兑换~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''    
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")           
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            #正常购买
            staff_point -= commodity_point
            commodity_rest -= 1
            db_s.updata_commodity_rest(commodity_id,commodity_rest)
            db_s.updata_staff_point(rx_msg_staff[0],staff_point)
            #创建订单
            order_msg=db_s.creat_order(staff_name,commodity_name)
            order_id=order_msg[0]
            order_commodity=order_msg[2]
            db_words="您已成功兑换商品\r\n【"+str(order_commodity)+"】\r\n订单号【"+str(order_id)+"】\r\n已推送给xxxx，还待确认中......."
            mail.send("创建订单","您有新的订单啦："+str(order_id)+"\r\n用户："+staff_name+"\r\n商品："+commodity_name)

            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''       
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")        
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg



        #撤销订单
        if "撤销订单" in rx_msg[0] :
            #数据拼接
            msg=rx_msg[0]
            id=msg[4:]
            try:
                order_id=(int)(id)
            except:
                db_words="请输入正确的订单编号哦~"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''            
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")   
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            
            db_words=""

            #先查个人所有订单
            db_s=sql.sql_real()
            order_table=db_s.all_order(rx_msg_staff[0])
            #个人没有订单或没有想撤销的订单号
            #若用户无订单
            if order_table==None:
                db_words="您还没有订单可撤销哦~抓紧上车兑换礼品！"
                #设置回复内容
                body_data = '''<xml>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA['''+db_words+''']]></Content>
                </xml>'''        
                #加个log
                logging.info("用户"+staff_real_name+"："+rx_msg[0])
                logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")       
                #加密返回
                ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
                if( ret!=0 ):
                    print("故障码:",ret)
                    return("故障码",ret)
                return sMsg
            else:
                try:
                    for i in range(0,1000):
                        #在自己的订单列表中找到想要撤销的订单
                        if order_table[i][0]==order_id:
                            #未完成时可撤销
                            if order_table[i][4] == "已完成":
                                db_words="对不起，你的订单已发货，不可撤销了哦~"
                            else :
                                if order_table[i][4] == "未完成":

                                    cancel_msg=db_s.cancel_order(rx_msg_staff[0],order_id)
                                    if cancel_msg == None:
                                        db_words="哎呀，撤销订单失败了，请找管理员处理~"
                                    else:
                                        staff_name=order_table[i][1]
                                        commodity_name=order_table[i][2]
                                        mail.send("撤销订单","订单被取消："+str(order_id)+"\r\n用户："+staff_name+"\r\n商品："+commodity_name)
                                        db_words="【订单"+str(order_id)+"】"+commodity_name+"\r\n撤销成功!已将信息推送给xxx咯~"
                                    
                                else:
                                    if order_table[i][4] == "已撤销":
                                        db_words="您的订单已经撤销啦~不要重复操作哦~"
                                    else:
                                        db_words="订单状态错误，请上报管理员"
                            break                         
                except:
                    #在自己的订单列表中未找到想要撤销的订单
                    db_words="您不能撤销该订单呀~是不是写错订单号了呢？"

                          
            db_s.close()
            #设置回复内容
            body_data = '''<xml>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA['''+db_words+''']]></Content>
            </xml>'''       
            #加个log
            logging.info("用户"+staff_real_name+"："+rx_msg[0])
            logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")        
            #加密返回
            ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
            if( ret!=0 ):
                print("故障码:",ret)
                return("故障码",ret)
            return sMsg


        #全都没匹配到
        db_s=sql.sql_real()
        db_words=db_s.no_match()

        body_data = '''<xml>
       <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA['''+db_words+''']]></Content>
       </xml>'''
        #加个log
        logging.info("用户"+staff_real_name+"："+rx_msg[0])
        logging.info("回复：\r\n"+db_words[0:40]+"\r\n下略")   
        
        ret,sMsg=sb.EncryptMsg(body_data, nonce,timestamp)
        if( ret!=0 ):
            print("故障码:",ret)
            return("故障码",ret)
        db_s.close()
        return sMsg
    
    

if __name__ == '__main__':
    # 通过url_map可以查看整个flask中的路由信息
    #print (app.url_map)
    # 启动flask程序
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=8889,debug=False)

