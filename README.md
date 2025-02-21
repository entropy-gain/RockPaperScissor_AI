# Rock Paper Scissors AI

## Overview

This project is an AI-powered Rock Paper Scissors game that utilizes various machine learning models to predict and counter player moves. The backend is built with FastAPI and deployed via AWS Lambda, while the frontend is developed using HTML.

## Project Structure
 
```plaintext
rock-paper-scissors-ai/          # Root directory
│── rock_paper_scissors_ai/      # Python package (matches pyproject.toml name)
│   ├── __init__.py              # Marks this as a Python package
│   ├── app.py                   # FastAPI entry point, handles API requests via Lambda
│   ├── models/                  # AI-related models
│   │   ├── __init__.py          # Marks this as a Python package
│   │   ├── base_ai.py           # AI base class
│   │   ├── random_ai.py         # Random strategy AI
│   │   ├── pattern_ai.py        # Pattern-based AI (history-based prediction)
│   │   ├── markov_ai.py         # Markov Chain AI
│   │   ├── memm_ai.py           # Maximum Entropy Markov Chain AI
│   │   ├── crf_ai.py            # Conditional Random Field AI
│   │   ├── rl_ai.py             # Reinforcement Learning AI
│   ├── database/                # Database operations
│   │   ├── __init__.py          # Marks this as a Python package
│   │   ├── db.py                # Connects to AWS DynamoDB and handles queries
│   ├── schemas/                 # Pydantic models for request/response validation
│   │   ├── __init__.py          # Marks this as a Python package
│   │   ├── game.py              # Game-related schemas (GameRequest, GameResponse)
│   ├── routes/                  # FastAPI routes
│   │   ├── __init__.py          # Marks this as a Python package
│   │   ├── game.py              # Handles game logic API
│   │   ├── history.py           # Handles game history API
│   │   ├── stats.py             # Handles win/loss stats API
│── lambda_package/              # AWS Lambda runtime environment (not necessary)
│── frontend/                    # Frontend project
│   ├── public/                  # Static assets
│   ├── src/                     # Vue.js/React source code
│── deploy/                      # Deployment scripts
│   ├── deploy_lambda.sh         # Deploys AWS Lambda
│   ├── deploy_frontend.sh       # Deploys frontend to S3
│   ├── terraform/               # Infrastructure as code (AWS resource management)
│   │   ├── main.tf              # Terraform configuration for AWS resources
│── pyproject.toml               # Poetry dependency management
│── poetry.lock                  # Dependency lock file
│── requirements.txt             # Exported Lambda dependencies from Poetry
│── lambda.zip                   # Packaged ZIP file for AWS Lambda deployment
│── README.md                    # Documentation

