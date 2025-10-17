"""
OpenAI RAG Agent
Alternative to Claude for comparison
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# FORCE reload .env to get latest keys
load_dotenv(override=True)

try:
    from openai import OpenAI
except ImportError:
    print("Installing OpenAI...")
    os.system("pip install openai")
    from openai import OpenAI


class OpenAIRAGAgent:
    """RAG Agent using OpenAI GPT models"""
    
    def __init__(self, data_path="scraped_data/gitbook_data.json", 
                 openai_api_key: Optional[str] = None):
        """
        Initialize RAG agent with OpenAI
        
        Args:
            data_path: Path to scraped data
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.data_path = Path(data_path)
        
        # FORCE reload environment
        load_dotenv(override=True)
        
        # Setup OpenAI
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        # DEBUG: Show exactly what we got
        print(f"[DEBUG] OpenAI key from env: {repr(os.getenv('OPENAI_API_KEY'))}")
        
        # Log key status (first/last chars only for security)
        if self.api_key:
            # Remove any whitespace or quotes
            self.api_key = self.api_key.strip().strip('"').strip("'")
            
            if len(self.api_key) > 20 and self.api_key.startswith('sk-'):
                key_preview = f"{self.api_key[:10]}...{self.api_key[-6:]}"
                print(f"[OK] OpenAI API Key loaded: {key_preview} (length: {len(self.api_key)})")
                self.client = OpenAI(api_key=self.api_key)
            else:
                print(f"[ERROR] Invalid OpenAI key format: {self.api_key[:20]}... (length: {len(self.api_key)})")
                self.client = None
        else:
            print("[ERROR] No OpenAI API key found in environment!")
            print(f"[DEBUG] All env vars with 'OPENAI': {[k for k in os.environ.keys() if 'OPENAI' in k]}")
            self.client = None
        
        # Setup ChromaDB with local embeddings
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print("Using local embeddings (all-MiniLM-L6-v2)")
        
        # Try to load complete collection
        try:
            self.collection = self.chroma_client.get_collection(
                name="auto_finance_complete",
                embedding_function=self.embedding_function
            )
            print(f"Loaded COMPLETE collection with {self.collection.count()} chunks")
            print("  (includes docs + website + blog)")
        except:
            try:
                self.collection = self.chroma_client.get_collection(
                    name="auto_finance_docs",
                    embedding_function=self.embedding_function
                )
                print(f"Loaded docs-only collection with {self.collection.count()} chunks")
            except:
                self.collection = None
                print("No collection found. Run scrape_all_data.py first.")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant chunks"""
        if not self.collection:
            raise ValueError("Index not built. Run scrape_all_data.py first.")
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'text': results['documents'][0][i],
                'title': results['metadatas'][0][i]['title'],
                'url': results['metadatas'][0][i]['url'],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def build_index(self):
        """Build index - delegates to build_complete_index.py"""
        print("\nTo build the complete index, run:")
        print("  python scrape_all_data.py")
        print("\nThis will scrape docs + website + blog and build the index.")
        raise NotImplementedError("Use scrape_all_data.py to build complete index")
    
    def ask(self, question: str, model: str = "gpt-4o-mini", 
            max_tokens: int = 2000, n_results: int = 10) -> Dict:
        """
        Ask a question using OpenAI
        
        Args:
            question: User's question
            model: OpenAI model (gpt-4o-mini, gpt-4o, etc.)
            max_tokens: Max response length
            n_results: Number of chunks to retrieve
        
        Returns:
            Dict with 'answer', 'sources', 'usage', etc.
        """
        if not self.client:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Retrieve relevant chunks
        print(f"Searching for: {question}")
        results = self.search(question, n_results=n_results)
        
        # Build context
        context_parts = []
        sources = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}] {result['title']}\n{result['text']}\n")
            sources.append({
                'title': result['title'],
                'url': result['url'],
                'relevance': 1 - result['distance'] if result['distance'] else None
            })
        
        context = "\n".join(context_parts)
        
        # Create prompt (same style as Claude version)
        system_prompt = """You're a helpful assistant knowledgeable about Auto Finance and DeFi.

CRITICAL RULES:
- NEVER say "from the docs" or "the documentation shows" or "according to"
- NEVER say "their" or "the project" when referring to Auto Finance
- Be CONCISE - get to the point quickly (2-4 sentences for simple questions)
- Sound natural and conversational

TONE:
- Casual and friendly
- Direct and to the point
- No formality or corporate speak

REFERRING TO AUTO FINANCE:
- Say "Auto Finance has..." or "Autopools work by..." or just name the feature directly
- DON'T say "their autopools" or "the project's TVL"
- DO say "plasmaUSD has..." or "Auto Finance offers..."

KNOWLEDGE:
- Answer from your general DeFi knowledge
- Use the provided context for Auto Finance specifics
- The context contains REAL DATA from the website - use it!
- If specific numbers/counts are in the context, USE THEM

LENGTH:
- Simple questions: 2-3 sentences max
- Complex questions: 4-6 sentences
- Get to the point FAST"""

        user_prompt = f"""Context (Auto Finance info - includes LIVE DATA):
{context}

Question: {question}

Answer directly and concisely using the context above. If numbers/counts are in the context, USE THEM. Be casual. 2-4 sentences for simple questions."""

        # Call OpenAI
        print(f"Generating answer with {model}...")
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context,
            'model': model,
            'usage': {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }


def main():
    """Demo"""
    agent = OpenAIRAGAgent()
    
    if agent.collection and agent.collection.count() > 0:
        print(f"\nAgent ready with {agent.collection.count()} chunks")
        
        # Test search
        results = agent.search("What are autopools?", n_results=3)
        print("\nTest search:")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r['title']}")
    else:
        print("\nNo collection found. Run scrape_all_data.py first.")


if __name__ == "__main__":
    main()

