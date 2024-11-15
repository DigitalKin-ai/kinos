# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

KinOS est un framework d'agents autonomes qui opère directement dans votre dossier de projet. Aucune configuration n'est requise - il suffit de lancer la commande `kin` dans n'importe quel dossier.

## Commandes Simplifiées

```bash
# Lancer KinOS dans le dossier courant
cd votre-projet
kin

# Lancer une équipe spécifique
kin coding      # Équipe de développement
kin book        # Équipe de rédaction
kin review      # Équipe de revue

# Options globales
kin -v                                    # Mode verbeux
kin -p /chemin                            # Dossier spécifique
kin --model claude-3-haiku-20240307      # Utiliser un modèle spécifique
kin --model gpt-4-0125-preview           # Utiliser GPT-4

# Système de Phases
kin phase                 # Voir statut actuel
kin phase status         # Détails d'utilisation
kin phase set expansion  # Forcer phase expansion
kin phase set convergence # Forcer phase convergence

# Surveillance des Tokens
kin tokens              # Vue d'ensemble
kin tokens list        # Liste par fichier
kin tokens check       # Vérifier alertes
kin tokens headroom    # Marge disponible

# Métriques et Limites
- Limite totale : 128k tokens
- EXPANSION : < 76.8k tokens (60%)
- CONVERGENCE : > 76.8k tokens
- Retour EXPANSION : < 64k tokens (50%)
```

## Système de Phases

Le système de phases optimise automatiquement l'utilisation des ressources selon l'usage des tokens :

### EXPANSION (< 60% tokens)
- Création libre de contenu
- Développement de nouvelles fonctionnalités
- Documentation extensive
- Optimisation non prioritaire

### CONVERGENCE (> 60% tokens)
- Optimisation du contenu existant
- Réduction de la duplication
- Consolidation des documents
- Limitation des nouvelles créations

### Commandes de Phase
```bash
# Statut et Métriques
kin phase status      # Phase actuelle et utilisation
kin phase metrics     # Métriques détaillées
kin phase history     # Historique des transitions

# Contrôle Manuel (utiliser avec précaution)
kin phase set expansion    # Forcer phase expansion
kin phase set convergence  # Forcer phase convergence

# Surveillance des Tokens
kin tokens list      # Utilisation par fichier
kin tokens check     # Alertes et avertissements
kin tokens headroom  # Marge disponible
kin tokens usage     # Utilisation totale

# Seuils et Transitions
- Limite totale : 128k tokens
- CONVERGENCE : > 76.8k tokens (60%)
- EXPANSION : < 64k tokens (50%)
```

## Comportement

- **Contexte** : Utilise le dossier courant comme racine du projet
- **Configuration** : Aucune configuration requise
- **Phases** : Transition automatique selon l'utilisation des tokens
  * EXPANSION (< 60% tokens)
  * CONVERGENCE (> 60% tokens)

## Exemples Pratiques

```bash
# Démarrer dans un projet
cd mon-projet
kin

# Utiliser un modèle spécifique
kin coding --model claude-3-haiku-20240307    # Utiliser Claude 3 Haiku
kin book --model gpt-4-0125-preview           # Utiliser GPT-4
kin review --model invalid-model              # Voir les modèles disponibles

# Surveiller l'utilisation des tokens
kin phase status
kin tokens list

# Optimiser quand nécessaire
kin phase set convergence
kin tokens check
```

## Dépannage

1. **Vérifications de Base**
   - Vous êtes dans le bon dossier
   - Les clés API sont configurées
   - Aider est installé et fonctionnel

2. **Logs et Diagnostic**
   - Utilisez `-v` pour le mode verbeux
   - Consultez les logs dans `./logs/`
   - Vérifiez le statut des phases

3. **Problèmes Courants**
   - Permission denied → Vérifiez les droits du dossier
   - API key error → Reconfigurez les clés API
   - Phase errors → Vérifiez l'utilisation des tokens

## Version et Compatibilité

- Version : 0.2.0
- Python : 3.8+
- Mise à jour : 2024-03-21
