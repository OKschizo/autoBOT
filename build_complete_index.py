"""
Build complete index merging docs + website + blog
Creates new collection: "auto_finance_complete"
Keeps original "auto_finance_docs" untouched
"""

import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import time


class CompleteIndexBuilder:
    """Builds complete index with all data sources"""
    
    def __init__(self):
        self.chunker_size = 800
        self.chunker_overlap = 100
        
        # Setup ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        print("Using local embeddings (all-MiniLM-L6-v2)")
    
    def load_docs_data(self):
        """Load existing documentation data"""
        docs_path = Path("scraped_data/gitbook_data.json")
        
        if not docs_path.exists():
            print("Warning: No docs data found")
            return []
        
        with open(docs_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)
        
        print(f"Loaded {len(docs)} documentation pages")
        return docs
    
    def load_website_data(self):
        """Load website data"""
        website_path = Path("scraped_data/website/website_data.json")
        
        if not website_path.exists():
            print("Warning: No website data found")
            return []
        
        with open(website_path, 'r', encoding='utf-8') as f:
            website = json.load(f)
        
        print(f"Loaded {len(website)} website pages")
        return website
    
    def load_blog_data(self):
        """Load blog data"""
        blog_path = Path("scraped_data/blog/blog_posts.json")
        
        if not blog_path.exists():
            print("Warning: No blog data found")
            return []
        
        with open(blog_path, 'r', encoding='utf-8') as f:
            blog = json.load(f)
        
        print(f"Loaded {len(blog)} blog posts")
        return blog
    
    def chunk_content(self, content, title, url, metadata=None):
        """Chunk content into smaller pieces"""
        chunks = []
        
        if len(content) <= self.chunker_size:
            return [{
                'text': content,
                'title': title,
                'url': url,
                'metadata': metadata or {}
            }]
        
        # Split by paragraphs
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_id = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunker_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'title': title,
                    'url': url,
                    'chunk_id': chunk_id,
                    'metadata': metadata or {}
                })
                
                # Keep overlap
                words = current_chunk.split()
                overlap_text = ' '.join(words[-self.chunker_overlap:]) if len(words) > self.chunker_overlap else ""
                current_chunk = overlap_text + "\n\n" + para
                chunk_id += 1
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'title': title,
                'url': url,
                'chunk_id': chunk_id,
                'metadata': metadata or {}
            })
        
        return chunks
    
    def prepare_all_chunks(self):
        """Prepare all data for indexing"""
        all_chunks = []
        
        # Load all data
        docs = self.load_docs_data()
        website = self.load_website_data()
        blog = self.load_blog_data()
        
        print("\nChunking documentation...")
        for doc in docs:
            chunks = self.chunk_content(
                doc['content'],
                doc['title'],
                doc['url'],
                {'source': 'docs', 'headings': doc.get('headings', [])}
            )
            all_chunks.extend(chunks)
        
        print(f"  Created {len(all_chunks)} doc chunks")
        
        # Chunk website data
        print("\nChunking website pages...")
        website_chunk_start = len(all_chunks)
        for page in website:
            metadata = {
                'source': 'website',
                'scraped_at': page.get('scraped_at')
            }
            
            # Add pool data if available
            if page.get('pool_data'):
                metadata['pool_data'] = page['pool_data']
                
                # BUILD A SUMMARY with pool stats AT THE TOP
                pool_summary = ""
                
                # Individual pool page
                if '/pools/' in page['url']:
                    pool_name = page['url'].split('/pools/')[-1]
                    pool_summary = f"\n=== {pool_name.upper()} AUTOPOOL ===\n"
                    
                    # Basic metrics
                    if 'apy' in page['pool_data']:
                        pool_summary += f"APY: {page['pool_data']['apy']}\n"
                    if 'tvl' in page['pool_data']:
                        pool_summary += f"TVL (Total Value Locked): {page['pool_data']['tvl']}\n"
                    if 'daily_returns' in page['pool_data']:
                        pool_summary += f"Daily Returns: {page['pool_data']['daily_returns']}\n"
                    if 'volume' in page['pool_data']:
                        pool_summary += f"Total Automated Volume: {page['pool_data']['volume']}\n"
                    
                    # Extended data
                    if 'chain' in page['pool_data']:
                        pool_summary += f"Chain: {page['pool_data']['chain']}\n"
                    if 'tokens' in page['pool_data']:
                        pool_summary += f"Tokens: {page['pool_data']['tokens']}\n"
                    if 'protocols' in page['pool_data']:
                        pool_summary += f"Protocols: {page['pool_data']['protocols']}\n"
                    if 'top_destinations' in page['pool_data']:
                        pool_summary += f"Top Allocations: {page['pool_data']['top_destinations']}\n"
                    
                    pool_summary += "=" * 50 + "\n"
                
                # Main pools page
                else:
                    if 'total_pools' in page['pool_data']:
                        pool_summary = f"\nAuto Finance has {page['pool_data']['total_pools']} autopools total.\n"
                    if 'total_tvl' in page['pool_data']:
                        pool_summary += f"Site-wide Total TVL: {page['pool_data']['total_tvl']}\n"
                    if 'total_volume' in page['pool_data']:
                        pool_summary += f"Site-wide Total Volume: {page['pool_data']['total_volume']}\n"
                
                # Prepend summary to content for better retrieval
                content = pool_summary + "\n" + page['content']
            else:
                content = page['content']
            
            chunks = self.chunk_content(
                content,
                page['title'],
                page['url'],
                metadata
            )
            all_chunks.extend(chunks)
        
        print(f"  Created {len(all_chunks) - website_chunk_start} website chunks")
        
        # Chunk blog posts
        print("\nChunking blog posts...")
        blog_chunk_start = len(all_chunks)
        for post in blog:
            metadata = {
                'source': 'blog',
                'scraped_at': post.get('scraped_at'),
                **post.get('metadata', {})
            }
            
            chunks = self.chunk_content(
                post['content'],
                post['title'],
                post['url'],
                metadata
            )
            all_chunks.extend(chunks)
        
        print(f"  Created {len(all_chunks) - blog_chunk_start} blog chunks")
        
        print(f"\nTotal chunks: {len(all_chunks)}")
        return all_chunks
    
    def build_index(self):
        """Build the complete index"""
        print("\n" + "="*60)
        print("Building Complete Index")
        print("="*60)
        
        # Prepare chunks
        all_chunks = self.prepare_all_chunks()
        
        if not all_chunks:
            print("Error: No chunks to index!")
            return
        
        # Delete existing complete collection if it exists
        try:
            self.client.delete_collection(name="auto_finance_complete")
            print("\nDeleted existing 'auto_finance_complete' collection")
        except:
            pass
        
        # Create new collection
        print("\nCreating new collection: 'auto_finance_complete'")
        collection = self.client.create_collection(
            name="auto_finance_complete",
            embedding_function=self.embedding_function,
            metadata={"description": "Complete Auto Finance data: docs + website + blog"}
        )
        
        # Add chunks in batches
        print("\nIndexing chunks...")
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            
            # Prepare metadata
            metadatas = []
            for chunk in batch:
                meta = {
                    'title': chunk['title'],
                    'url': chunk['url'],
                    'chunk_id': str(chunk.get('chunk_id', 0)),
                    'source': chunk['metadata'].get('source', 'unknown')
                }
                
                # Add pool data if available
                if 'pool_data' in chunk['metadata']:
                    meta['has_live_data'] = 'true'
                
                metadatas.append(meta)
            
            collection.add(
                documents=[chunk['text'] for chunk in batch],
                metadatas=metadatas,
                ids=[f"chunk_{i+j}" for j in range(len(batch))]
            )
            
            print(f"  Batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
        
        print(f"\n[OK] Index built successfully!")
        print(f"  Total chunks indexed: {len(all_chunks)}")
        print(f"  Collection: 'auto_finance_complete'")
        print(f"  Original 'auto_finance_docs' collection preserved")
    
    def verify_index(self):
        """Verify the index was created successfully"""
        try:
            collection = self.client.get_collection(
                name="auto_finance_complete",
                embedding_function=self.embedding_function
            )
            
            count = collection.count()
            print(f"\n[OK] Verification: Collection has {count} chunks")
            
            # Test search
            results = collection.query(
                query_texts=["What are Autopools?"],
                n_results=3
            )
            
            print(f"[OK] Test search successful, found {len(results['ids'][0])} results")
            return True
            
        except Exception as e:
            print(f"[ERROR] Verification failed: {e}")
            return False


def main():
    """Main function"""
    builder = CompleteIndexBuilder()
    
    # Build index
    builder.build_index()
    
    # Verify
    print("\n" + "="*60)
    print("Verifying Index")
    print("="*60)
    builder.verify_index()
    
    print("\n" + "="*60)
    print("Complete! Your bot can now use the new collection.")
    print("Original docs-only collection is still available as backup.")
    print("="*60)


if __name__ == "__main__":
    main()

