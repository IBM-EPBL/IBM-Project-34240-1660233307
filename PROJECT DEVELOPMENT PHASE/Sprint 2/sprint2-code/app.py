from turtle import st
from flask import Flask, render_template, request, redirect, url_for, session
from markupsafe import escape
# import ibm_db_dbi
import re
import random
import ibm_db
import string
from datetime import datetime
# userid=""

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=21fecfd8-47b7-4937-840d-d791d0218660.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31864;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lvh24264;PWD=gZS5lI5g0AJ3CrRN",'','')
# ibm_db_conn = ibm_db.connect(conn,'','')
app = Flask(__name__)
app.secret_key = 'ibm'

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/login',methods =['GET', 'POST'])
def login():
    # global userid
    msg = ''

    if request.method == 'POST' :
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM credential WHERE email = ? and password = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.bind_param(stmt, 2, password)
        result = ibm_db.execute(stmt)
        account = ibm_db.fetch_row(stmt)
        
        param = "SELECT * FROM credential WHERE email = " + "\'" + email + "\'" + " and password = " + "\'" + password + "\'"
        res = ibm_db.exec_immediate(conn, param)
        dictionary = ibm_db.fetch_assoc(res)


        if account:
            session['loggedin'] = True
            session['email'] = dictionary["EMAIL"]
            session['userid']=dictionary["USERID"]
            session['username']=dictionary["USERNAME"]
            sql = "SELECT * FROM user WHERE email = ? "
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, email)
            result = ibm_db.execute(stmt)
            account = ibm_db.fetch_row(stmt)
            return redirect('/base')
        else:
            msg = 'Incorrect username / password !'
        
    return render_template('login.html', msg = msg)

@app.route('/register', methods =['GET', 'POST'])
def register():
    response = ''
    if request.method == 'POST' :
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM credential WHERE email = ?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_row(stmt)

        # param = "SELECT * FROM credential WHERE email = " + "\'" + name + "\'"
        # res = ibm_db.exec_immediate(conn, param)
        # dictionary = ibm_db.fetch_assoc(res)
        # while dictionary != False:
        #     dictionary = ibm_db.fetch_assoc(res)
  
        if account:
            response = 'Username already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            response = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', name):
            response = 'name must contain only characters and numbers !'
        else:
            sql2 = "INSERT INTO credential (username, email,password,userid) VALUES (?, ?, ?,?)"
            stmt2 = ibm_db.prepare(conn, sql2)
            ibm_db.bind_param(stmt2, 1, name)
            ibm_db.bind_param(stmt2, 2, email)
            ibm_db.bind_param(stmt2, 3, password)
            currentid=createId('')
            ibm_db.bind_param(stmt2,4,currentid)
            ibm_db.execute(stmt2)
            initializeUser(currentid,name,email)
            response = 'You have successfully registered !'
        return render_template('login.html', response = response)
    else:
        return render_template('register.html')  

@app.route('/base')
def dashboard():
  print(datetime.now().month)
  return render_template('base.html')

@app.route('/add-category',methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        categoryName = request.form['category']
        limit = float(request.form['range'])
        print(limit)
        description = request.form['description']
        sql = "INSERT INTO category (categoryname, limit,description,userid,balance) VALUES (?, ?, ?,?,?)"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, categoryName)
        ibm_db.bind_param(stmt, 2, limit)
        ibm_db.bind_param(stmt, 3, description)
        ibm_db.bind_param(stmt, 4, str(session['userid']))
        ibm_db.bind_param(stmt, 5, 0.0)
        ibm_db.execute(stmt)
        return render_template('add-category.html')
    else:
        return render_template('add-category.html')
#change
@app.route('/add-expense',methods=['GET', 'POST'])
def addExpense():
  if request.method == 'POST' :
    description= request.form['description']
    date = request.form['date']
    time = request.form['time']
    amount = request.form['amount']
    category = request.form['category']
    paymode= request.form['modeofpayment']
    sql = "INSERT INTO expense (category, amount,modeofpayment,description,userid,expenseid,spentondate,addondate) VALUES (?, ?, ?,?,?,?,?,?)"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, category)
    ibm_db.bind_param(stmt, 2, amount)
    ibm_db.bind_param(stmt, 3, paymode)
    ibm_db.bind_param(stmt, 4, description)
    ibm_db.bind_param(stmt,5,str(session['userid']))
    ibm_db.bind_param(stmt,6,createId('EXP'))
    ibm_db.bind_param(stmt,7,date)
    ibm_db.bind_param(stmt,8,datetime.now())

    ibm_db.execute(stmt)
    return render_template('add-expense.html')
  else:
    categories = getCategories(str(session['userid']))
    print(categories)
    return render_template('add-expense.html',categories=categories)



def initializeUser(currrentid,name,mail):
  userid=currrentid
  username=name
  email=mail
  phoneno=""
  currentsavings=0
  sql = "INSERT INTO user (userid,username, email,phoneno,walletid,currentsavings,country,currency,targetdesc) VALUES (?,?, ?, ?,?,?,?,?,?)"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, userid)
  ibm_db.bind_param(stmt, 2, username)
  ibm_db.bind_param(stmt, 3, email)
  ibm_db.bind_param(stmt, 4, phoneno)
  ibm_db.bind_param(stmt,5,createId('WID'))
  ibm_db.bind_param(stmt,6,currentsavings)
  ibm_db.bind_param(stmt,7,"INDIA")
  ibm_db.bind_param(stmt,8,"RUPEES")
  ibm_db.bind_param(stmt,9,"")
  ibm_db.execute(stmt)    

@app.route("/view-history")
def viewHistory():
    res = getExpenseData(str(session['userid']))
    print(type(res))
    print(res)
    return render_template('view-history.html' ,expense = res)


def getCategories(userid):
    sql = "SELECT * from category where userid = ?"
    statement = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(statement,1,userid)
    ibm_db.execute(statement)        
    category = ibm_db.fetch_both(statement)
    categoryList = []
    while category != False:
        categoryList.append(category)
        category = ibm_db.fetch_both(statement)
    return categoryList


#change
@app.route("/manage-expense",methods=['GET', 'POST'])
def manageExpense():
  if request.method=='POST' and request.form['action']=='edit':
    editExpense(request)
  elif request.method=='POST' and request.form['action']=='delete':
    deleteExpense(request.form['expenseid'])  
  categories = getCategories(str(session['userid']))  
  expenses = getExpenseData(str(session['userid']))
  print("-----------------//////////////",expenses)
  return render_template('manage-expense.html',expense=expenses,categories=categories)

#change
@app.route("/view-profile",methods=['GET', 'POST'])
def viewProfile():
  if request.method == 'POST':
    print()
  else:
    sql = "SELECT * from user where userid = ?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,str(session['userid']))
    print(str(session['userid']))
    ibm_db.execute(stmt)
    userProfile = ibm_db.fetch_assoc(stmt)
    print(userProfile)
    return render_template('view-profile.html',userProfile=userProfile)


@app.route('/sign-out')
def logout():
   session.pop('loggedin', None)
   session.pop('userid', None)
   session.pop('email', None)
   return render_template('index.html')

#  all db functions
def getExpenseData(userid):
        sql = "SELECT * from expense where userid = ? ORDER BY SPENTONDATE desc"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,userid)
        ibm_db.execute(stmt)        
        expense = ibm_db.fetch_both(stmt)
        expensesList = []
        while expense != False:
            expense['SPENTONDATE'] = expense.get('SPENTONDATE').strftime("%d-%m-%Y")
            expense['ADDONDATE'] = expense.get('ADDONDATE').strftime("%d-%m-%Y")
            expensesList.append(expense)
            expense = ibm_db.fetch_both(stmt)
        return expensesList

#changed
def editExpense(request):
   datetimeans = datetime.strptime(request.form['date'], '%d-%m-%Y')
   sql = "UPDATE expense SET CATEGORY=?, AMOUNT=?, MODEOFPAYMENT=?, DESCRIPTION=?,SPENTONDATE=? WHERE EXPENSEID=?"
   stmt = ibm_db.prepare(conn, sql)
   ibm_db.bind_param(stmt, 1, request.form['category'])
   ibm_db.bind_param(stmt, 2, request.form['amount'])
   ibm_db.bind_param(stmt, 3, request.form['modeofpayment'])
   ibm_db.bind_param(stmt, 5, datetimeans)
   ibm_db.bind_param(stmt, 4, request.form['description'])
   ibm_db.bind_param(stmt, 6, request.form['expenseid'])
   ibm_db.execute(stmt)

def deleteExpense(expenseid):
  sql="DELETE FROM expense WHERE EXPENSEID = ?;"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,expenseid)
  ibm_db.execute(stmt)


def createId(pre):
  return pre+''.join([random.choice(string.ascii_letters+ string.digits) for n in range(32)])