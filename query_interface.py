#!/usr/bin/env python3
"""
Query Interface for Nelson Textbook Database
Provides semantic search capabilities over the uploaded data
"""

import os
import json
from typing import List, Dict, Any
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NelsonQueryInterface:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def semantic_search(self, query: str, table: str = 'nelson_textbook', limit: int = 5, threshold: float = 0.7) -> List[Dict]:
        """Perform semantic search using embeddings"""
        
        # Generate embedding for query
        query_embedding = self.generate_query_embedding(query)
        if not query_embedding:
            return []
        
        try:
            # Use the match_documents function
            result = self.supabase.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_table': table,
                'match_count': limit,
                'similarity_threshold': threshold
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error performing semantic search: {e}")
            return []

    def keyword_search(self, keywords: List[str], table: str = 'nelson_textbook', limit: int = 10) -> List[Dict]:
        """Perform keyword-based search"""
        try:
            if table == 'nelson_textbook':
                result = self.supabase.table(table).select('*').contains('keywords', keywords).limit(limit).execute()
            else:
                # For other tables, search in content
                query = self.supabase.table(table).select('*')
                for keyword in keywords:
                    query = query.ilike('content', f'%{keyword}%')
                result = query.limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error performing keyword search: {e}")
            return []

    def search_by_category(self, category: str, table: str = 'nelson_textbook', limit: int = 10) -> List[Dict]:
        """Search by medical category"""
        try:
            if table == 'nelson_textbook':
                result = self.supabase.table(table).select('*').eq('medical_category', category).limit(limit).execute()
            else:
                result = self.supabase.table(table).select('*').eq('category', category).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error searching by category: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Count records in each table
            nelson_count = self.supabase.table('nelson_textbook').select('id', count='exact').execute()
            resources_count = self.supabase.table('pediatric_medical_resources').select('id', count='exact').execute()
            sessions_count = self.supabase.table('chat_sessions').select('id', count='exact').execute()
            messages_count = self.supabase.table('chat_messages').select('id', count='exact').execute()
            
            stats['nelson_textbook_count'] = nelson_count.count
            stats['pediatric_resources_count'] = resources_count.count
            stats['chat_sessions_count'] = sessions_count.count
            stats['chat_messages_count'] = messages_count.count
            
            # Get categories
            categories = self.supabase.table('nelson_textbook').select('medical_category').execute()
            unique_categories = list(set([item['medical_category'] for item in categories.data]))
            stats['categories'] = unique_categories
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

    def interactive_search(self):
        """Interactive search interface"""
        print("🔍 Nelson Textbook Interactive Search")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Semantic search")
            print("2. Keyword search")
            print("3. Category search")
            print("4. Database statistics")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                query = input("Enter your search query: ").strip()
                if query:
                    results = self.semantic_search(query)
                    self.display_results(results, "Semantic Search")
            
            elif choice == '2':
                keywords_input = input("Enter keywords (comma-separated): ").strip()
                if keywords_input:
                    keywords = [k.strip() for k in keywords_input.split(',')]
                    results = self.keyword_search(keywords)
                    self.display_results(results, "Keyword Search")
            
            elif choice == '3':
                category = input("Enter medical category: ").strip()
                if category:
                    results = self.search_by_category(category)
                    self.display_results(results, "Category Search")
            
            elif choice == '4':
                stats = self.get_statistics()
                self.display_statistics(stats)
            
            elif choice == '5':
                print("Goodbye! 👋")
                break
            
            else:
                print("Invalid choice. Please try again.")

    def display_results(self, results: List[Dict], search_type: str):
        """Display search results"""
        print(f"\n📊 {search_type} Results ({len(results)} found)")
        print("=" * 60)
        
        if not results:
            print("No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Chapter: {result.get('chapter', 'N/A')}")
            print(f"   Section: {result.get('section', 'N/A')}")
            print(f"   Category: {result.get('medical_category', result.get('category', 'N/A'))}")
            
            if 'similarity' in result:
                print(f"   Similarity: {result['similarity']:.3f}")
            
            content = result.get('content', '')
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"   Content: {content}")
            print("-" * 40)

    def display_statistics(self, stats: Dict[str, Any]):
        """Display database statistics"""
        print("\n📈 Database Statistics")
        print("=" * 30)
        
        print(f"Nelson Textbook entries: {stats.get('nelson_textbook_count', 0)}")
        print(f"Medical resources: {stats.get('pediatric_resources_count', 0)}")
        print(f"Chat sessions: {stats.get('chat_sessions_count', 0)}")
        print(f"Chat messages: {stats.get('chat_messages_count', 0)}")
        
        categories = stats.get('categories', [])
        if categories:
            print(f"\nAvailable categories ({len(categories)}):")
            for category in sorted(categories):
                print(f"  • {category}")

if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.getenv('SUPABASE_SERVICE_KEY'):
        print("Error: SUPABASE_SERVICE_KEY not found in environment variables")
        exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not found. Semantic search will not work.")
    
    interface = NelsonQueryInterface()
    interface.interactive_search()

