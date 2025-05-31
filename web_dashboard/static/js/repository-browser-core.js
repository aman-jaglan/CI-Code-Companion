// Repository Browser Core Functionality
function repositoryBrowserCore() {
    return {
        // File Management with debouncing and non-blocking operations
        _fileSelectionInProgress: false,
        _pendingFileSelection: null,
        _diagnosticsTimeout: null,
        
        async selectFile(item) {
            console.log('🟦 [SELECTFILE] Starting selectFile for:', item.name);
            console.time('selectFile-total');
            
            // Debounce rapid file selections
            if (this._fileSelectionInProgress) {
                this._pendingFileSelection = item;
                console.log('🟨 [SELECTFILE] File selection in progress, queuing:', item.name);
                return;
            }
            
            // Prevent selecting the same file multiple times
            if (this.selectedFile?.path === item.path && this.monacoEditor) {
                console.log('🟩 [SELECTFILE] File already selected and editor ready');
                return;
            }
            
            this._fileSelectionInProgress = true;
            console.log('🟦 [SELECTFILE] Setting file selection in progress');
            
            // Show loading state immediately with file-specific message
            this.loading = true;
            this.loadingMessage = `Opening ${item.name}...`;
            console.log('🟦 [SELECTFILE] Loading state set');
            
            // Use requestAnimationFrame to ensure UI updates before heavy operations
            await new Promise(resolve => requestAnimationFrame(resolve));
            console.log('🟦 [SELECTFILE] UI update frame completed');
            
            try {
                console.log('🟦 [SELECTFILE] Starting file selection process for:', item.path);
                console.time('dispose-editor');
                
                // Dispose existing editor first (non-blocking)
                await this.disposeMonacoEditorAsync();
                console.timeEnd('dispose-editor');
                console.log('🟩 [SELECTFILE] Editor disposed successfully');
                
                // Update loading message
                this.loadingMessage = `Loading ${item.name} content...`;
                await new Promise(resolve => requestAnimationFrame(resolve));
                console.log('🟦 [SELECTFILE] Updated loading message');
                
                console.time('fetch-file');
                // Fetch file content with timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => {
                    console.log('🟥 [SELECTFILE] Fetch timeout triggered');
                    controller.abort();
                }, 15000); // 15 second timeout
                
                const response = await fetch(`/gitlab/repository/${this.projectId}/file?path=${encodeURIComponent(item.path)}&branch=${this.currentBranch}`, {
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                console.timeEnd('fetch-file');
                console.log('🟩 [SELECTFILE] File content fetched successfully');
                
                if (!response.ok) {
                    throw new Error(`Failed to load file: ${response.status} ${response.statusText}`);
                }
                
                const fileData = await response.json();
                console.log('🟩 [SELECTFILE] File data parsed, size:', fileData.size);
                
                // Update selected file state
                this.selectedFile = {
                    ...item,
                    content: fileData.content,
                    size: fileData.size
                };
                
                this.fileSize = this.formatFileSize(fileData.size);
                this.hasChanges = false;
                console.log('🟩 [SELECTFILE] File state updated');
                
                // Update loading message
                this.loadingMessage = `Initializing editor for ${item.name}...`;
                await new Promise(resolve => requestAnimationFrame(resolve));
                console.log('🟦 [SELECTFILE] Pre-editor initialization frame completed');
                
                console.time('monaco-init');
                console.log('🟨 [SELECTFILE] Starting Monaco editor initialization...');
                
                // Initialize Monaco editor with new content (non-blocking)
                await this.initMonacoEditorAsync(fileData.content, item.name);
                
                console.timeEnd('monaco-init');
                console.log('🟩 [SELECTFILE] Monaco editor initialized successfully');
                console.timeEnd('selectFile-total');
                console.log('🟩 [SELECTFILE] File selection completed successfully');
                
            } catch (error) {
                console.error('🟥 [SELECTFILE] Error selecting file:', error);
                console.timeEnd('selectFile-total');
                
                // Show user-friendly error message
                let errorMessage = 'Unknown error occurred';
                if (error.name === 'AbortError') {
                    errorMessage = 'File loading timed out';
                } else if (error.message.includes('timed out')) {
                    errorMessage = 'Editor initialization timed out';
                } else if (error.message.includes('Monaco')) {
                    errorMessage = 'Failed to initialize code editor';
                } else {
                    errorMessage = error.message;
                }
                
                this.showNotification('error', `Error loading file: ${errorMessage}`);
                
                // Reset state on error
                this.selectedFile = null;
                this.fileSize = '';
                this.hasChanges = false;
                await this.disposeMonacoEditorAsync();
                
            } finally {
                // Always clear loading state
                console.log('🟦 [SELECTFILE] Clearing loading state');
                this.loading = false;
                this.loadingMessage = '';
                this._fileSelectionInProgress = false;
                
                // Process any pending file selection
                if (this._pendingFileSelection) {
                    const pending = this._pendingFileSelection;
                    this._pendingFileSelection = null;
                    console.log('🟨 [SELECTFILE] Processing pending file selection:', pending.name);
                    // Use setTimeout to prevent immediate recursion
                    setTimeout(() => this.selectFile(pending), 100);
                }
                console.log('🟩 [SELECTFILE] Finally block completed');
            }
        },

        // Improved click handling with immediate feedback
        handleFileItemClick(item, event) {
            // Prevent default behavior and stop propagation
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            console.log('File item clicked:', item.name, 'Type:', item.type);
            
            // Immediate visual feedback
            if (item.type === 'tree') {
                // Handle folder toggle immediately (synchronous)
                this.toggleFileTreeItem(item);
            } else {
                // Handle file selection (asynchronous but with immediate loading state)
                this.selectFile(item);
            }
        },
        
        toggleFileTreeItem(item) {
            console.log('Toggling folder:', item.name);
            
            // Toggle expanded state immediately
            if (this.expandedFolders.has(item.path)) {
                this.expandedFolders.delete(item.path);
                item.expanded = false;
                console.log('Collapsed folder:', item.name);
            } else {
                this.expandedFolders.add(item.path);
                item.expanded = true;
                console.log('Expanded folder:', item.name);
                
                // Load subdirectory asynchronously if not loaded
                if (!item.children && !item._loading) {
                    item._loading = true;
                    this.loadSubdirectoryAsync(item.path).finally(() => {
                        item._loading = false;
                    });
                }
            }
            
            // Update file tree display immediately
            this.updateFileTreeDisplayAsync();
        },

        // IMPROVED NON-BLOCKING APPROACH with pre-warming and idle disposal
        async disposeMonacoEditorAsync() {
            if (this.monacoEditor) {
                console.log('🟦 [DISPOSE] Using improved approach with requestIdleCallback');
                
                try {
                    // Store reference for idle disposal
                    const editorToDispose = this.monacoEditor;
                    const modelToDispose = this.monacoEditor.getModel();
                    
                    // Clear references immediately
                    this.monacoEditor = null;
                    this._diffDecorations = [];
                    
                    console.log('🟩 [DISPOSE] References cleared immediately - no blocking!');
                    
                    // Dispose during browser idle time using requestIdleCallback
                    if (window.requestIdleCallback) {
                        window.requestIdleCallback(() => {
                            console.log('🟦 [DISPOSE] Disposing editor during idle time');
                            try {
                                if (modelToDispose) {
                                    modelToDispose.dispose();
                                }
                                editorToDispose.dispose();
                                console.log('🟩 [DISPOSE] Editor disposed during idle time');
                            } catch (error) {
                                console.error('🟥 [DISPOSE] Error during idle disposal:', error);
                            }
                        }, { timeout: 5000 }); // Fallback timeout
                    } else {
                        // Fallback for browsers without requestIdleCallback
                        setTimeout(() => {
                            console.log('🟦 [DISPOSE] Disposing editor with setTimeout fallback');
                            try {
                                if (modelToDispose) {
                                    modelToDispose.dispose();
                                }
                                editorToDispose.dispose();
                                console.log('🟩 [DISPOSE] Editor disposed with fallback');
                            } catch (error) {
                                console.error('🟥 [DISPOSE] Error during fallback disposal:', error);
                            }
                        }, 100);
                    }
                    
                } catch (error) {
                    console.error('🟥 [DISPOSE] Error in improved disposal:', error);
                }
                
                return Promise.resolve();
            } else {
                console.log('🟩 [DISPOSE] No Monaco editor to dispose');
                return Promise.resolve();
            }
        },

        // Pre-warm Monaco workers during initialization
        async preWarmMonacoWorkers() {
            console.log('🟦 [PREWARM] Pre-warming Monaco workers...');
            console.time('prewarm-workers');
            
            try {
                await this.loadMonacoGlobally();
                
                // Create dummy models to initialize workers
                const languages = ['typescript', 'javascript', 'python', 'json', 'css', 'html'];
                
                for (const lang of languages) {
                    try {
                        const dummyModel = monaco.editor.createModel('', lang);
                        // Dispose immediately - we just wanted to warm up the worker
                        setTimeout(() => dummyModel.dispose(), 10);
                        console.log(`🟩 [PREWARM] Warmed up ${lang} worker`);
                    } catch (error) {
                        console.warn(`🟨 [PREWARM] Could not warm up ${lang} worker:`, error);
                    }
                }
                
                console.timeEnd('prewarm-workers');
                console.log('🟩 [PREWARM] Monaco workers pre-warmed successfully');
                
            } catch (error) {
                console.error('🟥 [PREWARM] Error pre-warming workers:', error);
                console.timeEnd('prewarm-workers');
            }
        },

        // Remove the old disposal methods since we're not using them
        startBackgroundDisposal() {
            console.log('🟨 [DISPOSE] Background disposal disabled - using radical approach');
        },

        processEditorQueue() {
            console.log('🟨 [DISPOSE] Queue processing disabled - using radical approach');
        },
        
        // Non-blocking Monaco editor initialization with robust error handling
        async initMonacoEditorAsync(content, filename) {
            console.log('🟦 [MONACO] Starting Monaco initialization for:', filename);
            console.time('monaco-full-init');
            
            return new Promise((resolve, reject) => {
                const container = document.getElementById('monaco-editor-container');
                
                if (!container) {
                    console.log('🟥 [MONACO] Container not found');
                    reject(new Error('Monaco editor container not found'));
                    return;
                }
                
                console.log('🟦 [MONACO] Container found, clearing...');
                // Clear container immediately
                container.innerHTML = '';
                console.log('🟩 [MONACO] Container cleared');
                
                // Set up timeout to prevent hanging
                const timeout = setTimeout(() => {
                    console.log('🟥 [MONACO] Initialization timeout triggered');
                    reject(new Error('Monaco editor initialization timed out'));
                }, 30000); // 30 second timeout
                
                const cleanup = () => {
                    clearTimeout(timeout);
                };
                
                console.log('🟦 [MONACO] Starting global Monaco loader...');
                console.time('monaco-loader');
                
                // Use global Monaco loader to prevent require.config conflicts
                this.loadMonacoGlobally()
                    .then(() => {
                        console.timeEnd('monaco-loader');
                        console.log('🟩 [MONACO] Global Monaco loaded successfully');
                        
                        try {
                            console.time('monaco-create');
                            console.log('🟦 [MONACO] Getting language and options...');
                            
                            const language = this.getMonacoLanguage(filename);
                            const editorOptions = this.getEditorOptions(language, content);
                            
                            console.log('🟦 [MONACO] Language:', language, 'Content size:', content.length);
                            
                            // Check for large files that might cause freezing
                            const isLargeFile = content.length > 100000; // 100KB threshold
                            if (isLargeFile) {
                                console.log('🟨 [MONACO] Large file detected, using optimized options');
                                // Disable heavy features for large files
                                editorOptions.minimap = { enabled: false };
                                editorOptions.folding = false;
                                editorOptions.wordWrap = 'off';
                                editorOptions.semanticHighlighting = { enabled: false };
                                editorOptions.largeFileOptimizations = true; // Enable Monaco's built-in optimizations
                                editorOptions.renderValidationDecorations = 'off'; // Disable validation decorations
                                editorOptions.renderIndentGuides = false;
                                editorOptions.occurrencesHighlight = false;
                                editorOptions.selectionHighlight = false;
                                // Limit content for very large files
                                if (content.length > 500000) { // 500KB
                                    console.log('🟨 [MONACO] Very large file, truncating content');
                                    editorOptions.value = content.substring(0, 500000) + '\n\n... [File truncated for performance]';
                                }
                            } else {
                                // For normal files, enable performance optimizations
                                editorOptions.largeFileOptimizations = false;
                                editorOptions.renderValidationDecorations = 'on';
                                editorOptions.renderIndentGuides = true;
                                editorOptions.occurrencesHighlight = true;
                                editorOptions.selectionHighlight = true;
                            }
                            
                            console.log('🟨 [MONACO] About to create Monaco editor - THIS MIGHT BLOCK');
                            
                            // 🚨 MAKE THIS NON-BLOCKING BY USING setTimeout 🚨
                            setTimeout(() => {
                                try {
                                    console.log('🟦 [MONACO] Creating editor in timeout (non-blocking)');
                                    this.monacoEditor = monaco.editor.create(container, editorOptions);
                                    
                                    console.timeEnd('monaco-create');
                                    console.log('🟩 [MONACO] Monaco editor created successfully');
                                    
                                    // Configure editor features
                                    console.log('🟦 [MONACO] Configuring editor features...');
                                    requestAnimationFrame(() => {
                                        console.time('monaco-configure');
                                        
                                        try {
                                            // Configure language-specific features
                                            this.configureLanguageFeatures(language);
                                            console.log('🟩 [MONACO] Language features configured');
                                            
                                            // Track changes with language-aware validation and debounced diagnostics
                                            this.monacoEditor.onDidChangeModelContent(() => {
                                                // Skip change tracking during programmatic fixes to prevent infinite loops
                                                if (this._isApplyingFix) {
                                                    return;
                                                }
                                                
                                                const newContent = this.monacoEditor.getValue();
                                                this.hasChanges = newContent !== this.selectedFile.content;
                                                
                                                // Clear any existing diagnostics timeout
                                                if (this._diagnosticsTimeout) {
                                                    clearTimeout(this._diagnosticsTimeout);
                                                }
                                                
                                                // Disable heavy diagnostics while typing (debounced approach)
                                                this.monacoEditor.updateOptions({ 
                                                    renderValidationDecorations: 'off' 
                                                });
                                                
                                                // Re-enable diagnostics after user stops typing (1 second delay)
                                                this._diagnosticsTimeout = setTimeout(() => {
                                                    if (this.monacoEditor && !isLargeFile) {
                                                        this.monacoEditor.updateOptions({ 
                                                            renderValidationDecorations: 'on' 
                                                        });
                                                        console.log('🟩 [MONACO] Re-enabled diagnostics after typing pause');
                                                    }
                                                }, 1000);
                                                
                                                // Trigger language-specific validation (debounced) - safely
                                                if (typeof this.validateContent === 'function') {
                                                    this.debouncedValidation = this.debouncedValidation || this.debounce(
                                                        () => this.validateContent(language, newContent), 
                                                        500
                                                    );
                                                    this.debouncedValidation();
                                                }
                                            });
                                            console.log('🟩 [MONACO] Change tracking configured');
                                            
                                            // Setup language-specific keyboard shortcuts
                                            this.setupLanguageShortcuts(language);
                                            
                                            // Force layout update and complete initialization
                                            setTimeout(() => {
                                                console.log('🟦 [MONACO] Final layout and completion...');
                                                
                                                try {
                                                    if (this.monacoEditor) {
                                                        // Make layout call non-blocking with requestAnimationFrame
                                                        requestAnimationFrame(() => {
                                                            try {
                                                                console.log('🟦 [MONACO] Performing layout in animation frame...');
                                                                this.monacoEditor.layout();
                                                                console.log('🟩 [MONACO] Layout completed successfully');
                                                                
                                                                console.timeEnd('monaco-configure');
                                                                console.timeEnd('monaco-full-init');
                                                                console.log('🟩 [MONACO] Monaco editor fully initialized and ready');
                                                                cleanup();
                                                                resolve();
                                                            } catch (layoutError) {
                                                                console.error('🟥 [MONACO] Error during layout:', layoutError);
                                                                // Still resolve - layout errors shouldn't break initialization
                                                                console.timeEnd('monaco-configure');
                                                                console.timeEnd('monaco-full-init');
                                                                console.log('🟨 [MONACO] Monaco editor initialized (layout failed)');
                                                                cleanup();
                                                                resolve();
                                                            }
                                                        });
                                                    } else {
                                                        console.log('🟥 [MONACO] Editor was disposed during initialization');
                                                        cleanup();
                                                        reject(new Error('Monaco editor was disposed during initialization'));
                                                    }
                                                } catch (error) {
                                                    console.error('🟥 [MONACO] Error in final completion step:', error);
                                                    cleanup();
                                                    reject(error);
                                                }
                                            }, 10); // Reduced from 50ms to 10ms for faster response
                                            
                                        } catch (error) {
                                            console.error('🟥 [MONACO] Error configuring Monaco editor:', error);
                                            console.timeEnd('monaco-configure');
                                            cleanup();
                                            reject(error);
                                        }
                                    });
                                    
                                } catch (error) {
                                    console.error('🟥 [MONACO] Error creating Monaco editor in timeout:', error);
                                    console.timeEnd('monaco-create');
                                    cleanup();
                                    reject(error);
                                }
                            }, 10); // Small delay to make it non-blocking
                            
                        } catch (error) {
                            console.error('🟥 [MONACO] Error creating Monaco editor:', error);
                            console.timeEnd('monaco-create');
                            cleanup();
                            reject(error);
                        }
                    })
                    .catch((error) => {
                        console.error('🟥 [MONACO] Failed to load Monaco editor:', error);
                        console.timeEnd('monaco-loader');
                        cleanup();
                        reject(error);
                    });
            });
        },

        // Global Monaco loader to prevent require.config conflicts
        async loadMonacoGlobally() {
            // If Monaco is already loaded globally, return immediately
            if (window.monaco) {
                return Promise.resolve();
            }
            
            // If Monaco is currently loading, wait for it
            if (window._monacoLoading) {
                return window._monacoLoading;
            }
            
            // Start loading Monaco
            window._monacoLoading = new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Monaco CDN loading timed out'));
                }, 15000);
                
                const cleanup = () => {
                    clearTimeout(timeout);
                    delete window._monacoLoading;
                };
                
                // Use the centralized require configuration
                if (window.ensureRequireConfig) {
                    window.ensureRequireConfig();
                } else {
                    // Fallback if global config not available
                    if (!window._requireConfigured) {
                        require.config({ 
                            paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' },
                            waitSeconds: 15
                        });
                        window._requireConfigured = true;
                    }
                }
                
                require(['vs/editor/editor.main'], 
                    () => {
                        cleanup();
                        console.log('Monaco editor loaded successfully');
                        resolve();
                    },
                    (error) => {
                        cleanup();
                        console.error('Monaco loading error:', error);
                        reject(new Error(`Failed to load Monaco: ${error.message || 'AMD loading error'}`));
                    }
                );
            });
            
            return window._monacoLoading;
        },

        // Legacy synchronous methods for backward compatibility
        disposeMonacoEditor() {
            this.disposeMonacoEditorAsync();
        },
        
        async initMonacoEditor(content, filename) {
            return this.initMonacoEditorAsync(content, filename);
        },

        setupWindowResizeHandler() {
            // Debounced resize handler
            let resizeTimeout;
            const handleResize = () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    if (this.monacoEditor) {
                        console.log('Updating Monaco editor layout after resize');
                        this.monacoEditor.layout();
                    }
                }, 100);
            };
            
            window.addEventListener('resize', handleResize);
            
            // Cleanup on page unload
            window.addEventListener('beforeunload', () => {
                window.removeEventListener('resize', handleResize);
                this.disposeMonacoEditorAsync();
            });
        },

        // Async directory loading
        async loadSubdirectoryAsync(path) {
            try {
                console.log('Loading subdirectory:', path);
                const response = await fetch(`/gitlab/repository/${this.projectId}/tree?branch=${this.currentBranch}&path=${path}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load directory: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Process subdirectory files
                const subFiles = data.items.map(item => ({
                    ...item,
                    depth: path.split('/').length,
                    expanded: false,
                    hasIssues: Math.random() < 0.3,
                    isModified: Math.random() < 0.2,
                    isNew: Math.random() < 0.1
                })).sort((a, b) => {
                    if (a.type !== b.type) return a.type === 'tree' ? -1 : 1;
                    return a.name.localeCompare(b.name);
                });
                
                // Add to file tree if not already present
                subFiles.forEach(subFile => {
                    if (!this.fileTree.find(f => f.path === subFile.path)) {
                        this.fileTree.push(subFile);
                    }
                });
                
                await this.updateFileTreeDisplayAsync();
                console.log(`Loaded ${subFiles.length} items from ${path}`);
                
            } catch (error) {
                console.error('Error loading subdirectory:', error);
                this.showNotification('error', `Failed to load directory: ${error.message}`);
                throw error;
            }
        },

        // Legacy method for backward compatibility
        async loadSubdirectory(path) {
            return this.loadSubdirectoryAsync(path);
        },

        // Async file tree display update
        async updateFileTreeDisplayAsync() {
            // Use requestAnimationFrame to prevent blocking
            await new Promise(resolve => requestAnimationFrame(resolve));
            
            // Convert flat file list to hierarchical structure with proper depth
            this.filteredFiles = this.buildHierarchicalTree(this.fileTree);
            
            // Another frame to ensure UI updates
            await new Promise(resolve => requestAnimationFrame(resolve));
        },

        // Legacy method for backward compatibility
        updateFileTreeDisplay() {
            this.updateFileTreeDisplayAsync();
        },
        
        buildHierarchicalTree(files, parentPath = '', depth = 0) {
            const result = [];
            const pathParts = parentPath.split('/').filter(p => p);
            
            files.forEach(file => {
                if (parentPath === '' || file.path.startsWith(parentPath + '/')) {
                    const relativePath = parentPath === '' ? file.path : file.path.substring(parentPath.length + 1);
                    const isDirectChild = !relativePath.includes('/');
                    
                    if (isDirectChild) {
                        file.depth = depth;
                        file.expanded = this.expandedFolders.has(file.path);
                        result.push(file);
                        
                        // Add children if folder is expanded
                        if (file.type === 'tree' && file.expanded) {
                            const children = this.buildHierarchicalTree(files, file.path, depth + 1);
                            result.push(...children);
                        }
                    }
                }
            });
            
            return result;
        },

        // Utility Functions
        showNotification(type, message) {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
            
            const colors = {
                success: 'bg-green-600 text-white',
                error: 'bg-red-600 text-white',
                warning: 'bg-yellow-600 text-black',
                info: 'bg-blue-600 text-white'
            };
            
            const icons = {
                success: 'fas fa-check-circle',
                error: 'fas fa-exclamation-circle',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info-circle'
            };
            
            notification.classList.add(...colors[type].split(' '));
            notification.innerHTML = `
                <div class="flex items-center space-x-2">
                    <i class="${icons[type]}"></i>
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        },

        formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        },

        // Debounce utility function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func.apply(this, args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Get optimized editor options with performance considerations
        getEditorOptions(language, content) {
            const isLargeFile = content.length > 100000; // 100KB threshold
            
            const baseOptions = {
                value: content,
                language: language,
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                lineHeight: 21,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                scrollBeyondLastLine: false,
                smoothScrolling: true,
                mouseWheelZoom: true,
                contextmenu: true,
                minimap: { enabled: !isLargeFile },
                folding: !isLargeFile,
                wordWrap: isLargeFile ? 'off' : 'bounded',
                wordWrapColumn: 120,
                bracketPairColorization: { enabled: !isLargeFile },
                guides: {
                    bracketPairs: !isLargeFile,
                    indentation: !isLargeFile
                },
                suggest: {
                    enabled: !isLargeFile,
                    showMethods: !isLargeFile,
                    showFunctions: !isLargeFile,
                    showConstructors: !isLargeFile,
                    showFields: !isLargeFile,
                    showVariables: !isLargeFile,
                },
                quickSuggestions: !isLargeFile,
                parameterHints: { enabled: !isLargeFile },
                hover: { enabled: !isLargeFile },
                lightbulb: { enabled: !isLargeFile },
                codeActionMenu: { enabled: !isLargeFile },
                // Performance optimizations
                largeFileOptimizations: isLargeFile,
                renderValidationDecorations: isLargeFile ? 'off' : 'on',
                renderIndentGuides: !isLargeFile,
                occurrencesHighlight: !isLargeFile,
                selectionHighlight: !isLargeFile,
                semanticHighlighting: { enabled: !isLargeFile },
                // Scrollbar optimizations
                scrollbar: {
                    vertical: 'auto',
                    horizontal: 'auto',
                    useShadows: !isLargeFile,
                    handleMouseWheel: true,
                    arrowSize: isLargeFile ? 8 : 11
                }
            };
            
            // Additional optimizations for very large files
            if (content.length > 500000) { // 500KB
                baseOptions.value = content.substring(0, 500000) + '\n\n... [File truncated for performance]';
                baseOptions.readOnly = true; // Make very large files read-only
            }
            
            return baseOptions;
        },

        // Get Monaco language from filename
        getMonacoLanguage(filename) {
            const ext = filename.split('.').pop()?.toLowerCase();
            const languageMap = {
                'js': 'javascript',
                'jsx': 'javascript',
                'ts': 'typescript',
                'tsx': 'typescript',
                'py': 'python',
                'pyw': 'python',
                'json': 'json',
                'html': 'html',
                'htm': 'html',
                'css': 'css',
                'scss': 'scss',
                'sass': 'scss',
                'less': 'less',
                'xml': 'xml',
                'yaml': 'yaml',
                'yml': 'yaml',
                'md': 'markdown',
                'sh': 'shell',
                'bash': 'shell',
                'zsh': 'shell',
                'fish': 'shell',
                'sql': 'sql',
                'php': 'php',
                'rb': 'ruby',
                'go': 'go',
                'rs': 'rust',
                'java': 'java',
                'cpp': 'cpp',
                'c': 'cpp',
                'h': 'cpp',
                'hpp': 'cpp',
                'cs': 'csharp',
                'vue': 'vue',
                'svelte': 'svelte',
                'dockerfile': 'dockerfile'
            };
            
            // Special cases
            if (filename.toLowerCase() === 'dockerfile') return 'dockerfile';
            if (filename.toLowerCase().includes('makefile')) return 'makefile';
            if (filename.toLowerCase().includes('readme')) return 'markdown';
            
            return languageMap[ext] || 'plaintext';
        },

        // Configure language-specific features
        configureLanguageFeatures(language) {
            if (!this.monacoEditor || !monaco.languages) {
                return;
            }
            
            try {
                // Configure language-specific settings
                const model = this.monacoEditor.getModel();
                if (!model) return;
                
                // Set language for the model
                monaco.editor.setModelLanguage(model, language);
                
                // Configure language-specific options
                switch (language) {
                    case 'typescript':
                    case 'javascript':
                        // Enable TypeScript/JavaScript specific features
                        this.monacoEditor.updateOptions({
                            suggest: { enabled: true },
                            quickSuggestions: true,
                            parameterHints: { enabled: true },
                            hover: { enabled: true },
                            occurrencesHighlight: true
                        });
                        break;
                        
                    case 'python':
                        // Python-specific configurations
                        this.monacoEditor.updateOptions({
                            tabSize: 4,
                            insertSpaces: true,
                            wordWrap: 'bounded',
                            wordWrapColumn: 79 // PEP 8 line length
                        });
                        break;
                        
                    case 'json':
                        // JSON-specific configurations
                        this.monacoEditor.updateOptions({
                            tabSize: 2,
                            insertSpaces: true,
                            formatOnPaste: true,
                            formatOnType: true
                        });
                        break;
                        
                    case 'markdown':
                        // Markdown-specific configurations
                        this.monacoEditor.updateOptions({
                            wordWrap: 'on',
                            lineNumbers: 'off',
                            folding: false
                        });
                        break;
                        
                    default:
                        // Default configurations for other languages
                        this.monacoEditor.updateOptions({
                            suggest: { enabled: true },
                            quickSuggestions: false
                        });
                }
                
                console.log(`🟩 Configured ${language} language features`);
                
            } catch (error) {
                console.warn(`🟨 Could not configure ${language} features:`, error);
            }
        },

        // Setup language-specific keyboard shortcuts
        setupLanguageShortcuts(language) {
            if (!this.monacoEditor) return;
            
            try {
                // Add common shortcuts that work across all languages
                this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
                    // Save file shortcut
                    if (this.hasChanges) {
                        this.commitChanges();
                    }
                });
                
                // Language-specific shortcuts
                switch (language) {
                    case 'typescript':
                    case 'javascript':
                    case 'jsx':
                        // Format document shortcut
                        this.monacoEditor.addCommand(monaco.KeyMod.Alt | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
                            this.monacoEditor.getAction('editor.action.formatDocument')?.run();
                        });
                        break;
                        
                    case 'python':
                        // Python-specific shortcuts could go here
                        break;
                        
                    default:
                        // Default shortcuts for other languages
                        break;
                }
                
                console.log(`🟩 Configured ${language} shortcuts`);
                
            } catch (error) {
                console.warn(`🟨 Could not setup shortcuts for ${language}:`, error);
            }
        }
    };
} 