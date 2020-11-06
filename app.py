from flask import Flask, render_template, redirect, url_for, flash, session, logging, request
#from data import Reviews
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)


#Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mogbo0108'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


#Initialize MySQL
mysql = MySQL(app)

#Reviews = Reviews()

#Route for Index/Home page
@app.route('/')
def index():
    return render_template('home.html')

#Route for About page
@app.route('/about')
def about():
    return render_template('about.html')

#Route for all Reviews
@app.route('/reviews')
def reviews():
    
    #Create Cursor
    cur = mysql.connection.cursor()

    #Get Reviews
    result = cur.execute("SELECT * FROM reviews")

    reviews = cur.fetchall()
            
    if result > 0:
        return render_template('reviews.html', reviews = reviews)
    else:
        msg = 'No Reviews Found'
        return render_template('reviews.html', msg = msg)

#Route for searching
@app.route('/search',  methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search = request.form['search']
        #Create Cursor
        cur = mysql.connection.cursor()

        #Get Reviews
        result = cur.execute("SELECT title FROM reviews WHERE title LIKE %s", [search])

        reviews = cur.fetchall()
                
        if result > 0:
            return render_template('reviews.html', reviews = reviews)
        else:
            msg = 'No Reviews Found'
            return render_template('reviews.html', msg = msg)
    
    


#Route for each Review
@app.route('/review/<string:id>/')
def review(id):
    #Create Cursor
    cur = mysql.connection.cursor()

    #Get Review
    result = cur.execute("SELECT * FROM reviews WHERE id = %s", [id])

    review = cur.fetchone()
    
    return render_template('review.html', review = review)
 
#Registration Form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)", (name,email,username,password))
        
        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('You are now registered and can now log in', 'success')
        
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        #Create Cursor
        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        
        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in',category='success')
                return redirect(url_for('index'))
            else:
                error = 'Password is incorrect'
                return render_template('login.html', error = error)
            #Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error = error)

    return render_template('login.html')

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#User Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create Cursor
    cur = mysql.connection.cursor()

    #Get Reviews
    result = cur.execute("SELECT * FROM reviews")

    reviews = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', reviews = reviews)
    else:
        msg = 'No Reviews Found'
        return render_template('dashboard.html', msg = msg)

#Add Review Form class
class ReviewForm(Form):
    title = StringField('Tile', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

#Add reviews route
@app.route('/add_review', methods=['GET', 'POST'])
@is_logged_in
def add_review():
    form = ReviewForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("INSERT INTO reviews(title, body, author) VALUES(%s,%s,%s)",(title, body, session['username']))    

        #Commit to Db 
        mysql.connection.commit()

        #Close connection
        cur.close()   

        flash('Review Created',category='success')

        return redirect(url_for('dashboard'))

    return render_template('add_review.html', form=form)

#Edit reviews route
@app.route('/edit_review/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_review(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get review by id
    result = cur.execute("SELECT * FROM reviews WHERE id = %s", [id])
    review = cur.fetchone()

    #Get form
    form = ReviewForm(request.form)
    
    #Populate article form fields
    form.title.data = review['title']
    form.body.data = review['body']
    

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create Cursor
        cur = mysql.connection.cursor()

        #Execute
        cur.execute("UPDATE reviews SET title = %s, body = %s WHERE id = %s", (title, body, id))    

        #Commit to Db 
        mysql.connection.commit()

        #Close connection
        cur.close()   

        flash('Review Updated',category='success')

        return redirect(url_for('dashboard'))

    return render_template('edit_review.html', form=form)

#Delete reviews route
@app.route('/delete_review/<string:id>', methods=['POST'])
@is_logged_in
def delete_review(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("DELETE FROM reviews WHERE id = %s", [id])

    #Commit to Db 
    mysql.connection.commit()

    #Close connection
    cur.close() 

    flash('Review Deleted',category='success')

    return redirect(url_for('dashboard'))  

    
    

if __name__ == '__main__':
    app.secret_key = 'mogbo0108'
    app.run(debug=True)