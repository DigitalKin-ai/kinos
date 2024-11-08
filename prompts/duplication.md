# Agent de Détection de Duplication

## Instructions

est-ce qu'il y a de la duplication de fonction ou d'information ? à partir des informations disponibles, réduis la duplication dans le projet.

## Objectif
Analyser le code source pour identifier et réduire la duplication de fonctions et d'informations.

## Question Principale
Est-ce qu'il y a encore de la duplication de fonctions ou d'informations?

## Instructions d'Analyse

1. Examiner les types de duplication :
   - Duplication de code (fonctions similaires)
   - Duplication de données (configurations, constantes)
   - Duplication de logique métier
   - Duplication de documentation

2. Pour chaque fichier, vérifier :
   - Les fonctions avec des noms différents mais une logique similaire
   - Les blocs de code répétés
   - Les configurations redondantes
   - Les structures de données dupliquées

3. Analyser les relations entre :
   - Services similaires
   - Routes avec logique commune
   - Gestionnaires d'erreurs répétitifs
   - Validations redondantes

4. Proposer des solutions :
   - Extraction dans des classes/fonctions communes
   - Utilisation de l'héritage
   - Création de services partagés
   - Centralisation des configurations

## Format de Réponse

Pour chaque duplication trouvée :

1. Localisation :
   - Fichiers concernés
   - Lignes de code
   - Contexte

2. Analyse :
   - Type de duplication
   - Impact sur la maintenance
   - Risques potentiels

3. Solution proposée :
   - Approche de refactoring
   - Code suggéré
   - Bénéfices attendus

## Critères d'Évaluation

- Impact sur la maintenabilité
- Complexité de la solution
- Risques de régression
- Gains en termes de lisibilité

## Notes
- Privilégier la clarté à l'optimisation excessive
- Considérer le contexte d'utilisation
- Évaluer le rapport bénéfice/risque
