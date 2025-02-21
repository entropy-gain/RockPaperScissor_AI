# Rock Paper Scissors AI

### Overview

This project is an AI-powered Rock Paper Scissors game that utilizes various machine learning models to predict and counter player moves. The backend is built with FastAPI and deployed via AWS Lambda, while the frontend is developed using Vue.js/React.

### Project Structure
 
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
```

### Git Workflow and Best Practices

#### Branch Naming Convention

- **feature/xxx** - New features or enhancements
- **bugfix/xxx** - Bug fixes
- **hotfix/xxx** - Critical hotfixes for production
- **refactor/xxx** - Code refactoring without changing functionality
- **docs/xxx** - Documentation updates

#### Git Workflow

1. **Always create a new branch** for new work instead of pushing directly to `main`.
2. **Never push directly to `main`**; all code must go through a **merge request (pull request)**.
3. **Merge requests should be reviewed** before merging into `main`.
4. **Keep commits atomic**, meaning each commit should serve a single purpose.
5. **Write meaningful commit messages**, following the format: `type(scope): description` (e.g., `feat(game): add new AI model`).
6. **Sync with `main` regularly** to avoid merge conflicts.

#### Common Git Commands

```sh
# Check the current remote repository
git remote -v

# Check the current status of your repository
git status

# Add files to staging area
git add <file> # Add a specific file
git add .      # Add all changes

# Create a new branch
git branch feature/new-feature

# Switch to a branch
git checkout feature/new-feature

# Commit changes with a message
git commit -m "feat(game): improve AI prediction accuracy"

# Push changes to a remote branch
git push origin feature/new-feature

# Pull the latest changes from `main`
git pull origin main

# Merge another branch into your current branch
git merge feature/new-feature

# Delete a branch after merging
git branch -d feature/new-feature
```

#### Additional Git Tips for Beginners

- **Use descriptive branch names** that indicate their purpose.
- **Commit frequently** to avoid losing work.
- **Avoid large, unstructured commits**—each commit should ideally address a single issue.
- **Use `git stash`** to temporarily store changes when switching branches.
- **Review changes before committing** using `git diff`.
- **Always fetch the latest updates** using `git fetch` before working on a branch.
- **Resolve merge conflicts carefully** and test thoroughly after merging.

By following these best practices, we ensure a clean and maintainable codebase for the project.

