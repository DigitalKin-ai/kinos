import os
import chromadb
import time
import fnmatch
from utils.logger import Logger

class RedundancyManager:
    """
    Manager class for handling content redundancy detection using vector similarity search.
    Uses Chroma for embedding storage and similarity comparisons.
    """

    def __init__(self):
        """
        Initialize RedundancyManager with Chroma client and logger.
        Sets up initial database connection and configuration.
        """
        self.logger = Logger()
        self.chroma_client = None
        self.collection = None
        self.collection_name = "kinos_paragraphs"

    def _initialize_chroma(self):
        """
        Initialize connection to Chroma database with OpenAI embeddings.
        
        Creates in-memory client and configures OpenAI embedding function.
        Sets up collection with proper schema for text-embedding-3-large (3072 dimensions).
        
        Raises:
            ChromaDBConnectionError: If connection fails
            ValueError: If OpenAI API key is not configured
        """
        try:
            # Initialize OpenAI embedding function
            import openai
            from dotenv import load_dotenv
            import os

            # Load API key
            load_dotenv()
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise ValueError("OpenAI API key not found in environment variables")

            # Create embedding function using text-embedding-3-large
            class OpenAIEmbeddingFunction:
                def __init__(self):
                    self.client = openai.OpenAI()

                def __call__(self, input):
                    # Ensure input is a list
                    if isinstance(input, str):
                        input = [input]
                    
                    # Process in batches of 100
                    all_embeddings = []
                    for i in range(0, len(input), 100):
                        batch = input[i:i + 100]
                        response = self.client.embeddings.create(
                            model="text-embedding-3-large",
                            input=batch,
                            encoding_format="float"
                        )
                        embeddings = [e.embedding for e in response.data]
                        all_embeddings.extend(embeddings)
                    return all_embeddings

            # Create in-memory client for better performance
            self.chroma_client = chromadb.Client()

            # Create or get collection with OpenAI embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=OpenAIEmbeddingFunction(),
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

            self.logger.info("✨ Initialized ChromaDB with OpenAI text-embedding-3-large")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize ChromaDB: {str(e)}")
            raise

    def _ensure_collection(self):
        """
        Create or get existing collection for paragraph embeddings.
        
        Creates collection if it doesn't exist, otherwise gets existing one.
        
        Returns:
            Collection: Chroma collection object
            
        Raises:
            ChromaDBError: If collection creation/access fails
        """
        try:
            if not self.chroma_client:
                self._initialize_chroma()
                
            if not self.collection:
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                
            return self.collection
            
        except Exception as e:
            self.logger.error(f"Failed to ensure collection: {str(e)}")
            raise

    def _reset_collection(self):
        """
        Clear all data from current collection.
        
        Use with caution - permanently deletes all stored embeddings.
        
        Raises:
            ChromaDBError: If reset operation fails
        """
        try:
            if self.collection:
                self.chroma_client.delete_collection(self.collection_name)
                self.collection = None
                self.logger.info(f"Reset collection: {self.collection_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to reset collection: {str(e)}")
            raise

    def _split_into_paragraphs(self, text):
        """
        Split text content into meaningful paragraphs using newlines.
        
        Args:
            text (str): Raw text content to split
            
        Returns:
            list: List of paragraph strings
        """
        if not text:
            return []
            
        # Split on double newlines to preserve paragraph structure
        paragraphs = [p.strip() for p in text.split('\n\n')]
        
        # Filter out empty paragraphs and normalize single newlines
        paragraphs = [p.replace('\n', ' ') for p in paragraphs if p.strip()]
        
        return paragraphs

    def _clean_paragraph(self, paragraph):
        """
        Normalize and clean paragraph text for consistent comparison.
        
        Args:
            paragraph (str): Raw paragraph text
            
        Returns:
            str: Cleaned and normalized text
        """
        if not paragraph:
            return ""
            
        # Basic cleaning
        cleaned = paragraph.strip()
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Remove common punctuation that doesn't affect meaning
        cleaned = cleaned.replace('  ', ' ')
        
        return cleaned

    def _generate_metadata(self, paragraph, file_path, position):
        """
        Create metadata for paragraph embedding.
        
        Args:
            paragraph (str): Paragraph text
            file_path (str): Source file path
            position (int): Paragraph position in file
            
        Returns:
            dict: Metadata dictionary including source info and position
        """
        return {
            "file_path": file_path,
            "position": position,
            "length": len(paragraph),
            "timestamp": time.time()
        }

    def analyze_paragraph(self, paragraph, threshold=0.85):
        """
        Compare single paragraph against entire database.
        
        Args:
            paragraph (str): Paragraph to analyze
            threshold (float): Similarity threshold (0.0 to 1.0)
            
        Returns:
            dict: Analysis results including:
                - similarity_scores: List of scores
                - similar_paragraphs: List of matching texts
                - sources: List of source locations
                
        Raises:
            ValueError: If paragraph is empty or invalid
        """
        if not paragraph:
            raise ValueError("Empty paragraph provided")
            
        # Clean input paragraph
        cleaned_paragraph = self._clean_paragraph(paragraph)
        if not cleaned_paragraph:
            raise ValueError("Paragraph contains no content after cleaning")
            
        try:
            # Ensure collection exists
            if not self.collection:
                self._initialize_chroma()
                
            # Query collection for similar paragraphs
            results = self.collection.query(
                query_texts=[cleaned_paragraph],
                n_results=5,  # Get top 5 matches
                where=None,  # No filtering
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            similar_paragraphs = []
            similarity_scores = []
            sources = []
            
            if results['documents']:
                for doc, meta, distance in zip(
                    results['documents'][0],  # First query results
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    # Convert distance to similarity score (cosine similarity)
                    similarity = 1 - (distance / 2)  # Convert to 0-1 range
                    
                    if similarity >= threshold:
                        similar_paragraphs.append(doc)
                        similarity_scores.append(similarity)
                        sources.append(meta)
                        
            return {
                'similarity_scores': similarity_scores,
                'similar_paragraphs': similar_paragraphs,
                'sources': sources
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing paragraph: {str(e)}")
            raise

    def analyze_file(self, file_path, threshold=0.85):
        """
        Analyze entire file for redundant content.
        
        Args:
            file_path (str): Path to file to analyze
            threshold (float): Similarity threshold (0.0 to 1.0)
            
        Returns:
            dict: Analysis results including:
                - redundant_paragraphs: List of paragraphs with duplicates
                - matches: Dictionary mapping paragraphs to their matches
                - scores: Dictionary of similarity scores
                
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        try:
            # Verify file exists and is readable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Read and split file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            paragraphs = self._split_into_paragraphs(content)
            
            # Initialize results
            results = {
                'redundant_paragraphs': [],
                'matches': {},
                'scores': {}
            }
            
            # Analyze each paragraph
            for position, paragraph in enumerate(paragraphs):
                analysis = self.analyze_paragraph(paragraph, threshold)
                
                # If similar paragraphs found
                if analysis['similar_paragraphs']:
                    results['redundant_paragraphs'].append(paragraph)
                    results['matches'][paragraph] = analysis['similar_paragraphs']
                    results['scores'][paragraph] = analysis['similarity_scores']
                    
                    # Log findings
                    self.logger.info(
                        f"📝 Found {len(analysis['similar_paragraphs'])} similar paragraphs "
                        f"for position {position} in {file_path}"
                    )
                    
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze file {file_path}: {str(e)}")
            raise

    def analyze_all_files(self, threshold=0.85):
        """
        Perform redundancy analysis across all project files.
        
        Args:
            threshold (float): Similarity threshold (0.0 to 1.0)
            
        Returns:
            dict: Comprehensive analysis including:
                - redundancy_clusters: Groups of similar content
                - cross_file_redundancies: Duplicates across files
                - statistics: Overall redundancy metrics
                
        Note:
            Can be resource-intensive for large projects
        """
        try:
            # Initialize results
            results = {
                'redundancy_clusters': [],
                'cross_file_redundancies': [],
                'statistics': {
                    'total_paragraphs': 0,
                    'redundant_paragraphs': 0,
                    'files_analyzed': 0,
                    'cluster_count': 0
                }
            }
            
            # Track processed paragraphs to avoid duplicates
            processed = set()
            
            # Analyze each markdown and text file
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        
                        # Analyze file
                        analysis = self.analyze_file(file_path, threshold)
                        results['statistics']['files_analyzed'] += 1
                        
                        # Process redundant paragraphs
                        for paragraph in analysis['redundant_paragraphs']:
                            if paragraph not in processed:
                                processed.add(paragraph)
                                
                                # Create cluster
                                cluster = {
                                    'original': paragraph,
                                    'matches': analysis['matches'][paragraph],
                                    'scores': analysis['scores'][paragraph],
                                    'files': [file_path]
                                }
                                
                                # Add to appropriate category
                                if any(m['file_path'] != file_path for m in analysis['sources']):
                                    results['cross_file_redundancies'].append(cluster)
                                results['redundancy_clusters'].append(cluster)
                                
                        # Update statistics
                        results['statistics']['total_paragraphs'] += len(analysis['redundant_paragraphs'])
                        results['statistics']['redundant_paragraphs'] += len(analysis['redundant_paragraphs'])
                        
            results['statistics']['cluster_count'] = len(results['redundancy_clusters'])
            
            self.logger.success(
                f"✨ Analysis complete: Found {results['statistics']['redundant_paragraphs']} "
                f"redundant paragraphs in {results['statistics']['cluster_count']} clusters"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze all files: {str(e)}")
            raise

    def add_paragraph(self, paragraph, file_path, position):
        """
        Add single paragraph to vector database.
        
        Args:
            paragraph (str): Paragraph text to add
            file_path (str): Source file path
            position (int): Position in source file
            
        Raises:
            ValueError: If paragraph is empty or invalid
            ChromaDBError: If database operation fails
        """
        if not paragraph:
            raise ValueError("Empty paragraph provided")
            
        # Clean input paragraph
        cleaned_paragraph = self._clean_paragraph(paragraph)
        if not cleaned_paragraph:
            raise ValueError("Paragraph contains no content after cleaning")
            
        try:
            # Ensure collection exists
            self._ensure_collection()
            
            # Generate metadata
            metadata = self._generate_metadata(cleaned_paragraph, file_path, position)
            
            # Add to collection
            self.collection.add(
                documents=[cleaned_paragraph],
                metadatas=[metadata],
                ids=[f"{file_path}_{position}"]
            )
            
            self.logger.debug(f"Added paragraph from {file_path} at position {position}")
            
        except Exception as e:
            self.logger.error(f"Failed to add paragraph: {str(e)}")
            raise

    def add_file(self, file_path):
        """
        Process and add entire file to database.
        
        Args:
            file_path (str): Path to file to process
            
        Returns:
            int: Number of paragraphs added
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        try:
            # Verify file exists and is readable
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split into paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            # Add each paragraph
            for position, paragraph in enumerate(paragraphs):
                self.add_paragraph(paragraph, file_path, position)
                
            self.logger.info(f"✨ Added {len(paragraphs)} paragraphs from {file_path}")
            return len(paragraphs)
            
        except Exception as e:
            self.logger.error(f"Failed to add file {file_path}: {str(e)}")
            raise

    def _get_ignore_patterns(self):
        """Get patterns from .gitignore and .aiderignore."""
        patterns = []
        
        # Always exclude these patterns
        patterns.extend([
            '.git*',
            '.aider*',
            'node_modules',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ])
        
        # Read .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r', encoding='utf-8') as f:
                patterns.extend(line.strip() for line in f 
                              if line.strip() and not line.startswith('#'))
                
        return patterns

    def _should_ignore(self, file_path, ignore_patterns):
        """Check if file should be ignored based on patterns."""
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def add_all_files(self):
        """
        Populate database with all project files.
        
        Returns:
            dict: Statistics about added content:
                - total_files: Number of files processed
                - total_paragraphs: Number of paragraphs added
                - errors: Any files that couldn't be processed
                
        Note:
            Clears existing collection before adding
        """
        try:
            # Reset collection
            self._reset_collection()
            
            # Get ignore patterns
            ignore_patterns = self._get_ignore_patterns()
            
            # Initialize statistics
            stats = {
                'total_files': 0,
                'total_paragraphs': 0,
                'errors': []
            }
            
            # Get all markdown and text files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        # Convert to relative path with forward slashes
                        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                        
                        # Skip ignored files
                        if self._should_ignore(rel_path, ignore_patterns):
                            continue
                        try:
                            paragraphs_added = self.add_file(file_path)
                            stats['total_files'] += 1
                            stats['total_paragraphs'] += paragraphs_added
                        except Exception as e:
                            stats['errors'].append({
                                'file': file_path,
                                'error': str(e)
                            })
                            
            self.logger.success(
                f"✨ Added {stats['total_paragraphs']} paragraphs "
                f"from {stats['total_files']} files"
            )
            if stats['errors']:
                self.logger.warning(
                    f"⚠️ Failed to process {len(stats['errors'])} files"
                )
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to add all files: {str(e)}")
            raise

    def generate_redundancy_report(self, analysis_results):
        """
        Create detailed report from redundancy analysis.
        
        Args:
            analysis_results (dict): Results from analysis functions
            
        Returns:
            str: Formatted markdown report including:
                - Redundancy clusters with similarity scores
                - File locations and context
                - Suggested consolidation actions
                
        Note:
            Report format matches KinOS markdown conventions
        """
        try:
            report = ["# Redundancy Analysis Report\n"]
            
            # Add summary section
            stats = analysis_results['statistics']
            report.append("## Summary\n")
            report.append(f"- Files analyzed: {stats['files_analyzed']}")
            report.append(f"- Total paragraphs: {stats['total_paragraphs']}")
            report.append(f"- Redundant paragraphs: {stats['redundant_paragraphs']}")
            report.append(f"- Redundancy clusters: {stats['cluster_count']}\n")
            
            # Add cross-file redundancies section
            if analysis_results['cross_file_redundancies']:
                report.append("## Cross-File Redundancies\n")
                for cluster in analysis_results['cross_file_redundancies']:
                    report.append(f"### Cluster (Similarity: {max(cluster['scores']):.2f})\n")
                    report.append("**Original Content:**")
                    report.append(f"```\n{cluster['original']}\n```\n")
                    report.append("**Similar Content:**")
                    for match, score in zip(cluster['matches'], cluster['scores']):
                        report.append(f"- Similarity: {score:.2f}")
                        report.append(f"```\n{match}\n```\n")
                    report.append("**Files Affected:**")
                    for file in cluster['files']:
                        report.append(f"- {file}\n")
                        
            # Add all clusters section
            report.append("## All Redundancy Clusters\n")
            for i, cluster in enumerate(analysis_results['redundancy_clusters'], 1):
                report.append(f"### Cluster {i} (Similarity: {max(cluster['scores']):.2f})\n")
                report.append("**Original Content:**")
                report.append(f"```\n{cluster['original']}\n```\n")
                report.append("**Similar Content:**")
                for match, score in zip(cluster['matches'], cluster['scores']):
                    report.append(f"- Similarity: {score:.2f}")
                    report.append(f"```\n{match}\n```\n")
                    
            # Add recommendations section
            report.append("## Recommendations\n")
            report.append("1. Review high-similarity clusters (>0.90) for potential consolidation")
            report.append("2. Check cross-file redundancies for information fragmentation")
            report.append("3. Consider updating documentation to reference single source of truth")
            report.append("4. Evaluate lower similarity matches for potential restructuring\n")
            
            return "\n".join(report)
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise
