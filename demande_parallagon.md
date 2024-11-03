# Parallagon
*Framework d'Agents Autonomes Parallèles*

## 1. Vue d'Ensemble

### 1.1 Vision
Parallagon est un framework minimaliste d'agents autonomes travaillant en parallèle pour accélérer et améliorer le développement de projets complexes. Chaque agent gère son propre fichier et opère de manière continue et indépendante.

### 1.2 Principes Fondamentaux
- Simplicité maximale dans la conception
- Communication via fichiers markdown
- Modifications non-linéaires via SEARCH/REPLACE
- Autonomie complète des agents
- État persistant dans les fichiers

## 2. Architecture

### 2.1 Structure des Fichiers
```plaintext
/parallagon
  specifications.md  # Agent Spécification
  management.md     # Agent Management
  production.md     # Agent Production
  evaluation.md     # Agent Evaluation
```

### 2.2 Format Standard des Fichiers
```markdown
# État Actuel
[status: STATUS]
Description de l'état...

# Signaux
- À [Agent]: [Message]
- De [Agent]: [Message]
- Action requise: [Description]

# Contenu Principal
[Contenu spécifique à chaque agent]

# Historique
- [Timestamp] Action effectuée
- [Timestamp] Modification réalisée
```

### 2.3 Format du Template (specifications.md)
```markdown
# Section 1
[contraintes: description des exigences pour cette section]

# Section 2
[contraintes: description des exigences pour cette section]

# Section N
[contraintes: description des exigences pour cette section]
```

## 3. Agents

### 3.1 Agent Spécification
- **Fichier**: specifications.md
- **Rôle**: Gestion du template et de la structure documentaire
- **Responsabilités**:
  * Définition du template de document
  * Gestion des sections requises
  * Maintien des contraintes par section
  * Synchronisation de la structure avec production.md

### 3.2 Agent Management
- **Fichier**: management.md
- **Rôle**: Coordination et planification
- **Responsabilités**:
  * Planification des tâches
  * Résolution des blocages
  * Priorisation des actions
  * Suivi de l'avancement

### 3.3 Agent Production
- **Fichier**: production.md
- **Rôle**: Création et implémentation du contenu
- **Responsabilités**:
  * Développement du contenu selon le template
  * Respect des contraintes de section
  * Documentation technique
  * Signalement des problèmes de contenu

### 3.4 Agent Évaluation
- **Fichier**: evaluation.md
- **Rôle**: Contrôle qualité et validation
- **Responsabilités**:
  * Tests et validation
  * Feedback sur la qualité
  * Identification des améliorations
  * Sign-off final

## 4. Pattern de Modification

### 4.1 Principe SEARCH/REPLACE
```python
def update_file(file_path, old_str, new_str):
    content = read_file(file_path)
    assert content.count(old_str) == 1, "Le texte à remplacer doit être unique"
    updated_content = content.replace(old_str, new_str)
    write_file(file_path, updated_content)
```

### 4.2 Règles de Modification
1. `old_str` doit être exactement identique au texte à remplacer
2. `old_str` doit apparaître une seule fois dans le fichier
3. Modifications atomiques et précises
4. Points d'ancrage clairs (titres, sections)

### 4.3 Exemples de Modification
```python
# Mise à jour d'état
old_str = "[status: DRAFT]"
new_str = "[status: REVIEW]"

# Ajout de signal
old_str = "# Signaux\n"
new_str = """# Signaux
- À Production: Nouvelle tâche
"""

# Mise à jour de contenu
old_str = "Section Alpha..."
new_str = """Section Alpha:
- Nouveau point ajouté
- Modification effectuée"""
```

## 5. Cycle de Fonctionnement

### 5.1 Boucle Principale d'un Agent
1. Lire tous les fichiers pertinents
2. Analyser les changements et signaux
3. Prendre des décisions basées sur l'analyse
4. Effectuer les modifications nécessaires
5. Pause courte
6. Répéter

### 5.2 États Possibles
- DRAFT: En cours de travail
- REVIEW: En attente de validation
- APPROVED: Validé et finalisé
- BLOCKED: Nécessite une intervention

### 5.3 Communication
- Via section "Signaux" des fichiers
- Format : "À/De [Agent]: [Message]"
- Chaque agent surveille ses signaux
- Messages clairs et actionnables

### 5.4 Synchronisation Template-Production
1. L'agent Spécification définit/met à jour le template
2. Détection automatique des changements de structure
3. Synchronisation des sections dans production.md :
   - Ajout des nouvelles sections avec placeholder
   - Suppression des sections obsolètes
   - Conservation du contenu existant des sections maintenues
4. Notification des changements structurels aux autres agents

## 6. Implémentation

### 6.1 Prérequis
- Python 3.9+
- Accès aux API LLM ()
- Système de fichiers standard

### 6.2 Configuration Minimale
```python
AGENT_CONFIG = {
    "model": "claude-3-5-sonnet-20241022",
    "file_path": "path/to/file.md",
    "check_interval": 5,  # seconds
}
```

### 6.3 Structure de Base d'un Agent
```python
class ParallagonAgent:
    def __init__(self, config):
        self.config = config
        self.file_path = config["file_path"]
    
    def run(self):
        while True:
            self.read_files()
            self.analyze()
            self.update()
            time.sleep(self.config["check_interval"])
```

## 7. Best Practices

### 7.1 Modification de Fichiers
- Structure gérée exclusivement par l'agent Spécification
- Modifications de contenu uniquement dans les sections définies
- Respect des contraintes de section
- Documentation des changements de contenu

### 7.2 Communication
- Messages clairs et concis
- Une action par signal
- Accuser réception des messages importants
- Escalader les problèmes au management

### 7.3 Gestion d'État
- Transitions d'état explicites
- Documentation des raisons de changement
- Validation avant approbation finale
- Traçabilité des décisions

## 8. Limites et Contraintes

### 8.1 Techniques
- Un agent par fichier
- Modifications atomiques uniquement
- Pas de modifications simultanées
- Temps de réponse non garanti

### 8.2 Opérationnelles
- Dépendance aux LLMs
- Latence inhérente aux lectures/écritures
- Besoin de points d'ancrage uniques
- Gestion manuelle des deadlocks

## 9. Extensions Futures

### 9.1 Améliorations Potentielles
- Support multi-projets
- Agents spécialisés additionnels
- Interface de monitoring
- Analyse de performance

### 9.2 Domaines d'Application
- Développement logiciel
- Création de contenu
- Gestion de documentation
- Projets créatifs

## 10. Relations avec l'Objet Section

### 10.1 Structure de l'Objet Section
```python
@dataclass
class Section:
    title: str                # Titre de la section
    constraints: str          # Contraintes définies
    content: Optional[str]    # Contenu actuel
    evaluation: Optional[str] # État d'évaluation
    todo: Optional[List[str]] # Liste des tâches à faire
```

### 10.2 Responsabilités des Agents

#### SpecificationsAgent
- **Rôle Principal**: Définition et gestion de la structure des sections
- **Interactions**:
  * Crée les sections avec leurs contraintes initiales
  * Définit la hiérarchie des sections (niveau 1, 2, 3)
  * Met à jour les contraintes selon l'évolution des besoins
  * Synchronise la structure avec production.md
- **Attributs gérés**: `title`, `constraints`

#### ProductionAgent
- **Rôle Principal**: Gestion du contenu des sections
- **Interactions**:
  * Remplit le contenu des sections existantes
  * Met à jour le contenu selon les directives
  * Respecte les contraintes définies
  * Ne peut pas modifier la structure
- **Attributs gérés**: `content`

#### EvaluationAgent
- **Rôle Principal**: Évaluation de la qualité des sections
- **Interactions**:
  * Analyse le contenu par rapport aux contraintes
  * Attribue un état d'évaluation (VALIDATED|NEEDS_WORK|REJECTED)
  * Fournit des retours détaillés par section
  * Maintient les métriques de qualité
- **Attributs gérés**: `evaluation`

#### ManagementAgent
- **Rôle Principal**: Coordination et suivi des sections
- **Interactions**:
  * Priorise les sections à traiter
  * Coordonne les mises à jour entre agents
  * Suit l'avancement global
  * Gère les blocages et dépendances
  * Définit et met à jour les tâches par section
- **Attributs consultés**: Tous
- **Attributs modifiés**: `todo` (liste des tâches à faire)

### 10.3 Flux de Travail des Sections

1. **Création & Structure** (SpecificationsAgent)
   ```plaintext
   Section créée → Contraintes définies → Structure synchronisée
   ```

2. **Production de Contenu** (ProductionAgent)
   ```plaintext
   Section vide → Contenu initial → Mises à jour itératives
   ```

3. **Évaluation** (EvaluationAgent)
   ```plaintext
   Contenu produit → Analyse → Attribution état → Feedback
   ```

4. **Coordination** (ManagementAgent)
   ```plaintext
   Suivi états → Priorisation → Résolution blocages → Direction
   ```

### 10.4 Règles de Modification

1. **Modifications Structurelles**
   - Exclusivement via SpecificationsAgent
   - Nécessite synchronisation avec production.md
   - Préserve le contenu existant

2. **Modifications de Contenu**
   - Uniquement via ProductionAgent
   - Dans les sections existantes
   - Respecte les contraintes

3. **Modifications d'Évaluation**
   - Exclusivement via EvaluationAgent
   - Format standardisé
   - Basées sur critères définis

4. **Coordination**
   - ManagementAgent orchestre
   - Ne modifie pas directement
   - Communique via signaux

### 10.5 Communication Inter-Agents

```plaintext
SpecificationsAgent ←→ ProductionAgent
    - Synchronisation structure
    - Mise à jour contraintes

ProductionAgent ←→ EvaluationAgent
    - Soumission contenu
    - Retours évaluation

EvaluationAgent ←→ ManagementAgent
    - Rapports qualité
    - Priorisation révisions

ManagementAgent ←→ Tous
    - Coordination globale
    - Résolution blocages
```

### 10.6 Gestion des États

1. **États de Section**
   - Structure: Définie/En révision
   - Contenu: Vide/En cours/Complet
   - Évaluation: VALIDATED/NEEDS_WORK/REJECTED

2. **Transitions**
   ```plaintext
   Création → Production → Évaluation → Validation
   ↑__________________________|
   (Si révision nécessaire)
   ```

3. **Synchronisation**
   - Atomique par section
   - Préservation des données
   - Gestion des conflits

### 9.1 Améliorations Potentielles
- Support multi-projets
- Agents spécialisés additionnels
- Interface de monitoring
- Analyse de performance

### 9.2 Domaines d'Application
- Développement logiciel
- Création de contenu
- Gestion de documentation
- Projets créatifs

# Interface Graphique Parallagon

## 1. Structure des Fichiers
```plaintext
/parallagon
  demande.md         # Fichier de demande utilisateur
  specifications.md  # Agent Spécification
  management.md     # Agent Management
  production.md     # Agent Production
  evaluation.md     # Agent Evaluation
```

## 2. Format demande.md
```markdown
# Demande Actuelle
[timestamp: 2024-11-02 15:30]
[status: EN_COURS]

Description de la demande utilisateur...

# Historique des Demandes
- [2024-11-02 15:00] Demande précédente
- [2024-11-02 14:30] Autre demande
```

## 3. Interface Graphique

### 3.1 Layout
```plaintext
┌────────────────────────────────────────────────┐
│ ⚫ Parallagon                             - □ x │
├────────────────────────────────────────────────┤
│ [Start] [Stop]                                 │
├────────────────────────────────────┬───────────┤
│ Demande:                           │ Status:   │
│ [Zone de texte demande]           │ ● Running  │
│                                   │           │
├───────────────┬───────────────────┴───────────┤
│ Specification │ Management                     │
│ [Contenu]     │ [Contenu]                     │
│               │                               │
├───────────────┼───────────────────────────────┤
│ Production    │ Evaluation                    │
│ [Contenu]     │ [Contenu]                     │
│               │                               │
└───────────────┴───────────────────────────────┘
```

### 3.2 Composants
1. **Contrôles**
   - Bouton Start: Lance tous les agents
   - Bouton Stop: Arrête tous les agents
   - Indicateur de statut (rouge/vert)

2. **Zone Demande**
   - Champ texte pour la nouvelle demande
   - Affichage de la demande en cours
   - Historique des demandes récentes

3. **Zones Agents**
   - 4 panneaux de taille égale
   - Mise à jour en temps réel
   - Scroll automatique
   - Highlight des modifications récentes

## 4. Fonctionnement

### 4.1 Actualisation
```python
class ParallagonGUI:
    def __init__(self):
        self.update_interval = 1000  # ms
        self.running = False
    
    def start_update_loop(self):
        while True:
            if self.running:
                self.update_all_panels()
            time.sleep(1)
```

### 4.2 Lecture des Fichiers
```python
def update_panel_content(self, file_path, panel):
    content = read_file(file_path)
    panel.set_text(content)
    panel.highlight_changes()
```

### 4.3 Gestion des Demandes
```python
def submit_request(self, text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_request = f"""# Demande Actuelle
[timestamp: {timestamp}]
[status: EN_COURS]

{text}

# Historique des Demandes"""
    
    update_file("demande.md", old_str="# Demande Actuelle", new_str=new_request)
```

## 5. Implémentation Technique

### 5.1 Technologies
- Python + Tkinter (simple, intégré)
- Pas de dépendances externes
- Architecture single-thread avec update loop

### 5.2 Classes Principales
```python
class ParallagonGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_ui()
        
    def setup_ui(self):
        self.create_control_panel()
        self.create_request_panel()
        self.create_agent_panels()

class AgentPanel:
    def __init__(self, parent, title):
        self.frame = tk.Frame(parent)
        self.text = tk.Text(self.frame)
        self.setup_view()
```

## 6. Comportement

### 6.1 Start/Stop
- Start: Lance les agents et l'update loop
- Stop: Arrête les agents proprement
- Statut visuel clair de l'état du système

### 6.2 Mise à Jour
- Lecture non-bloquante des fichiers
- Highlight temporaire des changements
- Scrolling intelligent (garder la position)

### 6.3 Soumission Demande
- Validation basique du texte
- Confirmation visuelle
- Mise à jour immédiate du panneau

## 7. Contraintes

### 7.1 Performance
- Update max 1/s par panneau
- Taille maximale affichée: 1000 lignes
- Pas de recherche temps réel

### 7.2 Interface
- Pas de redimensionnement complexe
- Pas de thèmes personnalisés
- Pas de raccourcis clavier complexes

## 8. Extensions Futures

# Demande Actuelle
[timestamp: 2024-03-21 10:00]
[status: NEW]

Créer une nouvelle fonctionnalité pour exporter les logs de l'application dans un fichier texte.
Cette fonctionnalité devrait:
- Permettre de sauvegarder les logs dans un fichier
- Inclure les horodatages
- Formater les logs de manière lisible
- Être accessible depuis l'interface graphique

# Historique des Demandes
- [2024-03-21 10:00] Demande d'export des logs
- [INIT] Création du fichier
