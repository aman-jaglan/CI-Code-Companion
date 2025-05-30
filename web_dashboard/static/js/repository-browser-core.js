// Repository Browser Core Functionality
function repositoryBrowserCore() {
    return {
        // File Management with debouncing and non-blocking operations
        _fileSelectionInProgress: false,
        _pendingFileSelection: null,
        
        async selectFile(item) {
            // Debounce rapid file selections
            if (this._fileSelectionInProgress) {
                this._pendingFileSelection = item;
                console.log('File selection in progress, queuing:', item.name);
                return;
            }
            
            // Prevent selecting the same file multiple times
            if (this.selectedFile?.path === item.path && this.monacoEditor) {
                console.log('File already selected and editor ready');
                return;
            }
            
            this._fileSelectionInProgress = true;
            
            // Show loading state immediately with file-specific message
            this.loading = true;
            this.loadingMessage = `Opening ${item.name}...`;
            
            // Use requestAnimationFrame to ensure UI updates before heavy operations
            await new Promise(resolve => requestAnimationFrame(resolve));
            
            try {
                console.log('Selecting file:', item.path);
                
                // Dispose existing editor first (non-blocking)
                await this.disposeMonacoEditorAsync();
                
                // Update loading message
                this.loadingMessage = `Loading ${item.name} content...`;
                await new Promise(resolve => requestAnimationFrame(resolve));
                
                // Fetch file content
                const response = await fetch(`/gitlab/repository/${this.projectId}/file?path=${encodeURIComponent(item.path)}&branch=${this.currentBranch}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load file: ${response.status} ${response.statusText}`);
                }
                
                const fileData = await response.json();
                
                // Update selected file state
                this.selectedFile = {
                    ...item,
                    content: fileData.content,
                    size: fileData.size
                };
                
                this.fileSize = this.formatFileSize(fileData.size);
                this.hasChanges = false;
                
                // Update loading message
                this.loadingMessage = `Initializing editor for ${item.name}...`;
                await new Promise(resolve => requestAnimationFrame(resolve));
                
                // Initialize Monaco editor with new content (non-blocking)
                await this.initMonacoEditorAsync(fileData.content, item.name);
                
                console.log('File selection completed successfully');
                
            } catch (error) {
                console.error('Error selecting file:', error);
                this.showNotification('error', `Error loading file: ${error.message}`);
                
                // Reset state on error
                this.selectedFile = null;
                this.fileSize = '';
                this.hasChanges = false;
                await this.disposeMonacoEditorAsync();
                
            } finally {
                this.loading = false;
                this.loadingMessage = '';
                this._fileSelectionInProgress = false;
                
                // Process any pending file selection
                if (this._pendingFileSelection) {
                    const pending = this._pendingFileSelection;
                    this._pendingFileSelection = null;
                    console.log('Processing pending file selection:', pending.name);
                    // Use setTimeout to prevent immediate recursion
                    setTimeout(() => this.selectFile(pending), 100);
                }
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

        // Async version of Monaco editor disposal
        async disposeMonacoEditorAsync() {
            if (this.monacoEditor) {
                try {
                    console.log('Disposing Monaco editor');
                    
                    // Use requestAnimationFrame to ensure UI responsiveness
                    await new Promise(resolve => requestAnimationFrame(resolve));
                    
                    this.monacoEditor.dispose();
                    this.monacoEditor = null;
                    
                    // Clear any decorations
                    this._diffDecorations = [];
                    
                    // Another frame to ensure disposal is complete
                    await new Promise(resolve => requestAnimationFrame(resolve));
                    
                } catch (error) {
                    console.warn('Error disposing Monaco editor:', error);
                    this.monacoEditor = null;
                }
            }
        },
        
        // Non-blocking Monaco editor initialization
        async initMonacoEditorAsync(content, filename) {
            return new Promise((resolve, reject) => {
                const container = document.getElementById('monaco-editor-container');
                
                if (!container) {
                    reject(new Error('Monaco editor container not found'));
                    return;
                }
                
                // Clear container immediately
                container.innerHTML = '';
                
                // Use setTimeout to make the require call non-blocking
                setTimeout(() => {
                    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }});
                    
                    require(['vs/editor/editor.main'], () => {
                        // Use setTimeout to break up the synchronous work
                        setTimeout(() => {
                            try {
                                const language = this.getMonacoLanguage(filename);
                                const editorOptions = this.getEditorOptions(language, content);
                                
                                console.log(`Creating Monaco editor for ${filename} (${language})`);
                                
                                // Create editor in chunks to prevent blocking
                                this.monacoEditor = monaco.editor.create(container, editorOptions);
                                
                                // Use requestAnimationFrame for the rest of the setup
                                requestAnimationFrame(() => {
                                    try {
                                        // Configure language-specific features
                                        this.configureLanguageFeatures(language);
                                        
                                        // Track changes with language-aware validation
                                        this.monacoEditor.onDidChangeModelContent(() => {
                                            // Skip change tracking during programmatic fixes to prevent infinite loops
                                            if (this._isApplyingFix) {
                                                return;
                                            }
                                            
                                            const newContent = this.monacoEditor.getValue();
                                            this.hasChanges = newContent !== this.selectedFile.content;
                                            
                                            // Trigger language-specific validation (debounced)
                                            this.debouncedValidation = this.debouncedValidation || this.debounce(
                                                () => this.validateContent(language, newContent), 
                                                500
                                            );
                                            this.debouncedValidation();
                                        });
                                        
                                        // Configure language-specific keyboard shortcuts
                                        this.setupLanguageShortcuts(language);
                                        
                                        // Force layout update
                                        setTimeout(() => {
                                            if (this.monacoEditor) {
                                                this.monacoEditor.layout();
                                            }
                                            
                                            console.log('Monaco editor created successfully');
                                            resolve();
                                        }, 50);
                                        
                                    } catch (error) {
                                        console.error('Error configuring Monaco editor:', error);
                                        reject(error);
                                    }
                                });
                                
                            } catch (error) {
                                console.error('Error creating Monaco editor:', error);
                                reject(error);
                            }
                        }, 10);
                    });
                }, 10);
            });
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
        }
    };
} 