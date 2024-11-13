import sqlite3

# Open database
conn = sqlite3.connect('openu.db')

# Create tables
conn.execute('''CREATE TABLE user (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    name VARCHAR(20),
    username VARCHAR(20) NOT NULL,
    emailAddr VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(60) NOT NULL
)''')

conn.execute('''CREATE TABLE blogPosts (
    id INTEGER PRIMARY KEY NOT NULL,
    userID TEXT,
    authorname VARCHAR(20),
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL, 
    imagepath VARCHAR(255),
    publish BOOLEAN,
    likes INTERGER DEFAULT 0,
    FOREIGN KEY(userID) REFERENCES user(id)
)''')


conn.execute('''CREATE TABLE commentsBlog (
    id INTEGER PRIMARY KEY NOT NULL,
    title VARCHAR(100) NOT NULL,
    username VARCHAR(20),
    comment TEXT NOT NULL, 
    FOREIGN KEY(title) REFERENCES blogPosts(title)
)''')



# Table for saving the user's current chat
conn.execute('''CREATE TABLE chat (
    id TEXT PRIMARY KEY UNIQUE NOT NULL,
    userID1 TEXT NOT NULL,
    userID2 TEXT NOT NULL,
    FOREIGN KEY(userID1) REFERENCES user(id),
    FOREIGN KEY(userID2) REFERENCES user(id),
    UNIQUE(userID1, userID2) 
)''')


# Tables for sacing whats to be the room chat id
conn.execute('''CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id VARCHAR(50) UNIQUE NOT NULL,
    FOREIGN KEY(room_id) REFERENCES chat(id)
)''')


conn.execute('''CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    sender_id INTEGER NOT NULL,
    sender_username VARCHAR(50) NOT NULL,
    room_id VARCHAR(50) NOT NULL,
    FOREIGN KEY(room_id) REFERENCES messages(room_id)
)''')


conn.execute('''CREATE TABLE notification (
    count INTEGER PRIMARY KEY AUTOINCREMENT,
    myid INTEGER  NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    from_id VARCHAR(50) NOT NULL,
    ischat BOOLEAN
)''')


conn.execute('''CREATE TABLE likedBlogs (
    title VARCHAR(100) NOT NULL,
    userID TEXT NOT NULL,
    liked BOOLEAN,
    FOREIGN KEY(title) REFERENCES blogPosts(title),
    FOREIGN KEY(userID) REFERENCES user(id)
)''')



# Close the connection
conn.close()
