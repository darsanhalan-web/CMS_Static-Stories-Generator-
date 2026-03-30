# Implementation Plan: CMS Static Stories Generator

## Background & Goal
We need to build a custom Content Management System (CMS) application from scratch. The app will live entirely on your local machine under `d:\AntiGravity Projects\My Apps\CMS_Static Stories Generator\`. It will provide a friendly, split-pane (70:30) User Interface to accept formatted rich text from Microsoft Word, process metadata (title, type, images), embed videos, and allow the user to iteratively generate and preview static `.html` files before officially "Approving" and pushing them to the live `darsan-halan-website` folder.

## User Review Required
> [!IMPORTANT]
> **Architecture Decision: Local Web App vs. Native Desktop App**
> Building a traditional Python desktop app (using `tkinter`) makes it extremely difficult to preserve rich text formatting (bold, italics, headers) when pasting from MS Word.
> **My Proposal:** We build this as a **Local Python Web Application (using Flask)**. 
> - You will double-click a simple `.bat` script on your desktop.
> - A local server spins up instantly, and the "CMS Gui" opens in your browser at `http://localhost:5000`.
> - **Why this is better:** Modern browsers natively handle pasting rich text from Word perfectly. We can also easily embed a free WYSIWYG editor (like Quill.js) and easily achieve the exact styling you requested (Solar Gold, Electric Blue, Half-White background, 70:30 split) using CSS, which looks vastly superior to traditional clunky desktop windows. 
> 
> *Do you approve of using a Local Flask Web App architecture for this tool?*

## Proposed Changes

### `CMS_Static Stories Generator/` (New Project Folder)

#### [NEW] `app.py` 
The core Python server.
 - Handles routing and serving the GUI.
 - Contains the logic for the `Generate` endpoint: Takes JSON payload from the frontend (Title, type, rich text HTML body), parses it, extracts youtube/facebook links to swap for iframe embeds, and injects it into a copy of `reader_template.html`.
 - Saves the temporary output to a `temp_builds/` folder and returns the URL for previewing.
 - Contains the logic for the `Approve` endpoint: Moves the temporary file permanently to `d:\AntiGravity Projects\darsan-halan-website\stories\`, and updates the website's `stories.json`.

#### [NEW] `templates/index.html` & `static/style.css`
The front-end GUI.
 - **CSS Layout:** A CSS Grid or Flexbox 70:30 split. Background `color: #F8F9FA` (Half-white). Buttons styled with `border: 2px solid #FFD700` (Solar Gold) and `color: #7DF9FF` (Electric blue). Everything locked at `font-size: 12px`.
 - **Inputs:** Title, Subtitle, Checkboxes (JS logic to ensure only 1 is checked), Image path, Sources text area.
 - **Editor:** Integration of a free Rich Text Editor library (like Quill) to receive Word docx pastes.
 - **Right Pane Stats:** Fetch past files from the live `stories.json` and a local database/JSON tracker to calculate generated file sizes, creation dates, and categorized totals.

#### [NEW] `temp_builds/`
A local subfolder to hold iterative drafts of the HTML files safely away from the live site while the user is actively tweaking and hitting the "Generate" preview button.

## Verification Plan
1. Create the new folder structure.
2. Build the basic UI and ensure the 70:30 split, colors, and 12px fonts match exactly.
3. Test pasting a complex MS Word document into the editor to verify formatting retention.
4. Test the Generate -> Preview -> Tweaking -> Approve lifecycle to ensure files are moved properly to the `darsan-halan-website` project without dirtying the git history with drafts.
