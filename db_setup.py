from RockPaperScissor.repositories.db import create_tables_if_not_exist

if __name__ == "__main__":
    print("Creating DynamoDB tables...")
    result = create_tables_if_not_exist()
    print(f"Tables created successfully: {result}")