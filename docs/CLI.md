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

# Options de Modèle
kin --model <model-name>   # Utiliser un modèle spécifique

Modèles disponibles :
- Anthropic : claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022
- OpenAI : gpt-4o, gpt-4o-mini

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

## Exemples Pratiques

```bash
# Démarrer dans un projet
cd mon-projet
kin

# Utiliser un modèle spécifique
kin coding --model claude-3-haiku-20240307    # Utiliser Claude 3 Haiku
kin book --model gpt-4-0125-preview           # Utiliser GPT-4
kin review --model invalid-model              # Voir les modèles disponibles
```
## Version et Compatibilité

- Version : 0.2.0
- Python : 3.8+
- Mise à jour : 2024-03-21
