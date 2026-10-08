# ERUDITE 2026 NexusCX Presentation - Instructions

## Overview
This presentation is designed for the ERUDITE 2026 internship presentation requirements, showcasing your work on the NexusCX project.

## Files Included
1. `ERUDITE_2026_NexusCX_Presentation.html` - Main presentation file
2. `ERUDITE_2026_Presentation_Outline.md` - Detailed outline of presentation content
3. `PRESENTATION_INSTRUCTIONS.md` - This file

## How to Use the Presentation

### Option 1: Direct Browser Opening (Recommended)
1. Navigate to the NEXUSCX directory in your file explorer
2. Double-click on `ERUDITE_2026_NexusCX_Presentation.html` to open it in your default web browser
3. Use the following controls to navigate:
   - **Left/Right Arrow Keys**: Navigate between slides
   - **Spacebar**: Advance to next slide
   - **Shift + Spacebar**: Go to previous slide
   - **F**: Toggle fullscreen mode
   - **O**: Toggle overview mode (see all slides)
   - **Esc**: Exit overview or fullscreen mode

### Option 2: Local Web Server
For best performance (especially with the embedded Archify diagram), you can serve the presentation via a local web server:
```bash
# Using Python (if available)
python -m http.server 8000
# Then navigate to http://localhost:8000 in your browser

# Using Node.js (if available)
npx serve
# Then navigate to the provided URL in your browser
```

## Special Features

### Archify Diagram Integration
Slide 11 contains an embedded interactive architecture diagram from Archify:
- The diagram loads automatically within the presentation
- To interact with the diagram:
  - **Press F**: Enter presentation mode (clean, focused view of diagram)
  - **Press E**: Open export options (PNG, SVG, WebM, etc.)
  - **Press ?**: View all keyboard shortcuts
  - **Click and drag**: Pan the diagram
  - **Scroll**: Zoom in/out
  - **Click on nodes**: Select and explore components

### Presentation Tips
1. **Practice the timing**: Aim for 7-8 minutes total (~40-50 seconds per slide)
2. **Speak freely**: Use the slides as visual aids, don't read directly from them
3. **Engage with the diagram**: When you reach Slide 11, take time to explore the architecture interactively
4. **Know your audience**: Focus on your individual contributions and learning as per ERUDITE guidelines
5. **Have backup**: Consider exporting the Archify diagram as PNG/JPEG in case of technical issues

## Customization
To personalize the presentation:
1. Open `ERUDITE_2026_NexusCX_Presentation.html` in a text editor
2. Update the placeholders in Slide 1 (Title Slide):
   - `[Your Name]`
   - `[Your Course and Institution]`
   - `[Your Role, e.g., AI/ML Engineering Intern]`
   - `[Start Date] to [End Date]`
3. Save the file and reopen in your browser to see changes

## Technical Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for loading Reveal.js from CDN (first load)
- Local file access for the embedded Archify diagram
- Recommended: 1280x720 display or higher for optimal viewing

## Troubleshooting
- **Archify diagram not loading**: Check that you're opening the presentation from the NEXUSCX directory
- **Performance issues**: Try using a local web server as described above
- **CDN loading problems**: Ensure you have internet access for initial load
- **Keyboard shortcuts not working**: Click on the presentation area to give it focus

## Contact
If you encounter any issues or have questions about the presentation, refer to the project documentation or consult with your mentor.