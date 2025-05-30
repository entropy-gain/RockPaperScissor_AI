---
title: Rock Paper Scissors AI Battleground
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: gradio
# sdk_version: 4.26.0 # Specify a recent Gradio version
app_file: app.py
python_version: 3.9 # Or your target Python version
# secrets: # Uncomment and add if you use S3
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - S3_BUCKET_NAME
#   - S3_ENDPOINT_URL # If using a custom S3 endpoint
---

# Rock Paper Scissors AI Battleground
Play Rock, Paper, Scissors against various AI opponents!
Select an AI model from the dropdown and try to outsmart it.

**Hugging Face Spaces Version:**
- This version is ready for deployment on Hugging Face Spaces.
- It uses only in-memory storage (no persistent storage/database).
- All persistent storage code is commented out and can be re-enabled for local or advanced deployments.
- Game stats and history will reset on every restart (as required by Hugging Face Spaces free tier).

This application integrates a Python backend with multiple AI strategies and a Gradio UI.