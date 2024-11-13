@app.route("/")
@app.route("/home")
def home():
    if session.get('loggedin') == True:
        cursor, conn = getDB()
        id = session['id']
        cursor.execute("SELECT id FROM user WHERE id = ?",(id,)).fetchone()
        if id:        
            profile_pic = None
            
            blog_info = cursor.execute("SELECT title, content FROM blogPosts WHERE publish = 1 ORDER BY RANDOM() LIMIT 5").fetchall()

            user_info = cursor.execute("SELECT username FROM user WHERE id = ?", (id,)).fetchone()
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], id)
            avatar_path_full = avatar_path + '/avatar.jpg'
            print(avatar_path_full)     
            if os.path.exists(avatar_path_full):
                profile_pic = id + '/' + 'avatar.jpg'
            if profile_pic == None:
                profile_pic = os.path.join("", "../../img/avatar.jpg")
            #print(blog_info)
            return render_template('index.html', blog_info=blog_info,user_info = user_info,profile_pic=profile_pic)
        return redirect('/login')
    else:
        return redirect('/login')
