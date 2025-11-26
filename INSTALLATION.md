# Guide d'installation pour débutants - Mandala PDF Generator

Ce guide vous explique comment installer et utiliser Mandala PDF Generator sur Windows, même si vous n'avez jamais utilisé Python.

## Table des matières
1. [Installation de Python](#1-installation-de-python)
2. [Installation des dépendances](#2-installation-des-dépendances)
3. [Lancement de l'application](#3-lancement-de-lapplication)
4. [Dépannage](#4-dépannage)

---

## 1. Installation de Python

### Télécharger Python

1. Allez sur le site officiel de Python : https://www.python.org/downloads/
2. Cliquez sur le bouton jaune **"Download Python 3.x.x"** (la version la plus récente)
3. Attendez que le téléchargement se termine

### Installer Python

1. **Double-cliquez** sur le fichier téléchargé (par exemple `python-3.11.x-amd64.exe`)

2. **IMPORTANT** : Avant de cliquer sur "Install Now", **cochez la case** en bas :
   ```
   ☑ Add python.exe to PATH
   ```
   Cette étape est cruciale !

3. Cliquez sur **"Install Now"**

4. Attendez la fin de l'installation (quelques minutes)

5. Cliquez sur **"Close"** quand c'est terminé

### Vérifier l'installation

1. Appuyez sur les touches `Windows + R` ensemble
2. Tapez `cmd` et appuyez sur `Entrée`
3. Une fenêtre noire s'ouvre (l'invite de commandes)
4. Tapez cette commande et appuyez sur `Entrée` :
   ```
   python --version
   ```
5. Vous devriez voir quelque chose comme : `Python 3.11.x`

**Si vous voyez un message d'erreur** :
- Recommencez l'installation de Python
- Assurez-vous de bien cocher "Add python.exe to PATH"
- Redémarrez votre ordinateur après l'installation

---

## 2. Installation des dépendances

Les dépendances sont les bibliothèques dont le programme a besoin pour fonctionner.

### Méthode 1 : Installation automatique (recommandé)

1. **Extrayez le ZIP** que vous avez téléchargé dans un dossier de votre choix
   - Faites un clic droit sur le ZIP
   - Choisissez "Extraire tout..."
   - Choisissez un emplacement facile à retrouver (par exemple : `C:\MandalaGenerator`)

2. **Ouvrez l'invite de commandes dans ce dossier** :
   - Ouvrez le dossier où vous avez extrait les fichiers
   - Dans la barre d'adresse en haut (où il y a le chemin), cliquez dedans
   - Tapez `cmd` et appuyez sur `Entrée`
   - Une fenêtre noire s'ouvre, déjà positionnée dans votre dossier

3. **Installez les dépendances** :
   - Dans la fenêtre noire, tapez cette commande et appuyez sur `Entrée` :
   ```
   pip install -r requirements.txt
   ```
   - Attendez que tous les packages se téléchargent et s'installent (cela peut prendre 2-5 minutes)
   - Vous verrez défiler beaucoup de texte, c'est normal !

4. **Vérifiez l'installation** :
   - Quand c'est terminé, tapez cette commande :
   ```
   pip list
   ```
   - Vous devriez voir une liste de packages incluant PyQt6, Pillow, et reportlab

### Méthode 2 : Installation manuelle (si la méthode 1 ne fonctionne pas)

Si la commande `pip` ne fonctionne pas, essayez avec `python -m pip` :

```
python -m pip install PyQt6 Pillow reportlab
```

---

## 3. Lancement de l'application

### Première utilisation

1. **Assurez-vous d'être dans le bon dossier** :
   - Ouvrez l'invite de commandes dans le dossier du programme (voir étape 2.2)

2. **Lancez l'application** :
   - Tapez cette commande et appuyez sur `Entrée` :
   ```
   python gui_pdf_generator.py
   ```
   - L'interface graphique devrait s'ouvrir après quelques secondes

### Utilisations suivantes

Pour relancer l'application plus tard :

1. Naviguez vers le dossier où vous avez extrait les fichiers
2. Dans la barre d'adresse, tapez `cmd` et appuyez sur `Entrée`
3. Tapez : `python gui_pdf_generator.py`

### Créer un raccourci (optionnel)

Pour faciliter le lancement, vous pouvez créer un fichier batch :

1. Dans le dossier du programme, créez un nouveau fichier texte
2. Renommez-le en `Lancer_Mandala.bat` (changez bien l'extension de .txt à .bat)
3. Faites un clic droit → "Modifier"
4. Copiez-collez ce texte :
   ```batch
   @echo off
   cd /d "%~dp0"
   python gui_pdf_generator.py
   pause
   ```
5. Enregistrez et fermez
6. Double-cliquez sur `Lancer_Mandala.bat` pour lancer l'application

---

## 4. Dépannage

### Problème : "python n'est pas reconnu..."

**Cause** : Python n'est pas dans le PATH système

**Solution** :
1. Désinstallez Python (Panneau de configuration → Programmes)
2. Réinstallez en cochant bien "Add python.exe to PATH"
3. Redémarrez votre ordinateur

### Problème : "pip n'est pas reconnu..."

**Cause** : pip n'est pas installé ou pas dans le PATH

**Solution** :
1. Utilisez `python -m pip` au lieu de `pip` dans toutes les commandes
2. Exemple : `python -m pip install -r requirements.txt`

### Problème : "No module named 'PyQt6'"

**Cause** : Les dépendances ne sont pas installées

**Solution** :
1. Ouvrez l'invite de commandes dans le dossier du programme
2. Tapez : `pip install -r requirements.txt`
3. Attendez la fin de l'installation
4. Réessayez de lancer le programme

### Problème : L'application se ferme immédiatement

**Cause** : Erreur Python non visible

**Solution** :
1. Lancez l'application depuis l'invite de commandes (pas en double-cliquant)
2. Les messages d'erreur seront visibles dans la fenêtre noire
3. Notez le message d'erreur et cherchez la solution correspondante

### Problème : "Access Denied" lors de l'installation

**Cause** : Droits administrateur requis

**Solution** :
1. Fermez l'invite de commandes
2. Recherchez "cmd" dans le menu Démarrer
3. Faites un clic droit → "Exécuter en tant qu'administrateur"
4. Naviguez vers votre dossier avec `cd C:\chemin\vers\votre\dossier`
5. Réessayez l'installation

---

## Utilisation de l'application

Une fois l'application lancée :

1. **Onglet Quality** : Réglez la qualité du PDF (DPI, anti-aliasing)
2. **Onglet Layout** : Choisissez le format de page (A4, A3, Letter)
3. **Onglet Design** : Configurez le nombre de cercles et de rayons
4. **Onglet Style** : Personnalisez les couleurs et styles de lignes
5. **Bouton Generate PDF** : Cliquez pour créer votre PDF

Le PDF sera créé dans le même dossier que le programme.

---

## Besoin d'aide ?

- **Documentation complète** : Consultez le fichier README.md
- **Issues GitHub** : https://github.com/remmmi/mandala_empty_templates_generator/issues
- **Code source** : https://github.com/remmmi/mandala_empty_templates_generator

---

**Bon génération de mandalas !** ✨
