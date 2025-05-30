// Main Repository Browser Application
function repositoryBrowser() {
    // Combine the core functionality with Monaco utilities
    const core = repositoryBrowserCore();
    const monacoUtils = monacoLanguageUtils();
    
    return {
        ...core,
        ...monacoUtils,
        
        // Data
        projectId: null,
        projectName: 'Loading...',
        currentBranch: 'main',
        branches: [],
        currentPath: '',
        fileTree: [],
        filteredFiles: [],
        fileSearch: '',
        globalSearch: '',
        selectedFile: null,
        fileSize: '',
        commits: [],
        pullRequests: [],
        loading: false,
        loadingMessage: 'Loading...',
        hasChanges: false,
        
        // Enhanced UI State
        activeTab: 'files',
        bottomTab: 'analysis',
        showBottomPanel: false,
        prFilter: 'all',
        analysisType: null,
        analysisStep: 1,
        
        // Collapsible sections state
        collapsedSections: {
            files: false,
            commits: false,
            pullrequests: false,
            insights: true
        },
        
        // Enhanced file tree state
        expandedFolders: new Set(),
        otherBranches: [],
        
        // Progress tracking
        analysisProgress: 0,
        analysisStartTime: null,
        currentStep: { title: '', description: '' },
        analysisSteps: [],
        currentInsights: [],
        analysisStats: { issuesFound: 0, linesAnalyzed: 0, suggestions: 0 },
        realTimeIssues: [],
        
        // AI Analysis
        analysisResults: [],
        suggestions: [],
        generatedTests: null,
        
        // Monaco Editor
        monacoEditor: null,
        
        // Fix application flag to prevent infinite loops
        _isApplyingFix: false,
        
        // Diff decorations storage
        _diffDecorations: [],
        
        init() {
            console.log('=== Repository Browser Initializing ===');
            try {
                this.initFromURL();
                this.loadProject();
                
                // Add window resize handler for Monaco editor
                this.setupWindowResizeHandler();
                
                console.log('Repository Browser initialized successfully');
            } catch (error) {
                console.error('Error initializing Repository Browser:', error);
            }
        },
        
        initFromURL() {
            const urlParams = new URLSearchParams(window.location.search);
            this.projectId = urlParams.get('project_id');
            this.projectName = urlParams.get('name') || 'Unknown Project';
            
            if (!this.projectId) {
                alert('No project selected');
                window.location.href = '/projects';
                return;
            }
        },
        
        async loadProject() {
            try {
                this.loading = true;
                this.loadingMessage = 'Loading project...';
                
                await Promise.all([
                    this.loadBranches(),
                    this.loadFileTree(),
                    this.loadCommits(),
                    this.loadPullRequests()
                ]);
                
                this.loading = false;
            } catch (error) {
                console.error('Error loading project:', error);
                alert('Error loading project: ' + error.message);
                this.loading = false;
            }
        },
        
        async loadBranches() {
            try {
                const response = await fetch(`/gitlab/repository/${this.projectId}/branches`);
                const data = await response.json();
                this.branches = data.branches;
                this.currentBranch = data.default_branch || 'main';
            } catch (error) {
                console.error('Error loading branches:', error);
            }
        },
        
        async loadFileTree(path = '') {
            try {
                const response = await fetch(`/gitlab/repository/${this.projectId}/tree?branch=${this.currentBranch}&path=${path}`);
                const data = await response.json();
                
                // Process files with enhanced metadata
                const processedFiles = data.items.map(item => ({
                    ...item,
                    depth: 0,
                    expanded: false,
                    hasIssues: Math.random() < 0.3, // Simulate files with issues
                    isModified: Math.random() < 0.2, // Simulate modified files
                    isNew: Math.random() < 0.1 // Simulate new files
                })).sort((a, b) => {
                    if (a.type !== b.type) return a.type === 'tree' ? -1 : 1;
                    return a.name.localeCompare(b.name);
                });
                
                if (path === '') {
                    // Root level - replace entire tree
                    this.fileTree = processedFiles;
                } else {
                    // Subdirectory - merge with existing tree
                    this.fileTree = [...this.fileTree, ...processedFiles];
                }
                
                this.updateFileTreeDisplay();
                this.currentPath = path;
            } catch (error) {
                console.error('Error loading file tree:', error);
            }
        },

        // UI Helpers
        async switchBranch() {
            await this.loadFileTree();
            await this.loadCommits();
            if (this.selectedFile) {
                await this.selectFile(this.selectedFile);
            }
        },
        
        toggleSection(sectionName) {
            this.collapsedSections[sectionName] = !this.collapsedSections[sectionName];
        },

        // Computed properties
        get pathParts() {
            return this.currentPath ? this.currentPath.split('/') : [];
        },
        
        getPathUpTo(index) {
            return this.pathParts.slice(0, index + 1).join('/');
        },

        // Global search functionality
        performGlobalSearch() {
            if (!this.globalSearch.trim()) {
                this.filteredFiles = this.fileTree;
                return;
            }
            
            const searchTerm = this.globalSearch.toLowerCase();
            this.filteredFiles = this.fileTree.filter(item => 
                item.name.toLowerCase().includes(searchTerm) ||
                item.path.toLowerCase().includes(searchTerm)
            );
        },

        // Mock data loaders (implement these based on your backend)
        async loadCommits() {
            try {
                const response = await fetch(`/gitlab/repository/${this.projectId}/commits?branch=${this.currentBranch}&per_page=20`);
                const data = await response.json();
                this.commits = data.commits;
            } catch (error) {
                console.error('Error loading commits:', error);
            }
        },

        async loadPullRequests() {
            // Mock implementation for now
            this.pullRequests = [];
        },

        // AI Analysis function (simplified for now)
        async analyzeCode(type) {
            console.log('Starting AI analysis:', type);
            this.showNotification('info', `${type} analysis feature coming soon!`);
        },

        async commitChanges() {
            if (!this.selectedFile || !this.monacoEditor || !this.hasChanges) return;
            
            const newContent = this.monacoEditor.getValue();
            const commitMessage = prompt('Enter commit message:', `Update ${this.selectedFile.name}`);
            
            if (!commitMessage) return;
            
            try {
                this.loading = true;
                this.loadingMessage = 'Committing changes...';
                
                const response = await fetch(`/gitlab/repository/${this.projectId}/commit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_path: this.selectedFile.path,
                        branch: this.currentBranch,
                        content: newContent,
                        commit_message: commitMessage
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.hasChanges = false;
                    this.selectedFile.content = newContent;
                    this.showNotification('success', 'Changes committed successfully!');
                    await this.loadCommits(); // Refresh commits
                } else {
                    this.showNotification('error', 'Error committing changes: ' + result.error);
                }
                
                this.loading = false;
                
            } catch (error) {
                console.error('Error committing changes:', error);
                this.showNotification('error', 'Error committing changes: ' + error.message);
                this.loading = false;
            }
        },

        navigateToPath(path) {
            this.loadFileTree(path);
        },

        // File status helpers
        getFileStatus(item) {
            if (item.hasIssues) return '!';
            if (item.isModified) return 'M';
            if (item.isNew) return '+';
            if (this.selectedFile?.path === item.path) return '●';
            return '';
        },
        
        getFileStatusClass(item) {
            if (item.hasIssues) return 'status-issues';
            if (item.isModified) return 'status-modified';
            if (item.isNew) return 'status-new';
            if (this.selectedFile?.path === item.path) return 'status-selected';
            return '';
        },
        
        // File icon helpers
        getFileIcon(item) {
            if (item.type === 'tree') return 'fas fa-folder text-blue-400';
            
            if (!item.name) return 'fas fa-file text-gray-400';
            
            const ext = item.name.split('.').pop()?.toLowerCase();
            const filename = item.name.toLowerCase();
            
            // Handle special filenames
            const specialFiles = {
                'readme': 'fas fa-book-open text-green-400',
                'readme.md': 'fas fa-book-open text-green-400',
                'license': 'fas fa-certificate text-yellow-400',
                'dockerfile': 'fab fa-docker text-blue-500',
                'package.json': 'fab fa-npm text-red-500',
                'yarn.lock': 'fab fa-yarn text-blue-400',
                '.gitignore': 'fab fa-git-alt text-orange-500',
                '.env': 'fas fa-cog text-green-400'
            };
            
            if (specialFiles[filename]) {
                return specialFiles[filename];
            }
            
            // Handle by extension
            const iconMap = {
                'py': 'fab fa-python text-yellow-400',
                'js': 'fab fa-js-square text-yellow-500',
                'jsx': 'fab fa-react text-blue-400',
                'ts': 'fas fa-code text-blue-500',
                'tsx': 'fab fa-react text-blue-400',
                'html': 'fab fa-html5 text-orange-500',
                'css': 'fab fa-css3-alt text-blue-500',
                'scss': 'fab fa-sass text-pink-500',
                'json': 'fas fa-brackets-curly text-green-400',
                'yaml': 'fas fa-code text-red-400',
                'yml': 'fas fa-code text-red-400',
                'md': 'fab fa-markdown text-gray-400',
                'txt': 'fas fa-file-alt text-gray-400',
                'sql': 'fas fa-database text-blue-400',
                'sh': 'fas fa-terminal text-green-400',
                'bash': 'fas fa-terminal text-green-400',
                'dockerfile': 'fab fa-docker text-blue-500',
                'tf': 'fas fa-cloud text-purple-500',
                'java': 'fab fa-java text-orange-500',
                'php': 'fab fa-php text-purple-500',
                'rb': 'fas fa-gem text-red-500',
                'go': 'fab fa-golang text-blue-400',
                'rs': 'fas fa-box text-orange-500',
                'swift': 'fab fa-swift text-orange-500',
                'kt': 'fas fa-code text-purple-500',
                'cs': 'fas fa-code text-purple-500',
                'cpp': 'fas fa-code text-blue-500',
                'c': 'fas fa-code text-blue-500',
                'h': 'fas fa-code text-blue-500',
                'vue': 'fab fa-vuejs text-green-500',
                'dart': 'fas fa-mobile-alt text-blue-400',
                'xml': 'fas fa-code text-orange-400',
                'svg': 'fas fa-vector-square text-green-400',
                'toml': 'fas fa-cog text-orange-400',
                'ini': 'fas fa-cog text-gray-400',
                'cfg': 'fas fa-cog text-gray-400',
                'conf': 'fas fa-cog text-gray-400',
                'log': 'fas fa-list text-gray-400',
                'lock': 'fas fa-lock text-yellow-500'
            };
            
            return iconMap[ext] || 'fas fa-file text-gray-400';
        },
        
        getFileLanguage(file) {
            if (!file || !file.name) return 'Text';
            
            const ext = file.name.split('.').pop()?.toLowerCase();
            const filename = file.name.toLowerCase();
            
            // Handle special filenames
            const specialFileLanguages = {
                'dockerfile': 'Docker',
                'docker-compose.yml': 'Docker Compose',
                'makefile': 'Makefile',
                'package.json': 'Package Config',
                'composer.json': 'Composer Config',
                'gemfile': 'Ruby Gems',
                'requirements.txt': 'Python Requirements',
                'pipfile': 'Python Pipfile',
                'setup.py': 'Python Setup',
                'cargo.toml': 'Rust Cargo',
                'go.mod': 'Go Module',
                '.gitignore': 'Git Ignore',
                '.env': 'Environment'
            };
            
            if (specialFileLanguages[filename]) {
                return specialFileLanguages[filename];
            }
            
            const langMap = {
                'py': 'Python',
                'js': 'JavaScript',
                'jsx': 'React JSX',
                'ts': 'TypeScript',
                'tsx': 'React TSX',
                'html': 'HTML',
                'css': 'CSS',
                'scss': 'Sass (SCSS)',
                'sass': 'Sass',
                'less': 'Less CSS',
                'json': 'JSON',
                'yaml': 'YAML',
                'yml': 'YAML',
                'toml': 'TOML',
                'ini': 'INI Config',
                'xml': 'XML',
                'svg': 'SVG',
                'md': 'Markdown',
                'txt': 'Plain Text',
                'sql': 'SQL',
                'sh': 'Shell Script',
                'bash': 'Bash Script',
                'dockerfile': 'Docker',
                'tf': 'Terraform',
                'java': 'Java',
                'php': 'PHP',
                'rb': 'Ruby',
                'go': 'Go',
                'rs': 'Rust',
                'swift': 'Swift',
                'kt': 'Kotlin',
                'cs': 'C#',
                'cpp': 'C++',
                'c': 'C',
                'h': 'C Header',
                'vue': 'Vue.js',
                'dart': 'Dart',
                'log': 'Log File',
                'lock': 'Lock File'
            };
            
            return langMap[ext] || 'Text';
        }
    };
} 