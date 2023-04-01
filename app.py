from flask import Flask, render_template, request, redirect, url_for, session,jsonify, Response, stream_with_context
import os
#import streamlink 
from bs4 import BeautifulSoup
import requests
import uuid
#import boto3
from werkzeug.datastructures import Headers
import filetype
from flask_mysqldb import MySQL
import MySQLdb.cursors
import uuid
import re
import os,json,hashlib
from cryptography.fernet import Fernet
#01/04/2023_last_1
app = Flask(__name__)
#app.secret_key = 'your secret key'
file= open("config.json",)
config=json.load(file)
file.close()
private_key=config["Server_Config"]["Private_Key"]
if private_key=="":
        private_key = bcrypt.gensalt(50)
        file= open("config.json")
        config=json.load(file)
        file.close()
        config["Server_Config"]["Private_Key"]=private_key.decode('utf-8')
        write_file=open("config.json","w")
        write_file.write(json.dumps(config))
        write_file.close()
else:
    private_key=private_key
app.config['MYSQL_HOST'] = config["Mysql_Config"]["HOST"]
app.config['MYSQL_USER'] = config["Mysql_Config"]["USER"]
app.config['MYSQL_PASSWORD'] = config["Mysql_Config"]["PASSWORD"]
app.config['MYSQL_DB'] = config["Mysql_Config"]["DATABASE_NAME"]
app.config['UPLOAD_FOLDER'] = config["Server_Config"]["UPLOAD_FOLDER"]
app.config['MAX_CONTENT_LENGTH'] = config["Server_Config"]["MAX_CONTENT_LENGTH"]
ALLOWED_EXTENSIONS = set(['ts','m3u8', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

 
mysql = MySQL(app)

def link_mp4_bayfiles(bayfiles_url):
    req = requests.get( bayfiles_url)
    soup = BeautifulSoup(req.text, "html.parser")
    
    for url in soup.findAll('a', attrs={'href': re.compile("^https://cdn-")}):
        return (url.get('href'))
    return False       

def link_mp4_openload(openload_url):
    req = requests.get(openload_url)
    soup = BeautifulSoup(req.text, "html.parser")
    
    for url in soup.findAll('a', attrs={'href': re.compile("^https://cdn-")}):
        return (url.get('href'))
    return False       



def is_url(url):
    return bool(re.match(
        r"(https?|ftp)://" # protocol
        r"(\w+(\-\w+)*\.)?" # host (optional)
        r"((\w+(\-\w+)*)\.(\w+))" # domain
        r"(\.\w+)*" # top-level domain (optional, can have > 1)
        r"([\w\-\._\~/]*)*(?<!\.)" # path, params, anchors, etc. (optional)
    , url))


def check_api_available(api_key):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql="SELECT * FROM accounts WHERE api_key=\"{}\"".format(api_key)
    cursor.execute(sql)
    api_result=cursor.fetchone()
    if api_result:
        print(api_result)
        return True
    return False    

def check_video_code_exits(video_code):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql="SELECT * FROM video_infomations WHERE video_code=\"{}\"".format(video_code)
    cursor.execute(sql)
    data = cursor.fetchone()    
    print(data)
    if data:
        return True
    return False



def add_movie_infomation(video_title,video_code,video_torrent_url,video_tags,actress,video_image,category,country,release_date,trailer_link):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql="INSERT INTO video_infomations(video_title,video_code,video_torrent_url,video_tags,actress,video_image,status,category,country,release_date,trailer_link) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    data = (video_title,video_code,video_torrent_url,video_tags,actress,video_image,1,category,country,release_date,trailer_link)
    print(data)
    #try:
   
    cursor.execute(sql,data)
    print(cursor.rowcount)
    mysql.connection.commit()
   
    #    return False
 
    #print(cursor.rowcount,"Video CODE %s is add to Database"%video_info["video_code"])
    
    return True



def Stream_MP4_URL(url):
    
    media_stream = requests.Session()
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
    media_stream=media_stream.get(url,headers=headers,stream=True)
    print(media_stream.headers)
    content_type=media_stream.headers["Content-Type"]
    print(content_type)
    full_content = media_stream.headers['Content-Length']
    headers = Headers()
    status = 200
    range_header = request.headers.get('Range', None)
    print(range_header)
    if range_header!=None:
        byte_start, byte_end, length = get_byte_range(range_header)
        if byte_end:
            status = 206
            headers_stream = {f"Content-Range": f"bytes={byte_start}-{byte_end}"}
            print(headers_stream)
            media_stream = requests.get(url,stream=True, headers=headers_stream)
            print(media_stream.headers)
            end = byte_start + length - 1
            headers.add('Content-Range', f'bytes {byte_start}-{end}/{full_content}')
            headers.add('Accept-Ranges', 'bytes')
            headers.add('Content-Transfer-Encoding', 'binary')
            headers.add('Connection', 'Keep-Alive')
            headers.add('Content-Type', content_type)
            if byte_end == 1:
                headers.add('Content-Length', '1')
            else:
                headers.add('Content-Length', media_stream.headers['Content-Length'])

            response = Response(
                stream_with_context(media_stream.iter_content(chunk_size=124)),
                mimetype=content_type,
                content_type=content_type,
                headers=headers,
                status=status,
                direct_passthrough=True
            )
            return response

    headers.add('Content-Type', content_type)
    headers.add('Content-Length', media_stream.headers['Content-Length'])
    print(media_stream)
    response = Response(
        stream_with_context(media_stream.iter_content(chunk_size=124)),
        mimetype=content_type,
        content_type=content_type,
        headers=headers,
        status=status
        )
    return response

def Stream_Mp4_AWS(key):
    storage = boto3.client('s3')
    media_stream = storage.get_object(Bucket=bucket_name, Key=key)
    full_content = media_stream['ContentLength']
    headers = Headers()
    status = 200
    range_header = request.headers.get('Range', None)
    if range_header:
        byte_start, byte_end, length = get_byte_range(range_header)
        if byte_end:
            status = 206
            media_stream = storage.get_object(Bucket=BUCKET_NAME, Key=key, Range=f'bytes={byte_start}-{byte_end}')
            end = byte_start + length - 1
            headers.add('Content-Range', f'bytes {byte_start}-{end}/{full_content}')
            headers.add('Accept-Ranges', 'bytes')
            headers.add('Content-Transfer-Encoding', 'binary')
            headers.add('Connection', 'Keep-Alive')
            headers.add('Content-Type', content_type)
            if byte_end == 1:
                headers.add('Content-Length', '1')
            else:
                headers.add('Content-Length', media_stream['ContentLength'])

            response = Response(
                stream_with_context(media_stream['Body'].iter_chunks()),
                mimetype=content_type,
                content_type=content_type,
                headers=headers,
                status=status,
                direct_passthrough=True
            )
            return response

    headers.add('Content-Type', content_type)
    headers.add('Content-Length', media_stream['ContentLength'])
    response = Response(
        stream_with_context(media_stream['Body'].iter_chunks()),
        mimetype=content_type,
        content_type=content_type,
        headers=headers,
        status=status
        )
    return response



def encrypt_string(source_string):
    return hashlib.sha512(source_string.encode())


def generate_random_password(length):
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits
    symbols = string.punctuation

    all = lower + upper + num + symbols
    temp = random.sample(all,length)

    return  "".join(temp)

# Flask maps HTTP requests to Python functions.
# The process of mapping URLs to functions is called routing.
@app.route('/', methods=['GET'])
def home():
    return "<h1>MONAV API</h1><p>API for Lazyer Tool</p>"



@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        user = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE user = % s AND password = % s', (user, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = str(request.form['username'])
        password = str(request.form['password'])
        password=encrypt_string(password)
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)    

@app.route('/api/v1/create_api', methods =['GET', 'POST'])
def create_api():

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        user = str(request.form['username'])
        password = str(request.form['password'])
        password=encrypt_string(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE user = % s AND password = % s', (user, password, ))
        account = cursor.fetchone()
        if account:
            api_key=uuid.uuid4()
            sql="UPDATE accounts SET api=\"{}\",IP=\"{}\" WHERE user=\"{}\"".format(api_key,request.remote_addr,user)
            cursor.execute(sql)
            mysql.connect.commit()
            if cursor.rowcount!=0:
                return jsonify(status=True,api_key=api_key)
    return jsonify(status=False)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))
 

# A route to return all of available entries i our catalog.
@app.route('/api/v1/current_status', methods=['GET'])
def current_status():
    return jsonify(status="OK",current_status="ON")

@app.route("/api/v1/test_connect")
def test_connect():
    return jsonify(status="OK")
#Check token is available
@app.route("/api/v1/check_available")
def check_available():
    api_key=str(request.form("api_key"))
    IP=request.remote_addr
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql="SELECT * from accounts where api=\"{}\",IP=\"{}\" ".format(api_key,IP)
    cursor.execute(sql)
    result=cursor.fetchone()
    if result:
        return jsonify(status="OK")
    return jsonify(status="Fail")


@app.route("/api/v1/link_account") 
def link_account():
    username_device=str(request.form["username_device"])
    password_device=str(request.form["password_device"])
    api_monsmarttools=str(request.form["api_key"])
    password_device=encrypt_string(password_device)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM auto_lights WHERE username = % s AND password = % s', (username_device, password_device, ))
    account_device = cursor.fetchone()
    if account_device:
        sql="SELECT * FROM accounts WHERE api=\"{}\"".format(api_monsmarttools)
        cursor.execute(sql)
        api_result=cursor.fetchone()
        if api_result:
            sql="INSERT INTO autolight_items (user_id,autolight_id) VALUES ({},{})".format(account_device["id"],api_result["id"])
            cursor.execute(sql)
            mysql.connect.commit()
            if cursor.rowcount!=0:
                return jsonify(status="OK",code=200)
    return jsonify(status="Fail",code=200)

@app.route("/api/v1/al/login",methods=["POST"])
def login_al():
    #if request.method == 'POST':
        user = str(request.form.get('username_device'))
        print(user)
        password = str(request.form.get('password_device'))
        #password=encrypt_string(password)
        print(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM auto_lights WHERE username = % s AND password = % s', (user, password, ))
        account = cursor.fetchone()
        print(account)
        if account:
            temp_token=uuid.uuid4()
            sql="UPDATE auto_lights SET temp_token=\"{}\",IP=\"{}\" WHERE username=\"{}\"".format(temp_token,request.remote_addr,user)
            print(sql)
            cursor.execute(sql)
            mysql.connection.commit()
            if cursor.rowcount!=0:
                return jsonify(status="OK",temp_token=temp_token)
        return jsonify(status="Fail")
    

    



@app.route("/api/v1/al/check_status")
def al_check_status():
    #id=int(request.form("id"))
    IP=request.remote_addr
    api_key=str(request.form("api_key"))
    sql="SELECT * from auto_light where api_key=\"{}\"".format(api_key)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(sql)
    device_result =cursor.fetchone()
    #if device_result:
        
   # if id_result&api_result:



@app.route("/api/v1/al/current_status",methods=["POST"])
def al_current_status():
    if  request.method == 'POST':
        #id=int(request.form("id"))
        IP=request.remote_addr
        temp_token=str(request.form["temp_token"])
        status=int(request.form["status"])
        sql="SELECT * from auto_lights where temp_token=\"{}\"".format(temp_token)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        device_result =cursor.fetchone()
        print(device_result)
        if device_result:
            sql="UPDATE auto_lights SET status=\"{}\",lastUpdate =(now()) WHERE temp_token=\"{}\"".format(status,temp_token) #update
            cursor.execute(sql)
            mysql.connection.commit()
            print(cursor.rowcount)
            if cursor.rowcount!=0:
                return jsonify(status="OK")
        return jsonify(status="Fail")
    
        
        
   
        
        

    
    
@app.route("/api/v1/get/al")
def get_info_aut_light():
    api_key=request.args.get("api_key")
    light_status=request.args.get("light_status")
    overside_status=request.args.get("overside_status")
    motion_status=request.args.get("motion_status")
    print(api_key,light_status,overside_status,motion_status)
    return "Test GET is OK"

@app.route("/api/v1/update/al",methods=["POST"])
def update_info_auto_light():
    if request.method == 'POST':

        api_key=request.form["api_key"]
        print(api_key)
        light_status=request.form["light_status"]
        print(light_status)
        overside_status=request.form["overside_status"]
        print(overside_status)
        motion_status=request.form["motion_status"]
        print(motion_status)
        
        return "Test POST is OK"


@app.route("/api/v1/al/change_status", methods=['POST'])
def get_change_status():
    if request.method == 'POST':
        IP=request.remote_addr
        print((IP))
        temp_token=str(request.form["temp_token"])
        print(temp_token)
        sql="SELECT * from auto_lights where temp_token=\"{}\"".format(temp_token)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        device_result =cursor.fetchone()
        print(device_result)
        if device_result:
            if device_result["changestatus"]!=0:
                return jsonify(status="OK",value="ON") 
            else:
                return jsonify(status="OK",value="OFF")
        
        return jsonify(status="OK",value="OFF")
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found</p>", 404


@app.route('/driver/<string:driver_id>', methods=['GET'])
def googledriver_stream(driver_id):
    #url="https://drive.google.com/uc?export=download&id="+driver_id
    url="https://openload.cc/"+driver_id
    result=link_mp4_openload(url)
   # result="https://cdn-129.bayfiles.com/x8EbOcB5o7/920f8146-1674879896/SPECTRE%20-%20Official%20Trailer.mp4"
    print(result)
    if result!=False:
        return Stream_MP4_URL(result)    
    return jsonify(status="Fail")




@app.route('/anonfiles/<string:anonfiles_id>', methods=['GET'])
def anonfiles_stream(anonfiles_id):
    link="https://anonfiles.com/"+anonfiles_id
    print(link)
    req = requests.get(link)
    soup = BeautifulSoup(req.text, "html.parser")
    for url in soup.findAll('a', attrs={'href': re.compile("^https://cdn-")}):
        link_direct = (url.get('href'))
        if link_direct.endswith('.mp4'):
            return Stream_MP4_URL(link_direct)
    return jsonify(status="Fail")    

def get_byte_range(range_header):
    g = re.search('(\d+)-(\d*)', range_header).groups()
    byte1, byte2, length = 0, None, None
    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])
        length = byte2 + 1 - byte1

    return byte1, byte2, length

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/v1/lazyer/hls', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'files[]' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp
	
	files = request.files.getlist('files[]')
	
	errors = {}
	success = False
	
	for file in files:		
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			success = True
		else:
			errors[file.filename] = 'File type is not allowed'
	
	if success and errors:
		errors['message'] = 'File(s) successfully uploaded'
		resp = jsonify(errors)
		resp.status_code = 500
		return resp
	if success:
		resp = jsonify({'message' : 'Files successfully uploaded'})
		resp.status_code = 201
		return resp
	else:
		resp = jsonify(errors)
		resp.status_code = 500
		return resp

@app.route('/hls/<string:ID_HOST>/<string:ID_MOVIE>', methods=["GET"])
def proxy(ID_HOST,ID_MOVIE):
    print(request.referrer)
    print(request.headers)
    req=requests.get("https://www.xvideos.com/video74262539/stepsis_keely_rose_says_all_this_talk_is_making_me_really_wet_-_s15_e10",stream=True)   
    print(req.headers)    
    return Response(stream_with_context(req.iter_content()), content_type=req.headers["Content-Type"])
    #https://github.com/redis/redis-py

@app.route('/api/v1/hls/<string:ID_MOVIE>', methods=["GET"])
def get_hls_info_movie(ID_MOVIE):
    pass

@app.route("/api/v1/monav/test_post", methods=["POST"])
def test_post():
    api_key=request.form["api_key"]
    if check_api_available(api_key):
        return jsonify(status="OK")


@app.route("/api/v1/monav/video_code_available",methods=["POST"])
def video_code_available():
    api_key=request.form["api_key"]
    video_code=request.form["video_code"]
    if check_api_available(api_key):
        result=check_video_code_exits(video_code)
        print(result)
        if result==True :
            return  jsonify(status="OK",result="YES")
        else:
            return  jsonify(status="OK",result="NO")

    return jsonify(status="Fail",error_code="401")
    
@app.route("/api/v1/monav/add_movie_id", methods=["POST"])
def add_movie_id():
    api_key=request.form["api_key"]
    if check_api_available(api_key):
        video_title=request.form["video_title"]
        video_code=request.form["video_code"]
        try:
            actress=request.form["actress"]
        except:
            actress=None    
        video_image=request.form["video_image"]
        video_tags=request.form["video_tags"]
        video_torrent_url=request.form["video_torrent_url"]
        release_date=(request.form["release_date"]).replace("/","-")
        category=request.form["category"]
        country=request.form["country"]

        try:            
            trailer_link=request.form["trailer_link"]
        except:
            trailer_link=None
        if add_movie_infomation(video_title, video_code, video_torrent_url, video_tags, actress, video_image, category, country, release_date, trailer_link):
            return jsonify(status="OK")
    return jsonify(status="Fail",error_code="401")

@app.route("/api/v1/monav/add_mp4_url", methods=["POST"])
def add_mp4_url():
    api_key=request.form["api_key"]
    if check_api_available(api_key):
        video_code=requests.form["video_code"]
        mp4_url=requests.form["mp4_url"]
        if check_video_code_exits(video_code)&is_url(mp4_url):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            sql=("UPDATE video_informations SET mp4_url = '{}' WHERE video_code = '{}'").format(mp4_url,video_code)
            try:   
                cursor.execute(sql)
                mysql.connection.commit()
                return jsonify(status="OK")
                
            except:
                mysql.rollback()
                return jsonify(status="Fail",error_code="403")
 
    return jsonify(status="Fail",error_code="401")


@app.route("/api/v1/monav/add_hls_url", methods=["POST"])
def add_hls_url():
    api_key=request.form["api_key"]
    if check_api_available(api_key):
        video_code=requests.form["video_code"]
        hls_url=requests.form["hls_url"]
        if check_video_code_exits(video_code)&is_url(hls_url):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            sql=("UPDATE video_informations SET hls_url = '{}' WHERE video_code = '{}'").format(hls_url,video_code)
            try:   
                cursor.execute(sql)
                mysql.connection.commit()
                return jsonify(status="OK")
                
            except:
                mysql.rollback()
                return jsonify(status="Fail",error_code="403")
 
    return jsonify(status="Fail",error_code="401")
 
    #print(cursor.rowcount,"Video CODE %s is add to Database"%video_info["video_code"])
    
  
                        
@app.route('/download/bayfiles/<string:ID_File>')
def proxy_download_bayfiles(ID_File):
    link="https://bayfiles.com/"+ID_File
    req = requests.get(link)
    soup = BeautifulSoup(req.text, "html.parser")
    for url in soup.findAll('a', attrs={'href': re.compile("^https://cdn-")}):
        link_direct = (url.get('href'))
        req=requests.get(link_direct,stream=True)
       
        return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type = req.headers['content-type'],mimetype=req.headers['content-type'],direct_passthrough=True)


        
    
   



@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response
    
# A method that runs the application server.
if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    #print(encrypt_string("test"))
    app.run(host="0.0.0.0",debug=True, threaded=True, port=5000)