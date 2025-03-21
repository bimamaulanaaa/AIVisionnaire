import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Initialize Pinecone
print("Initializing Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Get index
index_name = os.getenv("PINECONE_INDEX_NAME")
print(f"Connecting to index: {index_name}")
index = pc.Index(index_name)

# Query the index to see what user data exists
print("\nQuerying for existing data...")
try:
    # Use a dummy vector to query based on metadata
    results = index.query(
        vector=[0] * 1536,
        top_k=10,
        include_metadata=True
    )
    
    # Check if there are any results
    if not results.matches:
        print("No data found in the index.")
    else:
        print(f"Found {len(results.matches)} records")
        
        # Count unique users
        users = set()
        for match in results.matches:
            if "user_id" in match.metadata:
                users.add(match.metadata["user_id"])
        
        print(f"Found data for {len(users)} unique users: {users}")
        
        # Show a sample of data
        if results.matches:
            sample = results.matches[0]
            print("\nSample record:")
            print(f"ID: {sample.id}")
            print(f"User ID: {sample.metadata.get('user_id', 'N/A')}")
            print(f"Timestamp: {sample.metadata.get('timestamp', 'N/A')}")
            print(f"Human Message: {sample.metadata.get('human_message', 'N/A')[:100]}...")
            print(f"AI Message: {sample.metadata.get('ai_message', 'N/A')[:100]}...")
            
except Exception as e:
    print(f"Error querying Pinecone: {e}")

print("\nTesting complete!") 