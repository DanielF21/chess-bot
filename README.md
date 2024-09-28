# DanielBot Chess Engine

This repository contains the backend code for the DanielBot chess engine, playable at [danielfleming.xyz](https://danielfleming.xyz).

## Project Structure

- `preprocessing/`: Contains all necessary preprocessing steps
- `training/`:
  - `model.py`: Neural network architecture
  - `load.py`: Data loading script
  - `stream.py`: Alternative loading script (trades speed for memory efficiency)
  - `train.py`: Main training script
  - `gcloud_train.py`: Modified training script for Google Cloud Platform
- `app.py`: Flask application for serving the model
- `chess_gui.py`: Local GUI for playing against the bot

## Playing Locally

To play against DanielBot on your local machine:

1. Clone this repository: 
```
git clone https://github.com/DanielF21/chess-bot.git
```
2.  Install the required dependencies: 
```
pip install -r requirements.txt
```
3. Run the chess GUI: 
```
python chess_gui.py
