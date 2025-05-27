// DiffViewer.js
import { createTheme } from '../utils/theme.js';

class DiffViewer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            language: options.language || 'python',
            theme: options.theme || 'vs-dark',
            ...options
        };
        this.diffEditor = null;
        this.initialize();
    }

    initialize() {
        if (!this.container) {
            console.error('Container element not found');
            return;
        }

        // Register custom theme
        monaco.editor.defineTheme('custom-diff', createTheme());

        // Create diff editor with improved options
        this.diffEditor = monaco.editor.createDiffEditor(this.container, {
            theme: 'custom-diff',
            language: this.options.language,
            renderSideBySide: true,
            enableSplitViewResizing: true,
            originalEditable: false,
            modifiedEditable: false,
            fontSize: 14,
            lineHeight: 21,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            folding: true,
            lineNumbers: 'on',
            renderIndicators: true,
            renderOverviewRuler: false,
            diffWordWrap: 'on',
            ignoreTrimWhitespace: false,
            renderWhitespace: 'boundary',
            scrollbar: {
                vertical: 'visible',
                horizontal: 'visible',
                useShadows: false,
                verticalHasArrows: false,
                horizontalHasArrows: false
            }
        });
    }

    setContent(originalCode, modifiedCode) {
        if (!this.diffEditor) return;

        this.diffEditor.setModel({
            original: monaco.editor.createModel(originalCode, this.options.language),
            modified: monaco.editor.createModel(modifiedCode, this.options.language)
        });
    }

    highlightChanges(suggestion) {
        if (!this.diffEditor || !suggestion) return;

        const lineNumber = parseInt(suggestion.line_number);
        this.diffEditor.revealLineInCenter(lineNumber);

        // Add decorations to highlight the changed lines
        const oldLines = suggestion.old_content.split('\n').length;
        const newLines = suggestion.new_content.split('\n').length;

        const originalDecorations = [{
            range: new monaco.Range(lineNumber, 1, lineNumber + oldLines - 1, 1),
            options: {
                isWholeLine: true,
                className: 'diff-line-deleted',
                glyphMarginClassName: 'diff-glyph-deleted'
            }
        }];

        const modifiedDecorations = [{
            range: new monaco.Range(lineNumber, 1, lineNumber + newLines - 1, 1),
            options: {
                isWholeLine: true,
                className: 'diff-line-inserted',
                glyphMarginClassName: 'diff-glyph-inserted'
            }
        }];

        this.diffEditor.getOriginalEditor().deltaDecorations([], originalDecorations);
        this.diffEditor.getModifiedEditor().deltaDecorations([], modifiedDecorations);
    }

    updateSuggestionInfo(suggestion) {
        if (!suggestion) return;

        const infoContainer = document.createElement('div');
        infoContainer.className = 'diff-suggestion-info';
        infoContainer.innerHTML = `
            <h4>Suggested Change</h4>
            <p><strong>Issue:</strong> ${suggestion.issue_description}</p>
            <p><strong>Explanation:</strong> ${suggestion.explanation}</p>
            <div class="impact-list">
                <strong>Impact:</strong>
                <ul>
                    ${suggestion.impact.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
            <p>
                <span class="badge badge-${suggestion.severity}">
                    ${suggestion.severity.toUpperCase()}
                </span>
                <span class="badge badge-info ml-2">
                    ${suggestion.category}
                </span>
            </p>
        `;

        // Replace or append the info container
        const existingInfo = this.container.querySelector('.diff-suggestion-info');
        if (existingInfo) {
            existingInfo.replaceWith(infoContainer);
        } else {
            this.container.appendChild(infoContainer);
        }
    }

    dispose() {
        if (this.diffEditor) {
            this.diffEditor.dispose();
        }
    }
}

export default DiffViewer; 