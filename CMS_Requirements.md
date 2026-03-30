# Product Requirements Document (PRD): CMS Static Stories Generator

## 1. Overview
The "CMS Static Stories Generator" is a local desktop application designed to streamline the creation of content (Short Stories, Research, Articles) for the Darsan Halan website. It provides a visual interface for non-technical users to input content, retain complex formatting, preview the generated web pages, and push finalized content directly to the live website repository.

## 2. Workspace & Setup
- **Directory**: Must completely reside outside the website codebase in a new folder located at `d:\AntiGravity Projects\My Apps\CMS_Static Stories Generator`.
- **Core Technology**: Python-based application.

## 3. Data Input Fields (Left Pane - 70%)
The system requires the following inputs:
- **Title**: Text field (Mandatory).
- **Subtitle**: Text field (Mandatory).
- **Type**: Mutually exclusive checkboxes (Short Story, Research, Article). Checking one automatically unchecks the others.
- **Image**: File browser to select an image path (Optional).
- **Body**: A robust Rich Text Editor capable of handling up to 5000 words. 
  - Must seamlessly accept and retain formatting copied directly from MS Word (`.docx`) or rich text.
  - Must support embedding YouTube and Facebook video links, explicitly pulling them out and making them visible between text blocks in the generated output.
- **Sources**: A large text field to accept a set of links. These will be appended as a dedicated source block at the end of the generated static page (Optional).

## 4. UI Layout & Design details
- **Layout Split**: A 70:30 horizontal split.
  - **Left Pane (70%)**: Houses all data input fields, rich text editor, and action buttons.
  - **Right Pane (30%)**: A historical tracker containing a scrollable list of previously generated files, including their specific size and creation date.
  - **Bottom Right Pane**: A dynamic summary dashboard showing the total count of all files, paired with a categorization breakdown (e.g., Total: 10 | Short Stories: 5, Research: 3, Articles: 2).
- **Design System**: 
  - **Background Colors**: "Half white" (an off-white, light gray/cream that is easy on the eyes).
  - **Buttons**: Unique styling featuring a "Solar Gold" colored border and an "Electric Blue" colored font.
  - **Typography**: Clean, simple, highly legible font sizes locked at exactly `12px` for all labels and standard text.

## 5. Workflow & Functional Requirements
1. **Drafting Content**: The user fills out the form. 
2. **Generating a Preview**: The user clicks the `Generate` button.
   - The app compiles the inputs into a static HTML file (using the website's existing template) in a temporary, local storage location *outside* the live website directory.
   - The app instantly opens this new temporary HTML page in a new browser window for visual review.
3. **Iterative Tweaking**: If the user spots an error in the preview, they can return to the app, tweak their inputs in the exact same fields, and hit `Generate` again. A new preview will overwrite the old temporary file and open for review.
4. **Final Approval**: Once fully satisfied with the preview, the user clicks the `Approve` button.
   - The app permanently copies the static HTML file directly into the `darsan-halan-website/stories/` folder.
   - The app automatically parses the metadata and immediately updates the live `stories.json` file to reflect the new post type and details.
   - The historical tracker on the right pane refreshes.
