# Paste-to-Cells Feature

## Overview
The paste-to-cells feature allows users to quickly convert pasted text content into an annotated document with navigable cells and comments, without manually creating and formatting a markdown file.

## User Workflow

### 1. Creating a Paste File
- User clicks **"📋 New Paste"** button in the left pane toolbar
- A paste dialog window appears with a large text area
- User pastes their content (any text, code blocks, lists, etc.)
- Preview shows how content will be split into cells
- User clicks "Create File" to save

### 2. File Creation
- Dialog prompts user to save the file with a save dialog
- File is saved as `.md` (markdown format)
- Content is automatically parsed into cells
- File opens immediately in the viewer for annotation

### 3. Navigation & Comments
- User navigates cells with **Up/Down arrow keys** (existing feature)
- User adds comments to cells using existing comment system
- Comments are stored in database with cell content hash
- Support for fuzzy matching if cell content changes

### 4. Export
- User presses **Cmd+E** to export annotated version
- Export filename: `{original_name}__annotated__{timestamp}.md`
- Exported file contains all cells with embedded comments as blockquotes
- Comments include timestamp and confidence indicator if fuzzy-matched

## Cell Parsing Algorithm

### Input Processing
- Split content by **blank lines** (2+ consecutive newlines)
- Each paragraph/block becomes a single cell

### Cell Structure
Auto-generated markdown structure with headings:
```
# Cell 1
[First paragraph]

# Cell 2
[Second paragraph]

# Cell 3
[Third paragraph]
```

### Safety Limits
- Files larger than 5MB: show warning, treat as single block
- More than 50,000 lines: truncate to limit
- More than 1,000 cells: truncate with notice

## UI Specifications

### New Paste Button
- Location: Left pane toolbar, next to "Go" button
- Icon: 📋
- Label: "New Paste"
- Styling: Matches existing toolbar buttons

### Paste Dialog Window
- **Size**: 600x400 minimum, resizable
- **Components**:
  - Text area for input (monospace font recommended)
  - **Preview section**: Shows cell count and first few cells
  - **"Create File" button**: Primary action
  - **"Cancel" button**: Close without saving

### Preview Display
Shows:
- Total cell count
- First 3-4 cells as preview (truncated if too long)
- Visual separator between cells (e.g., "---")

## Integration with Existing Features

### Comments System
- Comments attach to cells by:
  1. Cell heading text (`# Cell N`)
  2. Content hash (MD5 of full cell text)
  3. Fuzzy matching if content changes
- All existing comment features work:
  - Add/view/delete comments
  - Comment narration (if enabled)
  - Comment dating

### Export System
- Cmd+E export works unchanged
- Generates annotated version with comments as blockquotes
- Timestamp suffix: `__annotated__{YYYYMMDD_HHMM}.md`
- Confidence markers for fuzzy-matched comments

### Navigation
- All existing keyboard controls work:
  - **Up/Down**: Navigate cells
  - **Cmd+Up/Down**: Jump to first/last cell
  - **Cmd+C**: Copy cell to clipboard with comments
  - **Cmd+,**: Read comments aloud
  - **Cmd+.**: Previous comment
  - **Cmd+/**: Next comment

## Database Schema
**No changes needed** - Uses existing tables:
- `comments`: Stores annotations by heading text and content hash
- `settings`: Stores user preferences
- `starred`: Starred files/folders

## File Format Specifications

### File Naming
- User chooses filename and location via save dialog
- Recommended extension: `.md` (markdown)
- Can also use `.txt`, `.paste`, or any extension

### Internal Structure
- Markdown format with H1 headings (# Cell N)
- Plain text content preserved
- Compatible with any markdown viewer

## Error Handling

### Invalid Content
- Empty paste: Show message "Please paste some content first"
- Very large content: Warn user about truncation limits
- File save failure: Show error dialog with reason

### Edge Cases
- Paste with only whitespace: Treat as single empty cell
- Paste with code blocks: Preserved as-is (can span multiple lines)
- Paste with special characters: UTF-8 handled normally

## Implementation Checklist
- [x] Plan feature design
- [ ] Add "New Paste" button to toolbar
- [ ] Implement paste dialog window
- [ ] Add `parse_paste_cells()` method
- [ ] Integrate with file save dialog
- [ ] Test cell navigation
- [ ] Test comment functionality
- [ ] Test export with comments
- [ ] Verify database integration

## Future Enhancements
- Auto-detect content type (code, prose, structured data)
- Optional cell numbering or custom heading templates
- Batch paste operations
- Import from clipboard on app launch
- Template system for common paste structures
