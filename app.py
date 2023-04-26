from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import os
from datetime import datetime

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
 
if (local_server) :
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else :
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    email = db.Column(db.String(20),nullable=False)
    phone_no = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable = True)

class Posts(db.Model):
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),nullable=False)
    subtitle = db.Column(db.String(80),nullable=True)
    content = db.Column(db.String(300),nullable=False)
    date = db.Column(db.String(12), nullable = True)
    slug = db.Column(db.String(21), nullable = False)
    bg_image_link = db.Column(db.String(80), nullable = True)

@app.route('/')
def home() :
    return redirect('/page=0')


@app.route('/page=<int:page>')
def pagination(page) :
    range = int(params['no-of-posts'])
    count = page * range
    posts = Posts.query.all()
    size = len(posts)
    posts = Posts.query.order_by(Posts.date.desc()).limit(range).offset(count).all()
    return render_template('index.html',params = params,posts = posts,page = page,range = range,size = size)


@app.route('/post/<string:post_slug>', methods = ["GET"])
def post(post_slug) :
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html',params = params,post = post)


@app.route('/edit/<string:post_id>', methods=["GET","POST"])
def edit(post_id) :
    if ('user' in session and session['user'] == params['admin-user'] ):
        if request.method == 'POST' :
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            bg_image_link = request.form.get('bg_img_link')

            if post_id == '0' :
                post_entry = Posts(title = title, subtitle = tagline, content = content, date = datetime.now(), slug = slug,bg_image_link = bg_image_link)
                db.session.add(post_entry)
                db.session.commit()
            else :
                post = Posts.query.filter_by(post_id = post_id).first()
                post.title = title
                post.subtitle = tagline
                post.slug = slug
                post.content = content
                post.date = datetime.now()
                post.bg_image_link = bg_image_link
                db.session.commit()
                return redirect('/edit/' + post_id);
        post = Posts.query.filter_by(post_id = post_id).first()
        return render_template('edit.html',params = params,post = post,post_id = post_id)


@app.route('/uploader', methods=["GET","POST"])
def uploader():
    if ('user' in session and session['user'] == params['admin-user'] ):
        if request.method == 'POST' :
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"


@app.route('/delete/<string:post_id>') 
def delete(post_id):
    if ('user' in session and session['user'] == params['admin-user'] ):
        post = Posts.query.filter_by(post_id = post_id).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard') 


@app.route('/contact', methods=["GET","POST"])
def contact() :
    if request.method == 'POST' :
        # add entry to database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name = name, email = email, phone_no = phone, message = message, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + "My Email :" + email + "\n" + "My Phone no :" + phone)
    return render_template('contact.html',params = params)


@app.route('/dashboard', methods=["GET","POST"])
def dashboard() :
    if ('user' in session and session['user'] == params['admin-user'] ):
        posts = Posts.query.all()
        return render_template('dashboard.html',posts = posts,params = params)

    if request.method == 'POST' :
        username = request.form.get('uname')
        userpass = request.form.get('pass')

        if(username == params['admin-user'] and userpass == params['admin-password']) :
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',posts = posts,params = params)

    return render_template('login.html',params = params)


@app.route('/logout')
def logout() :
    if ('user' in session and session['user'] == params['admin-user'] ):
        session.pop('user')
    return redirect('/dashboard')


@app.route('/about')
def about() :
    return render_template('about.html',params = params)


app.run(debug=True);