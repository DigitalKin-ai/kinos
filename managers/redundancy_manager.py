import os
import chromadb
import time
import fnmatch
import subprocess
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
        self.SECTION_THRESHOLD = 3  # Split files with more than 3 sections/subsections

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
        """
        try:
            self.logger.info("🔍 Starting project-wide redundancy analysis...")
            self.logger.info(f"⚙️ Using similarity threshold: {threshold}")

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
            
            # Get ignore patterns
            ignore_patterns = self._get_ignore_patterns()
            self.logger.info(f"📋 Loaded {len(ignore_patterns)} ignore patterns")
            
            # Count total eligible files first
            total_eligible_files = 0
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                        if not self._should_ignore(rel_path, ignore_patterns):
                            total_eligible_files += 1
            
            self.logger.info(f"🔍 Found {total_eligible_files} eligible files to process")
            
            # Track processed paragraphs to avoid duplicates
            processed = set()
            current_file = 0
            
            # Analyze each markdown and text file
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        # Convert to relative path with forward slashes
                        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                        
                        # Skip ignored files
                        if self._should_ignore(rel_path, ignore_patterns):
                            self.logger.debug(f"⏩ Skipping ignored file: {rel_path}")
                            continue
                        
                        current_file += 1
                        self.logger.info(f"📄 Processing file {current_file}/{total_eligible_files}: {rel_path}")
                        
                        try:
                            # Analyze file
                            analysis = self.analyze_file(file_path, threshold)
                            results['statistics']['files_analyzed'] += 1
                            
                            # Process redundant paragraphs
                            if analysis['redundant_paragraphs']:
                                self.logger.info(f"🔄 Found {len(analysis['redundant_paragraphs'])} redundant paragraphs in {rel_path}")
                            
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
                                        self.logger.info(f"🔗 Found cross-file redundancy in {rel_path}")
                                    results['redundancy_clusters'].append(cluster)
                                    
                            # Update statistics
                            results['statistics']['total_paragraphs'] += len(analysis['redundant_paragraphs'])
                            results['statistics']['redundant_paragraphs'] += len(analysis['redundant_paragraphs'])
                            
                            # Log progress percentage
                            progress = (current_file / total_eligible_files) * 100
                            self.logger.info(f"⏳ Progress: {progress:.1f}% ({current_file}/{total_eligible_files})")
                            
                        except Exception as e:
                            self.logger.warning(f"⚠️ Failed to analyze {file_path}: {str(e)}")
                            continue
                            
            results['statistics']['cluster_count'] = len(results['redundancy_clusters'])
            
            # Final summary
            self.logger.success(
                f"\n✨ Analysis complete:\n"
                f"   - Files analyzed: {results['statistics']['files_analyzed']}\n"
                f"   - Total paragraphs: {results['statistics']['total_paragraphs']}\n"
                f"   - Redundant paragraphs: {results['statistics']['redundant_paragraphs']}\n"
                f"   - Redundancy clusters: {results['statistics']['cluster_count']}\n"
                f"   - Cross-file redundancies: {len(results['cross_file_redundancies'])}"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze all files: {str(e)}")
            raise

    def add_paragraph(self, paragraph, file_path, position):
        """
        Add single paragraph to vector database if not already present.
        
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
            
            # Generate unique ID for this paragraph
            paragraph_id = f"{file_path}_{position}"
            
            # Check if this exact ID already exists
            existing_ids = self.collection.get(
                ids=[paragraph_id],
                include=["metadatas"]
            )
            
            if existing_ids['ids']:
                self.logger.debug(f"⏩ Skipping existing paragraph from {file_path} at position {position}")
                return
                
            # Generate metadata
            metadata = self._generate_metadata(cleaned_paragraph, file_path, position)
            
            # Add to collection
            self.collection.add(
                documents=[cleaned_paragraph],
                metadatas=[metadata],
                ids=[paragraph_id]
            )
            
            self.logger.debug(f"📝 Added new paragraph from {file_path} at position {position}")
            
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

    def _should_ignore(self, file_path, ignore_patterns=None):
        """Check if file should be ignored based on patterns."""
        if ignore_patterns is None:
            ignore_patterns = self._get_ignore_patterns()
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def split_file(self, file_path):
        """Split a file into sections/subsections if thresholds exceeded"""
        
        # Early exit if file should be ignored
        if self._should_ignore(file_path):
            return False
            
        try:
            # Read file content with robust encoding handling
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeError:
                    continue
                    
            if content is None:
                raise ValueError(f"Could not read {file_path} with any supported encoding")
                
            # Count sections and subsections
            sections = []
            current_section = []
            current_level = 0
            
            for line in content.split('\n'):
                if line.startswith('#'):
                    # Count number of # to determine level
                    level = len(line) - len(line.lstrip('#'))
                    if level <= 2:  # Only count up to ## level
                        if current_section:
                            sections.append((current_level, current_section))
                        current_section = [line]
                        current_level = level
                    else:
                        current_section.append(line)
                else:
                    current_section.append(line)
                    
            if current_section:
                sections.append((current_level, current_section))
                
            # Check if we need to split
            if len(sections) <= self.SECTION_THRESHOLD:
                return False
                
            # Prepare directory and create README
            dir_name = self._prepare_split_directory(file_path)
            new_files = []
            
            # Save each section
            for index, (level, section_content) in enumerate(sections, 1):
                # Get section title from first line
                title = section_content[0].lstrip('#').strip()
                
                # Save section and track new file
                new_file = self._save_section(dir_name, level, title, section_content, index)
                if new_file:
                    new_files.append(new_file)
                    
            if not new_files:
                self.logger.warning(f"⚠️ No valid sections remained after deduplication in {file_path}")
                return False
                
            # Update references in other files
            self._update_references(file_path, new_files)
            
            # Handle git operations
            self._update_git(file_path, new_files)
            
            # Update global map for each new file
            from managers.map_manager import MapManager
            map_manager = MapManager()
            for new_file in new_files:
                map_manager.update_global_map(new_file)
                
            self.logger.success(f"Split {file_path} into {len(new_files)} sections in {dir_name}/")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to split {file_path}: {str(e)}")
            raise

    def _generate_section_filename(self, level, title, index):
        """Generate unique, well-ordered filenames for sections"""
        # Clean title
        safe_title = "".join(c for c in title if c.isalnum() or c in (' -_')).strip()
        safe_title = safe_title.replace(' ', '_').lower()
        if not safe_title:
            safe_title = 'section'
        
        # Add padding for proper sorting
        level_prefix = f"{level:02d}"
        index_prefix = f"{index:03d}"
        
        return f"{level_prefix}_{index_prefix}_{safe_title}.md"

    def _validate_section_content(self, content):
        """Validate section content before saving"""
        if not content:
            return False
            
        # Check minimum content length
        min_length = 50  # characters
        content_text = '\n'.join(content).strip()
        if len(content_text) < min_length:
            return False
            
        # Check for required elements (e.g., must have header)
        if not any(line.startswith('#') for line in content):
            return False
            
        return True

    def _prepare_split_directory(self, original_file):
        """
        Create a clean directory for split file sections.
        
        Args:
            original_file (str): Path to the file being split
            
        Returns:
            str: Path to the created directory
            
        Raises:
            OSError: If directory creation fails
            ValueError: If original_file path is invalid
        """
        if not original_file or not isinstance(original_file, str):
            raise ValueError("Invalid original file path")
            
        dir_name = os.path.splitext(original_file)[0]
        os.makedirs(dir_name, exist_ok=True)
        
        return dir_name

    def _update_git(self, original_file, new_files):
        """Handle git operations for split files"""
        try:
            # Remove original from git
            subprocess.run(['git', 'rm', original_file], check=True)
            
            # Add new directory and files
            for new_file in new_files:
                subprocess.run(['git', 'add', new_file], check=True)
                
            # Create commit
            msg = f"♻️ Split {original_file} into sections for better management"
            subprocess.run(['git', 'commit', '-m', msg], check=True)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {str(e)}")
            raise

    def _update_references(self, original_file, new_files):
        """Update references in other files after splitting"""
        try:
            # Find all markdown files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        
                        # Skip the split files themselves
                        if file_path in new_files:
                            continue
                            
                        # Update references with robust encoding handling
                        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                            try:
                                with open(file_path, 'r', encoding=encoding) as f:
                                    content = f.read()
                                    
                                # Replace references to original file with new structure
                                if original_file in content:
                                    new_content = content.replace(
                                        original_file, 
                                        f"{os.path.splitext(original_file)[0]}/README.md"
                                    )
                                    with open(file_path, 'w', encoding=encoding) as f:
                                        f.write(new_content)
                                break  # Successfully read and wrote file
                            except UnicodeError:
                                continue
                        else:
                            self.logger.warning(f"⚠️ Could not process {file_path} with any supported encoding")
                                
        except Exception as e:
            self.logger.error(f"Failed to update references: {str(e)}")
            raise

    def _save_section(self, dir_name, level, title, content, index):
        """
        Save a section to its own file, removing duplicates with same title.
        
        Args:
            dir_name (str): Directory to save section in
            level (int): Section level (1 for #, 2 for ##, etc)
            title (str): Section title
            content (list): Section content lines
            index (int): Section index for ordering
            
        Returns:
            str: Path to saved file, or None if validation failed or duplicate title
        """
        # Validate content
        if not self._validate_section_content(content):
            self.logger.debug(f"⏩ Skipping invalid section: {title}")
            return None
            
        # Generate filename
        filename = self._generate_section_filename(level, title, index)
        file_path = os.path.join(dir_name, filename)
        
        # Check for existing file with same title
        for existing_file in os.listdir(dir_name):
            if existing_file.endswith(f"_{title.lower().replace(' ', '_')}.md"):
                self.logger.warning(
                    f"⚠️ Duplicate section '{title}' detected - removing duplicate content"
                )
                return None
        
        # Write new content if no duplicate title found
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            return file_path
        except Exception as e:
            self.logger.error(f"Error saving section: {str(e)}")
            return None

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
            self.logger.info("🔄 Initializing redundancy database...")
            
            # Reset collection
            self._reset_collection()
            self.logger.info("✨ Database reset complete")
            
            # Get ignore patterns
            ignore_patterns = self._get_ignore_patterns()
            self.logger.info(f"📋 Loaded {len(ignore_patterns)} ignore patterns")
            
            # Initialize statistics
            stats = {
                'total_files': 0,
                'total_paragraphs': 0,
                'errors': []
            }
            
            # Count total eligible files first
            total_eligible_files = 0
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                        if not self._should_ignore(rel_path, ignore_patterns):
                            total_eligible_files += 1
            
            self.logger.info(f"🔍 Found {total_eligible_files} eligible files to process")
            
            # Process files with progress tracking
            current_file = 0
            
            # Get all markdown and text files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt')):
                        file_path = os.path.join(root, file)
                        # Convert to relative path with forward slashes
                        rel_path = os.path.relpath(file_path, '.').replace(os.sep, '/')
                        
                        # Skip ignored files
                        if self._should_ignore(rel_path, ignore_patterns):
                            self.logger.debug(f"⏩ Skipping ignored file: {rel_path}")
                            continue
                        
                        current_file += 1
                        self.logger.info(f"📄 Processing file {current_file}/{total_eligible_files}: {rel_path}")
                        
                        try:
                            # Read file content first to catch encoding issues
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                paragraphs = self._split_into_paragraphs(content)
                                self.logger.info(f"📝 Found {len(paragraphs)} paragraphs in {rel_path}")
                            except UnicodeDecodeError:
                                self.logger.warning(f"⚠️ Encoding issue with {rel_path}, trying alternative encodings...")
                                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                                    try:
                                        with open(file_path, 'r', encoding=encoding) as f:
                                            content = f.read()
                                        paragraphs = self._split_into_paragraphs(content)
                                        self.logger.info(f"✅ Successfully read {rel_path} with {encoding} encoding")
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                else:
                                    raise ValueError(f"Could not read {rel_path} with any supported encoding")
                            
                            # Add paragraphs to database
                            paragraphs_added = self.add_file(file_path)
                            stats['total_files'] += 1
                            stats['total_paragraphs'] += paragraphs_added
                            
                            # Log progress percentage
                            progress = (current_file / total_eligible_files) * 100
                            self.logger.info(f"⏳ Progress: {progress:.1f}% ({current_file}/{total_eligible_files})")
                            
                        except Exception as e:
                            error_msg = f"❌ Error processing {rel_path}: {str(e)}"
                            self.logger.error(error_msg)
                            stats['errors'].append({
                                'file': file_path,
                                'error': str(e)
                            })
                            
            # Final summary
            self.logger.success(
                f"✨ Database population complete:\n"
                f"   - Processed {stats['total_files']}/{total_eligible_files} files\n"
                f"   - Added {stats['total_paragraphs']} paragraphs\n"
                f"   - Encountered {len(stats['errors'])} errors"
            )
            
            # Log any errors in detail
            if stats['errors']:
                self.logger.warning("\n⚠️ Errors encountered:")
                for error in stats['errors']:
                    self.logger.warning(f"   - {error['file']}: {error['error']}")
                
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add all files: {str(e)}")
            raise

    def delete_duplicates(self, auto_mode=False, interactive=False, threshold=0.95, 
                     keep_strategy="longest", dry_run=False):
        """
        Delete duplicate content based on specified strategy.
        """
        try:
            self.logger.info(f"🔍 Starting duplicate analysis (interactive={interactive}, threshold={threshold})")
            if dry_run:
                self.logger.info("🏃 DRY RUN MODE - No changes will be made")
            if interactive:
                self.logger.info("👤 INTERACTIVE MODE - You will be prompted for each duplicate")
            if auto_mode:
                self.logger.info(f"🤖 AUTO MODE - Using '{keep_strategy}' strategy")

            # Initialize ChromaDB if needed
            if not self.collection:
                self.logger.info("🔄 Initializing ChromaDB...")
                self._initialize_chroma()
                self.logger.info("✅ ChromaDB initialized successfully")

            # Check if database has any content
            try:
                count = len(self.collection.get()['ids'])
                self.logger.info(f"📊 Found {count} documents in database")
                if count == 0:
                    self.logger.info("⚠️ Database is empty. Please run 'kin redundancy add' first")
                    return {'files_modified': 0, 'duplicates_removed': 0, 'errors': []}
            except Exception as e:
                self.logger.error(f"Error checking database content: {str(e)}")
                raise

            # Get all duplicates with detailed logging
            self.logger.info("🔍 Starting file analysis...")
            results = self.analyze_all_files(threshold=threshold)
            self.logger.info(f"📈 Analysis complete - Found {len(results.get('redundancy_clusters', []))} clusters")

            # Log detailed cluster information
            if results.get('redundancy_clusters'):
                self.logger.info("\n=== Cluster Details ===")
                for i, cluster in enumerate(results['redundancy_clusters'], 1):
                    self.logger.info(f"\nCluster {i}:")
                    self.logger.info(f"- Similarity scores: {cluster['scores']}")
                    self.logger.info(f"- Files affected: {cluster['files']}")
            else:
                self.logger.info("⚠️ No redundancy clusters found in results")
            
            # Log detailed cluster information
            if results.get('redundancy_clusters'):
                self.logger.info("\n=== Cluster Details ===")
                for i, cluster in enumerate(results['redundancy_clusters'], 1):
                    self.logger.info(f"\nCluster {i}:")
                    self.logger.info(f"- Similarity scores: {cluster['scores']}")
                    self.logger.info(f"- Files affected: {cluster['files']}")
            else:
                self.logger.info("⚠️ No redundancy clusters found in results")
            
            stats = {
                'files_modified': 0,
                'duplicates_removed': 0,
                'errors': []
            }
            
            if not results['redundancy_clusters']:
                self.logger.info("✨ No duplicates found above threshold")
                return stats
            
            total_clusters = len(results['redundancy_clusters'])
            self.logger.info(f"📝 Found {total_clusters} duplicate clusters")
            
            # Process each cluster
            for cluster_idx, cluster in enumerate(results['redundancy_clusters'], 1):
                try:
                    self.logger.info(f"\n🔄 Processing cluster {cluster_idx}/{total_clusters}")
                    
                    if interactive:
                        # Show cluster contents with more detail
                        self.logger.info("\n=== Duplicate Content Cluster ===")
                        self.logger.info(f"Original File: {cluster['sources'][0]['file_path']}")
                        print("\nOriginal Content:")
                        print("```")
                        print(cluster['original'])
                        print("```")
                        
                        print("\nDuplicates Found:")
                        for i, (match, source) in enumerate(zip(cluster['matches'], cluster['sources'][1:]), 1):
                            print(f"\n{i}. File: {source['file_path']}")
                            print("```")
                            print(match)
                            print("```")
                            
                        # Ask which to keep with better prompting
                        if not dry_run:
                            print("\n--- Action Required ---")
                            print("Enter number to keep that version:")
                            print("0: Keep original")
                            for i in range(1, len(cluster['matches']) + 1):
                                print(f"{i}: Keep duplicate #{i}")
                            print("s: Skip this cluster")
                            
                            choice = input("\nYour choice (0-N or s): ")
                            self.logger.info(f"User selected: {choice}")
                            
                            if choice.lower() == 's':
                                self.logger.info("⏭️ Skipping this cluster")
                                continue
                            try:
                                keep_index = int(choice)
                                if 0 <= keep_index <= len(cluster['matches']):
                                    if not dry_run:
                                        self.logger.info(f"🔨 Removing duplicates, keeping version {keep_index}")
                                        self._remove_duplicates(cluster, keep_index)
                                        stats['duplicates_removed'] += len(cluster['matches']) - 1
                                        stats['files_modified'] += len(set(s['file_path'] for s in cluster['sources'])) - 1
                                else:
                                    self.logger.warning(f"❌ Invalid choice {keep_index}, must be between 0 and {len(cluster['matches'])}")
                            except ValueError:
                                self.logger.warning("❌ Invalid input, skipping cluster")
                                
                    elif auto_mode:
                        # Determine which version to keep
                        if keep_strategy == "longest":
                            versions = [cluster['original']] + cluster['matches']
                            keep_index = max(range(len(versions)), key=lambda i: len(versions[i]))
                            self.logger.info(f"📏 Auto-selecting longest version (index {keep_index})")
                        else:  # keep_strategy == "first"
                            keep_index = 0
                            self.logger.info("1️⃣ Auto-selecting first version")
                            
                        if not dry_run:
                            self.logger.info(f"🔨 Removing duplicates, keeping version {keep_index}")
                            self._remove_duplicates(cluster, keep_index)
                            stats['duplicates_removed'] += len(cluster['matches']) - 1
                            stats['files_modified'] += len(set(s['file_path'] for s in cluster['sources'])) - 1
                            
                except Exception as e:
                    error_msg = f"Error processing cluster {cluster_idx}: {str(e)}"
                    self.logger.error(f"❌ {error_msg}")
                    stats['errors'].append(error_msg)
                    
            # Final summary
            if not dry_run:
                self.logger.success(
                    f"\n✨ Deduplication complete:\n"
                    f"   - Modified {stats['files_modified']} files\n"
                    f"   - Removed {stats['duplicates_removed']} duplicates\n"
                    f"   - Encountered {len(stats['errors'])} errors"
                )
            else:
                self.logger.info(
                    f"\n🏃 Dry run complete - would have:\n"
                    f"   - Modified {stats['files_modified']} files\n"
                    f"   - Removed {stats['duplicates_removed']} duplicates"
                )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete duplicates: {str(e)}")
            raise
            
    def _remove_duplicates(self, cluster, keep_index):
        """
        Remove duplicate content from files, keeping the specified version.
        
        Args:
            cluster (dict): Cluster of duplicate content
            keep_index (int): Index of version to keep (0 for original)
        """
        try:
            # Get version to keep
            keep_version = cluster['original'] if keep_index == 0 else cluster['matches'][keep_index - 1]
            keep_source = cluster['sources'][keep_index]
            
            # Process each file except the one we're keeping
            for i, source in enumerate(cluster['sources']):
                if i == keep_index:
                    continue
                    
                file_path = source['file_path']
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Get version to remove
                    remove_version = cluster['original'] if i == 0 else cluster['matches'][i - 1]
                    
                    # Replace duplicate with empty string
                    new_content = content.replace(remove_version, '')
                    
                    # Write updated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
                    self.logger.info(f"Removed duplicate from {file_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {str(e)}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"Failed to remove duplicates: {str(e)}")
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
