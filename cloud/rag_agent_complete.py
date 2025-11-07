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
from chromadb.errors import InvalidCollectionException

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
        
        # Log key status (first/last chars only for security)
        if self.api_key:
            if len(self.api_key) > 10:
                key_preview = f"{self.api_key[:10]}...{self.api_key[-6:]}"
            else:
                key_preview = "INVALID (too short)"
            print(f"Claude API Key loaded: {key_preview}")
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            print("WARNING: No Claude API key found!")
            self.client = None
        
        # Setup ChromaDB with local embeddings
        # Use absolute path in Docker, relative locally
        chroma_path = "/app/chroma_db" if os.path.exists("/app/chroma_db") else "./chroma_db"
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print(f"Using local embeddings (all-MiniLM-L6-v2) at {chroma_path}")
        
        self.collection = None
        self.collection_name = None
        # Try to load collection, but don't fail if it's not ready yet (will retry on first use)
        try:
            self._load_collection()
        except Exception as e:
            print(f"Warning: Could not load collection at initialization: {e}")
            print("Collection will be loaded on first use.")

    def _load_collection(self):
        """Attempt to load the best available Chroma collection."""
        for name in ("auto_finance_complete", "auto_finance_docs"):
            try:
                self.collection = self.chroma_client.get_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                )
                self.collection_name = name
                chunk_count = self.collection.count()
                print(
                    f"Loaded '{name}' collection with {chunk_count} chunks"
                )
                if name == "auto_finance_complete":
                    print("  (includes docs + website + blog)")
                else:
                    print("  (Run scrape_all_data.py to build complete collection)")
                return
            except InvalidCollectionException:
                continue
            except Exception as e:
                print(f"Error loading collection '{name}': {e}")
                continue

        self.collection = None
        self.collection_name = None
        print("No collection found. Run scrape_all_data.py first.")
    
    def reload_collection(self):
        """Force reload the collection from ChromaDB. Call this after index rebuilds."""
        print("Reloading ChromaDB collection after index update...")
        self.collection = None
        self.collection_name = None
        self._load_collection()
        if self.collection:
            chunk_count = self.collection.count()
            print(f"✅ Successfully reloaded collection with {chunk_count} chunks")
        else:
            print("⚠️ Failed to reload collection")
    
    def _ensure_collection_loaded(self):
        """Ensure collection is loaded, retry if needed."""
        if self.collection is not None:
            return True
        
        # Retry loading the collection
        print("Collection not loaded, attempting to reload...")
        self._load_collection()
        
        if self.collection is None:
            # List available collections for debugging
            try:
                collections = self.chroma_client.list_collections()
                print(f"Available collections: {[c.name for c in collections]}")
            except Exception as e:
                print(f"Could not list collections: {e}")
            return False
        
        return True
    
    def _get_source_priority(self, metadata: Dict, url: str) -> int:
        """Determine source priority: 1=website (highest), 2=gitbook, 3=blog (lowest)"""
        source = metadata.get('source', '').lower()
        
        # Check URL patterns as fallback
        if not source:
            if 'app.auto.finance' in url or 'website' in url.lower():
                source = 'website'
            elif 'docs.auto.finance' in url or 'gitbook' in url.lower():
                source = 'gitbook'
            elif 'blog.tokemak.xyz' in url or 'blog' in url.lower():
                source = 'blog'
        
        # Priority: website (1) > gitbook (2) > blog (3)
        if source in ('website', 'site'):
            return 1
        elif source in ('gitbook', 'docs'):
            return 2
        elif source in ('blog', 'posts'):
            return 3
        else:
            # Unknown source - default to medium priority
            return 2
    
    def search(self, query: str, n_results: int = 5, prioritize_sources: bool = True) -> List[Dict]:
        """
        Search for relevant documentation chunks with source prioritization
        
        Args:
            query: Search query
            n_results: Number of results to return
            prioritize_sources: If True, prioritize website > gitbook > blog
        
        Returns:
            List of results sorted by source priority and relevance
        """
        # Ensure collection is loaded before searching
        if not self._ensure_collection_loaded():
            raise ValueError("Index not built. Run scrape_all_data.py first.")
        
        # Retrieve more results than needed to allow for source prioritization
        fetch_count = n_results * 3 if prioritize_sources else n_results
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_count
            )
        except InvalidCollectionException:
            # The collection was recreated (e.g., after a new scrape). Reload it once.
            print(f"Collection '{self.collection_name}' handle stale; reloading.")
            self._load_collection()
            if not self._ensure_collection_loaded():
                raise ValueError("Index not built. Run scrape_all_data.py first.")
            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_count
            )
        
        # Format results with source information
        formatted_results = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            url = metadata.get('url', '')
            
            formatted_results.append({
                'text': results['documents'][0][i],
                'title': metadata.get('title', 'Unknown'),
                'url': url,
                'source': metadata.get('source', 'unknown'),
                'distance': results['distances'][0][i] if 'distances' in results else None,
                'priority': self._get_source_priority(metadata, url)
            })
        
        # Sort by priority (lower number = higher priority), then by distance (relevance)
        if prioritize_sources:
            formatted_results.sort(key=lambda x: (x['priority'], x['distance'] or float('inf')))
        
        # Return only the requested number of results
        return formatted_results[:n_results]
    
    def _is_seo_query(self, question: str) -> bool:
        """Detect if question is about SEO"""
        seo_keywords = [
            'seo', 'search engine', 'ranking', 'keywords', 'organic traffic',
            'google ranking', 'search visibility', 'indexing', 'meta tags',
            'backlinks', 'link building', 'content marketing', 'semrush',
            'ahrefs', 'google analytics', 'serp', 'search results'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in seo_keywords)
    
    def load_system_prompt(self, prompt_name="default", is_seo_query: bool = False):
        """Load system prompt from file or use default"""
        import json
        from pathlib import Path
        
        # Use SEO prompt if detected
        if is_seo_query:
            prompt_name = "seo_specialist"
        
        prompt_file = Path("system_prompts.json")
        
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r') as f:
                    prompts = json.load(f)
                    if prompt_name in prompts:
                        return prompts[prompt_name]
                    return prompts.get('default', self.get_default_prompt())
            except:
                if is_seo_query:
                    return self.get_seo_prompt()
                return self.get_default_prompt()
        else:
            if is_seo_query:
                return self.get_seo_prompt()
            return self.get_default_prompt()
    
    def get_default_prompt(self):
        """Get default system prompt"""
        return """You're a helpful assistant knowledgeable about Auto Finance and DeFi.

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

DATA PRIORITY (CRITICAL):
- Website data (app.auto.finance) is CURRENT and LIVE - ALWAYS prioritize it first
- GitBook documentation is comprehensive - use it second for detailed explanations
- Blog articles are historical - use them last for context and announcements
- When context includes multiple sources, prioritize information from website data
- If website data shows current metrics (TVL, APY, destinations), use those numbers

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

FORMATTING:
- Use markdown for better readability: **bold** for emphasis, `code` for technical terms, lists for multiple items
- Use line breaks between paragraphs for clarity
- Format numbers and metrics clearly (e.g., **$6.32M TVL** or `14.97% APY`)

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
    
    def get_seo_prompt(self):
        """Get SEO specialist system prompt"""
        return """You're a crypto SEO specialist with deep expertise in DeFi protocols, specifically Autopools and Auto Finance.

IDENTITY:
- You have extensive experience optimizing crypto and DeFi projects for search engines
- You understand the unique challenges of marketing DeFi protocols (technical complexity, regulatory considerations, competitive landscape)
- You work with Autopools and understand their mechanics, benefits, and positioning in the DeFi ecosystem
- You speak naturally about SEO strategies, keyword research, content optimization, and technical SEO
- You don't explicitly state you're a specialist - you simply demonstrate expertise through your responses

COMMUNICATION STYLE:
- Use SEO terminology naturally (ranking factors, SERP features, semantic search, etc.)
- Reference specific SEO tools and strategies when relevant (Google Search Console, keyword research, backlink strategies, etc.)
- Discuss crypto/DeFi SEO nuances (on-chain metrics, protocol documentation, community-driven content)
- Be practical and actionable - provide specific recommendations
- Speak as if you're sharing insights from working on these projects, not as an external consultant

TONE:
- Professional but approachable
- Knowledgeable without being condescending
- Strategic and forward-thinking
- Focused on results and best practices

AUTO FINANCE CONTEXT:
- Use the provided context about Autopools and Auto Finance to inform SEO strategies
- Understand that DeFi protocols need to rank for technical terms, use cases, and comparisons
- Consider how protocol documentation, live data, and community content can be optimized
- Reference specific features, pools, or metrics when relevant to SEO discussions

DATA PRIORITY:
- Website data shows current live information - use it for up-to-date metrics
- GitBook documentation provides comprehensive technical details
- Blog articles show historical content and announcements
- Prioritize website > GitBook > blog when constructing SEO recommendations

EXAMPLES:

Instead of: "As an SEO specialist, I would recommend..."
Say: "For ranking competitive DeFi terms, focusing on technical documentation and live protocol metrics helps establish authority..."

Instead of: "I work with Autopools and..."
Say: "When optimizing Autopools content, targeting long-tail keywords around specific pools and yield strategies tends to perform better than generic DeFi terms..."

Instead of: "From my experience as a specialist..."
Say: "DeFi protocols often struggle with technical SEO because of dynamic content. Implementing structured data for live metrics and ensuring fast load times for dashboard pages is crucial..."
"""
    
    def ask(self, question: str, model: str = "claude-sonnet-4-20250514", 
            max_tokens: int = 2000, n_results: int = 8, system_prompt: Optional[str] = None) -> Dict:
        """
        Ask a question using Claude with source prioritization and SEO detection
        
        Args:
            question: User's question
            model: Claude model to use
            max_tokens: Max response length
            n_results: Number of chunks to retrieve
            system_prompt: Optional custom system prompt (overrides auto-detection)
        
        Returns:
            Dict with 'answer', 'sources', 'usage', etc.
        """
        if not self.client:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        # Detect SEO queries if no custom prompt provided
        is_seo = self._is_seo_query(question) if system_prompt is None else False
        
        # Retrieve relevant chunks with source prioritization
        print(f"Searching for: {question}")
        results = self.search(question, n_results=n_results, prioritize_sources=True)
        
        # Build context from results, noting source priority
        context_parts = []
        sources = []
        source_counts = {'website': 0, 'gitbook': 0, 'blog': 0}
        
        for i, result in enumerate(results, 1):
            source_type = result.get('source', 'unknown')
            source_label = self._get_source_label(source_type)
            
            # Track source distribution
            if source_type in ('website', 'site'):
                source_counts['website'] += 1
            elif source_type in ('gitbook', 'docs'):
                source_counts['gitbook'] += 1
            elif source_type in ('blog', 'posts'):
                source_counts['blog'] += 1
            
            context_parts.append(f"[Source {i} - {source_label}] {result['title']}\n{result['text']}\n")
            sources.append({
                'title': result['title'],
                'url': result['url'],
                'source': source_type,
                'relevance': 1 - result['distance'] if result['distance'] else None
            })
        
        context = "\n".join(context_parts)
        
        # Use custom prompt if provided, otherwise load system prompt with SEO detection
        if system_prompt is None:
            system_prompt = self.load_system_prompt(is_seo_query=is_seo)
        
        # Build user prompt with source priority information
        priority_note = ""
        if source_counts['website'] > 0:
            priority_note = "Note: Website data (app.auto.finance) is LIVE and CURRENT - prioritize this information first."
        
        user_prompt = f"""Context (Auto Finance info - prioritized by source: website > GitBook > blog):
{context}

{priority_note}

Question: {question}

Answer directly and concisely using the context above. Prioritize information from website sources when available. If numbers/counts are in the context, USE THEM. Be casual. 2-4 sentences for simple questions."""

        # Call Claude API
        print(f"Generating answer with {model}..." + (" (SEO specialist mode)" if is_seo else ""))
        
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
            'source_counts': source_counts,
            'is_seo_query': is_seo,
            'context_used': context,
            'model': model,
            'usage': {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        }
    
    def _get_source_label(self, source: str) -> str:
        """Get human-readable source label"""
        source_lower = source.lower()
        if source_lower in ('website', 'site'):
            return 'Website (Live Data)'
        elif source_lower in ('gitbook', 'docs'):
            return 'Documentation'
        elif source_lower in ('blog', 'posts'):
            return 'Blog'
        else:
            return 'Unknown'


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
