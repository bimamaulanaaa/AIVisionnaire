# AI Visionnaire

An AI-powered chat application with secure authentication using Firebase.

## Features

- Secure authentication with Firebase Authentication
- AI chat capabilities using OpenAI
- Vector storage with Pinecone
- Modern UI with Gradio

## Prerequisites

- Python 3.8 or higher
- Firebase project with Email/Password authentication enabled
- OpenAI API key
- Pinecone API key

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd AIVisionnaire
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirementstwo.txt
```

4. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

5. Update the `.env` file with your:
   - OpenAI API key
   - Pinecone API key and settings
   - Firebase API key

## Running the Application

```bash
python gradio-frontend.py
```

The application will be available at `http://localhost:7860`

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENV`: Your Pinecone environment
- `PINECONE_INDEX_NAME`: Your Pinecone index name
- `FIREBASE_API_KEY`: Your Firebase project Web API key

## Project Structure

- `gradio-frontend.py`: Main application file with Gradio UI
- `auth_handler.py`: Authentication handling with Firebase
- `auth_config.py`: Firebase configuration
- `assistant.py`: AI chat functionality
- `requirementstwo.txt`: Python dependencies

## Security Notes

- Never commit your `.env` file
- Keep your API keys secure
- Use environment variables for sensitive data

## License

[Your License Here]
