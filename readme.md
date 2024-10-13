# TapTap Trivia AI Assistant

## Purpose

This project creates an AI-powered assistant to help answer questions in the TapTap Trivia game. The assistant captures the game screen, processes the questions and answer options, and provides intelligent responses to help users excel in the trivia game.

## Key Technologies

- **Screen Capture**: Uses Python's `tkinter` and `PIL` (Python Imaging Library) for capturing and processing game screen images.
- **Optical Character Recognition (OCR)**: Employs `pytesseract` to extract text from the captured images, identifying questions and answer options.
- **AI Language Model**: Utilizes the Anthropic API (Claude) for generating accurate and relevant answers to trivia questions.
- **Python**: The core programming language used for implementing the project's functionality.

## Features

- Real-time screen capture and analysis
- Automatic question and answer option detection
- AI-powered answer generation using Claude
- User-friendly interface for easy interaction

## Setup

1. Ensure Python is installed on your system.
2. Install required dependencies: `pip install -r requirements.txt`
3. Set up a `.env` file with your Anthropic API key.
4. Run the main script to start the assistant.

This project combines computer vision techniques, natural language processing, and artificial intelligence to create a sophisticated tool for enhancing the TapTap Trivia gaming experience.
