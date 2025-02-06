import os
import json
import csv
import langchain
import pinecone
import pandas as pd
from datetime import datetime
from pinecone import Pinecone as PineconeClient
from langchain_pinecone import PineconeVectorStore
from langchain.schema import AIMessage, HumanMessage
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())
openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
PineconeClient.api_key = os.environ["PINECONE_API_KEY"]
PineconeClient.environment = os.environ["PINECONE_ENV"]
PineconeClient.index = os.environ["PINECONE_INDEX_NAME"]
pinecone = PineconeClient(api_key = PineconeClient.api_key, environment = PineconeClient.environment)
index = pinecone.Index(PineconeClient.index)
llm = ChatOpenAI(model="gpt-4o", temperature=0)
vector_store = PineconeVectorStore(index, embeddings, "text")


template = """
You are a chatbot. Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question:
------
<ctx>
{context}
</ctx>
------
<hs>
{history}
</hs>
------
{question}
Answer:
"""

prompt = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=template,
)


def validate_user(user_id: str) -> tuple:    
    """Validate user ID against the CSV file."""
    
    
    with open('data/users.csv', 'r') as read_obj:
        csv_reader = csv.reader(read_obj)
        list_of_rows = list(csv_reader)
        list_of_rows = list_of_rows[1:]
        for row in list_of_rows:
            for value in range(0, 1):
                if(row[value]) == user_id:
                    print(row[value], row)
                    return "True", "Login successful! Welcome to the chatbot."
        return False, "Invalid user ID. Please try again."        


def register_user(name: str):        
    """Register a new user with preferences."""
    
    
    try:
        # Generate a new user ID
        user_data_df = pd.read_csv('data/users.csv')
        new_user_id = f"USER{len(user_data_df) + 1:03d}"
            
        # Create new user data
        new_user = pd.DataFrame({
                'user_id': [new_user_id],
                'name': [name]
        })
            
        # Append to existing users
        user_data_df = pd.concat([user_data_df, new_user], ignore_index=True)            
        # Save updated users to CSV
        user_data_df.to_csv('data/users.csv', index=False)            
        return True, f"Registration successful! Your User ID is: {new_user_id}"
    
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


def get_user_chat_history(user_id):
    "Retrieve user chat history from pinecone"
    
    
    try:
        results = index.query(vector=[0] * 1536, filter={"user_id": user_id}, top_k=1000, include_metadata=True)    
        history = []
        sorted_matches = sorted(results["matches"], key=lambda x: x["metadata"].get("timestamp", ""))
        for result in sorted_matches:
            human_message = result["metadata"].get("human_message", "")
            ai_message = result["metadata"].get("ai_message", "")
            if human_message:
                history.append(HumanMessage(content=human_message))
            if ai_message:
                history.append(AIMessage(content=ai_message))
        return history
    except Exception as e:
        print(f"Error retrieving chat history for user {user_id}: {e}")
        return []  # Return empty history if there is an error


def store_chat_in_pinecone(user_id, human_message, ai_message):
    "Store user chats in pinecone"
    
    
    unique_id = f"{user_id}_{datetime.utcnow().isoformat()}"
    vector = embeddings.embed_query(human_message)

    if not vector or not isinstance(vector, list):
        raise ValueError(f"Invalid vector generated: {vector}")

    metadata = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "human_message": human_message,
        "ai_message": ai_message,
    }

    print(f"Upserting with ID: {unique_id}, Vector Length: {len(vector)}, Metadata: {metadata}")

    # Upsert the data into Pinecone
    try:
        index.upsert(
            vectors=[(unique_id, vector, metadata)]
        )
    except Exception as e:
        raise ValueError(f"Error during Pinecone upsert: {e}")


def predict(message, history, user_id):
    """Handles user input, retrieves previous chat history, and generates a response using LangChain."""


    previous_history = get_user_chat_history(user_id)
    print("Previous history:", previous_history)

    # Format current session history for LangChain
    current_history = []
    for human, ai in history:
        current_history.append(HumanMessage(content=human))
        current_history.append(AIMessage(content=ai))
    
    print("Current history:", current_history)

    if(previous_history == current_history):
        full_history = current_history
    else:
        full_history = previous_history
    
    full_history.append(HumanMessage(content=message))

    print("Full history:", full_history)

    # Create QA system with the combined history
    memory = ConversationBufferMemory(
        memory_key="history",
        input_key="question"
    )
    memory.chat_memory.messages = full_history

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(namespace=user_id),
        chain_type_kwargs={
            "verbose": True,
            "prompt": prompt,
            "memory": memory
        },
    )

    try:
        answer = qa.run(message)
    except Exception as e:
        print(f"Error during response generation: {e}")
        answer = f"Error during response generation: {e}"
    
    try:
        store_chat_in_pinecone(user_id, message, answer)
    except Exception as e:
        print(f"Error storing chat in Pinecone: {e}")

    # Update Gradio's history with the new interaction
    history.append((message, answer))
    return history, history
