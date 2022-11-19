from flask import Flask, render_template, request, redirect, url_for, session, flash
import credentials
import re
import random
import ibm_db
import string
from datetime import datetime
from flask_mail import Mail, Message


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=21fecfd8-47b7-4937-840d-d791d0218660.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31864;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=lvh24264;PWD=gZS5lI5g0AJ3CrRN",'','')
app = Flask(__name__)
app.secret_key = 'ibm'
app.config['SECRET_KEY'] = 'top-secret'
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = credentials.SENDGRID_API_KEY
app.config['MAIL_DEFAULT_SENDER'] = credentials.MAIL_DEFAULT_SENDER

mail = Mail(app)

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
            lineChart = barChartFetchData(dictionary["USERID"])
            barChart = lineChartFetchData(str(session['userid']))
            categoryNames = getCategoryNames()
            return render_template('base.html',lineChart=lineChart,barChart=barChart,categoryNames=categoryNames,size = len(barChart))
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
            sendMail('Send Grid Registration Successful!!','Registration Successful','You have successfully created an account in Personal Expense Tracker!',email)
        return render_template('login.html', response = response)
    else:
        return render_template('register.html')  

@app.route('/base')
def dashboard():
  lineChart = barChartFetchData(str(session['userid']))
  barChart = lineChartFetchData(str(session['userid']))
  categoryNames = getCategoryNames()
  return render_template('base.html',lineChart=lineChart,barChart=barChart,categoryNames=categoryNames,size = len(barChart))

@app.route('/add-category',methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        categoryName = request.form['category']
        limit = float(request.form['range'])
        description = request.form['description']
        sql = "INSERT INTO category (categoryname, limit,description,userid,balance) VALUES (?, ?, ?,?,?)"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, categoryName)
        ibm_db.bind_param(stmt, 2, limit)
        ibm_db.bind_param(stmt, 3, description)
        ibm_db.bind_param(stmt, 4, str(session['userid']))
        ibm_db.bind_param(stmt, 5, 0.0  )
        ibm_db.execute(stmt)
        insertBudget(limit,categoryName)
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
    categories = overallCategory(str(session['userid']))
    updateBudget(category,amount,"increment")
    return render_template('add-expense.html',categories=categories)
  else:
    categories = overallCategory(str(session['userid']))
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
  defaultCategories=["Food","Entertainment","Business","Rent","EMI","Other"]
  for i in defaultCategories:
    sql = "INSERT INTO category (USERID,LIMIT,DESCRIPTION,BALANCE,CATEGORYNAME) VALUES(?,?,?,?,?)"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,userid)
    ibm_db.bind_param(stmt,2,5000.0)
    ibm_db.bind_param(stmt,3,"")
    ibm_db.bind_param(stmt,4,0.0)
    ibm_db.bind_param(stmt,5,i)
    ibm_db.execute(stmt)
  for i in defaultCategories:
    sql = "INSERT INTO budgeting (USERID,CATEGORYNAME,LIMIT,BALANCE) VALUES(?,?,?,?)"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,userid)
    ibm_db.bind_param(stmt,2,i)
    ibm_db.bind_param(stmt,3,5000.0)
    ibm_db.bind_param(stmt,4,0.0)
    ibm_db.execute(stmt)  
  #initialize budgeting  


@app.route("/edit-limit")
def editLimit():
  if request.method == 'POST' :
   sql = "UPDATE category SET LIMIT=?, DESCRIPTION=? WHERE USERID=? AND CATEGORYNAME=?"
   stmt = ibm_db.prepare(conn, sql)
   ibm_db.bind_param(stmt, 1, request.form['range'])
   ibm_db.bind_param(stmt, 2, request.form['description'])
   ibm_db.bind_param(stmt, 3, str(session['userid']))
   ibm_db.bind_param(stmt, 4, request.form['category'])
   ibm_db.execute(stmt)
   categories=getAllCategoryDetails()
  else:
    categories=getAllCategoryDetails()
  return render_template('edit-limit.html',categories=categories)

def getAllCategoryDetails():
  sql = "SELECT * from category where userid = ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,str(session['userid']))
  ibm_db.execute(stmt)        
  category = ibm_db.fetch_both(stmt)
  categoryList = []
  while category != False:
    categoryList.append(category)
    category = ibm_db.fetch_both(stmt)
  return categoryList

  

@app.route("/view-history")
def viewHistory():
    res = allExpenses(str(session['userid']))
    return render_template('view-history.html' ,expense = res)


def overallCategory(userid):
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
  categories = overallCategory(str(session['userid']))  
  expenses = allExpenses(str(session['userid']))
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
    ibm_db.execute(stmt)
    userProfile = ibm_db.fetch_assoc(stmt)
    return render_template('view-profile.html',userProfile=userProfile)

@app.route('/report')
def report():
  lineChart = barChartFetchData(str(session['userid']))
  barChart = lineChartFetchData(str(session['userid']))
  categoryNames = getCategoryNames()
  return render_template('report.html',lineChart=lineChart,barChart=barChart,categoryNames=categoryNames,size = len(barChart))

@app.route('/sign-out')
def logout():
   session.pop('loggedin', None)
   session.pop('userid', None)
   session.pop('email', None)
   return render_template('logout.html')

#  all db functions
def allExpenses(userid):
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


def barChartFetchData(userid):
  epenseMonthwise = {'1':0.0,'2':0.0,'3':0.0,'4':0.0,'5':0.0,'6':0.0,'7':0.0,'8':0.0,'9':0.0,'10':0.0,'11':0.0,'12':0.0}
  expenses = allExpenses(userid)
  for expense in expenses:
    date = expense.get('SPENTONDATE')
    datemonth = datetime.strptime(date, "%d-%m-%Y")
    epenseMonthwise[str(datemonth.month)] = epenseMonthwise[str(datemonth.month)]+expense.get('AMOUNT')
  return list(epenseMonthwise.values())


def categoryChart(userid):
  epenseMonthwise = {'1':0.0,'2':0.0,'3':0.0,'4':0.0,'5':0.0,'6':0.0,'7':0.0,'8':0.0,'9':0.0,'10':0.0,'11':0.0,'12':0.0}
  expenses = allExpenses(userid)
  for expense in expenses:
    date = expense.get('SPENTONDATE')
    datemonth = datetime.strptime(date, "%d-%m-%Y")
    epenseMonthwise[str(datemonth.month)] = epenseMonthwise[str(datemonth.month)]+expense.get('AMOUNT')
  return list(epenseMonthwise.values())

def getExpenseForCategory():
  sql="SELECT DISTINCT CATEGORY FROM expense WHERE USERID=? "
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,str(session['userid']))
  ibm_db.execute(stmt)
  result = ibm_db.fetch_assoc(stmt)

def createId(pre):
  return pre+''.join([random.choice(string.ascii_letters+ string.digits) for n in range(32)])

def getCategoryNames():
  sql="SELECT DISTINCT CATEGORY FROM expense WHERE USERID=? "
  statement = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(statement,1,str(session['userid']))
  ibm_db.execute(statement)
  category = ibm_db.fetch_assoc(statement)
  categoryNames = []
  while category != False:
    categoryNames.append(category.get('CATEGORY'))
    category = ibm_db.fetch_both(statement)
  return categoryNames

def lineChartFetchData(userid):
  categoryData = []
  categories = getCategoryNames()
  expenses = allExpenses(userid)
  for category in categories:
    epenseMonthwise = {'1':0.0,'2':0.0,'3':0.0,'4':0.0,'5':0.0,'6':0.0,'7':0.0,'8':0.0,'9':0.0,'10':0.0,'11':0.0,'12':0.0}
    for expense in expenses:
      if(expense.get('CATEGORY')==category):
        date = expense.get('SPENTONDATE')
        datemonth = datetime.strptime(date, "%d-%m-%Y")
        epenseMonthwise[str(datemonth.month)] = epenseMonthwise[str(datemonth.month)]+expense.get('AMOUNT')
    categoryData.append(list(epenseMonthwise.values()))
  return categoryData

def sendMail(body,htmlHead,message,mailId):
  recipient = []
  recipient.append(mailId)
  msg = Message('Twilio SendGrid', recipients=recipient)
  msg.body = (body)
  msg.html = ('<h1>'+htmlHead+'</h1><p>'+message+'</p>')
  mail.send(msg)
  flash(f'A test message was sent to {recipient}.')

def insertBudget(limit,categoryName):
  sql = "INSERT INTO budgeting (userid,limit, balance,categoryName) VALUES (?,?, ?, ?)"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, str(session['userid']))
  ibm_db.bind_param(stmt, 2, limit)
  ibm_db.bind_param(stmt, 3, 0.0)
  ibm_db.bind_param(stmt, 4, categoryName)
  ibm_db.execute(stmt)    

def updateBudget(categoryName,amount,function):
  balance = getCurrentBalance(categoryName)
  if(function == 'increment'):
    currBalance = balance.get('BALANCE')+float(amount)
  elif(function == 'decrement'):
    currBalance = abs(balance.get('BALANCE')- float(amount))


  if(balance.get('LIMIT')<currBalance):
    sendMail('Hey there! limit alert .... The Category: '+categoryName+' has been crossed!',' Category: '+categoryName+' limit has exceeded','The limit set on '+categoryName+' has been reached. Kindly check and keep track of your expenses, do exercise caution and avoid spending more.',str(session['email']))
  sql = "UPDATE budgeting SET balance = ? WHERE userid=? and categoryname = ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1,currBalance)
  ibm_db.bind_param(stmt, 2, str(session['userid']))
  ibm_db.bind_param(stmt, 3, categoryName)
  ibm_db.execute(stmt)

def getCurrentBalance(categoryName):
  sql = "SELECT balance,limit from budgeting WHERE userid = ? and categoryname = ?" 
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, str(session['userid']))
  ibm_db.bind_param(stmt, 2, categoryName)
  ibm_db.execute(stmt)
  balance = ibm_db.fetch_assoc(stmt)  
  return balance


def editExpense(request):
   currentBalance = getExpenseBalance(request.form['expenseid'])
   updateBudget(request.form['category'],currentBalance,"decrement")
   updateBudget(request.form['category'],float(request.form['amount']),"increment")
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
  updateBudget(request.form['category'],request.form['amount'],"decrement")
  sql="DELETE FROM expense WHERE EXPENSEID = ?;"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt,1,expenseid)
  ibm_db.execute(stmt)

def getExpenseBalance(expenseid):
  sql = "Select amount from expense where expenseid= ?"
  stmt = ibm_db.prepare(conn, sql)
  ibm_db.bind_param(stmt, 1, expenseid)
  ibm_db.execute(stmt)
  amount = ibm_db.fetch_assoc(stmt)
  return amount.get('AMOUNT')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  
