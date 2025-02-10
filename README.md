# AIVisionnaire

This project implements Visionnaire, a personalized AI Assistant with flexibility and persistent memory using GPT-4o. The whole project is built using Python 3.9.

# Set up and Installation

### Run Project in a local system environment 

The project can be run in a local system environment. For that purpose a conda environment should be created (**python 3.9**) to preserve the existant packages and dependencies in the system. The requirementstwo file should then be run in the environment to import the required libraries for the project. Once packages are imported the project can be run.

1. Clone the repository
```bash
git clone https://github.com/TSQCH/AIVisionnaire.git

cd AIVisionnaire
```

2. Set up the application and install relevant libraries
```bash
conda create --name py39 python=3.9

source activate py39

pip install -r requirementstwo.txt
```

3. Configure environment variables:

Backend (.env):
```env
OPENAI_API_KEY=your_openai_key
PINECONE_INDEX_NAME=your_pinecone_indexname
PINECONE_API_KEY=your_pinecone_apikey
PINECONE_ENV=your_pinecone_env
```

4. Run the application
```bash
python gradio-frontend.py
```

## Libraries

### Frontend
- Gradio

### Backend
- Langchain
- Pinecone
- OpenAI
- Tiktoken

### Prerequisites
- Python 3.9 or Python 3.10
- Pinecone Vector Database
- API keys for:
  - Pinecone
  - OpenAI
  
## Project Structure

```
.
├── data/               # data folder to record users registered with the chatbot
│   ├── users.csv
│── assistant.py        # python file containing the backend pipeline of the chatbot's functionalities
│── gradio-fronend.py   # python file containing the frontend features of the chatbot
│── requirementstwo.txt # text file containing the libraries required to run the application
```
