# CMS Static Stories Generator

A local, Python-based Content Management System (CMS) designed to elegantly formulate, review, and compile Static HTML story pages intended for integration into a live static website. It operates via a lightweight `Flask` backend paired with an intuitive split-pane Browser GUI, allowing for the direct styling and composition of articles, short stories, and research papers from Microsoft Word.

## Features
- **Local Browser GUI:** Seamless interface utilizing a 70:30 layout.
- **Rich Text Preservation:** Utilizes `Quill.js` to copy and paste styling cleanly from Microsoft Word documents.
- **Zero Configuration Server:** Employs relative system paths to guarantee cross-machine compatibility, with `.bat` click-to-start integration.
- **Automatic Content Routing:** Generates live Static HTML previews safely stored in `temp_builds/`. 
- **Live Publishing:** Pushes completely approved static pages actively into your site's target directory whilst automatically formatting and indexing metadata directly into `stories.json`.
- **Intelligent Media Embeds:** Detects and embeds Facebook/YouTube videos dynamically using native security tokens (`strict-origin-when-cross-origin`).
- **File System Handling:** Browse securely for local images; the tool natively copies assets systematically into the target application.

## Prerequisites
- Windows OS (designed for batch script launching)
- Python 3+

## Installation & Setup
1. Clone the repository.
2. Run `setup.bat` to install `Flask` and required dependencies.
3. (Optional) In `app.py`, configure the `WEBSITE_ROOT` path if the destination repository is located differently than the default `../../` relative path.

## Usage
Simply double-click `run.bat` to spark the python web server and securely initialize the browser portal!
