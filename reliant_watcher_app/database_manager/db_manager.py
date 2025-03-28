import sqlite3 as sql
from pathlib import Path
import sys
from collections import Counter, defaultdict
from datetime import datetime

# Move two levels up from this file's directory
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

from object_detection.yolox import YoloX

def create_schema(db_path: Path):
    # Connect to (or create) the SQLite database file
    connection = sql.connect(db_path)
    # Enable foreign key constraint checks
    connection.execute("PRAGMA foreign_keys = ON;")
    cursor = connection.cursor()

    # Table: metadata_objects
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Metadata_Object (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        object TEXT NOT NULL,
        UNIQUE (object)
    );
    ''')

    # Table: video_recording
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Video (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        UNIQUE (path)
    );
    ''')

    # Table: Recordings_Objects 
    # - references 'video_id' (ID) 
    # - references 'metadata_object_id' (ID)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Video_With_Metadata_Object (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL,
        metadata_object_id INTEGER,
        object_count INTEGER,
        FOREIGN KEY (video_id)
            REFERENCES Video(id),
        FOREIGN KEY (metadata_object_id)
            REFERENCES Metadata_Object(id)
    );
    ''')

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

def populate_metadata_objects(db_path: Path):
    connection = sql.connect(db_path)
    cursor = connection.cursor()

    # Insert the object labels into the 'Metadata_Object' table
    for object in YoloX._objects:
        cursor.execute("INSERT INTO Metadata_Object (object) VALUES (?)", (object,))
    connection.commit()
    connection.close()

def create_db(db_path: Path):
    create_schema(db_path)
    populate_metadata_objects(db_path)

def insert_video_with_metadata(db_path: Path, video_name: str, detected_objects: Counter):
    if not isinstance(detected_objects, Counter):
        raise ValueError("Object info to database is not a Counter object.")
    if not isinstance(video_name, str):
        raise ValueError("Video path to database is not a string.")
    video_path = Path(__file__).parent.parent / "video_recordings" / video_name
    if not video_path.exists():
        print(f"File not found: {video_name}")
        return
    connection = sql.connect(db_path)
    cursor = connection.cursor()
    
    # Insert the video file path into the 'Video' table
    cursor.execute("INSERT INTO Video (path) VALUES (?)", (video_name,))
    connection.commit()
    video_id = cursor.lastrowid
    
    # Insert the metadata objects into the 'Video_With_Metadata_Object' table
    if sum(detected_objects.values()) > 0:
        for key, value in detected_objects.items():
            cursor.execute("SELECT ID FROM Metadata_Object WHERE object =?", (key,))
            metadata_object_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO Video_With_Metadata_Object (video_id, metadata_object_id, object_count) VALUES (?,?,?)", 
                        (video_id, metadata_object_id, value))
    else:
        # insert only video id into Video_With_Metadata_Object table
        cursor.execute("INSERT INTO Video_With_Metadata_Object (video_id, metadata_object_id, object_count) VALUES (?,?,?)", 
                       (video_id, None, None))
    connection.commit()
    connection.close()
    print(f"Video name '{video_name}' with metadata {detected_objects} inserted successfully.")


db_path = Path(__file__).resolve().parent.parent / "database" / "video_with_metadata.db"

def get_video_path(filename):
    connection = sql.connect(db_path)
    cursor = connection.cursor()
    query = '''
            SELECT path FROM Video WHERE path LIKE ?
            '''
    cursor.execute(query, (f"%{filename}%",))
    result = cursor.fetchone()[0]
    connection.close()
    return Path(__file__).resolve().parent.parent / "video_recordings" / result

def get_latest_intrusion_videos(amount):
    connection = sql.connect(db_path)
    cursor = connection.cursor()
    query = '''
            SELECT 
                V.path AS video_path, 
                MO.object AS object_name, 
                VWMO.object_count
            FROM (
                SELECT id, path FROM Video ORDER BY id DESC LIMIT ?
            ) AS V
            LEFT JOIN Video_With_Metadata_Object VWMO ON V.id = VWMO.video_id
            LEFT JOIN Metadata_Object MO ON VWMO.metadata_object_id = MO.id
            ORDER BY V.id DESC, MO.object;
            '''
    cursor.execute(query, (amount,))
    result = cursor.fetchall()
    connection.close()

    result_to_counter = defaultdict(Counter)
    for path, obj, count in result:
        result_to_counter[path]
        if obj and count:  # Only add if object and count are valid
            result_to_counter[path][obj] += count  # Add count directly

    processed_result = {} # {path: message}
    for path, objs_counter in result_to_counter.items():
        processed_result[path] = convert_counter_to_message(objs_counter)
    return processed_result




# Helper function to reformat the date and time for use in the query.
def format_datetime(search_input):
    # Parse the input date/time ("YYYY-MM-DDTHH:MM") and convert it to "YYYY-MM-DDTHH:MM:SS.mp4"
    dt = datetime.strptime(search_input, "%Y-%m-%dT%H:%M")
    converted = dt.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{converted}.mp4"

def get_searched_intrusion_videos(objects: list, start_date: str, end_date: str):
    connection = sql.connect(db_path)
    cursor = connection.cursor()
    
    # Base query.
    base_query = '''
            SELECT 
                v.path AS video_path, 
                m.object AS object_name, 
                vwo.object_count AS object_count
            FROM Video v
            JOIN Video_With_Metadata_Object vwo ON v.id = vwo.video_id
            JOIN Metadata_Object m ON vwo.metadata_object_id = m.id
            WHERE
    '''
    
    conditions = []
    params = []
    
    # If objects list is provided, add the IN clause condition.
    if objects:
        placeholders = ','.join('?' for _ in objects)
        conditions.append(f"m.object IN ({placeholders})")
        params.extend(objects)
    
    # Always filter by date.
    conditions.append("v.path BETWEEN ? AND ?")
    
    # Build the final query string.
    query = base_query + " AND ".join(conditions) + ";"
    
    # Determine the formatted start date.
    if start_date == "":
        formatted_start_date = "0000-01-01T00:00:00.mp4"
    else:
        formatted_start_date = format_datetime(start_date)
    
    # Determine the formatted end date.
    if end_date == "":
        formatted_end_date = "9999-12-31T23:59:59.mp4"
    else:
        formatted_end_date = format_datetime(end_date)
    
    params.extend([formatted_start_date, formatted_end_date])
    
    cursor.execute(query, tuple(params))
    result = cursor.fetchall()
    connection.close()
    
    result_to_counter = defaultdict(Counter)
    for path, obj, count in result:
        if obj and count:
            result_to_counter[path][obj] += count
    
    processed_result = {}  # {path: message}
    for path, objs_counter in result_to_counter.items():
        processed_result[path] = convert_counter_to_message(objs_counter)
    return processed_result

def convert_counter_to_message(objs_counter: Counter):
    msg = ""
    if sum(objs_counter.values()) > 0:
        keys = list(objs_counter.keys())
        len_of_keys = len(keys)
        if len_of_keys == 1:
            msg += f"\n{objs_counter[keys[0]]} {keys[0]} detected in the scene."
        else:
            for i in range(len_of_keys):
                if i == 0:
                    msg += f"\n{objs_counter[keys[i]]} {keys[i]}"
                elif i == len_of_keys - 1:
                    msg += f" and {objs_counter[keys[i]]} {keys[i]} detected in the scene."
                else:
                    msg += f", {objs_counter[keys[i]]} {keys[i]}"
    return msg



if __name__ == "__main__":
    db_path = Path(__file__).resolve().parent.parent / "database" / "video_with_metadata.db"
    # create_db(db_path)
    # print("SQLite schema created successfully.")
    dd = get_latest_intrusion_videos(3)
    print(dd, "\n")

    ff = get_searched_intrusion_videos(["person", "remote"], "2025-03-17T01:28", "2025-03-18T01:30")
    print(ff)


