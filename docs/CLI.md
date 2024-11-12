# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

KinOS offre une interface en ligne de commande minimaliste qui opère directement dans votre dossier de projet.

## Commandes de Base

```bash
# Lancer KinOS dans le dossier courant
cd votre-projet
kin

# Lancer une équipe spécifique
kin coding
kin book-writing
kin literature-review

# Mode verbeux
kin -v

# Gestion des Phases
kin phase status      # Voir la phase actuelle
kin phase metrics     # Voir les métriques détaillées
kin phase set expansion    # Forcer la phase expansion
kin phase set convergence  # Forcer la phase convergence
kin phase history         # Voir l'historique des transitions

# Gestion des Tokens
kin tokens list      # Liste l'utilisation par fichier
kin tokens check     # Vérifier les avertissements
kin tokens headroom  # Voir la marge disponible
kin tokens usage     # Voir l'utilisation totale
```

## Gestion des Phases

Les phases permettent d'optimiser automatiquement l'utilisation des ressources :

### Phase Commands
```bash
# Voir le statut actuel
kin phase status      # Phase actuelle et utilisation
kin phase metrics     # Métriques détaillées
kin phase history     # Historique des transitions

# Forcer une phase (avec précaution)
kin phase set expansion    # Passer en phase expansion
kin phase set convergence  # Passer en phase convergence

# Surveillance des tokens
kin tokens list           # Utilisation par fichier
kin tokens check          # Vérifier les avertissements
kin tokens headroom       # Marge disponible
kin tokens usage          # Utilisation totale (128k max)

# Seuils de Phase
- EXPANSION   : < 60% tokens (76.8k)
- CONVERGENCE : > 60% tokens
- Retour EXPANSION : < 50% tokens (64k)
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
