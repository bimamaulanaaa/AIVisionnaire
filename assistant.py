import os
import json
import csv
import langchain
import pinecone
import pandas as pd
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
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

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index if it doesn't exist
index_name = os.getenv("PINECONE_INDEX_NAME")
try:
    # Try to get the index first
    index = pc.Index(index_name)
except Exception:
    # If index doesn't exist, create it
    pc.create_index(
        name=index_name,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ),
        dimension=1536,  # dimensionality of text-embedding-ada-002
        metric='cosine'
    )
    index = pc.Index(index_name)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
vector_store = PineconeVectorStore(index, embeddings, "text")

template = """
You are a helpful AI assistant. Use the following context (delimited by <ctx></ctx>) and the chat history (delimited by <hs></hs>) to answer the question:
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
    try:
        with open('data/users.csv', 'r') as read_obj:
            csv_reader = csv.reader(read_obj)
            list_of_rows = list(csv_reader)
            list_of_rows = list_of_rows[1:]
            for row in list_of_rows:
                if row[0] == user_id:
                    return True, "Login successful! Welcome to the chatbot."
            return False, "Invalid user ID. Please try again."
    except Exception as e:
        return False, f"Error validating user: {str(e)}"

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
    """Retrieve user chat history from pinecone"""
    try:
        if not user_id:
            print("Warning: User ID is empty, cannot retrieve chat history")
            return []
            
        print(f"Fetching chat history for user: {user_id}")
        
        # Query with a filter for this specific user
        results = index.query(
            vector=[0] * 1536,  # Dummy vector for metadata filtering
            filter={"user_id": user_id},
            top_k=100,  # Increase to get more history
            include_metadata=True
        )
        
        # Log the number of matches found
        print(f"Found {len(results.matches)} history entries for user {user_id}")
        
        # Process the matches
        history = []
        if results.matches:
            # Sort by timestamp to get chronological order
            sorted_matches = sorted(
                results.matches, 
                key=lambda x: x.metadata.get("timestamp", "") if x.metadata else ""
            )
            
            for match in sorted_matches:
                if not match.metadata:
                    continue
                    
                human_message = match.metadata.get("human_message", "")
                ai_message = match.metadata.get("ai_message", "")
                
                if human_message:
                    history.append(HumanMessage(content=human_message))
                if ai_message:
                    history.append(AIMessage(content=ai_message))
        
        return history
    except Exception as e:
        print(f"Error retrieving chat history for user {user_id}: {e}")
        return []

def store_chat_in_pinecone(user_id, human_message, ai_message):
    """Store user chats in pinecone"""
    try:
        if not user_id:
            print("Warning: User ID is empty, cannot store chat")
            return
            
        print(f"Storing chat for user: {user_id}")
        
        # Create a unique ID for this message pair
        timestamp = datetime.utcnow().isoformat()
        unique_id = f"{user_id}_{timestamp}"
        
        # Create the embedding for the human message
        vector = embeddings.embed_query(human_message)

        # Create metadata
        metadata = {
            "user_id": user_id,
            "timestamp": timestamp,
            "human_message": human_message,
            "ai_message": ai_message,
        }

        # Upsert the data into Pinecone
        print(f"Upserting to Pinecone with ID: {unique_id}")
        index.upsert(
            vectors=[
                {
                    "id": unique_id,
                    "values": vector,
                    "metadata": metadata
                }
            ]
        )
        print(f"Successfully stored chat in Pinecone for user {user_id}")
    except Exception as e:
        print(f"Error storing chat in Pinecone: {e}")

def predict(message, history, user_id):
    """Handles user input, retrieves previous chat history, and generates a response using LangChain."""
    try:
        if not message or not user_id:
            print(f"Warning: Empty message or user_id - message: '{message}', user_id: '{user_id}'")
            if history:
                return history, history
            return [], []
            
        print(f"Processing message for user: {user_id}")
        
        # Format current session history for LangChain
        current_history = []
        for human, ai in history:
            current_history.append(HumanMessage(content=human))
            current_history.append(AIMessage(content=ai))
        
        # Get previous history from Pinecone
        print("Retrieving previous chat history from Pinecone")
        previous_history = get_user_chat_history(user_id)
        print(f"Retrieved {len(previous_history)} previous messages")
        
        # Combine histories
        full_history = previous_history + current_history
        full_history.append(HumanMessage(content=message))

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

        print("Generating response...")
        answer = qa.run(message)
        print(f"Generated response: {answer[:100]}...")
        
        # Store the interaction in Pinecone
        print("Storing conversation in Pinecone")
        store_chat_in_pinecone(user_id, message, answer)
        
        # Update Gradio's history with the new interaction
        history.append((message, answer))
        return history, history
        
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(f"Error in predict function: {error_message}")
        history.append((message, error_message))
        return history, history
