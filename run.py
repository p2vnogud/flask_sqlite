from app import app, socket
import os
from flask_socketio import emit, join_room, leave_room
import sqlite3  

curr_dir = os.path.dirname(os.path.abspath(__file__))
print(curr_dir)
# ConnectDB
def getDB():
    conn = sqlite3.connect(os.path.join(curr_dir, "app/openu.db"))
    cursor = conn.cursor()
    return cursor, conn

@socket.on("add_stack_noti")
def hehe(data):
    to_id = data["to"]
    from_id = data["from"]
    time = data['timestamp']
    content = data['message']
    
    
    cursor, conn = getDB()
    # cursor.execute("INSERT into username FROM user WHERE id = ?", (id2,))
    query = "INSERT INTO notification (myid, content, timestamp, from_id, ischat) VALUES (?, ?, ?, ?, 0)"
    cursor.execute(query, (to_id, content, time, from_id))
    conn.commit()

# Join room using flask_sockerIO by adding user in room and return messages
@socket.on("join-chat")
def join_private_chat(data):
    room = data["rid"]
    myid = data['myid']
    join_room(room=room)
    cursor, conn = getDB()  
    userID = cursor.execute("SELECT userID1,userID2 FROM chat WHERE id = ?", (room,)).fetchone()
    id1, id2 = userID
    if myid == id1:
        add_friend_info = cursor.execute("SELECT username FROM user WHERE id = ?", (id2,)).fetchone()
    else:
        add_friend_info = cursor.execute("SELECT username FROM user WHERE id = ?", (id1,)).fetchone()

    conn.commit()
    arr_data =[]
    arr_data.append(add_friend_info)
    arr_data.append(room)
    socket.emit(
        "joined-chat",
        arr_data,
        room = data["rid"]
    )



# Outgoing event handler
@socket.on("outgoing")
def chatting_event(json, methods=["GET", "POST"]):
    """
    handles saving messages and sending messages to all clients
    :param json: json
    :param methods: POST GET
    :return: None
    """
    room_id = json["rid"]
    timestamp = json["timestamp"]
    message = json["message"]
    sender_id = json["sender_id"]
    sender_username = json["sender_username"]

    try:
        # Thêm tin nhắn mới vào bảng chat_messages
        cursor, conn = getDB()
        cursor.execute(
                """
                INSERT INTO chat_messages (content, timestamp, sender_id, sender_username, room_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message, timestamp, sender_id, sender_username, room_id)
            )
        conn.commit()
        get_desit = cursor.execute(f"SELECT id, userID1, userID2 FROM chat WHERE id = ? ", (room_id, )).fetchone()
        roomid, id1, id2 = get_desit
        des_id = id1 
        if id1 == sender_id:
            des_id = id2
        checker = cursor.execute("select * from notification where myid = ? and from_id = ?", (des_id,sender_id, )).fetchall()
        if checker:
            # donothing
            a = 1
        else:
            query = "INSERT INTO notification (myid, content, timestamp, from_id, ischat) VALUES (?, ?, ?, ?, 1)"
            cursor.execute(query, (des_id, message, timestamp, sender_id))
            conn.commit()
        # Lưu tin nhắn mới vào cơ sở dữ liệu
        # (Do bạn không sử dụng SQLAlchemy, nên phần này không cần thiết)

    except Exception as e:
        # Xử lý lỗi cơ sở dữ liệu, ví dụ: ghi log lỗi hoặc gửi phản hồi lỗi cho client.
        print(f"Error saving message to the database: {str(e)}")

    # Phát tin nhắn đã gửi tới các người dùng khác trong phòng
    join_room(room=room_id)
    socket.emit(
        "message",
        json,
        room=room_id,
        include_self=False,
    )


if __name__ == "__main__":
    socket.run(app, allow_unsafe_werkzeug=True, debug=True)
