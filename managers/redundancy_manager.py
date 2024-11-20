import chromadb
import time
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
            def openai_embedding_function(texts):
                client = openai.OpenAI()
                # Batch texts in groups of 100 to stay within API limits
                embeddings = []
                for i in range(0, len(texts), 100):
                    batch = texts[i:i + 100]
                    response = client.embeddings.create(
                        model="text-embedding-3-large",
                        input=batch,
                        encoding_format="float"
                    )
                    embeddings.extend([e.embedding for e in response.data])
                return embeddings

            # Create in-memory client for better performance
            self.chroma_client = chromadb.Client()

            # Create or get collection with OpenAI embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=openai_embedding_function,
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
        pass

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
        pass

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
        pass

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
        pass

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
        pass
