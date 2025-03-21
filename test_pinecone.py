import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Test Pinecone connection and chat history')
parser.add_argument('--test-storage', action='store_true', help='Test storing a sample message')
parser.add_argument('--user-id', type=str, help='Specific user ID to query')
parser.add_argument('--delete', action='store_true', help='Delete test messages')
parser.add_argument('--verbose', action='store_true', help='Show detailed output')
args = parser.parse_args()

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Check required environment variables
required_vars = ["PINECONE_API_KEY", "PINECONE_INDEX_NAME", "OPENAI_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file")
    sys.exit(1)

# Initialize Pinecone
print("Initializing Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Initialize OpenAI Embeddings
print("Initializing OpenAI Embeddings...")
try:
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"ERROR: Failed to initialize OpenAI Embeddings: {str(e)}")
    sys.exit(1)

# Connect to or create index
index_name = os.getenv("PINECONE_INDEX_NAME")
print(f"Connecting to index: {index_name}")
try:
    index = pc.Index(index_name)
    print(f"✅ Successfully connected to existing Pinecone index: {index_name}")
except Exception as e:
    print(f"⚠️ Could not connect to index: {str(e)}")
    print(f"Attempting to create index: {index_name}")
    try:
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
        print(f"✅ Successfully created new Pinecone index: {index_name}")
    except Exception as create_error:
        print(f"❌ Failed to create index: {str(create_error)}")
        sys.exit(1)

# Test index stats
print("\nRetrieving index statistics...")
try:
    stats = index.describe_index_stats()
    print(f"Index size: {stats.get('total_vector_count', 'unknown')} vectors")
    print(f"Index dimension: {stats.get('dimension', 'unknown')}")
    namespaces = stats.get('namespaces', {})
    if namespaces:
        print(f"Namespaces: {json.dumps(namespaces, indent=2)}")
    else:
        print("No namespaces found")
except Exception as e:
    print(f"❌ Failed to get index stats: {str(e)}")

# Query the index for user data
def query_user_data(user_id=None):
    print("\nQuerying for chat history...")
    try:
        # Prepare filter if user_id is provided
        filter_dict = {"user_id": user_id} if user_id else None
        filter_msg = f" for user '{user_id}'" if user_id else ""
        
        print(f"Querying data{filter_msg}...")
        
        # Use a dummy vector to query based on metadata
        results = index.query(
            vector=[0] * 1536,
            filter=filter_dict,
            top_k=100,
            include_metadata=True
        )
        
        # Check if there are any results
        if not results.matches:
            print(f"No data found in the index{filter_msg}.")
            return []
        else:
            print(f"Found {len(results.matches)} records{filter_msg}")
            
            # Count unique users
            users = set()
            for match in results.matches:
                if "user_id" in match.metadata:
                    users.add(match.metadata["user_id"])
            
            print(f"Found data for {len(users)} unique users: {users}")
            
            # Show samples of data if verbose is enabled
            if args.verbose:
                print("\nSample records:")
                for i, match in enumerate(results.matches[:5]):  # Show up to 5 samples
                    print(f"\nRecord {i+1}:")
                    print(f"ID: {match.id}")
                    print(f"User ID: {match.metadata.get('user_id', 'N/A')}")
                    print(f"Timestamp: {match.metadata.get('timestamp', 'N/A')}")
                    print(f"Human Message: {match.metadata.get('human_message', 'N/A')[:100]}...")
                    print(f"AI Message: {match.metadata.get('ai_message', 'N/A')[:100]}...")
            
            return results.matches
            
    except Exception as e:
        print(f"❌ Error querying Pinecone: {str(e)}")
        return []

# Test storing a message
def test_storage():
    print("\nTesting message storage...")
    
    test_user_id = args.user_id or "test_user"
    test_human_msg = "This is a test message from the Pinecone test script"
    test_ai_msg = "This is a test response from the Pinecone test script"
    
    try:
        # Create unique ID and timestamp
        timestamp = datetime.utcnow().isoformat()
        unique_id = f"{test_user_id}_test_{timestamp}"
        
        # Generate vector embedding
        vector = embeddings.embed_query(test_human_msg)
        
        # Prepare metadata
        metadata = {
            "user_id": test_user_id,
            "timestamp": timestamp,
            "human_message": test_human_msg,
            "ai_message": test_ai_msg,
            "is_test": True
        }
        
        # Store in Pinecone
        print(f"Storing test message for user '{test_user_id}'...")
        index.upsert(
            vectors=[
                {
                    "id": unique_id,
                    "values": vector,
                    "metadata": metadata
                }
            ]
        )
        
        print(f"✅ Successfully stored test message with ID: {unique_id}")
        return unique_id
        
    except Exception as e:
        print(f"❌ Failed to store test message: {str(e)}")
        return None

# Delete test messages
def delete_test_messages():
    print("\nDeleting test messages...")
    try:
        # Find all test messages
        results = index.query(
            vector=[0] * 1536,
            filter={"is_test": True},
            top_k=100,
            include_metadata=True
        )
        
        if not results.matches:
            print("No test messages found to delete.")
            return
            
        # Get IDs of test messages
        test_ids = [match.id for match in results.matches]
        print(f"Found {len(test_ids)} test messages to delete.")
        
        # Delete test messages
        index.delete(ids=test_ids)
        print(f"✅ Successfully deleted {len(test_ids)} test messages.")
        
    except Exception as e:
        print(f"❌ Failed to delete test messages: {str(e)}")

# Run appropriate tests based on arguments
if args.user_id:
    print(f"Testing for specific user ID: {args.user_id}")
    
matches = query_user_data(args.user_id)

if args.test_storage:
    test_id = test_storage()
    if test_id:
        print("Verifying test message was stored...")
        # Query again to verify the test message is there
        query_user_data(args.user_id or "test_user")

if args.delete:
    delete_test_messages()

print("\nTest Summary:")
print("-------------")
print(f"✅ Pinecone connection: Success")
print(f"✅ Index '{index_name}': {'Exists' if index else 'Created'}")
if matches:
    print(f"✅ Chat history: Found {len(matches)} messages")
else:
    print(f"⚠️ Chat history: No messages found")
if args.test_storage:
    print(f"✅ Storage test: {'Completed' if test_id else 'Failed'}")
if args.delete:
    print(f"✅ Deletion test: Completed")

print("\nTesting complete!")
print("\nUsage:")
print("  Basic test: python test_pinecone.py")
print("  Test for specific user: python test_pinecone.py --user-id=<user_id>")
print("  Test storage: python test_pinecone.py --test-storage")
print("  Test and clean up: python test_pinecone.py --test-storage --delete")
print("  Verbose output: python test_pinecone.py --verbose") 