/**
 * Monaco Editor Diff Viewer Component
 * Provides clear red/green diff visualization with enhanced functionality
 */

class DiffViewer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.editor = null;
        this.diffEditor = null;
        this.options = {
            theme: 'vs-dark',
            language: 'python',
            readOnly: false,
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: 'on',
            wordWrap: 'on',
            automaticLayout: true,
            scrollBeyondLastLine: false,
            renderWhitespace: 'boundary',
            ...options
        };
        
        this.currentSuggestion = null;
        this.isApplying = false;
        
        this.init();
    }

    async init() {
        if (!this.container) {
            console.error(`Container with ID "${this.containerId}" not found`);
            return;
        }

        // Load Monaco Editor
        await this.loadMonaco();
        
        // Create the UI structure
        this.createUI();
        
        // Initialize the editor
        this.initializeEditor();
        
        // Set up event listeners
        this.setupEventListeners();
    }

    async loadMonaco() {
        if (typeof monaco === 'undefined') {
            return new Promise((resolve, reject) => {
                require.config({ 
                    paths: { 
                        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' 
                    }
                });
                
                require(['vs/editor/editor.main'], () => {
                    this.configureMonaco();
                    resolve();
                }, reject);
            });
        } else {
            this.configureMonaco();
        }
    }

    configureMonaco() {
        // Define custom theme with red/green colors only
        monaco.editor.defineTheme('diff-theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '6A737D' },
                { token: 'keyword', foreground: 'FF7B72' },
                { token: 'string', foreground: 'A5D6FF' },
                { token: 'number', foreground: '79C0FF' },
            ],
            colors: {
                'editor.background': '#1e1e1e',
                'editor.foreground': '#d4d4d4',
                'editorLineNumber.foreground': '#858585',
                'editorLineNumber.activeForeground': '#c6c6c6',
                
                // Diff colors - RED and GREEN only
                'diffEditor.insertedTextBackground': 'rgba(22, 163, 74, 0.15)',
                'diffEditor.insertedTextBorder': '#16a34a',
                'diffEditor.removedTextBackground': 'rgba(220, 38, 38, 0.15)',
                'diffEditor.removedTextBorder': '#dc2626',
                
                // Line number colors for diff
                'diffEditorGutter.insertedLineBackground': 'rgba(22, 163, 74, 0.2)',
                'diffEditorGutter.removedLineBackground': 'rgba(220, 38, 38, 0.2)',
                
                // Overview ruler
                'diffEditorOverview.insertedForeground': '#16a34a',
                'diffEditorOverview.removedForeground': '#dc2626',
            }
        });
    }

    createUI() {
        this.container.innerHTML = `
            <div class="diff-container">
                <div class="editor-header">
                    <div class="editor-tabs">
                        <button class="tab-button active" data-mode="diff">
                            <i class="fas fa-code-compare"></i>
                            Diff View
                        </button>
                        <button class="tab-button" data-mode="side-by-side">
                            <i class="fas fa-columns"></i>
                            Side by Side
                        </button>
                        <button class="tab-button" data-mode="unified">
                            <i class="fas fa-list"></i>
                            Unified
                        </button>
                    </div>
                    <div class="editor-controls">
                        <button class="control-btn" id="toggle-whitespace">
                            <i class="fas fa-eye"></i>
                            Whitespace
                        </button>
                        <button class="control-btn" id="toggle-minimap">
                            <i class="fas fa-map"></i>
                            Minimap
                        </button>
                    </div>
                </div>
                
                <div class="monaco-editor-container" id="${this.containerId}-editor">
                    <div class="loading-overlay" id="${this.containerId}-loading">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
                
                <div class="suggestion-panel" id="${this.containerId}-panel" style="display: none;">
                    <div class="suggestion-header">
                        <h3 class="suggestion-title" id="${this.containerId}-title">Code Suggestion</h3>
                        <div class="suggestion-badges">
                            <span class="severity-badge" id="${this.containerId}-severity">Medium</span>
                            <span class="category-badge" id="${this.containerId}-category">Style</span>
                        </div>
                    </div>
                    
                    <div class="suggestion-description" id="${this.containerId}-description">
                        Loading suggestion details...
                    </div>
                    
                    <div class="suggestion-explanation" id="${this.containerId}-explanation">
                        <i class="fas fa-lightbulb"></i>
                        AI Reasoning: Loading explanation...
                    </div>
                    
                    <div class="impact-list" id="${this.containerId}-impact">
                        <h4>Expected Impact:</h4>
                        <ul id="${this.containerId}-impact-list">
                            <li>Loading impact analysis...</li>
                        </ul>
                    </div>
                    
                    <div class="diff-actions">
                        <button class="btn btn-primary" id="${this.containerId}-apply">
                            <i class="fas fa-check"></i>
                            Apply Suggestion
                        </button>
                        <button class="btn btn-secondary" id="${this.containerId}-preview">
                            <i class="fas fa-eye"></i>
                            Preview Changes
                        </button>
                        <button class="btn btn-danger" id="${this.containerId}-reject">
                            <i class="fas fa-times"></i>
                            Reject
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    initializeEditor() {
        const editorContainer = document.getElementById(`${this.containerId}-editor`);
        
        // Create diff editor
        this.diffEditor = monaco.editor.createDiffEditor(editorContainer, {
            theme: 'diff-theme',
            ...this.options,
            renderSideBySide: true,
            enableSplitViewResizing: true,
            diffWordWrap: 'on',
            originalEditable: false,
            modifiedEditable: !this.options.readOnly,
        });

        // Hide loading overlay
        this.hideLoading();
    }

    setupEventListeners() {
        // Tab switching
        this.container.querySelectorAll('.tab-button').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const mode = e.target.closest('.tab-button').dataset.mode;
                this.switchViewMode(mode);
            });
        });

        // Control buttons
        document.getElementById('toggle-whitespace')?.addEventListener('click', () => {
            this.toggleWhitespace();
        });

        document.getElementById('toggle-minimap')?.addEventListener('click', () => {
            this.toggleMinimap();
        });

        // Action buttons
        document.getElementById(`${this.containerId}-apply`)?.addEventListener('click', () => {
            this.applySuggestion();
        });

        document.getElementById(`${this.containerId}-preview`)?.addEventListener('click', () => {
            this.previewChanges();
        });

        document.getElementById(`${this.containerId}-reject`)?.addEventListener('click', () => {
            this.rejectSuggestion();
        });

        // Editor events
        if (this.diffEditor) {
            this.diffEditor.onDidUpdateDiff(() => {
                this.highlightChanges();
            });
        }
    }

    switchViewMode(mode) {
        // Update tab states
        this.container.querySelectorAll('.tab-button').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.mode === mode);
        });

        // Update editor layout
        switch (mode) {
            case 'side-by-side':
                this.diffEditor.updateOptions({ renderSideBySide: true });
                break;
            case 'unified':
                this.diffEditor.updateOptions({ renderSideBySide: false });
                break;
            case 'diff':
            default:
                this.diffEditor.updateOptions({ renderSideBySide: true });
                break;
        }
    }

    toggleWhitespace() {
        const current = this.diffEditor.getOption(monaco.editor.EditorOption.renderWhitespace);
        const newValue = current === 'all' ? 'boundary' : 'all';
        this.diffEditor.updateOptions({ renderWhitespace: newValue });
    }

    toggleMinimap() {
        const current = this.diffEditor.getOption(monaco.editor.EditorOption.minimap);
        this.diffEditor.updateOptions({ 
            minimap: { enabled: !current.enabled } 
        });
    }

    showSuggestion(suggestion) {
        this.currentSuggestion = suggestion;
        
        // Set original and modified content
        const originalModel = monaco.editor.createModel(
            suggestion.old_content, 
            this.options.language
        );
        const modifiedModel = monaco.editor.createModel(
            suggestion.new_content, 
            this.options.language
        );

        this.diffEditor.setModel({
            original: originalModel,
            modified: modifiedModel
        });

        // Update suggestion panel
        this.updateSuggestionPanel(suggestion);
        
        // Show the panel
        document.getElementById(`${this.containerId}-panel`).style.display = 'block';
        
        // Highlight the changes
        this.highlightChanges();
    }

    updateSuggestionPanel(suggestion) {
        // Update title and description
        document.getElementById(`${this.containerId}-title`).textContent = 
            suggestion.issue_description || 'Code Suggestion';
        
        document.getElementById(`${this.containerId}-description`).textContent = 
            suggestion.issue_description || 'No description available';
        
        document.getElementById(`${this.containerId}-explanation`).innerHTML = 
            `<i class="fas fa-lightbulb"></i> AI Reasoning: ${suggestion.explanation || 'No explanation provided'}`;

        // Update severity badge
        const severityElement = document.getElementById(`${this.containerId}-severity`);
        severityElement.textContent = suggestion.severity || 'medium';
        severityElement.className = `severity-badge severity-${suggestion.severity || 'medium'}`;

        // Update category badge
        const categoryElement = document.getElementById(`${this.containerId}-category`);
        categoryElement.textContent = suggestion.category || 'general';
        categoryElement.className = `category-badge category-${suggestion.category || 'general'}`;

        // Update impact list
        const impactList = document.getElementById(`${this.containerId}-impact-list`);
        impactList.innerHTML = '';
        
        if (suggestion.impact && Array.isArray(suggestion.impact)) {
            suggestion.impact.forEach(impact => {
                const li = document.createElement('li');
                li.textContent = impact;
                impactList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'General code improvement';
            impactList.appendChild(li);
        }
    }

    highlightChanges() {
        // Add custom decorations for better visual feedback
        const modifiedEditor = this.diffEditor.getModifiedEditor();
        const originalEditor = this.diffEditor.getOriginalEditor();

        if (!modifiedEditor || !originalEditor) return;

        // Get diff changes
        const changes = this.diffEditor.getLineChanges() || [];
        
        const decorations = [];
        
        changes.forEach(change => {
            // Highlight added lines in green
            if (change.modifiedStartLineNumber && change.modifiedEndLineNumber) {
                decorations.push({
                    range: new monaco.Range(
                        change.modifiedStartLineNumber,
                        1,
                        change.modifiedEndLineNumber,
                        1
                    ),
                    options: {
                        isWholeLine: true,
                        className: 'line-insert',
                        marginClassName: 'margin-insert'
                    }
                });
            }
        });

        modifiedEditor.deltaDecorations([], decorations);
    }

    async applySuggestion() {
        if (!this.currentSuggestion || this.isApplying) return;

        this.isApplying = true;
        this.showLoading();
        
        try {
            // Emit event for suggestion application
            const event = new CustomEvent('suggestionApplied', {
                detail: {
                    suggestion: this.currentSuggestion,
                    newContent: this.diffEditor.getModifiedEditor().getValue()
                }
            });
            this.container.dispatchEvent(event);
            
            // Show success feedback
            this.showFeedback('Suggestion applied successfully!', 'success');
            
            // Hide the panel
            this.hideSuggestionPanel();
            
        } catch (error) {
            console.error('Error applying suggestion:', error);
            this.showFeedback('Failed to apply suggestion', 'error');
        } finally {
            this.isApplying = false;
            this.hideLoading();
        }
    }

    previewChanges() {
        if (!this.currentSuggestion) return;
        
        // Switch to side-by-side view for better preview
        this.switchViewMode('side-by-side');
        
        // Scroll to first change
        const changes = this.diffEditor.getLineChanges();
        if (changes && changes.length > 0) {
            const firstChange = changes[0];
            this.diffEditor.revealLineInCenter(firstChange.modifiedStartLineNumber || 1);
        }
    }

    rejectSuggestion() {
        if (!this.currentSuggestion) return;
        
        // Emit event for suggestion rejection
        const event = new CustomEvent('suggestionRejected', {
            detail: { suggestion: this.currentSuggestion }
        });
        this.container.dispatchEvent(event);
        
        this.hideSuggestionPanel();
        this.showFeedback('Suggestion rejected', 'info');
    }

    hideSuggestionPanel() {
        document.getElementById(`${this.containerId}-panel`).style.display = 'none';
        this.currentSuggestion = null;
    }

    showLoading() {
        document.getElementById(`${this.containerId}-loading`).style.display = 'flex';
    }

    hideLoading() {
        document.getElementById(`${this.containerId}-loading`).style.display = 'none';
    }

    showFeedback(message, type = 'info') {
        // Create feedback toast
        const toast = document.createElement('div');
        toast.className = `feedback-toast feedback-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    // Public API methods
    setContent(originalContent, modifiedContent = '') {
        if (!this.diffEditor) return;
        
        const originalModel = monaco.editor.createModel(originalContent, this.options.language);
        const modifiedModel = monaco.editor.createModel(modifiedContent, this.options.language);

        this.diffEditor.setModel({
            original: originalModel,
            modified: modifiedModel
        });
    }

    getModifiedContent() {
        return this.diffEditor?.getModifiedEditor()?.getValue() || '';
    }

    getOriginalContent() {
        return this.diffEditor?.getOriginalEditor()?.getValue() || '';
    }

    dispose() {
        if (this.diffEditor) {
            this.diffEditor.dispose();
        }
    }
}

// Export for use
window.DiffViewer = DiffViewer; 