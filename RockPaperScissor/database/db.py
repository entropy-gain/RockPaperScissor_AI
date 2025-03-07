import boto3
from datetime import datetime

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("GameHistory")

def save_game(user_id, user_move, ai_move, ai_type, result):
    """
    Saves a game record to DynamoDB.
    """
    table.put_item(
        Item={
            "user_id": user_id,
            "timestamp": str(datetime.utcnow()),
            "user_move": user_move,
            "ai_move": ai_move,
            "ai_type": ai_type,
            "result": result
        }
    )

def get_game_history(user_id):
    """
    Retrieves a user's game history from DynamoDB.
    """
    response = table.query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id}
    )
    return response.get("Items", [])

def get_user_stats(user_id):
    """
    Computes win/loss/draw statistics for a user.
    """
    games = get_game_history(user_id)
    wins = sum(1 for g in games if g["result"] == "win")
    losses = sum(1 for g in games if g["result"] == "lose")
    draws = sum(1 for g in games if g["result"] == "draw")
    return {"wins": wins, "losses": losses, "draws": draws}




"""
for local testing
"""
# Temporary in-memory database for local testing
game_records = []

def save_game(user_id, user_move, ai_move, ai_type, result):
    """
    Save the game result in memory instead of DynamoDB.
    """
    game_records.append({
        "user_id": user_id,
        "user_move": user_move,
        "ai_move": ai_move,
        "ai_type": ai_type,
        "result": result
    })
    print("Game saved:", game_records[-1])  # Debugging log


def get_game_history():
    """
    Retrieve all game records.
    """
    return game_records

def get_user_stats(user_id):
    """
    Retrieve the win/loss statistics for a given user.
    """
    user_games = [game for game in game_records if game["user_id"] == user_id]
    rock_count = sum(1 for game in user_games if game["user_move"] == "rock")
    paper_count = sum(1 for game in user_games if game["user_move"] == "paper")
    scissors_count = sum(1 for game in user_games if game["user_move"] == "scissors")
    return {"rock": rock_count, "paper": paper_count, "scissors": scissors_count}

# Add these functions to your existing db.py file

def get_all_users_stats():
    """
    Retrieves statistics for all users.
    
    Returns:
        List of dictionaries with user stats
    """
    # Replace this with your actual database query
    # This is just an example implementation
    
    # Example query:
    # cursor.execute("SELECT user_id, wins, losses, draws FROM user_stats")
    # return cursor.fetchall()
    
    # Placeholder implementation:
    from your_database_module import execute_query
    return execute_query("SELECT user_id, wins, losses, draws FROM user_stats")
    
    # If you're not using a database, you could have a dictionary like:
    # return [
    #     {"user_id": "test_user", "wins": 10, "losses": 5, "draws": 2},
    #     {"user_id": "player2", "wins": 7, "losses": 8, "draws": 3},
    # ]

def get_all_ai_stats():
    """
    Retrieves statistics for all AI models.
    
    Returns:
        List of dictionaries with AI model stats
    """
    # Replace this with your actual database query
    # Example query:
    # cursor.execute("SELECT ai_type, wins, losses, draws FROM ai_stats")
    # return cursor.fetchall()
    
    # Placeholder implementation:
    from your_database_module import execute_query
    return execute_query("SELECT ai_type, wins, losses, draws FROM ai_stats")
    
    # If you're not using a database, you could have a dictionary like:
    # return [
    #     {"ai_type": "random", "wins": 12, "losses": 18, "draws": 5},
    #     {"ai_type": "markov", "wins": 20, "losses": 10, "draws": 4},
    #     {"ai_type": "pattern", "wins": 15, "losses": 14, "draws": 6},
    # ]

def get_total_games():
    """
    Returns the total number of games played.
    """
    # Replace this with your actual database query
    # Example query:
    # cursor.execute("SELECT COUNT(*) FROM game_history")
    # return cursor.fetchone()[0]
    
    # Placeholder implementation:
    from your_database_module import execute_query
    result = execute_query("SELECT COUNT(*) FROM game_history")
    return result[0][0] if result else 0
    
    # Alternative approach if you track this separately:
    # cursor.execute("SELECT total_games FROM global_stats WHERE id=1")
    # return cursor.fetchone()[0]