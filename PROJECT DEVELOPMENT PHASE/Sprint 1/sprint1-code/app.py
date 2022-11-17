from turtle import st
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
from dbconn import *
import ibm_db
userid=""

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=21fecfd8-47b7-4937-840d-d791d0218660.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31864;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lvh24264;PWD=gZS5lI5g0AJ3CrRN",'','')

app = Flask(__name__)
app.secret_key = 'ibm'

@app.route('/')
def index():
  return render_template('index.html')


  
@app.route('/login',methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
   
  
    if request.method == 'POST' :
        email = request.form['email']
        password = request.form['password']

        
        sql = "SELECT * FROM credential WHERE email = ? and password = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.bind_param(stmt, 2, password)
        result = ibm_db.execute(stmt)
        print(result)
        account = ibm_db.fetch_row(stmt)
        print(account)
        
        param = "SELECT * FROM credential WHERE email = " + "\'" + email + "\'" + " and password = " + "\'" + password + "\'"
        res = ibm_db.exec_immediate(conn, param)
        dictionary = ibm_db.fetch_assoc(res)


        if account:
            session['loggedin'] = True
            session['email'] = dictionary["EMAIL"]
           
            return redirect('/base')
        else:
            msg = 'Incorrect username / password !'
        
    return render_template('login.html', msg = msg)


@app.route('/base')
def dashboard():
  return render_template('base.html')
