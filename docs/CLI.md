# KinOS Command Line Interface (CLI)

## Vue d'Ensemble

La CLI KinOS offre une interface simplifiée pour lancer des équipes d'agents dans le répertoire de travail actuel.

## Utilisation de Base

```bash
# Lancer une équipe dans le répertoire courant
kin <nom-equipe>
```

## Commandes Disponibles

### Lancement d'Équipe

#### Syntaxe Simplifiée
```bash
# Lancer l'équipe de rédaction
kin book-writing

# Lancer l'équipe de développement
kin coding

# Lancer l'équipe de revue littéraire
kin literature-review
```

### Équipes Prédéfinies

1. **book-writing**
   - Idéal pour la rédaction de contenu
   - Agents : Spécifications, Gestion, Évaluation, Rédacteur, etc.

2. **coding**
   - Pour les projets de développement logiciel
   - Agents : Spécifications, Production, Test, Validation, etc.

3. **literature-review**
   - Pour l'analyse et la revue de documents
   - Agents : Spécifications, Gestion, Évaluation, Chroniqueur, etc.

### Options Avancées

```bash
# Mode verbose pour plus de détails
kin <nom-equipe> -v

# Afficher l'aide
kin --help
```

## Comportement

- **Répertoire Courant** : L'équipe est lancée dans le dossier actuel
- **Équipe par Défaut** : Déterminée par le premier argument
- **Lancement Automatique** : Démarre immédiatement les agents

## Exemples Pratiques

```bash
# Dans un projet de livre
cd mon-projet-livre
kin book-writing

# Dans un projet de développement
cd mon-projet-code
kin coding

# Avec mode verbose
cd mon-projet-analyse
kin literature-review -v
```

## Prérequis

- Python 3.8+
- KinOS installé
- Clés API configurées
- Répertoire de projet initialisé

## Dépannage

- Vérifiez que vous êtes dans le bon répertoire
- Assurez-vous que les clés API sont configurées
- Consultez les logs en cas d'erreur
- Utilisez l'option `-v` pour plus de détails

## Versions

- Version actuelle : 0.1.0
- Dernière mise à jour : 2024-02-15
