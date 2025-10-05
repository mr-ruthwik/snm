# app.py
import re
from flask import Flask, request, render_template, redirect, url_for, flash, session 
from otp import genotp
from cmail import send_mail
from io import BytesIO
from stoken import entoken, dntoken
import mysql.connector
import mimetypes
import flask_excel as excel
from flask import send_file

# Set up the database connection
mydb = mysql.connector.connect(user='root', host='localhost', password='ruthwik', database='snmproject')
app = Flask(__name__)
app.secret_key = 'code@123'
excel.init_excel(app)

''' Welcome '''
@app.route('/')
def home():
    return render_template('welcome.html')

# --- User Authentication Routes ---
''' register '''
@app.route('/userregister',methods=['GET','POST'])
def userregister():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        useremail=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[useremail])
        email_count=cursor.fetchone()
        if email_count[0]==0:
            gotp=genotp()
            userdata={'useremail':useremail,'username':username,'password':password,'gotp':gotp}
            subject='OTP for SNM Application'
            body=f'Use the given otp{gotp}'
            send_mail(to=useremail,body=body,subject=subject)
            flash(f'Otp has sent to given mail {useremail}')
            return redirect(url_for('otpverify',endata=entoken(data=userdata))) 
        elif email_count[0]==1:
            flash(f'{useremail}already existed please login')
            return redirect(url_for('userregister'))
        else:
            flash('something went wrong')
            
    return render_template('register.html')

''' OTP Verification '''
@app.route('/otpverify/<endata>',methods=['GET','POST'])
def otpverify(endata):
    if request.method=="POST":
        user_otp=request.form['otp']
        dndata=dntoken(data=endata)   
        if dndata['gotp']==user_otp:
            cursor=mydb.cursor()
            cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dndata['username'],dndata['useremail'],dndata['password']])
            mydb.commit()
            flash (f'details registered successfully')
            return 'Success'
        else:
            flash('otp was incorect')
    return render_template('otp.html')

''' login '''
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('user'):
        if request.method=='POST':
            login_useremail=request.form['useremail']
            login_password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from users where useremail=%s',[login_useremail])
            email_count=cursor.fetchone()
            if email_count[0]==1:
                cursor.execute('select password from users where useremail=%s',[login_useremail])
                stored_password=cursor.fetchone()
                if stored_password[0]==login_password:
                    session['user']=login_useremail
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was incorrect')
                    return redirect(url_for('userlogin'))
            elif email_count[0]==0:
                flash(f'{login_useremail} not found')
                return redirect(url_for('userlogin'))
        return render_template('userlogin.html')
    else:
        return redirect(url_for('dashboard'))
    
# --- Dashboard and Notes Routes ---
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))

''' Add Notes '''
@app.route('/showaddnotes')
def showaddnotes():
    if session.get('user'):
        return render_template('dashboard.html', viewing_addnotes=True)
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))

''' Add Notes '''
@app.route('/addnotes', methods=['POST'])
def addnotes():
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['note-title']
            description = request.form['note-description']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s', [session.get('user')])
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute('insert into notes(title, decription, added_by) values(%s, %s, %s)', [title, description, user_id[0]])
                mydb.commit()
                flash('notes added successfully')
                return redirect(url_for('viewallnotes'))
            else:
                flash('user id not found')
                return redirect(url_for('addnotes'))
        else:
            flash('could not store data')
            return redirect(url_for('dashboard'))
    else:
        flash('please login first to add notes')
        return redirect(url_for('userlogin'))

''' View all notes '''
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from notes where added_by=(select userid from users where useremail=%s)', [session.get('user')])
        all_notesdata = cursor.fetchall()
        if all_notesdata:
            return render_template('dashboard.html', all_notesdata=all_notesdata, viewing_notes=True)
        else:
            flash('You don\'t have any notes yet.')
            return redirect(url_for('dashboard'))
    else: 
        flash('please login first to view notes')
        return redirect(url_for('userlogin'))

''' View notes '''
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s',[nid])
        note_data = cursor.fetchone()
        if note_data:
            return render_template('viewnotes.html', note_data=note_data)
        else:
            flash('could not fetch note data')
            return redirect(url_for('viewallnotes'))
    else:
        flash('please login first to view notes')
        return redirect(url_for('userlogin'))
    
''' Delete Notes '''
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s and added_by=(select userid from users where useremail=%s)', [nid, session.get('user')])
        mydb.commit()
        flash('note deleted successfully')
        return redirect(url_for('viewallnotes'))
    else:
        flash('please login first to delete notes')
        return redirect(url_for('userlogin'))
    
''' Update Notes '''
@app.route('/updatenotes/<nid>', methods=['GET', 'POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            cursor.execute('update notes set title=%s, decription=%s where nid=%s and added_by=(select userid from users where useremail=%s)', [title, description, nid, session.get('user')])
            mydb.commit()
            flash('note updated successfully')
            return redirect(url_for('viewallnotes'))
        else:
            cursor.execute('select * from notes where nid=%s and added_by=(select userid from users where useremail=%s)', [nid, session.get('user')])
            note_data = cursor.fetchone()
            if note_data:
                return render_template('updatenotes.html', note_data=note_data)
            else:
                flash('could not fetch note data')
                return redirect(url_for('viewallnotes'))
    else:
        flash('please login first to update notes')
        return redirect(url_for('userlogin'))

# --- File Management Routes ---
@app.route('/showuploadfiles')
def showuploadfiles():
    if session.get('user'):
        return render_template('dashboard.html', viewing_uploadfiles=True)
    else:
        flash('please login first')
        return redirect(url_for('userlogin'))

''' Upload File '''
@app.route('/uploadfile', methods=['GET', 'POST'])
def uploadfile():
    if session.get('user'):
        if request.method == 'POST':
            file_data=request.files['file-upload']
            fname=file_data.filename
            f_data=file_data.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute('Select userid from users where useremail=%s',[session.get('user')])
            user_id = cursor.fetchone()
            cursor.execute('insert into filesdata(fname,fda,added_by) values(%s,%s,%s)',[fname,f_data,user_id[0]])
            mydb.commit()   
            cursor.close()
            flash('file uploaded successfully')
        return redirect(url_for('viewallfiles'))
    else:
        flash('please login first to upload files')
        return redirect(url_for('userlogin'))

''' View all files '''
@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select fid,fname,created_at from filesdata where added_by=(select userid from users where useremail=%s)', [session.get('user')])
        all_filesdata = cursor.fetchall()
        if all_filesdata:
            return render_template('dashboard.html', all_filesdata=all_filesdata, viewing_files=True)
        else:
            flash('could not fetch files data')
            return redirect(url_for('dashboard'))
    else:
        flash('please login first to view files')
        return redirect(url_for('userlogin'))

''' Helper function to get MIME type from filename'''
def get_mimetype(filename):
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype is None:
        return 'application/octet-stream'
    return mimetype

''' View a single file '''
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if not session.get('user'):
        flash('Please log in to view files.')
        return redirect(url_for('userlogin'))

    cursor = mydb.cursor(buffered=True)
    cursor.execute('select fname from filesdata where fid=%s and added_by=(select userid from users where useremail=%s)', [fid, session.get('user')])
    file_data = cursor.fetchone()

    if not file_data:
        flash('File not found or you do not have permission to view it.')
        return redirect(url_for('viewallfiles'))

    file_name = file_data[0]
    mimetype = get_mimetype(file_name)
    
    if mimetype.startswith('image/'):
        return render_template('dashboard.html', viewing_image_content=True, file_name=file_name, fid=fid)
    elif mimetype.startswith('text/'):
        cursor.execute('select fda from filesdata where fid=%s', [fid])
        file_content = cursor.fetchone()[0]
        try:
            decoded_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            decoded_content = "File content cannot be displayed as text."
        return render_template('dashboard.html', viewing_file_content=True, file_name=file_name, file_content=decoded_content)
    else:
        return redirect(url_for('downloadfile', fid=fid))

''' Serve raw file data (for images)'''
@app.route('/servefile/<fid>')
def serve_file_data(fid):
    if not session.get('user'):
        return "Unauthorized", 401
    
    cursor = mydb.cursor(buffered=True)
    cursor.execute('select fname, fda from filesdata where fid=%s and added_by=(select userid from users where useremail=%s)', [fid, session.get('user')])
    file_data = cursor.fetchone()
    
    if not file_data:
        return "File not found", 404

    file_name, file_content = file_data
    mimetype = get_mimetype(file_name)
    
    return send_file(BytesIO(file_content), mimetype=mimetype, download_name=file_name)


''' Download a file '''
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select fname, fda from filesdata where fid=%s and added_by=(select userid from users where useremail=%s)', [fid, session.get('user')])
        file_data = cursor.fetchone()
        if file_data:
            file_name, file_content = file_data
            file_stream = BytesIO(file_content)
            return send_file(file_stream, download_name=file_name, as_attachment=True)
        else:
            flash('File not found or you do not have permission to download it.')
            return redirect(url_for('viewallfiles'))
    else:
        flash('Please log in to download files.')
        return redirect(url_for('userlogin'))

''' Delete a file '''
@app.route('/deletefile/<fid>')
def deletefile(fid):
    if session.get('user'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('delete from filesdata where fid=%s and added_by=(select userid from users where useremail=%s)', [fid, session.get('user')])
        mydb.commit()
        flash('File deleted successfully')
        return redirect(url_for('viewallfiles'))
    else:
        flash('Please log in to delete files.')
        return redirect(url_for('userlogin'))

''' Get excel Data '''
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from users where useremail=%s', [session.get('user')])
        user_id = cursor.fetchone()[0]
        cursor.execute('select * from notes where added_by=%s', [user_id])
        notes_data = cursor.fetchall()  
        data=[list(i) for i in notes_data]
        columns_heading=['Notes_Id','Title','Description','Created_at','User_Id']
        data.insert(0, columns_heading)
        return excel.make_response_from_array(data, 'xlsx',file_name='data')
    else:
        flash('please login first to download excel')
        return redirect(url_for('userlogin'))

''' Search Notes and Files'''
@app.route('/search_all', methods=['POST'])
def search_all():
    if session.get('user'):
        sdata = request.form['sdata']
        cursor = mydb.cursor(buffered=True)
        
        # Search for notes
        cursor.execute('select * from notes where (title LIKE %s OR decription LIKE %s) and added_by=(select userid from users where useremail=%s)', [f'%{sdata}%', f'%{sdata}%', session.get('user')])
        notes_results = cursor.fetchall()

        # Search for files
        cursor.execute('select fid, fname, created_at from filesdata where fname LIKE %s and added_by=(select userid from users where useremail=%s)', [f'%{sdata}%', session.get('user')])
        files_results = cursor.fetchall()
        
        if notes_results or files_results:
            return render_template('dashboard.html', notes_results=notes_results, files_results=files_results, search_term=sdata)
        else:
            flash(f'No matching notes or files found for "{sdata}".')
            return redirect(url_for('dashboard'))
    else:
        flash('Please login first to search.')
        return redirect(url_for('userlogin'))

''' Logout '''
@app.route('/userlogout')
def userlogout():
    session.pop('user', None)
    flash('logged out successfully')
    return redirect(url_for('userlogin'))

app.run(debug=True, use_reloader=True)