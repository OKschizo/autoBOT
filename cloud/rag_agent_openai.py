"""
OpenAI RAG Agent
Alternative to Claude for comparison
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from chromadb.errors import InvalidCollectionException
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
        # Use absolute path in Docker, relative locally
        chroma_path = "/app/chroma_db" if os.path.exists("/app/chroma_db") else "./chroma_db"
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print(f"Using local embeddings (all-MiniLM-L6-v2) at {chroma_path}")
        
        self.collection = None
        self.active_collection_name: Optional[str] = None
        self._load_collection()

    def _load_collection(self):
        """Load the best available Chroma collection and store metadata."""
        self.collection = None
        self.active_collection_name = None
        for name in ("auto_finance_complete", "auto_finance_docs"):
            try:
                collection = self.chroma_client.get_collection(
                    name=name,
                    embedding_function=self.embedding_function
                )
                self.collection = collection
                self.active_collection_name = name
                count = collection.count()
                if name == "auto_finance_complete":
                    print(f"Loaded COMPLETE collection with {count} chunks")
                    print("  (includes docs + website + blog)")
                else:
                    print(f"Loaded docs-only collection with {count} chunks")
                return
            except Exception as exc:
                print(f"[WARN] Could not load collection '{name}': {exc}")
        print("No collection found. Run scrape_all_data.py first.")
    
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
        Search for relevant chunks with source prioritization
        
        Args:
            query: Search query
            n_results: Number of results to return
            prioritize_sources: If True, prioritize website > gitbook > blog
        
        Returns:
            List of results sorted by source priority and relevance
        """
        if not self.collection:
            self._load_collection()
        if not self.collection:
            raise ValueError("Index not built. Run scrape_all_data.py first.")
        
        # Retrieve more results than needed to allow for source prioritization
        fetch_count = n_results * 3 if prioritize_sources else n_results
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_count
            )
        except InvalidCollectionException:
            print("[WARN] Active collection changed. Reloading Chroma client...")
            self._load_collection()
            if not self.collection:
                raise ValueError("Index not available. Run scrape_all_data.py first.")
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
    
    def build_index(self):
        """Build index - delegates to build_complete_index.py"""
        print("\nTo build the complete index, run:")
        print("  python scrape_all_data.py")
        print("\nThis will scrape docs + website + blog and build the index.")
        raise NotImplementedError("Use scrape_all_data.py to build complete index")
    
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
    
    def _get_seo_prompt(self) -> str:
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
    
    def ask(self, question: str, model: str = "gpt-4o-mini", 
            max_tokens: int = 2000, n_results: int = 10, system_prompt: Optional[str] = None) -> Dict:
        """
        Ask a question using OpenAI with source prioritization and SEO detection
        
        Args:
            question: User's question
            model: OpenAI model (gpt-4o-mini, gpt-4o, etc.)
            max_tokens: Max response length
            n_results: Number of chunks to retrieve
            system_prompt: Optional custom system prompt (overrides auto-detection)
        
        Returns:
            Dict with 'answer', 'sources', 'usage', etc.
        """
        if not self.client:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
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
        
        # Use custom prompt if provided, otherwise create prompt with SEO detection
        if system_prompt is None:
            if is_seo:
                system_prompt = self._get_seo_prompt()
            else:
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

LENGTH:
- Simple questions: 2-3 sentences max
- Complex questions: 4-6 sentences
- Get to the point FAST

FORMATTING:
- Use markdown for better readability: **bold** for emphasis, `code` for technical terms, lists for multiple items
- Use line breaks between paragraphs for clarity
- Format numbers and metrics clearly (e.g., **$6.32M TVL** or `14.97% APY`)"""

        # Build user prompt with source priority information
        priority_note = ""
        if source_counts['website'] > 0:
            priority_note = "Note: Website data (app.auto.finance) is LIVE and CURRENT - prioritize this information first."
        
        user_prompt = f"""Context (Auto Finance info - prioritized by source: website > GitBook > blog):
{context}

{priority_note}

Question: {question}

Answer directly and concisely using the context above. Prioritize information from website sources when available. If numbers/counts are in the context, USE THEM. Be casual. 2-4 sentences for simple questions."""

        # Call OpenAI
        print(f"Generating answer with {model}..." + (" (SEO specialist mode)" if is_seo else ""))
        
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
            'source_counts': source_counts,
            'is_seo_query': is_seo,
            'context_used': context,
            'model': model,
            'usage': {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
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
