# Voice-Activated Wikipedia Assistant

A Python-based voice assistant that answers queries using a local knowledge base and Wikipedia, powered by speech recognition and text-to-speech. It extracts topics with spaCy, caches responses for efficiency, and supports hands-free interaction with a "Hey bro" activation phrase.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Overview
This project is a voice-activated assistant designed to provide information from a local JSON-based knowledge base or Wikipedia. It uses `speech_recognition` for voice input, `pyttsx3` for text-to-speech output, and `spaCy` for natural language processing to extract query topics. The assistant supports conversational queries, caches Wikipedia results for performance, and updates its knowledge base with new responses. It’s ideal for users seeking a hands-free, interactive way to access factual information.

## Features
- **Voice Interaction**: Recognizes queries via microphone input and responds with synthesized speech.
- **Knowledge Base**: Stores and retrieves answers from a local JSON file, reducing external API calls.
- **Wikipedia Integration**: Fetches summaries from Wikipedia using `wikipediaapi` and `wikipedia` for robust search.
- **Topic Extraction**: Uses `spaCy` for entity and noun chunk extraction to identify query topics.
- **Response Caching**: Caches Wikipedia summaries in a JSON file with a 7-day expiry for faster responses.
- **Disambiguation Handling**: Resolves Wikipedia disambiguation pages by selecting the most relevant link.
- **Word Limit Control**: Limits summaries to 250 words per topic and 700 words total for concise responses.
- **Logging**: Detailed logging for debugging and monitoring query processing.
- **Responsive Design**: Hands-free activation with "Hey bro" and deactivation with phrases like "Ok thank you".

## Prerequisites
- **Python**: Version 3.8 or higher.
- **System Requirements**: Microphone for voice input, speakers for output, at least 4GB RAM, and a modern CPU.
- **Internet Connection**: Required for initial Wikipedia queries and NLTK/spaCy model downloads.
- **Optional**: Virtual environment for dependency management.

## Installation
1. **Clone the Repository**
   ```bash
   git clone https://github.com/sohaibzafar701/Voice-Activated-Wikipedia-Assistant.git
   cd Voice-Activated-Wikipedia-Assistant
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   Install required packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   Expected dependencies include:
   - `speech_recognition==3.10.0`
   - `pyttsx3==2.90`
   - `spacy==3.7.2`
   - `nltk==3.8.1`
   - `wikipedia-api==0.6.0`
   - `wikipedia==1.4.0`
   - `difflib` (built-in)
   If issues arise, install individually:
   ```bash
   pip install speech_recognition pyttsx3 spacy nltk wikipedia-api wikipedia
   ```

4. **Download spaCy Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Download NLTK Data**
   The script automatically downloads `punkt` for sentence tokenization during execution.

## Setup
1. **Initialize Knowledge Base**
   The script automatically creates a `knowledge_base.json` file with sample Q&A pairs if it doesn’t exist:
   ```json
   {
       "what is the capital of france": "The capital of France is Paris.",
       "who invented the telephone": "Alexander Graham Bell invented the telephone.",
       ...
   }
   ```

2. **Ensure Microphone and Speakers**
   - Test your microphone and speakers to ensure they work with `speech_recognition` and `pyttsx3`.
   - On Linux, you may need to install `espeak` or `pulseaudio` for `pyttsx3` to function.

## Running the Application
1. **Start the Assistant**
   ```bash
   python assistant.py
   ```
   The assistant enters idle mode, listening for the activation phrase "Hey bro".

2. **Interact with the Assistant**
   - Say "Hey bro" to activate.
   - Ask a question (e.g., "What is the capital of France?" or "Tell me about the French Revolution from Wikipedia").
   - Deactivate with "Ok thank you" or similar phrases.

## Usage
1. **Activate the Assistant**
   - Say "Hey bro" to switch from idle to active mode. The assistant responds, "Yes, I'm here. How can I help you?"

2. **Ask Questions**
   - General queries (e.g., "Who invented the telephone?") are answered from the knowledge base first.
   - Wikipedia queries (e.g., "Tell me about Python from Wikipedia") fetch summaries from Wikipedia.
   - The assistant extracts topics (e.g., "Python", "History of Python") and provides concise summaries.

3. **Deactivate**
   - Say "Ok thank you" to return to idle mode.

4. **Example Interaction**
   ```
   You: Hey bro
   Assistant: Yes, I'm here. How can I help you?
   You: What is the capital of France?
   Assistant: The capital of France is Paris.
   You: Tell me about the French Revolution from Wikipedia
   Assistant: French Revolution: The French Revolution was a period of radical social and political upheaval in France from 1789 to 1799...
   You: Ok thank you
   Assistant: Goodbye!
   ```

## Project Structure
```
Voice-Activated-Wikipedia-Assistant/
├── assistant.py           # Main script with voice assistant logic
├── knowledge_base.json    # Local Q&A knowledge base
├── wiki_cache.json        # Cache for Wikipedia summaries
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Troubleshooting
- **Speech Recognition Errors**:
  - Ensure your microphone is functional and selected as the default input device.
  - Check for `sr.RequestError`: Verify internet connectivity for Google Speech Recognition API.
  - If `sr.UnknownValueError` occurs frequently, reduce background noise or adjust `recognizer.adjust_for_ambient_noise` duration.

- **Text-to-Speech Issues**:
  - On Linux, install `espeak` or `pulseaudio`: `sudo apt-get install espeak pulseaudio`.
  - Ensure speakers are connected and not muted.

- **spaCy Model Errors**:
  - Confirm `en_core_web_sm` is installed: `python -m spacy download en_core_web_sm`.
  - Use Python 3.8–3.10 for compatibility.

- **Wikipedia API Errors**:
  - Check internet connectivity for Wikipedia queries.
  - If disambiguation fails, rephrase the query to be more specific (e.g., "French Revolution" instead of "Revolution").

- **Dependency Installation Issues**:
  - Upgrade pip: `pip install --upgrade pip setuptools wheel`.
  - Install packages individually if `requirements.txt` fails.
  - Clear pip cache if disk space is low: `pip cache purge`.

- **Performance Tips**:
  - Reduce `SUMMARY_WORD_LIMIT` or `TOTAL_WORD_LIMIT` in `assistant.py` for faster responses.
  - Clear `wiki_cache.json` if it grows too large.
  - Use a lightweight spaCy model (`en_core_web_sm`) to minimize memory usage.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m 'Add your feature'`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Open a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments
- `speech_recognition`: For voice input processing.
- `pyttsx3`: For text-to-speech functionality.
- `spaCy`: For NLP and topic extraction.
- `wikipedia-api` and `wikipedia`: For Wikipedia integration.
- `nltk`: For sentence tokenization.
- Built with ❤️ by Sohaib Zafar

**Last updated**: June 2025
