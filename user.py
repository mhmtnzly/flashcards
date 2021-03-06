import psycopg2
import time
import os
import json
from datetime import datetime, timedelta
import hashlib, binascii, os


class User:
    def __init__(self,username,password):
        self.password=password
        self.username=username
        self.connect()
    def control_username(self):
        self.cur.execute("SELECT username from users where username='{}'".format(self.username))
        result=len(self.cur.fetchall())
        if result==0:
            return True
        else:
            return False
    def signup(self):
        hash_pass=self.hash_password(self.password)
        self.cur.execute("insert into users (username, password,user_level,user_time) values ('{}','{}',{},{})".format(self.username,hash_pass,1,0)) 
        self.cur.close()
        self.conn.commit()
    def login(self):
        self.cur.execute("select password from users where username='{}'".format(self.username,self.password))
        result=self.cur.fetchone()
        if result==None:
            return False
        else:
            result_pass=self.verify_password(result[0],self.password)
            if result_pass and len(result)!=0:
                self.user_id_catch()
                return True
            else:
                return False
    def start_time(self):
        self.time_start=time.perf_counter()
    def stop_time(self):
        self.counter_second = time.perf_counter()-self.time_start
        self.time_end=round(self.counter_second)
    def progress(self):
        self.cur.execute("select user_level from users where username='{}'".format(self.username))
        level=self.cur.fetchone()[0]
        return level
    def progress_bar(self):
        return (self.progress()/250)*100
    def save_progress_time(self):
        self.stop_time()
        self.cur.execute("select user_time from users where username='{}'".format(self.username))
        user_time=self.cur.fetchone()[0]
        user_time+=self.time_end
        self.cur.execute("update users set user_time={} where username='{}'".format(user_time,self.username))
        self.conn.commit()
    def time_(self):
        self.cur.execute("select user_time from users where username='{}'".format(self.username))
        user_time=self.cur.fetchone()[0]
        sec=timedelta(seconds=user_time)
        d=datetime(1,1,1)+sec
        total_= str("%d day:%d hour:%d min:%d sec" % (d.day-1, d.hour, d.minute, d.second))
        return total_
    def connect(self):
        self.conn = psycopg2.connect(database = "flashcard",user = "postgres",host = "localhost",password = "1903")
        self.cur = self.conn.cursor()
    def close(self):
        self.conn.close()
    def hash_password(self,p):
        """Hash a password for storing."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', p.encode('utf-8'), 
                                    salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')
    
    def verify_password(self,stored_password, provided_password):
        """Verify a stored password against one provided by user"""
        salt = stored_password[:64]
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                    provided_password.encode('utf-8'), 
                                    salt.encode('ascii'), 
                                    100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password
    def user_id_catch(self):
        self.cur.execute("select user_id from users where username = '{}'".format(self.username))
        self.user_id = self.cur.fetchone()[0]
    def add_level(self,level_name,dutch_word,english_word):
        self.cur.execute("Insert into words(dutch,english,word_level,user_id) values ('{}','{}','{}','{}')".format(dutch_word,english_word,level_name,self.user_id))
        self.conn.commit()
    def combo_box_level(self):
        self.cur.execute("select distinct(word_level) from words where user_id={} order by 1".format(self.user_id))
        self.levels=[i[0] for i in self.cur.fetchall()]
        return self.levels
    def level_catch(self):
        self.cur.execute("select user_level from users where username = '{}'".format(self.username))
        self.user_level = self.cur.fetchone()[0]
        return self.user_level
    def next_level(self,percentage,level_game):
        self.cur.execute("select user_level from users where username='{}'".format(self.username))
        level=self.cur.fetchone()[0]
        try:
            self.success(int(level_game),percentage)
        except ValueError:
            pass
        if level == level_game:
            self.cur.execute("update users set user_level={} where username='{}'".format(level+1,self.username))
            self.conn.commit()
        else:
            return False
    def success(self,level,percentage):
        self.cur.execute("select user_id from users where username='{}'".format(self.username))
        user_id=self.cur.fetchone()[0]
        
        self.cur.execute(f"""SELECT * FROM  (select u.username,sp.current_level,sp.percentage from users u inner join
         success_percentage sp on u.user_id = sp.user_id  order by 3 asc) A WHERE username='{self.username}' AND current_level='{level}'
        """)
        if self.cur.rowcount == 0:
            self.cur.execute(f"""INSERT INTO success_percentage (user_id, current_level, percentage) VALUES ({user_id},'{level}',round({percentage},2)) 
                    """)
        elif self.cur.rowcount > 0:
            self.cur.execute(f"""UPDATE success_percentage SET  percentage = round({percentage},2) WHERE user_id ={user_id} AND current_level='{level}'
                    """)
        self.conn.commit()