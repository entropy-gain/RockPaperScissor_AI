# Rock Paper Scissors AI

### Overview

This project is an AI-powered Rock Paper Scissors game that utilizes various machine learning models to predict and counter player moves. The backend is built with FastAPI and deployed via AWS Lambda, while the frontend is developed using Vue.js/React.

### Project Structure
 
```plaintext
RockPaperScissor/
├── RockPaperScissor/              # Main application package
│   ├── __init__.py
│   ├── app.py                     # Main application entry point
│   │
│   ├── services/                  # Server logic layer
│   │   ├── __init__.py
│   │   ├── game_service.py        # Game-related server logic
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── db.py                  # Database connection
│   │   ├── game_repository.py     # Game data access
│   │
│   ├── models/                    # AI models
│   │   ├── __init__.py
│   │   ├── base_ai.py             # AI base class
│   │   ├── random_ai.py           # Random strategy AI
│   │   ├── pattern_ai.py          # Pattern strategy AI
│   │   └── ...
│   │
│   ├── schemas/                   # Data validation schemas
│   │   ├── __init__.py
│   │   ├── game.py                # Game-related schemas
│   │
│   ├── routes/                    # API routes
│   │   ├── __init__.py
│   │   ├── stats.py                # User-related routes
│   │   ├── game.py                # Game-related routes
│   │
│   ├── utils/                     # Utilities
│       ├── __init__.py
│       ├── logging.py             # Logging configuration
│
├── frontend/                      # Frontend project
│   ├── index.html                 # Main HTML entry page
│   ├── webpage.html               # Secondary HTML page
│
├── deploy/                        # All deployment resources
│   ├── lambda/                    # Lambda deployment resources
│   │   ├── package/               # Lambda package content
│   │   └── deploy_lambda.sh       # Lambda deployment script
│   │
│   ├── frontend/                  # Frontend deployment
│   │   └── deploy_frontend.sh     # Frontend deployment script
│   │
│   ├── terraform/                 # Infrastructure as code
│   │   ├── main.tf                # Main Terraform configuration
│   │   ├── variables.tf           # Terraform variables
│   │   └── outputs.tf             # Terraform outputs
│   │
│   └── scripts/                   # Utility deployment scripts
│       └── setup_aws_resources.sh # Script to initialize resources
│
├── config/                        # Configuration files
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   │   ├── services/              # Service tests
│   │   ├── repositories/          # Repository tests
│   │   └── models/                # Model tests
│   │
│   └── integration/               # Integration tests
│       └── api/                   # API tests
│
├── pyproject.toml                 # Poetry dependency management
├── poetry.lock                    # Dependency lock file
├── requirements.txt               # For Lambda dependencies
├── .gitignore                     # Git ignore file
├── README.md                      # Documentation
└── .devcontainer                  # Container
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

