import random
import re
import pymysql
import time

class sql_real:
    
    def __init__(self):
        # 打开数据库连接
        #(host="localhost", user="root", password="xxx", database="xxxx")
        self.db = pymysql.connect(host="xx.xx.xxx.xxx",user="xxxxxxx",password="xxxxxxxxxxxxxx",database="xxxxxxxxxxxx",autocommit=True)
        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.db.cursor()


    #返回帮助表
    def all_help(self):
        all_help='''SELECT * FROM help_list ;'''
        self.cursor.execute(all_help)
        data = self.cursor.fetchall()
        return(data)


    #返回员工信息表
    def sql_staff(self,account):
        try:
            sql_staff='''SELECT * FROM staff WHERE staff_account = \'''' + account + '''\' ;'''
            self.cursor.execute(sql_staff)
            data = self.cursor.fetchone()
            if data == None:
                sql_staff='''insert into staff values (\'''' + account + '''\',\'''' + account + '''\',"未知",0)'''          
                self.cursor.execute(sql_staff)
                print("未知新用户"+account+"进入")
                return(None)

        except:
            #sql_staff='''SELECT * FROM staff WHERE staff_account = "test" ;'''
            #self.cursor.execute(sql_staff)
            #data = self.cursor.fetchone()
            #return(data)
            return(None)
        return(data)

    
    #修改员工积分信息      
    def updata_staff_point(self,staff_account,staff_point):
        try:
            updata_point='''update staff set staff_point =\''''+str(staff_point)+'''\' WHERE  staff_account =\''''+staff_account+'''\';'''
            self.cursor.execute(updata_point)
        except:
            return 0
        return 1


    #返回单个商品信息      
    def sql_commodity(self,commodity_id):
        try:
            sql_commodity='''SELECT * FROM commodity WHERE commodity_id = \'''' + str(commodity_id) + '''\' AND commodity_rest != 0 ;'''
            self.cursor.execute(sql_commodity)
            data = self.cursor.fetchone()
        except:
            return(None)
        return(data)

    
    #修改单个商品库存      
    def updata_commodity_rest(self,commodity_id,commodity_rest):
        try:
            updata_commodity_rest='''update commodity set commodity_rest =\''''+str(commodity_rest)+'''\' WHERE  commodity_id =\''''+str(commodity_id)+'''\';'''
            self.cursor.execute(updata_commodity_rest)
        except:
            return 0
        return 1


    #返回所有商品信息表
    def all_commodity(self):
        try:
            all_commodity='''SELECT * FROM commodity WHERE commodity_rest!=0;'''
            self.cursor.execute(all_commodity)
            data = self.cursor.fetchall()
        except:
            return(None)
        return(data)


    #签到
    def check_in(self,account):
        #检查该用户今日签到情况记录
        check_in='''SELECT * FROM check_in WHERE staff_name = ( SELECT staff_name FROM staff WHERE staff_account = \'''' + account + '''\' ) AND check_in_data = \'''' + time.strftime("%Y-%m-%d", time.localtime()) + '''\';'''
        self.cursor.execute(check_in)
        data = self.cursor.fetchone()
        #未查找到签到记录，则新增记录
        if data == None:
            check_in='''insert into check_in(staff_name,check_in_data,check_in_time) values ( (SELECT staff_name FROM staff WHERE staff_account=\'''' + account + '''\') , \'''' + time.strftime("%Y-%m-%d", time.localtime()) + '''\', \'''' + time.strftime("%H:%M:%S", time.localtime()) + '''\') ;'''          
            self.cursor.execute(check_in)
            #拿员工积分信息
            get_point='''SELECT staff_point FROM staff WHERE staff_account = \'''' + account + '''\' ;'''
            self.cursor.execute(get_point)
            staff_point = self.cursor.fetchone()
            point = staff_point[0]+1
            updata_point='''update staff set staff_point =\''''+str(point)+'''\' WHERE  staff_account =\''''+account+'''\';'''
            self.cursor.execute(updata_point)
            #插入失败
            if data != None:
                return("哎呀!签到发生错误了!请联系管理员~")
            else:
                return("打卡成功~新增1个xxxx分~您现有"+str(point)+"点xxx分~")
        return("今天您今日已经打过卡了哟")


    #返回所有个人签到信息
    def all_check_in(self,account):
        try:
            all_check_in='''SELECT * FROM check_in WHERE staff_name = ( SELECT staff_name FROM staff WHERE staff_account = \'''' + account + '''\' ) ;'''
            self.cursor.execute(all_check_in)
            data = self.cursor.fetchall()
        except:
            return(None)
        return(data)


    #返回所有个人订单信息表
    def all_order(self,account):
        try:
            all_order='''SELECT * FROM commodity_order WHERE staff = ( SELECT staff_name FROM staff WHERE staff_account = \'''' + account + '''\' );'''
            self.cursor.execute(all_order)
            data = self.cursor.fetchall()
        except:
            #all_order='''SELECT * FROM commodity_order WHERE staff = "test" ;'''
            #self.cursor.execute(all_order)
            #data = self.cursor.fetchone()
            return(None)
        return(data)


    
    #创建订单并返回订单信息
    def creat_order(self,staff,commodity):
        creat_order='''insert into commodity_order(staff,commodity,commodity_number,order_status,order_time) values (  \'''' + staff + '''\' , \'''' + commodity + '''\' , "1" , "未完成", \'''' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '''\' )  ;'''          
        self.cursor.execute(creat_order)
        search_order='''SELECT * FROM commodity_order where staff = \'''' + staff + '''\' ORDER BY order_id DESC'''
        self.cursor.execute(search_order)
        data = self.cursor.fetchone()
        return(data)

    def cancel_order(self,account,order_id):
        #更新撤销状态
        updata_status='''UPDATE commodity_order SET order_status = "已撤销" WHERE order_id = \'''' + str(order_id) + '''\' ;'''
        self.cursor.execute(updata_status)
        #拿积分信息
        get_point='''SELECT staff_point FROM staff WHERE staff_account = \'''' + account + '''\' ;'''
        self.cursor.execute(get_point)
        staff_point = self.cursor.fetchone()
        point = staff_point[0]
        #拿商品信息
        get_community_msg = '''SELECT * FROM commodity WHERE commodity_name = ( SELECT commodity FROM commodity_order WHERE order_id = \'''' + str(order_id) + '''\' )  ;'''
        self.cursor.execute(get_community_msg)
        commodity_msg = self.cursor.fetchone()
        commodity_point = commodity_msg[3]
        commodity_rest = commodity_msg[4]
        #变动值，用户积分与商品数量
        commodity_rest = commodity_rest+1
        total_point = point+commodity_point
        #恢复用户积分
        updata_staff_point='''update staff set staff_point =\''''+str(total_point)+'''\' WHERE  staff_account =\''''+account+'''\';'''
        self.cursor.execute(updata_staff_point)
        #恢复商品数量
        updata_commodity_point='''update commodity set commodity_rest =\''''+str(commodity_rest)+'''\' WHERE commodity_name = ( SELECT commodity FROM commodity_order WHERE order_id = \'''' + str(order_id) + '''\' )  ;'''
        self.cursor.execute(updata_commodity_point)

        return "0"

    
    #根据订单号返回订单信息
    def one_order(self,order_id):
        try:
            one_order='''SELECT * FROM commodity_order WHERE  order_id = \'''' + str(order_id) + '''\' ;'''
            self.cursor.execute(one_order)
            data = self.cursor.fetchone()
        except:
            return(None)
        return(data)


    #未能匹配成功
    def no_match(self):
        msg_id = random.randint(1, 10)
        msg='''SELECT msg FROM no_match_msg WHERE msg_id = \'''' + str(msg_id) + '''\' ;'''

        self.cursor.execute(msg)
        data = self.cursor.fetchone()
        self.cursor.execute(msg)
        print(data[0])
        return(data[0])
    
    def close(self):
        # 关闭数据库连接
        self.db.close()
        
if __name__=="__main__":
    st=sql_real()
    st.close()