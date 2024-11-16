from flask import render_template, url_for, flash, redirect, request, send_file, send_from_directory, session, jsonify
from app import app, socket
import os
import sqlite3  
import bcrypt
import uuid
import re
from werkzeug.utils import secure_filename
import re
from urllib.parse import unquote, quote
from middlewares.loggin import check_session
from middlewares.file_upload import handle_file_upload
#Import required library      



# Settings the utils
curr_dir = os.path.dirname(os.path.abspath(__file__))
print(curr_dir)

def getDB():
    conn = sqlite3.connect(os.path.join(curr_dir, "openu.db"))
    cursor = conn.cursor()
    return cursor, conn


# Register route -----------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    try:
        if request.method == "POST":
            emailAddr = request.form['email'].strip()
            username = request.form['username'].strip()
            password = request.form['password'].strip()
            

            #Check for length and regex of the password, sẽ thêm vào để check cả name và email
            '''
            if len(password) < 6:
                message = "Length of password needs to be more than 6 chars."
                return render_template("register.html", message=message)
            if re.match("^[a-zA-Z0-9_]*$", username) is None:
                message = "Username cannot contain special characters."
                return render_template("register.html", message=message)
            '''

            cursor, conn = getDB()
            rows = cursor.execute("SELECT username FROM user WHERE emailAddr = ?", (emailAddr,)).fetchall()

            if rows:
                message = "User already exists"
            else:
                # Generate ID and hash password
                id = str(uuid.uuid4())
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                print(hashed_password)

                # Create sessions
                session['loggedin'] = True
                session['id'] = id


                # Adding data to db
                query = "INSERT INTO user (id, username, emailAddr, password) VALUES (?, ?, ?, ?)"
                cursor.execute(query, (id, username, emailAddr, hashed_password))
                conn.commit()

                # Create folder to save user's uploads
                user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], id)
                if not os.path.exists(user_upload_folder):
                    os.makedirs(user_upload_folder)

                message = "Registration successful"
                return redirect('/home')
    # Catch error
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "You broke the server :(", 400

    return render_template("register.html", message=message)



# Login route -----------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    try:
        if (request.method == "POST"):

            emailAddr = request.form['email'].strip()
            password = request.form['password'].strip()

            # Get user data
            cursor, conn = getDB()
            user_info = cursor.execute("SELECT id, password FROM user WHERE emailAddr = ?",(emailAddr,)).fetchone()

            if user_info:
                id, hashed_password = user_info

                # Check if password is equal to hash
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                    session['loggedin'] = True
                    session['id'] = id
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'],session.get('id'))
                    #notes_list = os.listdir(file_path)

                    return redirect('/home')   
                else:
                     return render_template('login.html', message="Wrong Email or Password aa")
            else:
                return render_template('login.html', message="Wrong Email or Password gg")
        return render_template("login.html")
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "You broke the server :(", 400


@app.route("/")
@app.route("/home")
@check_session
def home():
    #Check if the ID is actually exist in the database
    cursor, conn = getDB()
    id = session['id']
    ischat = None
    
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if id:        
        
        profile_pic = None
        count_noti = cursor.execute("SELECT count(*) from notification where myid= ?",(id,)).fetchone()
        count_noti_chat = cursor.execute("SELECT count(*) from notification where myid= ? and ischat = 1",(id,)).fetchone()
        
        #Retrieve the needed data
        blog_info = cursor.execute("SELECT title, content FROM blogPosts WHERE publish = 1 ORDER BY RANDOM() LIMIT 5").fetchall()
        user_info = cursor.execute("SELECT username FROM user WHERE id = ?", (id,)).fetchone()
        

        #Set up the avatar
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
        avatar_path_full = avatar_path + '/avatar.jpg'
        # print(avatar_path_full)     
        if os.path.exists(avatar_path_full):
            profile_pic = id + '/' + 'avatar.jpg'
        if profile_pic == None:
            profile_pic = os.path.join("", "../../img/avatar.jpg")
        data = []
        noti_list = cursor.execute("SELECT myid, content, timestamp, from_id, ischat from notification where myid = ?",(id,)).fetchall()
        if noti_list:
            for noti in noti_list:
                myid , content, timestamp, fromid, ischat = noti
                rid = cursor.execute("SELECT id FROM chat WHERE userID1 = ? and userID2 = ? or userID1= ? and userID2 = ?", (id,fromid, fromid, id)).fetchall()
                
                # select name sender noti
                sender_pic = None
                sender_name = cursor.execute("SELECT username from user where id = ?",(fromid,)).fetchone()
                sender_ava = os.path.join(app.config['UPLOAD_FOLDER'], fromid)
                sender_ava_full = sender_ava + '/avatar.jpg'
                if os.path.exists(sender_ava_full):
                    sender_pic = fromid + '/' + 'avatar.jpg'
                if sender_pic == None:
                    sender_pic = os.path.join("", "../../img/avatar.jpg")
                if rid != []: 
                    data.append({
                            "myid": myid,
                            "fromid": fromid,
                            "fromname": sender_name,
                            "content": content,
                            "time": timestamp,
                            "sender_pic":sender_pic,
                            "ischat": ischat,
                            "rid" : rid
                        })
                else:
                    data.append({
                            "myid": myid,
                            "fromid": fromid,
                            "fromname": sender_name,
                            "content": content,
                            "time": timestamp,
                            "sender_pic":sender_pic,
                            "ischat": ischat,
                            "rid" : None
                        })
        #Return the index template
        return render_template('index.html', blog_info=blog_info,user_info = user_info,profile_pic=profile_pic, myid = id, data = data, count_noti=count_noti, count_noti_chat = count_noti_chat)

    return redirect('/login')



# Profile route -----------------------------------------------
@app.route('/profile')
@check_session
def profile():
    cursor,conn = getDB()
    id = session['id']
    profile_pic = None
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if id:   
        cursor.execute("SELECT COUNT(*) FROM blogPosts WHERE userID = ?", (id,))
        blog_count = cursor.fetchone()[0]

        #Retrieve the data: username, blod title, content,...
        userName = cursor.execute("SELECT username FROM user WHERE id = ?",(id,)).fetchone()
        username = userName[0]
        print(username)
        blog_info = cursor.execute("SELECT id, title, content, authorname, publish FROM blogPosts WHERE userID = ?", (id,)).fetchall()
        print(blog_info)    

        published_blogs = cursor.execute("SELECT id, title, authorname, publish FROM blogPosts WHERE userID = ? and publish = 1",(id,)).fetchall()

        
        # Query về những cái blog đc like mà có tồn tại userID
        liked_blogs_title = cursor.execute("SELECT title FROM likedBlogs WHERE liked =  1 and userID = ?", (id,)).fetchall()
        print(liked_blogs_title)


        total_blog = []
        for title_blog in liked_blogs_title:
            final_title = title_blog[0]
            print(final_title)
            print("---------------------------------------------------")
            liked_blogs = cursor.execute("SELECT id, title, authorname, publish FROM blogPosts WHERE title = ?",(final_title,)).fetchall()
            print(liked_blogs)
            total_blog += liked_blogs
            print(total_blog)


            # Render avatar for the user
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
        avatar_path_full = avatar_path + '/avatar.jpg'
        print(avatar_path_full)     
        if os.path.exists(avatar_path_full):
            profile_pic = id + '/' + 'avatar.jpg'
        if profile_pic == None:
            profile_pic = os.path.join("", "../../img/avatar.jpg")



        return render_template('profile.html', username=username, blog_info=blog_info,profile_pic=profile_pic,  published_blogs=published_blogs,blog_count=blog_count, liked_blogs=total_blog)
    return redirect('/login')



# Settings user information route -------------------------------
@app.route('/settings', methods=["GET", "POST"])
@check_session
def settings():
    id = session.get('id')
    cursor, conn = getDB()
    
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's id doesn't exist
    

    user_info = cursor.execute("SELECT name, username, emailAddr, password FROM user WHERE id = ?", (id,)).fetchone()

    # Setting the data of user to output to screen
    name, username, emailAddr, hashed_password = user_info
    print(hashed_password)


    profile_pic = None

    # Change the upload folder to inside the user id
    user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], id)

    if request.method == "POST":
        
        # Check if the user sent updated information for name, username, or email
        if 'name' in request.form:
            new_name = request.form['name']
            cursor.execute("UPDATE user SET name = ? WHERE id = ?", (new_name, id))
            conn.commit()
            name = new_name

        if 'username' in request.form:
            new_username = request.form['username']
            cursor.execute("UPDATE user SET username = ? WHERE id = ?", (new_username, id))
            conn.commit()
            username = new_username

        if 'email' in request.form:
            new_email = request.form['email']
            cursor.execute("UPDATE user SET emailAddr = ? WHERE id = ?", (new_email, id))
            conn.commit()
            emailAddr = new_email   

        if 'password' in request.form:
            new_password = request.form['password']
            if new_password:

                if bcrypt.checkpw(new_password.encode('utf-8'), hashed_password):
                    print('Please provide a password different from your old one!')
                    return redirect(request.url)
                else:   
                    new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute("UPDATE user SET password = ? WHERE id = ?", (new_hashed_password, id))
                    conn.commit()
                    password = new_hashed_password
            else:
                pass
    
        #Using middlewware for uploading files
        result = handle_file_upload(request, user_upload_folder, id, name, username, emailAddr, profile_pic)
        if result:
            return result 
        

    avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
    avatar_path_full = avatar_path + '/avatar.jpg'
    print(avatar_path_full)     
    if os.path.exists(avatar_path_full):
        profile_pic = id + '/' + 'avatar.jpg'
    if profile_pic == None:
        profile_pic = os.path.join("", "../../img/avatar.jpg")
        # url("../assests/static/assests/../users_uploads/../../img/avtar.jpg")
    # Render the page with the user info that we retrieve
    return render_template('settings.html', name=name, username=username, email=emailAddr, profile_pic=profile_pic)

# Logout route -----------------------------------------------
@app.route('/logout')
def logout():
    session.pop('loggedin')
    session.pop('id')
    return redirect('/login')


# Called to when create blog ----------------------------------
@app.route("/save_blog", methods=["GET", "POST"])
@check_session
def save_blog():
    id = session.get('id')
    cursor, conn = getDB()
    
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's id doesn't exist

    # Retrieve data from database based on the id
    user_info = cursor.execute("SELECT id, username FROM user WHERE id = ?", (id,)).fetchone()
    username = user_info[1]



    if (request.method == "POST"):
        try:
            blogTitle = request.json.get('blogTitle')
            blogContent = request.json.get('blogContent')

            if blogContent and blogTitle:
                # Execute and save the database
                cursor.execute("INSERT INTO blogPosts (userID, title, content, authorname) VALUES (?, ?, ?, ?)", (id, blogTitle, blogContent, username,))
                conn.commit()
                conn.close()
                return "Blog successfully upload!"
            else:
                print(f"ERROR: {error}", flush=True)
        except Exception as error:
            print(f"ERROR: {error}", flush=True)
            return "You broke the server :(", 400
        
    else:
        return None
    
@app.route("/delete_blog", methods=["POST"])
@check_session
def delete_blog():
    id=session.get("id")
    cursor, conn = getDB()
    
    # Kiểm tra xem id có tồn tại trong cơ sở dữ liệu không
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Chuyển hướng đến trang đăng nhập nếu id người dùng không tồn tại
    
    try:
        # Lấy ID của blog cần xóa từ yêu cầu POST
        blog_id = request.form.get('blog_id')
        
        # Xóa blog từ cơ sở dữ liệu
        cursor.execute("DELETE FROM blogPosts WHERE id = ?", (blog_id,))
        conn.commit()
        
        # Redirect đến trang profile sau khi xóa blog thành công
        return redirect(url_for('profile'))
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "Internal Server Error", 500

# Route will be called when update publish or not
@app.route("/update_published", methods=["POST"])
@check_session
def published():
    id = session.get('id')
    cursor, conn = getDB()
    
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's id doesn't exist

    try:
        blogID = request.json.get('blogID')
        published = request.json.get('published')
        
        cursor.execute("UPDATE blogPosts SET publish = ? WHERE id = ?", (published, blogID))
        conn.commit()
        conn.close()
        return 'Updated'

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "You broke the server :(", 400\
        
#-----------------------------------------------------------------------------------------------   
#-------------------------------- Will look later -----------------------------------------------
# Routes to render out each individual blog when press on the title of a blog

@app.route('/blog/<string:blog_title>')
@check_session
def view_blog(blog_title):
    id = session.get('id')
    cursor, conn = getDB()
    
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's id doesn't exist
    


    #Url parse title name
    decode_title = unquote(blog_title)
    print(decode_title)
    
    #Connect to database
    cursor, conn = getDB()

    # Fetch the blog post from the database based on the provided blog_id
    blog_post = cursor.execute("SELECT title, content, likes, authorname, userID FROM blogPosts WHERE title = ? and publish = 1", (decode_title,)).fetchone()
    print(blog_post)

    # Check if the blog post exists
    if blog_post:
        title, content, likes, authorname, userID = blog_post

        comment_Content = cursor.execute("SELECT username, comment FROM commentsBlog WHERE title = ?", (decode_title,)).fetchall()

        liked = cursor.execute("SELECT liked FROM likedBlogs WHERE title = ? AND userID = ?", (decode_title, id)).fetchone()
        liked = liked[0] if liked else 0  # Default to 0 if the user has not liked the blog

        return render_template('blog.html', title=title, content=content, likes=likes, comment_Content=comment_Content, id=userID, authorname=authorname, liked=liked)
        

    #Update else, check xem liệu bài viết có của phải chính người dùng hay ko, nếu phải thì render, ko thì trả về home
    elif not blog_post:
        blog_post_2 = cursor.execute("SELECT title, content, likes, authorname, userID FROM blogPosts WHERE title = ?", (decode_title,)).fetchone()

        title, content, likes, authorname, userID = blog_post_2

        if userID == id:
            liked = cursor.execute("SELECT liked FROM likedBlogs WHERE title = ? AND userID = ?", (decode_title, id)).fetchone()
            liked = liked[0] if liked else 0  # Default to 0 if the user has not liked the blog

            return render_template('blog.html', title=title, content=content, likes=likes, id=userID, authorname=authorname, liked=liked)
        else:
            return redirect(url_for('home'))

    else:
        # If the blog post does not exist, render an error page or redirect to another page
        return redirect(url_for('home'))

#-----------------------------------------------------------------------------------------------   
#-----------------------------------------------------------------------------------------------   


# Routes for generating new chat by searching for users
from flask import jsonify

@app.route('/new_chat', methods=["POST"])
@check_session
def new_chat():
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's
    
    
    try:
        if request.method == "POST":
            if 'search_input' in request.form:
                search_input = request.form['search_input']
                # Check if the input matches the format of an email address
                if re.match(r'^[\w\.-]+@[\w\.-]+$', search_input):
                    # Search for the user in the database based on the provided email address
                    recipient_info = cursor.execute("SELECT id, username, emailAddr FROM user WHERE emailAddr = ?", (search_input,)).fetchone()
                else:
                    # Search for the user in the database based on the provided username
                    recipient_info = cursor.execute("SELECT id, username, emailAddr FROM user WHERE username = ?", (search_input,)).fetchone()
                    
                if recipient_info:
                    recipient_id, recipient_username, recipient_email = recipient_info
                    # Check if a chat already exists between the current user and the recipient
                    chat_exists = cursor.execute("SELECT id FROM chat WHERE (userID1 = ? AND userID2 = ?) OR (userID1 = ? AND userID2 = ?)", (id, recipient_id, recipient_id, id)).fetchone()
                    if chat_exists:
                        return jsonify({'error': 'Chat already exists'}), 400
                    else:
                        # Proceed with creating a new chat
                        # First, insert the new chat into the database
                        invite_input = request.form['invite_input']
                        query = "SELECT * from notification where myid = ? and from_id = ?"
                        check = cursor.execute(query, (recipient_id, id)).fetchone()
                        if check:
                            return jsonify({'error': 'You are already invited', 'chat_id': recipient_id, 'content': invite_input}), 404
                        else:    
                            return jsonify({'success': 'New chat created successfully', 'chat_id': recipient_id, 'content': invite_input}), 200
                        
                        chat_id = str(uuid.uuid4())

                        cursor.execute("INSERT INTO chat (id, userID1, userID2) VALUES (?, ?, ?)", (chat_id, id, recipient_id))
                        conn.commit()
                        # Retrieve the chat ID of the newly created chat
                        new_chat_id = chat_id

                        
                        # Create room id equal to message id to make eassier query nd understanding
                        chat_roomID = chat_id
                        cursor.execute("INSERT INTO messages (room_id) VALUES (?)", (chat_roomID,))
                        conn.commit()


                        return jsonify({'success': 'New chat created successfully', 'chat_id': new_chat_id}), 200
                else:
                    return jsonify({'error': 'User not found'}), 404

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "Internal Server Error", 500
    
    
    
@app.route('/deletenoti', methods=["POST"])
@check_session
def deletenoti():
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's
    
    
    try:
        if request.method == "POST":
            data = request.data.decode('utf-8')  # Decode data from bytes to string using utf-8 encoding
            data_dict = json.loads(data)  # Convert JSON string to Python dictionary
            if 'fromid' in data_dict:
                fromid = data_dict['fromid']
                toid = data_dict['toid']
                # search_input = request.form['search_input']
                # Check if the input matches the format of an email address

                recipient_info = cursor.execute("SELECT id, username, emailAddr FROM user WHERE id = ?", (toid,)).fetchone()
                    
                if recipient_info:
                    recipient_id, recipient_username, recipient_email = recipient_info
                    cursor.execute("DELETE FROM notification WHERE myid = ? AND from_id = ?", (id,fromid,))
                    conn.commit()
                
                else:
                    return jsonify({'error': 'User not found'}), 404

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "Internal Server Error", 500 
    

import json
@app.route('/accept', methods=["POST"])
@check_session
def accept():
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's
    
    
    try:
        if request.method == "POST":
            data = request.data.decode('utf-8')  # Decode data from bytes to string using utf-8 encoding
            data_dict = json.loads(data)  # Convert JSON string to Python dictionary
            # return  jsonify({'success': 'New chat created successfully', 'data': data_dict}), 200
            # return jsonify({'success': 'New chat created successfully', 'chatroom': 12222}), 200
            
            if 'data' in data_dict:
                senderid = data_dict['data']
                # Check if the input matches the format of an email address
                if re.match(r'^[\w\.-]+@[\w\.-]+$', senderid):
                    # Search for the user in the database based on the provided email address
                    recipient_info = cursor.execute("SELECT id, username, emailAddr FROM user WHERE emailAddr = ?", (senderid,)).fetchone()
                else:
                    # Search for the user in the database based on the provided username
                    recipient_info = cursor.execute("SELECT id, username, emailAddr FROM user WHERE id = ?", (senderid,)).fetchone()
                    
                if recipient_info:
                    recipient_id, recipient_username, recipient_email = recipient_info
                    # Check if a chat already exists between the current user and the recipient
                    chat_exists = cursor.execute("SELECT id FROM chat WHERE (userID1 = ? AND userID2 = ?) OR (userID1 = ? AND userID2 = ?)", (id, recipient_id, recipient_id, id)).fetchone()
                    if chat_exists:
                        return jsonify({'error': 'Chat already exists'}), 400
                    else:
                        # Proceed with creating a new chat
                        # First, insert the new chat into the database
                        chat_id = str(uuid.uuid4())

                        cursor.execute("INSERT INTO chat (id, userID1, userID2) VALUES (?, ?, ?)", (chat_id, id, recipient_id))
                        conn.commit()
                        # Retrieve the chat ID of the newly created chat
                        new_chat_id = chat_id

                        
                        # Create room id equal to message id to make eassier query nd understanding
                        chat_roomID = chat_id
                        cursor.execute("INSERT INTO messages (room_id) VALUES (?)", (chat_roomID,))
                        conn.commit()
                        # Delete noti all noti from 
                        
                        cursor.execute("DELETE FROM notification WHERE myid = ? AND from_id = ?", (id,senderid,))
                        conn.commit()

                        return jsonify({'success': 'New chat created successfully', 'chatroom': chat_roomID}), 200
                else:
                    return jsonify({'error': 'User not found'}), 404

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "Internal Server Error", 500



# Routes for chat (tất cả việc chat hay render list chat và tìm kiếm người dùng ở đây)
@app.route('/chat/', methods=["GET", "POST"])
@check_session
def allChat():
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's


    try:
        # Get the room ID for when user press into one will render it out
        room_id = request.args.get("rid", None)
        count_noti_chat = cursor.execute("SELECT count(*) from notification where myid= ? and ischat = 1",(id,)).fetchone()
        
        # Query all the chat using the current user ID to render out on the page
        chat_list = cursor.execute("SELECT id, userID1, userID2 FROM chat WHERE userID1 = ? or userID2 = ?", (id,id)).fetchall()
        count_noti = cursor.execute("SELECT count(*) from notification where myid= ?",(id,)).fetchone()
        print(chat_list)
        data = []
        messages=[]
        queryname = cursor.execute(f"SELECT id,username from user where id = ?",(id,)).fetchone()        
        
        myid,ownname = queryname
        des_id = None
        if chat_list:
            if room_id != id: 
                get_desit = cursor.execute(f"SELECT userID1, userID2 FROM chat WHERE id = ? ", (room_id, )).fetchall()
                if get_desit: 
                    id1 =  get_desit[0][0]
                    id2 = get_desit[0][1]
                    des_id = id1 
                    if id1 == id:
                        des_id = id2
            for chat in chat_list:
                chat_roomID, userID1, userID2 = chat
                try:
                    # Get all the message
                    messages_th = cursor.execute("SELECT id, content, timestamp, sender_id, sender_username, room_id FROM chat_messages WHERE room_id = ?", (chat_roomID,)).fetchall()

                    # Get the last messages to render out on the chat list(giống hiện tin nhắn gần nhất của mess)
                    latest_message = cursor.execute("SELECT id, content, timestamp, sender_id, sender_username, room_id FROM chat_messages WHERE room_id = ? ORDER BY timestamp DESC LIMIT 1", (chat_roomID,)).fetchone()
                    #---------------------------------------------------------------------
                    if userID1 == id:
                        friend = cursor.execute(f"SELECT username from user where id = ?",(userID2,)).fetchone()
                    else:
                        friend = cursor.execute(f"SELECT username from user where id = ?",(userID1,)).fetchone()
                        
                    if room_id == chat_roomID:
                        for message in messages_th:
                            var1, var2, var3, var4,var5,var6 = message
                            messages.append({
                                "content":var2,
                                "timestamp":var3,
                                "sender_username": var5,
                            }
                            )
                        

                except (AttributeError, IndexError):
                    # Set variable to this when no messages have been sent to the room
                    latest_message = "This place is empty. No messages ..."          
                    
                # Add the query to data
                data.append({
                    "username": friend,
                    "room_id": chat_roomID,
                    "last_message": latest_message,
                })

        else:
            chat_list = None
        messages = messages if room_id else []

        # messages = cursor.execute("SELECT id, content, timestamp, sender_id, sender_username, room_id FROM chat_messages WHERE room_id = ?", (chat_roomID,)).fetchall()
        profile_pic = None
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
        avatar_path_full = avatar_path + '/avatar.jpg'
        print(avatar_path_full)     
        if os.path.exists(avatar_path_full):
            profile_pic = id + '/' + 'avatar.jpg'
        if profile_pic == None:
            profile_pic = os.path.join("", "../../img/avatar.jpg")
        if chat_list == None:
            return render_template('chatbox-code.html', room_id=room_id, data=data,messages=messages,ownname=ownname, myid=myid, profile_pic= profile_pic, count_noti= count_noti, des_id=des_id, count_noti_chat = count_noti_chat)  
        else:
            return render_template('chatbox-code.html', room_id=room_id, data=data,messages=messages,ownname=ownname, myid=myid, profile_pic= profile_pic, count_noti= count_noti, des_id=des_id, count_noti_chat= count_noti_chat)
        
        
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return "Internal Server Error", 500
    


# Route to update the likes
@app.route('/updateLike', methods=["POST"])
@check_session
def update_like():
    id = session.get('id')
    cursor, conn = getDB()
    
    # Check if id exists in database
    cursor.execute("SELECT id FROM user WHERE id = ?", (id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's not logged in

    try:
        # Get post title and action from request
        post_title = request.form.get('post_title')
        action = request.form.get('action')

        # Determine the like_unlike value based on the action
        like_unlike = 1 if action == "like" else 0

        blog_and_user_existed = cursor.execute("SELECT * FROM likedBlogs WHERE title = ? AND userID = ?", (post_title, id)).fetchone()

        if blog_and_user_existed:
            cursor.execute("UPDATE likedBlogs SET liked = ? WHERE title = ? AND userID = ?", (like_unlike, post_title, id))
        else:
            cursor.execute("INSERT INTO likedBlogs (title, userID, liked) VALUES (?, ?, ?)", (post_title, id, like_unlike))

        # Commit the changes to the database
        conn.commit()
        conn.close()

        return jsonify({"message": "Likes updated successfully"}), 200

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return jsonify({"error": "Internal Server Error"}), 500




# Routes to add comment to the database, which will be retrieve when viewing each
@app.route('/addComment/<string:blog_title>', methods=["POST"])
@check_session
def addComments(blog_title):
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's

    user_info = cursor.execute("SELECT id, username FROM user WHERE id = ?", (id,)).fetchone()
    username = user_info[1]

    try:
        # Get the content from the request form
        commentContent = request.form['content']
        if commentContent:
            # Insert comment into database along with blog title
            cursor.execute("INSERT INTO commentsBlog (title, username, comment) VALUES (?, ?, ?)", (blog_title, username, commentContent))

            # Commit to the database
            conn.commit()
            conn.close()

            return "Comments added", 200
        else:
            return "Comments can't be empty :(", 400

    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return jsonify({"error": "Internal Server Error"}), 500
    



#Route to render about user information\
@app.route('/user/<string:user_id>', methods=["GET", "POST"])
@check_session
def viewProfile(user_id):
    id = session.get('id')
    cursor, conn = getDB()
        
    # Check if id exist in database
    cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
    if not id:        
        return redirect(url_for('login'))  # Redirect to login page if user's

    # Decode the id on the url
    decoded_id = unquote(user_id)
    print(decoded_id)


    try:
        # Truy xuất về thông tin người dùng trước
        user_info = cursor.execute("SELECT name, username, emailAddr FROM user WHERE id = ?", (decoded_id,)).fetchone()
        print(user_info)

        #Nếu thông tin người dùng có tồn tại
        if user_info:
            # Truy xuất các blog publish để vào profile
            name, username, emailAddr = user_info


            all_blogs = cursor.execute("SELECT title, likes FROM blogPosts WHERE userID = ? and publish = 1", (decoded_id,)).fetchall()
            print(all_blogs)

            if not all_blogs:
                return "lmao"
            else:
                return render_template("userProfile.html", all_blogs = all_blogs, name=name, username=username, emailAddr=emailAddr)


        else:
            return "No user found!!", 400


    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        return jsonify({"error": "Internal Server Error"}), 500



from datetime import datetime

@app.template_filter("ftime")
def ftime(date):
    # Kiểm tra nếu date là một chuỗi
    if isinstance(date, str):
        return date  # Trả về chuỗi nguyên thủy nếu không thể chuyển đổi

    # Chuyển đổi thành số nguyên nếu có thể
    try:
        dt = datetime.fromtimestamp(int(date))
    except ValueError:
        return str(date)  # Nếu không thể chuyển đổi thì change thành str

    time_format = "%I:%M %p"  # Use  %I for 12-hour clock format and %p for AM/PM
    formatted_time = dt.strftime(time_format)

    formatted_time += " | " + dt.strftime("%m/%d")
    return formatted_time




