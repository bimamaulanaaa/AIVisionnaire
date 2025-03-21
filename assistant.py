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
    print(f"Connected to existing Pinecone index: {index_name}")
except Exception as e:
    # If index doesn't exist, create it
    print(f"Creating new Pinecone index: {index_name}")
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
        print(f"Retrieving chat history for user: {user_id}")
        
        # Check if user_id is valid
        if not user_id:
            print("Warning: Empty user_id provided to get_user_chat_history")
            return []
        
        # Query Pinecone for user's chat history
        results = index.query(
            vector=[0] * 1536,  # Dummy vector for metadata filtering
            filter={"user_id": user_id},
            top_k=1000,
            include_metadata=True
        )
        
        # Check if we got any results
        if not results.matches:
            print(f"No chat history found for user: {user_id}")
            return []
            
        print(f"Retrieved {len(results.matches)} history items for user: {user_id}")
        
        # Process and sort the history by timestamp
        history = []
        try:
            sorted_matches = sorted(results.matches, key=lambda x: x.metadata.get("timestamp", ""))
            
            for match in sorted_matches:
                human_message = match.metadata.get("human_message", "")
                ai_message = match.metadata.get("ai_message", "")
                timestamp = match.metadata.get("timestamp", "unknown")
                
                print(f"History item from {timestamp}: Human: '{human_message[:30]}...'")
                
                if human_message:
                    history.append(HumanMessage(content=human_message))
                if ai_message:
                    history.append(AIMessage(content=ai_message))
        except Exception as sorting_error:
            print(f"Error sorting history: {sorting_error}")
            
        return history
    except Exception as e:
        print(f"Error retrieving chat history for user {user_id}: {e}")
        return []

def store_chat_in_pinecone(user_id, human_message, ai_message):
    """Store user chats in pinecone"""
    try:
        # Validate inputs
        if not user_id:
            print("Warning: Empty user_id provided to store_chat_in_pinecone")
            return
            
        if not human_message or not ai_message:
            print("Warning: Empty message provided to store_chat_in_pinecone")
            return
            
        # Create a unique ID for this chat entry
        unique_id = f"{user_id}_{datetime.utcnow().isoformat()}"
        timestamp = datetime.utcnow().isoformat()
        
        print(f"Storing chat for user {user_id} with ID {unique_id}")
        
        # Create the vector from the human message
        vector = embeddings.embed_query(human_message)

        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "timestamp": timestamp,
            "human_message": human_message,
            "ai_message": ai_message,
        }

        # Upsert the data into Pinecone
        index.upsert(
            vectors=[
                {
                    "id": unique_id,
                    "values": vector,
                    "metadata": metadata
                }
            ]
        )
        
        print(f"Successfully stored chat in Pinecone with ID: {unique_id}")
    except Exception as e:
        print(f"Error storing chat in Pinecone: {e}")

def predict(message, history, user_id):
    """Handles user input, retrieves previous chat history, and generates a response using LangChain."""
    try:
        print(f"Processing message for user: {user_id}")
        
        # Validate inputs
        if not user_id:
            print("Warning: Empty user_id provided to predict")
            error_message = "Session error: User ID not found. Please log in again."
            history.append((message, error_message))
            return history, history
            
        if not message.strip():
            print("Warning: Empty message provided to predict")
            return history, history
        
        # Format current session history for LangChain
        current_history = []
        for human, ai in history:
            current_history.append(HumanMessage(content=human))
            current_history.append(AIMessage(content=ai))
        
        # Get previous history from Pinecone
        previous_history = get_user_chat_history(user_id)
        
        # Log history information for debugging
        print(f"Current session history length: {len(current_history)} messages")
        print(f"Previous history length: {len(previous_history)} messages")
        
        # Combine histories - most recent messages have more importance
        # Limit history length to prevent token limit issues
        max_history_items = 20  # Adjust as needed
        full_history = previous_history[-max_history_items:] if previous_history else []
        full_history.extend(current_history)
        full_history.append(HumanMessage(content=message))

        # Create memory from the combined history
        memory = ConversationBufferMemory(
            memory_key="history",
            input_key="question"
        )
        memory.chat_memory.messages = full_history

        # Create QA system
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            chain_type_kwargs={
                "verbose": True,
                "prompt": prompt,
                "memory": memory
            },
        )

        # Generate the response
        print(f"Generating answer for: '{message[:50]}...'")
        answer = qa.run(message)
        print(f"Generated answer: '{answer[:50]}...'")
        
        # Store the interaction in Pinecone for future reference
        print("Storing chat in Pinecone...")
        store_chat_in_pinecone(user_id, message, answer)

        # Update Gradio's history with the new interaction
        history.append((message, answer))
        return history, history
        
    except Exception as e:
        print(f"Error in predict function: {str(e)}")
        error_message = f"Error generating response: {str(e)}"
        history.append((message, error_message))
        return history, history
