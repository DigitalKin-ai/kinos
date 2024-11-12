# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

KinOS offre une interface en ligne de commande minimaliste qui opère directement dans votre dossier de projet.

## Commande Principale

```bash
kin [options]
```

## Utilisation de Base

```bash
# Lancer KinOS dans le dossier courant
cd votre-projet
kin

# Activer le mode verbeux
kin -v

# Voir l'aide
kin --help
```

## Gestion des Phases

### Commandes de Phase
```bash
# Voir le statut actuel
kin phase status

# Voir les métriques de tokens
kin phase tokens

# Voir l'historique des transitions
kin phase history

# Forcer un changement de phase
kin phase set expansion   # Passer en phase d'expansion
kin phase set convergence # Passer en phase de convergence

# Surveiller les changements de phase
kin phase watch
```

### Gestion des Tokens
```bash
# Voir l'utilisation par fichier
kin tokens list

# Vérifier les avertissements
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
