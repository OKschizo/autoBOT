"""
Complete RAG Agent using All Data Sources
Uses: docs + website + blog data
Collection: "auto_finance_complete"
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions

try:
    import anthropic
except ImportError:
    print("Installing Anthropic SDK...")
    os.system("pip install anthropic")
    import anthropic


class CompleteRAGAgent:
    """RAG Agent using complete dataset (docs + website + blog)"""
    
    def __init__(self, data_path="scraped_data/gitbook_data.json", 
                 anthropic_api_key: Optional[str] = None):
        """
        Initialize RAG agent with complete dataset
        
        Args:
            data_path: Path to scraped data (not used, kept for compatibility)
            anthropic_api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.data_path = Path(data_path)
        
        # Setup Anthropic
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
        
        # Setup ChromaDB with local embeddings
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print("Using local embeddings (all-MiniLM-L6-v2)")
        
        # Try to load complete collection first, fall back to docs-only
        try:
            self.collection = self.chroma_client.get_collection(
                name="auto_finance_complete",
                embedding_function=self.embedding_function
            )
            print(f"Loaded COMPLETE collection with {self.collection.count()} chunks")
            print("  (includes docs + website + blog)")
        except:
            # Fall back to docs-only
            try:
                self.collection = self.chroma_client.get_collection(
                    name="auto_finance_docs",
                    embedding_function=self.embedding_function
                )
                print(f"Loaded docs-only collection with {self.collection.count()} chunks")
                print("  (Run scrape_all_data.py to build complete collection)")
            except:
                self.collection = None
                print("No collection found. Run scrape_all_data.py first.")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documentation chunks"""
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
    
    def ask(self, question: str, model: str = "claude-sonnet-4-20250514", 
            max_tokens: int = 2000, n_results: int = 8) -> Dict:
        """
        Ask a question using Claude
        
        Args:
            question: User's question
            model: Claude model to use
            max_tokens: Max response length
        
        Returns:
            Dict with 'answer', 'sources', 'usage', etc.
        """
        if not self.client:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        # Retrieve relevant chunks
        print(f"Searching for: {question}")
        results = self.search(question, n_results=n_results)
        
        # Build context from results
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
        
        # Create prompt for Claude
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
- Like a knowledgeable friend explaining

REFERRING TO AUTO FINANCE:
- Say "Auto Finance has..." or "Autopools work by..." or just name the feature directly
- DON'T say "their autopools" or "the project's TVL" or "their system"
- DO say "plasmaUSD has..." or "Auto Finance offers..." or "Autopools use..."

KNOWLEDGE:
- Answer from your general DeFi knowledge
- Use the provided context for Auto Finance specifics
- The context contains REAL DATA from the website - use it!
- If specific numbers/counts are in the context, USE THEM
- Don't say "I don't know" if the answer is clearly in the context

LENGTH:
- Simple questions: 2-3 sentences max
- Complex questions: 4-6 sentences
- Get to the point FAST

EXAMPLES:

Bad: "Their plasmaUSD pool has $6.32M TVL..."
Good: "plasmaUSD has $6.32M TVL..."

Bad: "The project's autopools use rebalancing..."
Good: "Autopools use automated rebalancing..."

Bad: "Auto Finance's system integrates with..."
Good: "Auto Finance integrates with Balancer, Curve, and Aave..."

Bad: "Based on the documentation, their autopools are..."
Good: "Autopools are automated vaults that handle rebalancing and yield optimization for you."
"""

        user_prompt = f"""Context (Auto Finance info - includes LIVE DATA from the website):
{context}

Question: {question}

Answer directly and concisely using the context above. If numbers/counts are in the context, USE THEM. Be casual. 2-4 sentences for simple questions."""

        # Call Claude API
        print(f"Generating answer with {model}...")
        
        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        answer = message.content[0].text
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': context,
            'model': model,
            'usage': {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        }


def main():
    """Demo"""
    agent = CompleteRAGAgent()
    
    if agent.collection and agent.collection.count() > 0:
        print(f"\n✓ Agent ready with {agent.collection.count()} chunks")
        
        # Test search
        results = agent.search("What is the current APY?", n_results=3)
        print("\nTest search results:")
        for i, r in enumerate(results, 1):
            source = r.get('title', 'Unknown')
            print(f"  [{i}] {source}")
    else:
        print("\n! No complete collection found.")
        print("  Run: python scrape_all_data.py")


if __name__ == "__main__":
    main()
