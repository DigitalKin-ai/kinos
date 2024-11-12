# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

KinOS offre une interface en ligne de commande minimaliste qui opère directement dans votre dossier de projet.

## Commandes de Base

```bash
# Lancer KinOS avec l'équipe par défaut
kin

# Lancer une équipe spécifique
kin coding
kin book-writing
kin literature-review

# Mode verbeux
kin -v coding
```

## Gestion des Phases

Les phases permettent d'optimiser automatiquement l'utilisation des ressources :

### Commandes
```bash
# Voir le statut actuel
kin phase status

# Voir les métriques détaillées
kin phase metrics

# Voir l'historique
kin phase history

# Forcer une phase (si nécessaire)
kin phase set expansion
kin phase set convergence
```

### Surveillance
```bash
# Voir l'utilisation des tokens
kin tokens list

# Vérifier les limites
kin tokens check

# Voir la marge disponible
kin tokens headroom
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
