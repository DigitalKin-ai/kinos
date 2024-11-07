from agents import (SpecificationsAgent, ProductionAgent, 
    ManagementAgent, EvaluationAgent, ContexteAgent)
from parallagon_agent import ParallagonAgent
from flask import Flask, render_template, jsonify, request, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
import time
import os
import git
from datetime import datetime
from typing import Dict, Any
from mission_service import MissionService
from file_manager import FileManager
from llm_service import LLMService
from search_replace import SearchReplace
from agents import (
    SpecificationsAgent,
    ProductionAgent,
    ManagementAgent,
    EvaluationAgent,
    ContexteAgent
)

class ParallagonWeb:
    # Log level colors
    LOG_COLORS = {
        'info': 'blue',
        'success': 'green', 
        'warning': 'orange',
        'error': 'red',
        'debug': 'gray'
    }

    TEST_DATA = """1. Reformulation de la Demande (corrigée)
Sujet scientifique : Traceurs IoT universels avec communication multi-réseaux incluant le système satellite Kineis - aspects software et firmware

Objectif de recherche : Être capable de concevoir un système IoT capable d'identifier les réseaux disponibles (LoRa, SigFox, Kineis) pour choisir le plus pertinent en consommant le moins d'énergie possible

Axes de travail :

Développement software pour l'identification et la sélection des réseaux
Optimisation du firmware pour la gestion efficace de l'énergie
Plage de dates : 2023-2024

Email : e.thery@digitalkin.ai

2. Détermination des manques actuels et maximisation de l'éligibilité au CIR (corrigée)
Résultat à considérer :

Système logiciel IoT multi-réseaux économe en énergie
Algorithme de sélection de réseau optimal
Atteinte de l'objectif idéal : Non

Preuves des manques actuels :

Algorithmes d'identification dynamique des réseaux
Logiciels de sélection en temps réel
Optimisation logicielle de l'énergie multi-réseaux
Intégration logicielle Kineis avec autres protocoles
Gestion firmware des protocoles multiples
Évaluation de l'éligibilité au CIR : L'éligibilité au CIR de ce projet reste favorable, en se concentrant sur les aspects software et firmware :

Verrous technologiques : Le développement d'algorithmes capables d'identifier et de basculer efficacement entre différents réseaux (LoRa, SigFox, Kineis) tout en optimisant la consommation d'énergie présente des défis techniques significatifs au niveau logiciel.

Incertitudes techniques : L'optimisation logicielle de la consommation d'énergie tout en gérant plusieurs protocoles de communication pose des incertitudes techniques importantes. La gestion efficace des ressources limitées d'un système embarqué pour supporter multiple protocoles est un défi complexe.

Innovation : La création d'un algorithme de sélection de réseau en temps réel, capable de prendre en compte multiples paramètres (disponibilité, consommation d'énergie, qualité de signal) représente une innovation potentielle dans le domaine du software IoT.

Avancement de l'état de l'art : Le développement d'un firmware capable de gérer efficacement les transitions entre technologies terrestres (LoRa, SigFox) et satellitaire (Kineis) tout en optimisant l'énergie pourrait représenter une avancée significative par rapport aux solutions existantes.

Ces éléments suggèrent que le projet comporte des aspects de recherche et développement logiciel qui vont au-delà de l'ingénierie courante, le rendant potentiellement éligible au CIR.

3. Génération des queries de recherche (inchangée)
Les queries restent pertinentes car elles se concentrent déjà sur les aspects software et firmware :

"IoT multi-network system energy efficient LoRa SigFox Kineis 2023 2024"

"IoT software network identification selection algorithm LoRa SigFox Kineis 2023 2024"

"IoT firmware energy optimization multi-network LoRa SigFox Kineis 2023 2024"

"Kineis satellite IoT integration energy efficient tracking 2023 2024"

### Niveau de profondeur
[x] Approfondi (10-15 pages)

# TEMPLATE ÉTAT DE L'ART CIR

## Introduction générale (200-250 mots)

**But** : Présenter le contexte global du projet de R&D et introduire les différents axes de recherche.

**Directives** :
- Contextualiser la problématique générale
- Présenter succinctement les axes de recherche (2-3 axes maximum)
- Justifier la décomposition en axes distincts
- Style : Accessible aux non-spécialistes tout en restant précis
- Aucune référence nécessaire dans cette section

## Pour chaque axe de recherche (1100-1450 mots par axe)

### 1. Introduction de l'axe (100-150 mots)

**But** : Contextualiser l'axe et établir son objectif de recherche spécifique.

**Directives** :
- Présenter l'axe et son objectif de recherche spécifique
- Montrer sa contribution à l'objectif global
- Justifier sa pertinence dans le projet
- Style : Concis, technique mais accessible
- Aucune référence nécessaire

### 2. Synthèse des connaissances actuelles (400-500 mots)

**But** : Établir l'état des connaissances existantes pertinentes pour l'axe.

**Directives** :
- Structurer par thèmes ou approches principales
- Présenter chronologiquement les avancées majeures
- Références : 6-8 publications clés (< 5 ans sauf si fondamentales)
- Style : Paragraphes courts, progressifs
- Privilégier la paraphrase aux citations directes
- Maintenir le fil conducteur vers l'objectif de l'axe

### 3. Analyse critique et limites (300-400 mots)

**But** : Démontrer l'insuffisance des approches actuelles.

**Directives** :
- Identifier 3-4 limites majeures
- Lier chaque limite à l'objectif de l'axe
- Références : 3-4 publications illustrant ces limites
- Un paragraphe par limite majeure
- Utiliser des connecteurs logiques
- Tone objectif et factuel

### 4. Verrous scientifiques et techniques (200-250 mots)

**But** : Identifier les obstacles spécifiques bloquant l'atteinte de l'objectif.

**Directives** :
- Structure pour chaque verrou :
  - Description du verrou
  - Impact sur l'objectif
  - Tentatives actuelles de résolution
  - Limitations de ces tentatives
- Références : 1-2 publications par verrou
- Style : Technique mais clair
- Lien explicite avec les critères CIR

### 5. Conclusion de l'axe (100-150 mots)

**But** : Synthétiser la nécessité de nouvelles recherches pour cet axe.

**Directives** :
- Résumer les limites principales
- Justifier le besoin de nouvelles approches
- Ne pas décrire les solutions envisagées
- Style : Synthétique et conclusif
- Aucune nouvelle référence

## Synthèse multi-axes (250-300 mots)

**But** : Démontrer la cohérence globale des axes et leur complémentarité.

**Directives** :
- Rappeler brièvement les verrous majeurs de chaque axe
- Montrer les interactions entre les axes
- Justifier la nécessité d'aborder tous les axes
- Expliquer la contribution de chaque axe à l'objectif global
- Style : Vue d'ensemble stratégique
- Aucune nouvelle référence

## Conclusion générale (150-200 mots)

**But** : Synthétiser la nécessité globale du projet de R&D.

**Directives** :
- Rappeler l'objectif global
- Résumer les principaux verrous identifiés
- Justifier la nécessité d'une approche R&D
- Style : Accessible aux non-spécialistes
- Aucune nouvelle référence

## Références bibliographiques

**Directives** :
- Format : Norme APA ou IEEE
- Organisation : Par ordre alphabétique ou d'apparition
- Nombre : 10-15 références par axe
- Qualité : Publications académiques, brevets, standards
- Date : Privilégier les références récentes (< 5 ans)
- Pertinence : Chaque référence doit être citée dans le texte

## Directives générales

### Format et style
- Longueur totale : 2000-2500 mots + 1100-1450 mots par axe
- Style scientifique et objectif
- Éviter le conditionnel sauf pour les perspectives
- Paragraphes courts et structurés
- Transitions logiques entre sections

### Critères CIR à satisfaire
- Démontrer l'état des connaissances accessibles
- Identifier clairement les limites actuelles
- Justifier la nécessité de travaux de R&D
- Établir le caractère nouveau des recherches
- Mettre en évidence les verrous technologiques

### Relations clés à maintenir
- État de l'art ↔ Objectif global
- État de l'art ↔ Objectifs spécifiques des axes
- Axes ↔ Verrous technologiques
- Verrous ↔ Critères CIR
- Axes entre eux (complémentarité)

## But global de l'état de l'art

Démontrer rigoureusement que l'objectif global du projet ne peut être atteint avec les connaissances et approches actuelles, justifiant ainsi la nécessité d'engager des travaux de R&D potentiellement éligibles au CIR. Pour cela, l'état de l'art doit :
1. Établir l'état des connaissances accessible
2. Identifier les limites des approches existantes
3. Démontrer l'existence de verrous technologiques
4. Justifier la nécessité d'une approche R&D structurée
5. Préparer la justification des travaux proposés
"""

    def __init__(self, config):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS
        self.monitor_thread = None  # Add monitor thread tracking
        self.mission_service = MissionService()
        
        # Ensure missions directory exists
        os.makedirs("missions", exist_ok=True)
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["1000 per minute"]
        )
        self.content_cache = {}
        self.last_modified = {}
        self.last_content = {}
        self.notifications_queue = []
        self.setup_error_handlers()
        # Add file paths configuration
        self.file_paths = {
            "demande": "demande.md",
            "specifications": "specifications.md",
            "management": "management.md", 
            "production": "production.md",
            "evaluation": "evaluation.md",
            "suivi": "suivi.md"  # Add suivi.md to managed files
        }
        self.file_manager = FileManager(self.file_paths)
        self.llm_service = LLMService(config["openai_api_key"])
        self.running = False
        self.agents = {}
        self.logs_buffer = []  # Store recent logs
        self.init_agents(config)
        self.setup_routes()

    def init_agents(self, config):
        """Initialisation des agents avec configuration standard"""
        try:
            self.log_message("Initializing agents...", level='info')
            
            # S'assurer que le dossier missions existe
            os.makedirs("missions", exist_ok=True)
            
            base_config = {
                "check_interval": 5,
                "anthropic_api_key": config["anthropic_api_key"],
                "openai_api_key": config["openai_api_key"],
                "logger": self.log_message
            }

            # Créer les agents avec leurs prompts dédiés
            self.agents = {
                "Specification": SpecificationsAgent({
                    **base_config,
                    "file_path": "specifications.md",
                    "watch_files": ["demande.md", "production.md"]
                }),
                "Production": ProductionAgent({
                    **base_config,
                    "file_path": "production.md",
                    "watch_files": ["specifications.md", "evaluation.md"]
                }),
                "Management": ManagementAgent({
                    **base_config,
                    "file_path": "management.md",
                    "watch_files": ["specifications.md", "production.md", "evaluation.md"]
                }),
                "Evaluation": EvaluationAgent({
                    **base_config,
                    "file_path": "evaluation.md",
                    "watch_files": ["specifications.md", "production.md"]
                }),
                "Contexte": ContexteAgent({
                    **base_config,
                    "file_path": "contexte.md",
                    "watch_files": ["demande.md", "specifications.md", "production.md"]
                })
            }

            # Vérifier que tous les agents sont correctement initialisés
            for name, agent in self.agents.items():
                if not agent:
                    raise ValueError(f"Agent {name} non initialisé correctement")
                self.log_message(f"✓ Agent {name} initialisé", level='success')

            self.log_message("Agents initialized successfully", level='success')
            
        except Exception as e:
            self.log_message(f"Error initializing agents: {str(e)}", level='error')
            import traceback
            self.log_message(traceback.format_exc(), level='error')
            raise

    def handle_content_change(self, file_path: str, content: str, panel_name: str = None, flash: bool = False):
        """Handle content change notifications"""
        try:
            # Format timestamp consistently
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Create notification with all required fields
            notification = {
                'type': 'info',
                'message': f'Content updated in {panel_name or os.path.basename(file_path)}',
                'timestamp': timestamp,
                'panel': panel_name or os.path.splitext(os.path.basename(file_path))[0],
                'status': os.path.basename(file_path),
                'operation': 'flash_tab',
                'id': len(self.notifications_queue)
            }
            
            # Add to notifications queue
            self.notifications_queue.append(notification)
            
            # Debug logs
            print(f"Added notification: {notification}")
            print(f"Current notifications queue: {self.notifications_queue}")
            
            # Update cache
            self.content_cache[file_path] = content
            self.last_modified[file_path] = time.time()
            
        except Exception as e:
            self.log_message(f"Error handling content change: {str(e)}", level='error')

    def toggle_agent(self, agent_id: str, action: str) -> bool:
        """
        Toggle an individual agent's state
        
        Args:
            agent_id: ID of the agent to toggle
            action: 'start' or 'stop'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            agent_name = agent_id.capitalize()
            if agent_name not in self.agents:
                self.log_message(f"Agent {agent_id} not found", level='error')
                return False
                
            agent = self.agents[agent_name]
            
            if action == 'start':
                if not agent.running:
                    agent.start()
                    thread = threading.Thread(
                        target=agent.run,
                        daemon=True,
                        name=f"Agent-{agent_name}"
                    )
                    thread.start()
                    self.log_message(f"Agent {agent_name} started", level='success')
            elif action == 'stop':
                if agent.running:
                    agent.stop()
                    self.log_message(f"Agent {agent_name} stopped", level='info')
            
            return True
            
        except Exception as e:
            self.log_message(f"Failed to toggle agent {agent_id}: {str(e)}", level='error')
            return False

    def setup_routes(self):
        @self.app.route('/api/missions/<int:mission_id>/content', methods=['GET'])
        def get_mission_content(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                content = {}
                for file_type, file_path in mission['files'].items():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content[file_type] = f.read()
                    except Exception as e:
                        self.log_message(f"Error reading {file_type} file: {str(e)}", level='error')
                        content[file_type] = ""
                        
                return jsonify(content)
                
            except Exception as e:
                self.log_message(f"Error getting mission content: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/content/<file_type>', methods=['POST'])
        def save_mission_content(mission_id, file_type):
            try:
                data = request.get_json()
                if not data or 'content' not in data:
                    return jsonify({'error': 'Content is required'}), 400
                    
                success = self.mission_service.save_mission_file(
                    mission_id,
                    file_type,
                    data['content']
                )
                
                if not success:
                    return jsonify({'error': 'Failed to save content'}), 500
                    
                self.log_message(f"Saved {file_type} content for mission {mission_id}", level='success')
                return jsonify({'status': 'success'})
                
            except Exception as e:
                self.log_message(f"Error saving mission content: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions', methods=['GET'])
        def get_missions():
            try:
                missions = self.mission_service.get_all_missions()
                if missions is None:
                    return jsonify({'error': 'Failed to fetch missions'}), 500
                    
                return jsonify(missions)
                
            except Exception as e:
                self.log_message(f"Error getting missions: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/validate-directory', methods=['POST'])
        def validate_mission_directory():
            """Validate that a directory contains required mission files"""
            try:
                data = request.get_json()
                if not data or 'path' not in data:
                    return jsonify({'error': 'Path is required'}), 400
                    
                path = data['path']
                
                # Verify only required files at root level
                required_files = [
                    "demande.md",
                    "specifications.md", 
                    "management.md",
                    "production.md",
                    "evaluation.md",
                    "suivi.md",
                    "contexte.md"
                ]
                
                missing_files = []
                for file in required_files:
                    if not os.path.isfile(os.path.join(path, file)):
                        missing_files.append(file)
                        
                if missing_files:
                    return jsonify({
                        'error': f'Dossier invalide. Fichiers manquants : {", ".join(missing_files)}'
                    }), 400
                    
                return jsonify({'status': 'valid'})
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/get-directory-path', methods=['POST'])
        def get_directory_path():
            """Get full path for a directory selected in the frontend"""
            try:
                data = request.get_json()
                if not data or 'name' not in data:
                    return jsonify({'error': 'Directory name is required'}), 400
                    
                directory_name = data['name']
                
                # Chercher le dossier dans les emplacements possibles
                possible_paths = [
                    os.path.abspath(directory_name),  # Chemin absolu
                    os.path.join(os.getcwd(), directory_name),  # Relatif au dossier courant
                    os.path.expanduser(f"~/{directory_name}"),  # Dans le home
                    os.path.join(os.path.expanduser("~/Documents"), directory_name),  # Dans Documents
                    os.path.join(os.path.expanduser("~"), "Documents", directory_name)  # Autre syntaxe pour Documents
                ]
                
                # Debug log
                self.log_message(f"Searching for directory: {directory_name}")
                self.log_message(f"Possible paths: {possible_paths}")
                
                # Trouver le premier chemin valide
                for path in possible_paths:
                    if os.path.isdir(path):
                        self.log_message(f"Found valid path: {path}")
                        return jsonify({'path': path})
                
                self.log_message(f"No valid path found for: {directory_name}", level='error')        
                return jsonify({'error': 'Directory not found'}), 404
                
            except Exception as e:
                self.log_message(f"Error getting directory path: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/link', methods=['POST'])
        def create_mission_link():
            """Create a mission from an external directory"""
            try:
                data = request.get_json()
                if not data or 'path' not in data:
                    return jsonify({'error': 'External path is required'}), 400
                    
                external_path = data['path']
                mission_name = data.get('name')  # Optional
                
                # Create mission link
                mission = self.mission_service.create_mission_link(
                    external_path=external_path,
                    mission_name=mission_name
                )
                
                self.log_message(
                    f"Created link to external mission at {external_path}", 
                    level='success'
                )
                return jsonify(mission), 201
                
            except Exception as e:
                self.log_message(f"Error creating mission link: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions', methods=['POST'])
        def create_mission():
            try:
                data = request.get_json()
                if not data or 'name' not in data:
                    return jsonify({'error': 'Name is required'}), 400
                    
                # Validate mission name
                mission_name = data['name'].strip()
                if not mission_name:
                    return jsonify({'error': 'Mission name cannot be empty'}), 400
                    
                # Check if mission already exists
                if self.mission_service.mission_exists(mission_name):
                    return jsonify({'error': 'Mission with this name already exists'}), 409
                    
                # Create mission in database
                mission = self.mission_service.create_mission(
                    name=mission_name,
                    description=data.get('description')
                )
                
                # Update FileManager's current mission
                self.file_manager.current_mission = mission_name
                
                # Create mission files
                if not self.file_manager.create_mission_files(mission_name):
                    # Rollback database creation if file creation fails
                    self.mission_service.delete_mission(mission['id'])
                    self.file_manager.current_mission = None
                    return jsonify({'error': 'Failed to create mission files'}), 500
                
                self.log_message(f"Mission '{mission_name}' created successfully", level='success')
                return jsonify(mission), 201
                
            except Exception as e:
                self.log_message(f"Error creating mission: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>', methods=['GET'])
        def get_mission(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                # Update FileManager's current mission
                self.file_manager.current_mission = mission['name']
                
                # Update agent paths when mission changes
                self.update_agent_paths(mission['name'])
                
                # Stop agents if they're running
                was_running = self.running
                if was_running:
                    self.stop_agents()
                    
                # Start agents again if they were running
                if was_running:
                    self.start_agents()
                    
                return jsonify(mission)
                
            except Exception as e:
                self.log_message(f"Error getting mission: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>', methods=['PUT'])
        def update_mission(mission_id):
            try:
                data = request.get_json()
                mission = self.mission_service.update_mission(
                    mission_id,
                    name=data.get('name'),
                    description=data.get('description'),
                    status=data.get('status')
                )
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404
                    
                self.log_message(f"Mission {mission_id} updated", level='success')
                return jsonify(mission)
                
            except Exception as e:
                self.log_message(f"Error updating mission: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/agent/<agent_id>/<action>', methods=['POST'])
        def control_agent(agent_id, action):
            """Control (start/stop) a specific agent"""
            try:
                # Debug logs
                self.log_message(f"Agent control request: {agent_id} - {action}", level='debug')
                
                # Validate action
                if action not in ['start', 'stop']:
                    return jsonify({'error': 'Invalid action'}), 400
                    
                # Convert agent_id to proper case and normalize
                agent_name = agent_id.capitalize()
                if agent_name.endswith('s'):
                    agent_name = agent_name[:-1]
                
                # Debug log
                self.log_message(f"Looking for agent: {agent_name}", level='debug')
                self.log_message(f"Available agents: {list(self.agents.keys())}", level='debug')
                
                if agent_name not in self.agents:
                    return jsonify({'error': f'Agent {agent_id} not found (normalized: {agent_name})'}), 404
                    
                agent = self.agents[agent_name]
                
                if action == 'start':
                    if not agent.running:
                        agent.start()
                        thread = threading.Thread(
                            target=agent.run,
                            daemon=True,
                            name=f"Agent-{agent_name}"
                        )
                        thread.start()
                        self.log_message(f"Agent {agent_name} started", level='success')
                else:  # stop
                    if agent.running:
                        agent.stop()
                        self.log_message(f"Agent {agent_name} stopped", level='success')
                        
                return jsonify({
                    'status': 'success',
                    'message': f'Agent {agent_name} {action}ed successfully',
                    'running': agent.running
                })
                
            except Exception as e:
                self.log_message(f"Error controlling agent {agent_id}: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/agents/status', methods=['GET'])
        def get_agents_status():
            """Get status of all agents"""
            try:
                status = {
                    name.lower(): {
                        'running': agent.running,
                        'last_run': agent.last_run.isoformat() if agent.last_run else None,
                        'last_change': agent.last_change.isoformat() if agent.last_change else None
                    }
                    for name, agent in self.agents.items()
                }
                return jsonify(status)
                
            except Exception as e:
                self.log_message(f"Failed to get agents status: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/clean')
        def clean_interface():
            try:
                with open('production.md', 'r', encoding='utf-8') as f:
                    content = f.read()
                with open('suivi.md', 'r', encoding='utf-8') as f:
                    suivi_content = f.read()
                with open('demande.md', 'r', encoding='utf-8') as f:
                    demande_content = f.read()
                return render_template('clean.html', 
                             content=content, 
                             suivi_content=suivi_content,
                             demande_content=demande_content)
            except Exception as e:
                return f"Error loading content: {str(e)}", 500

        @self.app.route('/api/missions/<int:mission_id>/test-data', methods=['POST'])
        def load_test_data(mission_id):
            """Load test data into the current mission"""
            try:
                # Vérifier que la mission existe
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                # Charger les données de test depuis la constante TEST_DATA
                test_data = self.TEST_DATA  # Déjà défini dans la classe

                # Sauvegarder dans le fichier demande.md de la mission
                mission_path = os.path.join("missions", mission['name'])
                demande_path = os.path.join(mission_path, "demande.md")

                try:
                    with open(demande_path, 'w', encoding='utf-8') as f:
                        f.write(test_data)

                    self.log_message(f"✓ Données de test chargées pour la mission {mission['name']}", level='success')
                    return jsonify({'status': 'success'})

                except Exception as write_error:
                    self.log_message(f"❌ Erreur d'écriture des données de test: {str(write_error)}", level='error')
                    return jsonify({'error': f'File write error: {str(write_error)}'}), 500

            except Exception as e:
                self.log_message(f"❌ Erreur chargement données test: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/missions/<int:mission_id>/reset', methods=['POST'])
        def reset_mission_files(mission_id):
            try:
                mission = self.mission_service.get_mission(mission_id)
                if not mission:
                    return jsonify({'error': 'Mission not found'}), 404

                # Réinitialiser chaque fichier de la mission
                for file_type, initial_content in self.file_manager._get_initial_contents().items():
                    success = self.mission_service.save_mission_file(
                        mission_id,
                        file_type,
                        initial_content
                    )
                    if not success:
                        return jsonify({'error': f'Failed to reset {file_type}'}), 500

                self.log_message(f"Files reset for mission {mission['name']}", level='success')
                return jsonify({'status': 'success'})
                
            except Exception as e:
                self.log_message(f"Error resetting files: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'running': self.running,
                'agents': {
                    name: {
                        'running': agent.should_run(),
                        'last_update': agent.last_update
                    }
                    for name, agent in self.agents.items()
                }
            })


        @self.app.route('/editor')
        def editor_interface():
            try:
                content = self.file_manager.read_file("production")
                if content is None:
                    content = ""
                    
                suivi_content = self.file_manager.read_file("suivi")
                if suivi_content is None:
                    suivi_content = ""
                    
                return render_template('editor.html', 
                                     content=content, 
                                     suivi_content=suivi_content)
            except Exception as e:
                self.log_message(f"Error loading editor: {str(e)}", level='error')
                return render_template('editor.html',
                                     content="Error loading content",
                                     suivi_content="Error loading suivi content")

        @self.app.route('/')
        def home():
            try:
                with open('production.md', 'r', encoding='utf-8') as f:
                    content = f.read()
                with open('suivi.md', 'r', encoding='utf-8') as f:
                    suivi_content = f.read()
                with open('demande.md', 'r', encoding='utf-8') as f:
                    demande_content = f.read()
                return render_template('clean.html', 
                             content=content, 
                             suivi_content=suivi_content,
                             demande_content=demande_content)
            except Exception as e:
                return f"Error loading content: {str(e)}", 500

        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'running': self.running,
                'agents': {name: agent.should_run() for name, agent in self.agents.items()}
            })

        @self.app.route('/api/content')
        def get_content():
            try:
                content = {}
                for file_name in self.file_paths:
                    try:
                        content[file_name] = self.file_manager.read_file(file_name)
                        # Mettre en cache le contenu
                        self.content_cache[file_name] = content[file_name]
                        self.last_modified[file_name] = time.time()
                    except Exception as e:
                        self.log_message(f"Error reading {file_name}: {str(e)}")
                        content[file_name] = ""
                        
                # Debug log pour vérifier le contenu
                self.log_message(f"Content loaded: {list(content.keys())}")
                return jsonify(content)
            except Exception as e:
                self.log_message(f"Error getting content: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/start', methods=['POST'])
        def start_agents():
            self.start_agents()
            return jsonify({'status': 'started'})

        @self.app.route('/api/stop', methods=['POST'])
        def stop_agents():
            self.stop_agents()
            return jsonify({'status': 'stopped'})

        @self.app.route('/api/logs')
        def get_logs():
            return jsonify({
                'logs': self.logs_buffer
            })
            

        @self.app.route('/api/logs/export')
        def export_logs():
            try:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"parallagon-logs-{timestamp}.txt"
                
                # Format logs with timestamps, levels, and metadata
                formatted_logs = []
                for log in self.logs_buffer:
                    timestamp = log.get('timestamp', '')
                    level = log.get('level', 'info')
                    message = log.get('message', '')
                    agent = log.get('agent', '')
                    operation = log.get('operation', '')
                    status = log.get('status', '')
                    
                    # Build log line with all available information
                    log_parts = [f"[{timestamp}]", f"[{level.upper()}]"]
                    if agent:
                        log_parts.append(f"[{agent}]")
                    if operation:
                        log_parts.append(f"[{operation}]")
                    if status:
                        log_parts.append(f"[{status}]")
                    log_parts.append(message)
                    
                    formatted_logs.append(" ".join(log_parts))
                
                # Add header with export information
                header = [
                    "Parallagon Log Export",
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Total Entries: {len(self.logs_buffer)}",
                    "-" * 80
                ]
                
                # Combine header and logs
                full_content = "\n".join(header + [""] + formatted_logs)
                
                # Create response with file download
                response = make_response(full_content)
                response.headers["Content-Disposition"] = f"attachment; filename={filename}"
                response.headers["Content-Type"] = "text/plain"
                
                self.log_message("Logs exported successfully", level='success')
                return response
            except Exception as e:
                self.log_message(f"Error exporting logs: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs/clear', methods=['POST'])
        def clear_logs():
            try:
                self.logs_buffer.clear()
                return jsonify({'status': 'success'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/suivi', methods=['GET', 'POST'])
        def suivi():
            if request.method == "GET":
                try:
                    content = self.file_manager.read_file("suivi")
                    if content is None:
                        content = ""
                    return jsonify({"content": content})
                except Exception as e:
                    self.log_message(f"Error reading suivi.md: {str(e)}", level='error')
                    return jsonify({"content": "", "error": str(e)}), 500
            elif request.method == "POST":
                try:
                    content = request.get_json()["content"]
                    success = self.file_manager.write_file("suivi", content)
                    if not success:
                        raise Exception("Failed to write suivi.md")
                    return jsonify({"status": "success"})
                except Exception as e:
                    self.log_message(f"Error writing suivi.md: {str(e)}", level='error')
                    return jsonify({"error": str(e)}), 500

        @self.app.route('/api/changes')
        def get_changes():
            """Return and clear pending changes"""
            try:
                # Obtenir le timestamp actuel
                current_time = datetime.now()
                
                # Convertir les timestamps des notifications en objets datetime pour comparaison
                recent_notifications = []
                for n in self.notifications_queue:
                    try:
                        # Convertir le timestamp de la notification en datetime
                        notif_time = datetime.strptime(n['timestamp'], "%H:%M:%S")
                        # Utiliser la date d'aujourd'hui avec l'heure de la notification
                        notif_datetime = current_time.replace(
                            hour=notif_time.hour,
                            minute=notif_time.minute,
                            second=notif_time.second
                        )
                        
                        # Garder seulement les notifications des 3 dernières secondes
                        if (current_time - notif_datetime).total_seconds() <= 3:
                            recent_notifications.append(n)
                            
                    except ValueError as e:
                        self.log_message(f"Invalid timestamp format in notification: {e}", level='error')
                        continue
                
                # Debug logging
                if recent_notifications:
                    self.log_message(
                        f"Sending {len(recent_notifications)} notifications", 
                        level='debug'
                    )
                
                # Clear queue after getting notifications
                self.notifications_queue = []
                
                return jsonify(recent_notifications)
                    
            except Exception as e:
                self.log_message(f"Error in get_changes: {str(e)}", level='error')
                return jsonify([])

        @self.app.route('/api/notifications', methods=['GET'])
        @self.limiter.limit("500 per minute")
        def get_notifications():
            """Get pending notifications"""
            try:
                # Récupérer les notifications en attente
                notifications = []
                
                # Ajouter les notifications de la queue
                while self.notifications_queue:
                    notification = self.notifications_queue.pop(0)
                    notifications.append(notification)
                    print(f"Sending notification: {notification}")  # Debug log
                    
                # Debug log
                if notifications:
                    print(f"Sending {len(notifications)} notifications to frontend")
                    
                return jsonify(notifications)
                
            except Exception as e:
                self.log_message(f"Error getting notifications: {str(e)}", level='error')
                # Retourner une liste vide au lieu d'une erreur 500
                return jsonify([])

        @self.app.route('/api/demande', methods=['POST'])
        def save_demande():
            try:
                data = request.get_json()
                
                # Debug logs
                self.log_message(f"Received save request with data: {data}", level='debug')
                
                if not data or 'content' not in data:
                    self.log_message("❌ Pas de contenu fourni pour la demande", level='error')
                    return jsonify({'error': 'No content provided'}), 400

                # Vérification explicite de la mission
                if 'missionId' not in data or 'missionName' not in data:
                    self.log_message("❌ Informations de mission manquantes", level='error')
                    return jsonify({'error': 'Mission information missing'}), 400

                # Mise à jour du FileManager avec le nom de la mission
                self.file_manager.current_mission = data['missionName']

                # Construction du chemin avec vérification
                mission_path = os.path.join("missions", data['missionName'])
                if not os.path.exists(mission_path):
                    os.makedirs(mission_path, exist_ok=True)
                    self.log_message(f"✓ Dossier mission créé: {mission_path}", level='info')

                demande_path = os.path.join(mission_path, "demande.md")
                
                # Log du chemin pour debug
                self.log_message(f"Saving to path: {demande_path}", level='debug')

                # Écriture du fichier
                try:
                    with open(demande_path, 'w', encoding='utf-8') as f:
                        f.write(data['content'])
                    
                    self.log_message("✓ Demande sauvegardée", level='success')
                    
                    # Notification du changement
                    self.handle_content_change(
                        'demande.md',
                        data['content'],
                        panel_name='Demande'
                    )
                    return jsonify({'status': 'success', 'success': True})
                    
                except Exception as write_error:
                    self.log_message(f"❌ Erreur d'écriture: {str(write_error)}", level='error')
                    return jsonify({'error': f'File write error: {str(write_error)}'}), 500
                    
            except Exception as e:
                self.log_message(f"❌ Erreur générale: {str(e)}", level='error')
                return jsonify({'error': str(e)}), 500

    def run(self, host='0.0.0.0', port=5000, **kwargs):
        """Run the Flask application with optional configuration parameters"""
        self.app.run(host=host, port=port, **kwargs)

    def monitor_agents(self):
        """Monitor agents and restart them if they crash"""
        while self.running:
            try:
                for name, agent in self.agents.items():
                    if agent.running:
                        # Check if agent is active but stuck
                        if (agent.last_run and 
                            (datetime.now() - agent.last_run).seconds > 30):  # 30s timeout
                            self.log_message(
                                f"Agent {name} seems stuck, restarting...", 
                                level='warning'
                            )
                            # Restart agent
                            agent.stop()
                            agent.start()
                            thread = threading.Thread(
                                target=agent.run,
                                daemon=True,
                                name=f"Agent-{name}"
                            )
                            thread.start()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                self.log_message(f"Error in monitor_agents: {str(e)}", level='error')

    def start_agents(self):
        """Start all agents"""
        try:
            self.log_message("🚀 Démarrage des agents...", level='info')
            self.running = True
            
            # Start monitor thread
            self.monitor_thread = threading.Thread(
                target=self.monitor_agents,
                daemon=True,
                name="AgentMonitor"
            )
            self.monitor_thread.start()
            
            # Start content update loop
            def update_loop():
                self.log_message("✓ Boucle de mise à jour démarrée", level='success')
                while self.running:
                    try:
                        self.check_content_updates()
                    except Exception as e:
                        self.log_message(f"❌ Erreur dans la boucle de mise à jour: {str(e)}", level='error')
                    time.sleep(1)  # Check every second
            
            # Start update loop in separate thread
            self.update_thread = threading.Thread(target=update_loop, daemon=True)
            self.update_thread.start()
            
            # Start agents in separate threads
            for name, agent in self.agents.items():
                try:
                    thread = threading.Thread(target=agent.run, daemon=True)
                    thread.start()
                    self.log_message(f"✓ Agent {name} démarré", level='success')
                except Exception as e:
                    self.log_message(f"❌ Erreur démarrage agent {name}: {str(e)}", level='error')
                    
            self.log_message("✨ Tous les agents sont actifs", level='success')
            
        except Exception as e:
            self.log_message(f"❌ Erreur globale: {str(e)}", level='error')
            raise

    def stop_agents(self):
        """Stop all agents and update loop"""
        try:
            self.running = False
            if hasattr(self, 'update_thread'):
                self.update_thread.join(timeout=2)
                
            # Arrêter chaque agent individuellement et réinitialiser leur état
            for name, agent in self.agents.items():
                try:
                    # Arrêter l'agent
                    agent.stop()
                    agent.running = False  # S'assurer que l'état est bien mis à False
                    
                    # Réinitialiser les métriques de l'agent
                    agent.last_run = None
                    agent.last_change = None
                    agent.consecutive_no_changes = 0
                    
                    # Notifier le frontend
                    self.handle_content_change(
                        agent.file_path,
                        "",  # contenu vide car on s'intéresse juste au changement d'état
                        panel_name=name,
                        flash=True
                    )
                    
                    self.log_message(f"Agent {name} stopped successfully", level='info')
                    
                except Exception as e:
                    self.log_message(f"Error stopping agent {name}: {str(e)}", level='error')
                    continue
                    
            # Vider la queue des agents en cours
            self.runningAgents = set()
            
            self.log_message("All agents stopped", level='success')
            
        except Exception as e:
            self.log_message(f"Error in stop_agents: {str(e)}", level='error')
            raise

    def log_message(self, message, operation: str = None, status: str = None, level: str = 'info'):
        """Log a message with optional operation, status and color"""
        try:
            # Utiliser un format de date cohérent
            timestamp = datetime.now().strftime("%H:%M:%S")  # Format court HH:MM:SS
            
            # Determine color based on level
            color = self.LOG_COLORS.get(level, 'black')
            
            # Format log entry
            if operation and status:
                log_entry = {
                    'id': len(self.logs_buffer),
                    'timestamp': timestamp,
                    'message': f"{operation}: {status} - {message}",
                    'level': level,
                    'color': color
                }
            else:
                log_entry = {
                    'id': len(self.logs_buffer),
                    'timestamp': timestamp,
                    'message': message,
                    'level': level,
                    'color': color
                }
            
            # Add to logs buffer
            self.logs_buffer.append(log_entry)
            
            # Keep only last 100 logs
            if len(self.logs_buffer) > 100:
                self.logs_buffer = self.logs_buffer[-100:]
            
            # Print to console for debugging
            print(f"[{timestamp}] [{level}] {message}")
                
        except Exception as e:
            print(f"Error logging message: {str(e)}")

    def safe_operation(self, operation_func):
        """Decorator for safe operation execution with recovery"""
        def wrapper(*args, **kwargs):
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    return operation_func(*args, **kwargs)
                except Exception as e:
                    retry_count += 1
                    self.log_message(
                        str(e),
                        operation=operation_func.__name__,
                        status=f"RETRY {retry_count}/{max_retries}"
                    )
                    
                    if retry_count == max_retries:
                        self.log_message(
                            "Operation failed permanently",
                            operation=operation_func.__name__,
                            status="FAILED"
                        )
                        raise
                    
                    time.sleep(1)  # Wait before retry
                    
        return wrapper

    def check_content_updates(self):
        """Check for content updates"""
        try:
            # Read current content of all files
            current_content = {}
            for file_name, path in self.file_paths.items():
                content = self.file_manager.read_file(file_name)
                if content is not None:
                    current_content[file_name] = content

            # Compare with last known content
            if not hasattr(self, 'last_content'):
                self.last_content = {}

            # Check changes for each file
            for file_name, content in current_content.items():
                if content is None:
                    continue
                    
                if (file_name not in self.last_content or 
                    content != self.last_content[file_name]):
                    # Content modified or new file
                    self.handle_content_change(
                        file_name, 
                        content,
                        panel_name=file_name.split('.')[0].capitalize()
                    )
                    self.last_content[file_name] = content
                    self.log_message(f"Content updated in {file_name}")

        except Exception as e:
            self.log_message(f"Error checking content updates: {str(e)}", level='error')

    def setup_error_handlers(self):
        @self.app.errorhandler(404)
        def not_found_error(error):
            return jsonify({'error': 'Resource not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500

        @self.app.errorhandler(Exception)
        def handle_exception(error):
            return jsonify({'error': str(error)}), 500

    def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            # Stop all agents
            self.stop_agents()
            
            # Clear caches
            self.content_cache.clear()
            self.last_modified.clear()
            
            # Export final logs
            self.export_logs()
            
            self.log_message("Application shutdown complete")
        except Exception as e:
            self.log_message(f"Error during shutdown: {str(e)}")

    def update_agent_paths(self, mission_name: str) -> None:
        """Update file paths for all agents when mission changes"""
        try:
            # Utiliser un chemin absolu pour le dossier mission
            mission_dir = os.path.abspath(os.path.join("missions", mission_name))
            
            self.log_message(f"Updating agent paths for mission: {mission_name}", level='debug')
            self.log_message(f"Mission directory (absolute): {mission_dir}", level='debug')
            
            # Créer les chemins absolus pour chaque fichier
            new_paths = {
                "Production": os.path.join(mission_dir, "production.md"),
                "Specification": os.path.join(mission_dir, "specifications.md"),
                "Management": os.path.join(mission_dir, "management.md"),
                "Evaluation": os.path.join(mission_dir, "evaluation.md"),
                "Suivi": os.path.join(mission_dir, "suivi.md"),
                "Contexte": os.path.join(mission_dir, "contexte.md")
            }
            
            # Mettre à jour les chemins des agents
            for name, agent in self.agents.items():
                if name in new_paths:
                    old_path = agent.file_path
                    # Mettre à jour avec le nouveau chemin absolu
                    agent.file_path = os.path.abspath(new_paths[name])
                    
                    # Debug log pour vérifier le changement
                    self.log_message(
                        f"Agent {name} path updated:\nOLD: {old_path}\nNEW: {agent.file_path}", 
                        level='debug'
                    )
                    
                    # Vérifier que le dossier existe
                    os.makedirs(os.path.dirname(agent.file_path), exist_ok=True)
                    
                    # Mettre à jour watch_files avec les nouveaux chemins absolus
                    agent.watch_files = [
                        os.path.abspath(new_paths[other_name])
                        for other_name in new_paths.keys()
                        if other_name != name
                    ]
            
            self.log_message(f"✓ Agent paths updated for mission: {mission_name}", level='success')
            
        except Exception as e:
            self.log_message(f"❌ Error updating agent paths: {str(e)}", level='error')
            import traceback
            self.log_message(traceback.format_exc(), level='error')

    def get_app(self):
        """Return the Flask app instance"""
        return self.app

if __name__ == "__main__":
    # Load keys from .env file
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    config = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY")
    }
    
    # Validate API keys
    if not config["openai_api_key"] or config["openai_api_key"] == "your-api-key-here":
        raise ValueError("OPENAI_API_KEY not configured in .env file")
        
    if not config["anthropic_api_key"] or config["anthropic_api_key"] == "your-api-key-here":
        raise ValueError("ANTHROPIC_API_KEY not configured in .env file")
    
    app = ParallagonWeb(config)
    # Change port to 8000 to match frontend
    app.run(host='0.0.0.0', port=8000, debug=True)
