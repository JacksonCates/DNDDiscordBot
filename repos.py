import pyodbc
from datetime import datetime

class PlayerDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
    def get_player_by_name(self, player_name):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = f"SELECT [id], name, player_name, role FROM players WHERE name = ?"
                cursor.execute(query, player_name)
                player = cursor.fetchone()
                
                if player:
                    player_info = {
                        "id": player.id,
                        "name": player.name,
                        "player_name": player.player_name,
                        "role": player.role
                    }
                    return player_info
                else:
                    return None
                    
        except pyodbc.Error as e:
            print("Error:", e)
            return None
        
    def get_all_players(self):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = f"SELECT [id], name, player_name, role FROM players"
                cursor.execute(query)
                players = cursor.fetchall()
                
                player_list = []
                for player in players:
                    player_info = {
                        "id": player.id,
                        "name": player.name,
                        "player_name": player.player_name,
                        "role": player.role
                    }
                    player_list.append(player_info)
                return player_list
        except pyodbc.Error as e:
            print("Error:", e)
            return None

    def get_all_dms(self):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = f"SELECT [id], name, player_name, role FROM players WHERE [role] = 'DM'"
                cursor.execute(query)
                players = cursor.fetchall()
                
                player_list = []
                for player in players:
                    player_info = {
                        "id": player.id,
                        "name": player.name,
                        "player_name": player.player_name,
                        "role": player.role
                    }
                    player_list.append(player_info)
                return player_list
        except pyodbc.Error as e:
            print("Error:", e)
            return None




class QuestDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    def add_quest(self, title, content, player_ids):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
            
                # Insert quest entry
                query_insert_log = "INSERT INTO quests (title, status, content, is_deleted) VALUES (?, ?, ?, ?)"
                cursor.execute(query_insert_log, title, "INPROGRESS", content, 0)
                print("Quest added successfully.")

                # Get the quest id
                query_latest_log = """
                    SELECT TOP 1 [id]
                    FROM quests
                    ORDER BY [id] DESC
                """
                cursor.execute(query_latest_log)
                quest_id = cursor.fetchone().id

                # Insert connections with player
                for player_id in player_ids:
                    query_insert_log = "INSERT INTO player_quests (quest_id, player_id) VALUES (?, ?)"
                    cursor.execute(query_insert_log, quest_id, player_id)
                conn.commit()
        except pyodbc.Error as e:
            print("Error:", e)

    def get_all_quest(self, player_name):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
            
                # Get player ID by name
                query_player_id = "SELECT ID FROM players WHERE name = ?"
                cursor.execute(query_player_id, player_name)
                player_id = cursor.fetchone()

                if player_id:
                    # gets the thing
                    query_all_quest = """
                        SELECT [id], title, status, content
                        FROM quests
                        RIGHT JOIN player_quests ON player_quests.quest_id = quests.[id] 
                        WHERE player_quests.player_id = ? AND is_deleted = 0
                    """
                    cursor.execute(query_all_quest, player_id)
                    all_quests = cursor.fetchall()

                    quests_list = []
                    for q in all_quests:
                        quest = {
                            "id": q.id,
                            "title": q.title,
                            "status": q.status,
                            "content": q.content,
                        }
                        quests_list.append(quest)
                    return quests_list

                else:
                    raise ValueError("Player not found. Log not added.")
        except pyodbc.Error as e:
            print("Error:", e)

    def get_all_deleted_quest(self, player_name):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
            
                # Get player ID by name
                query_player_id = "SELECT ID FROM players WHERE name = ?"
                cursor.execute(query_player_id, player_name)
                player_id = cursor.fetchone()

                if player_id:
                    # gets the thing
                    query_all_quest = """
                        SELECT [id], title, status, content
                        FROM quests
                        RIGHT JOIN player_quests ON player_quests.quest_id = quests.[id] 
                        WHERE player_quests.player_id = ? AND is_deleted = 1
                    """
                    cursor.execute(query_all_quest, player_id)
                    all_quests = cursor.fetchall()

                    quests_list = []
                    for q in all_quests:
                        quest = {
                            "id": q.id,
                            "title": q.title,
                            "status": q.status,
                            "content": q.content,
                        }
                        quests_list.append(quest)
                    return quests_list

                else:
                    raise ValueError("Player not found. Log not added.")
        except pyodbc.Error as e:
            print("Error:", e)

    def get_quest_by_id(self, quest_id):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query_all_quest = """
                    SELECT [id], title, status, content
                    FROM quests
                    WHERE [id] = ?
                """
                cursor.execute(query_all_quest, quest_id)
                quest = cursor.fetchone()
                
                if quest:

                    # Gets all the player info
                    query_all_players = """
                        SELECT * FROM player_quests
                        INNER JOIN players ON player_id = [id]
                        WHERE quest_id = ?
                    """
                    cursor.execute(query_all_players, quest_id)
                    all_players = cursor.fetchall()
                    players = []
                    for p in all_players:
                        player_info = {
                            "id": p.id,
                            "name": p.name,
                            "player_name": p.player_name,
                            "role": p.role
                        }
                        players.append(player_info)

                    quest_info = {
                        "id": quest.id,
                        "title": quest.title,
                        "status": quest.status,
                        "content": quest.content,
                        "players": players
                    }
                    return quest_info
                else:
                    return None
                    
        except pyodbc.Error as e:
            print("Error:", e)
            return None

    def edit_quest(self, quest_id, new_title=None, new_content=None, new_status=None, new_is_deleted=None):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()

                # Update the quest based on provided information
                update_query = "UPDATE quests SET"
                update_params = []
                if new_title:
                    update_query += " title = ?,"
                    update_params.append(new_title)
                if new_content:
                    update_query += " content = ?,"
                    update_params.append(new_content)
                if new_status:
                    update_query += " status = ?,"
                    update_params.append(new_status)
                if new_is_deleted is not None:
                    update_query += " is_deleted = ?,"
                    update_params.append(new_is_deleted)
                if not update_params:
                    print("No changes provided. Quest remains unchanged.")
                    return

                update_query = update_query.rstrip(',') + " WHERE id = ?"
                update_params.append(quest_id)

                cursor.execute(update_query, *update_params)
                conn.commit()
                print("Quest updated successfully.")

        except pyodbc.Error as e:
            print("Error:", e)

class LogDatabase:
    def __init__(self, server, database, username, password):
        self.connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        
    def add_log(self, content, player_name):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Get player ID by name
                query_player_id = "SELECT ID FROM players WHERE name = ?"
                cursor.execute(query_player_id, player_name)
                player_id = cursor.fetchone()
                
                if player_id:
                    # Insert log entry
                    current_datetime = datetime.now()
                    query_insert_log = "INSERT INTO logs (date, content, player_id) VALUES (?, ?, ?)"
                    cursor.execute(query_insert_log, current_datetime, content, player_id.ID)
                    conn.commit()
                    print("Log added successfully.")
                else:
                    raise ValueError("Player not found. Log not added.")
                    
        except pyodbc.Error as e:
            print("Error:", e)

    def get_latest_log(self):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query_latest_log = """
                    SELECT TOP 1 [id], date, content
                    FROM logs
                    ORDER BY logs.date DESC
                """
                cursor.execute(query_latest_log)
                latest_log = cursor.fetchone()
                
                if latest_log:
                    log_info = {
                        "id": latest_log.id,
                        "date": latest_log.date,
                        "content": latest_log.content
                    }
                    return log_info
                else:
                    return None
                    
        except pyodbc.Error as e:
            print("Error:", e)
            return None
        
    def get_all_logs(self):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query_all_logs = """
                    SELECT [id], date, content
                    FROM logs
                    ORDER BY logs.date DESC
                """
                cursor.execute(query_all_logs)
                all_logs = cursor.fetchall()
                
                log_list = []
                for log in all_logs:
                    log_info = {
                        "id": log.id,
                        "date": log.date,
                        "content": log.content
                    }
                    log_list.append(log_info)
                
                return log_list
                
        except pyodbc.Error as e:
            print("Error:", e)
            return []
        
    def get_all_logs_by_role(self, role):
        logs = self.get_all_logs()
        if role == "DM":
            return logs
        elif role == "player":
            return logs[:2] # Only gets the last 2 logs
        else:
            raise ValueError("Incorrect role. Was given " + role)

    def get_log_by_id(self, log_id):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query_log_by_id = """
                    SELECT [id], date, content
                    FROM logs
                    WHERE logs.id = ?
                """
                cursor.execute(query_log_by_id, log_id)
                log = cursor.fetchone()
                
                if log:
                    log_info = {
                        "id": log.id,
                        "date": log.date,
                        "content": log.content
                    }
                    return log_info
                else:
                    return None
                    
        except pyodbc.Error as e:
            print("Error:", e)
            return None
        
    def edit_log(self, log_id, new_content):
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query_edit_log = """
                    UPDATE logs
                    SET content = ?
                    WHERE id = ?
                """
                cursor.execute(query_edit_log, new_content, log_id)
                conn.commit()
                print("Log edited successfully.")
                
        except pyodbc.Error as e:
            print("Error:", e)