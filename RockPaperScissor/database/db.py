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
