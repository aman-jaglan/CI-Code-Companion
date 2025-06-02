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
        showAIPanel: false,  // AI panel state
        showGraphModal: false,  // Graph modal state
        prFilter: 'all',
        analysisType: null,
        analysisStep: 1,
        
        // Collapsible sections state
        collapsedSections: {
            files: false,
            commits: false,
            pullrequests: false,
            insights: true,
            dependencies: false,
            aiAssistant: false
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
        
        // Dependency Graph System
        dependencyGraph: { nodes: [], edges: [] },
        dependencyCache: new Map(),
        loadingGraph: false,
        loadingFullGraph: false,
        selectedNode: null,
        graphLayout: 'force',
        graphFilter: 'all',
        graphFilters: {
            imports: true,
            functions: true,
            classes: true
        },
        
        // Graph visualization instances
        miniGraphInstance: null,
        fullGraphInstance: null,
        
        // NEW: Cursor-style AI Assistant System
        assistantMode: 'code', // code, test, security
        selectedModel: 'gemini-2.5-pro',
        
        // Chat functionality
        chatLoading: false,
        chatLoadingMessage: 'Thinking...',
        chatMessages: [],
        chatInput: '',
        
        // File selections for different modes
        selectedTestFiles: [],
        selectedSecurityFiles: [],
        
        // Configuration objects
        testConfig: {
            type: 'unit',
            coverageFocus: {
                functions: true,
                edge_cases: true,
                error_handling: true
            }
        },
        
        securityConfig: {
            vulnerabilities: true,
            dependencies: false,
            codePatterns: true,
            compliance: false
        },
        
        // Legacy properties to maintain compatibility
        detectedTech: null,
        reviewLoading: false,
        reviewResults: [],
        testLoading: false,
        testResults: null,
        optimizeLoading: false,
        optimizationResults: [],
        
        init() {
            console.log('=== Repository Browser Initializing ===');
            try {
                this.initFromURL();
                this.loadProject();
                
                // Initialize horizontal sidebar tabs
                this.initializeSidebarTabs();
                
                // Initialize AI Assistant with welcome message
                this.addWelcomeMessage();
                
                // Add window resize handler for Monaco editor
                this.setupWindowResizeHandler();
                
                // Pre-warm Monaco workers for better performance
                console.log('🔥 Starting Monaco pre-warming...');
                this.preWarmMonacoWorkers().then(() => {
                    console.log('🟩 Monaco pre-warming completed');
                }).catch(error => {
                    console.warn('🟨 Monaco pre-warming failed:', error);
                });
                
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

        // Update file tree display after changes
        updateFileTreeDisplay() {
            this.filteredFiles = this.globalSearch ? 
                this.fileTree.filter(item => 
                    item.name.toLowerCase().includes(this.globalSearch.toLowerCase()) ||
                    item.path.toLowerCase().includes(this.globalSearch.toLowerCase())
                ) : 
                this.fileTree;
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
            this.updateFileTreeDisplay();
        },

        // File handling
        async handleFileItemClick(item, event) {
            if (item.type === 'tree') {
                item.expanded = !item.expanded;
                if (item.expanded && !item.children) {
                    await this.loadFileTree(item.path);
                }
            } else {
                await this.selectFile(item);
            }
        },

        // Mock data loaders (implement these based on your backend)
        async loadCommits() {
            try {
                const response = await fetch(`/gitlab/repository/${this.projectId}/commits?branch=${this.currentBranch}&per_page=20`);
                const data = await response.json();
                this.commits = data.commits || [];
            } catch (error) {
                console.error('Error loading commits:', error);
                this.commits = [];
            }
        },

        async loadPullRequests() {
            try {
                const response = await fetch(`/gitlab/repository/${this.projectId}/merge_requests?state=opened`);
                const data = await response.json();
                this.pullRequests = data.merge_requests || [];
            } catch (error) {
                console.error('Error loading pull requests:', error);
                this.pullRequests = [];
            }
        },

        // File status helpers
        getModifiedFiles() {
            return this.fileTree.filter(file => file.isModified || file.hasChanges) || [];
        },
        
        // File icon helpers
        getFileIcon(item) {
            if (item.type === 'tree') return item.expanded ? 'fas fa-folder-open' : 'fas fa-folder';
            
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
                'sh': 'fas fa-terminal text-green-400'
            };
            
            return iconMap[ext] || 'fas fa-file text-gray-400';
        },
        
        getFileLanguage(file) {
            if (!file || !file.name) return 'Text';
            
            const ext = file.name.split('.').pop()?.toLowerCase();
            const langMap = {
                'py': 'Python',
                'js': 'JavaScript',
                'jsx': 'React JSX',
                'ts': 'TypeScript',
                'tsx': 'React TSX',
                'html': 'HTML',
                'css': 'CSS',
                'json': 'JSON',
                'yaml': 'YAML',
                'yml': 'YAML',
                'md': 'Markdown',
                'txt': 'Plain Text',
                'sql': 'SQL'
            };
            
            return langMap[ext] || 'Text';
        },

        // AI Assistant methods
        addWelcomeMessage() {
            const welcomeMessage = {
                id: Date.now(),
                role: 'assistant',
                content: this.getModeWelcomeMessage(),
                timestamp: new Date(),
                actions: this.getModeActions()
            };
            this.chatMessages = [welcomeMessage];
        },
        
        getModeWelcomeMessage() {
            switch (this.assistantMode) {
                case 'code':
                    return `Hello! I'm your **Code Development Assistant** powered by ${this.selectedModel}. I can help you with:
- Code review and analysis
- Best practices and optimization
- Bug detection and fixes
- Architecture suggestions
- Framework-specific guidance

Select a file or ask me anything about your code!`;
                    
                case 'test':
                    return `Hello! I'm your **Testing Assistant** powered by ${this.selectedModel}. I can help you with:
- Generate comprehensive test suites
- Test strategy recommendations
- Coverage analysis
- Mock and fixture creation
- Performance testing

Select files to test or ask about testing strategies!`;
                    
                case 'security':
                    return `Hello! I'm your **Security Analysis Assistant** powered by ${this.selectedModel}. I can help you with:
- Vulnerability scanning
- Dependency security analysis
- Code pattern security review
- Compliance checking
- Security best practices

Configure your security scope or ask about security concerns!`;
                    
                default:
                    return 'Hello! How can I help you today?';
            }
        },
        
        getModeActions() {
            switch (this.assistantMode) {
                case 'code':
                    return [
                        { id: 'review-file', type: 'primary', icon: 'fas fa-search-code', label: 'Review Current File' },
                        { id: 'explain-code', type: 'secondary', icon: 'fas fa-question-circle', label: 'Explain Code' }
                    ];
                case 'test':
                    return [
                        { id: 'generate-tests', type: 'primary', icon: 'fas fa-vial', label: 'Generate Tests' },
                        { id: 'test-strategy', type: 'secondary', icon: 'fas fa-lightbulb', label: 'Test Strategy' }
                    ];
                case 'security':
                    return [
                        { id: 'scan-vulnerabilities', type: 'primary', icon: 'fas fa-shield-alt', label: 'Scan Vulnerabilities' },
                        { id: 'check-dependencies', type: 'secondary', icon: 'fas fa-cube', label: 'Check Dependencies' }
                    ];
                default:
                    return [];
            }
        },
        
        getModeIcon() {
            switch (this.assistantMode) {
                case 'code': return 'fas fa-code';
                case 'test': return 'fas fa-vial';
                case 'security': return 'fas fa-shield-alt';
                default: return 'fas fa-robot';
            }
        },
        
        getModeTitle() {
            switch (this.assistantMode) {
                case 'code': return 'Code Development';
                case 'test': return 'Testing & QA';
                case 'security': return 'Security Analysis';
                default: return 'AI Assistant';
            }
        },
        
        getModeDescription() {
            switch (this.assistantMode) {
                case 'code': return 'Get code reviews, optimizations, and development guidance';
                case 'test': return 'Generate tests, analyze coverage, and improve quality';
                case 'security': return 'Scan for vulnerabilities and security best practices';
                default: return 'How can I help you today?';
            }
        },
        
        getQuickSuggestions() {
            switch (this.assistantMode) {
                case 'code':
                    return [
                        { icon: 'fas fa-search-code', text: 'Review the current file for issues' },
                        { icon: 'fas fa-rocket', text: 'Suggest performance optimizations' },
                        { icon: 'fas fa-lightbulb', text: 'Explain how this code works' },
                        { icon: 'fas fa-bug', text: 'Find potential bugs' }
                    ];
                case 'test':
                    return [
                        { icon: 'fas fa-vial', text: 'Generate unit tests for selected files' },
                        { icon: 'fas fa-chart-bar', text: 'Analyze test coverage' },
                        { icon: 'fas fa-stopwatch', text: 'Create performance tests' },
                        { icon: 'fas fa-puzzle-piece', text: 'Generate integration tests' }
                    ];
                case 'security':
                    return [
                        { icon: 'fas fa-shield-alt', text: 'Scan for security vulnerabilities' },
                        { icon: 'fas fa-cube', text: 'Check dependency security' },
                        { icon: 'fas fa-lock', text: 'Review authentication patterns' },
                        { icon: 'fas fa-key', text: 'Analyze encryption usage' }
                    ];
                default:
                    return [];
            }
        },

        // Chat functionality
        async sendChatMessage() {
            if (!this.chatInput.trim() || this.chatLoading) return;
            
            const userMessage = {
                id: Date.now(),
                role: 'user',
                content: this.chatInput.trim(),
                timestamp: new Date()
            };
            
            this.chatMessages.push(userMessage);
            const inputText = this.chatInput.trim();
            this.chatInput = '';
            
            // Scroll to bottom
            this.$nextTick(() => {
                const chatContainer = document.querySelector('.ai-chat-messages');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            });
            
            this.chatLoading = true;
            this.chatLoadingMessage = this.getLoadingMessage();
            
            try {
                let response;
                switch (this.assistantMode) {
                    case 'code':
                        response = await this.sendCodeAnalysisRequest(inputText);
                        break;
                    case 'test':
                        response = await this.sendTestGenerationRequest(inputText);
                        break;
                    case 'security':
                        response = await this.sendSecurityAnalysisRequest(inputText);
                        break;
                    default:
                        response = await this.sendGeneralChatRequest(inputText);
                }
                
                // Debug logging for response
                console.log('🔍 FRONTEND DEBUG: Full API response:', response);
                console.log('🔍 FRONTEND DEBUG: response.response length:', response.response ? response.response.length : 'undefined');
                console.log('🔍 FRONTEND DEBUG: response.content:', response.content ? 'exists' : 'undefined');
                console.log('🔍 FRONTEND DEBUG: response.success:', response.success);
                if (response.metadata) {
                    console.log('🔍 FRONTEND DEBUG: response.metadata.model:', response.metadata.model);
                    console.log('🔍 FRONTEND DEBUG: response.metadata.agent:', response.metadata.agent);
                }
                
                const assistantMessage = {
                    id: Date.now(),
                    role: 'assistant',
                    content: response.content || response.response || 'No response received',
                    timestamp: new Date(),
                    actions: response.actions || [],
                    metadata: response.metadata || {}
                };
                
                console.log('🎉 FRONTEND DEBUG: Created assistant message with content length:', assistantMessage.content.length);
                
                this.chatMessages.push(assistantMessage);
                
            } catch (error) {
                console.error('Chat error:', error);
                const errorMessage = {
                    id: Date.now(),
                    role: 'assistant',
                    content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
                    timestamp: new Date()
                };
                this.chatMessages.push(errorMessage);
            } finally {
                this.chatLoading = false;
                this.$nextTick(() => {
                    const chatContainer = document.querySelector('.ai-chat-messages');
                    if (chatContainer) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                });
            }
        },
        
        getLoadingMessage() {
            switch (this.assistantMode) {
                case 'code': return 'Analyzing code...';
                case 'test': return 'Generating tests...';
                case 'security': return 'Scanning for security issues...';
                default: return 'Thinking...';
            }
        },
        
        async sendCodeAnalysisRequest(message) {
            const requestData = {
                message: message,
                mode: 'code',
                model: this.selectedModel,
                context: {
                    selectedFile: this.selectedFile,
                    hasChanges: this.hasChanges,
                    projectId: this.projectId,
                    branch: this.currentBranch
                }
            };
            
            const response = await fetch('/api/v2/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        },

        async sendTestGenerationRequest(message) {
            const requestData = {
                message: message,
                mode: 'test',
                model: this.selectedModel,
                context: {
                    selectedFiles: this.selectedTestFiles,
                    testConfig: this.testConfig,
                    projectId: this.projectId,
                    branch: this.currentBranch,
                    modifiedFiles: this.getModifiedFiles()
                }
            };
            
            const response = await fetch('/api/v2/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        },

        async sendSecurityAnalysisRequest(message) {
            const requestData = {
                message: message,
                mode: 'security',
                model: this.selectedModel,
                context: {
                    selectedFiles: this.selectedSecurityFiles,
                    securityConfig: this.securityConfig,
                    projectId: this.projectId,
                    branch: this.currentBranch
                }
            };
            
            const response = await fetch('/api/v2/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        },

        async sendGeneralChatRequest(message) {
            const requestData = {
                message: message,
                mode: 'general',
                model: this.selectedModel,
                context: {
                    projectId: this.projectId,
                    branch: this.currentBranch
                }
            };
            
            const response = await fetch('/api/v2/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        },

        sendQuickMessage(message) {
            this.chatInput = message;
            this.sendChatMessage();
        },

        executeAction(action) {
            console.log('Executing action:', action);
            
            switch (action.id) {
                case 'review-file':
                case 'review_js':
                case 'review_python':
                    if (this.selectedFile) {
                        this.sendQuickMessage(`Please review the file ${this.selectedFile.name} for potential issues, improvements, and best practices.`);
                    } else {
                        this.sendQuickMessage('Please review the current codebase for potential issues and improvements.');
                    }
                    break;
                    
                case 'explain-code':
                case 'explain_code':
                    if (this.selectedFile) {
                        this.sendQuickMessage(`Please explain how the code in ${this.selectedFile.name} works and what it does.`);
                    }
                    break;
                    
                case 'optimize_performance':
                    if (this.selectedFile) {
                        this.sendQuickMessage(`Analyze ${this.selectedFile.name} and suggest specific performance optimizations. Show me the exact code changes to implement.`);
                    }
                    break;
                    
                case 'check_pep8':
                    if (this.selectedFile) {
                        this.sendQuickMessage(`Check ${this.selectedFile.name} for PEP8 compliance and suggest specific formatting improvements with exact code changes.`);
                    }
                    break;
                    
                case 'generate-tests':
                case 'generate_unit_tests':
                    const testFiles = this.selectedTestFiles.length > 0 ? this.selectedTestFiles : [this.selectedFile?.path].filter(Boolean);
                    if (testFiles.length > 0) {
                        this.sendQuickMessage(`Generate ${this.testConfig.type} tests for: ${testFiles.join(', ')}. Please provide the complete test code that I can copy and use.`);
                    } else {
                        this.sendQuickMessage('Generate comprehensive test suites for the selected files.');
                    }
                    break;
                    
                case 'generate_integration_tests':
                    this.sendQuickMessage('Generate integration tests that test component interactions. Provide complete test code with setup instructions.');
                    break;
                    
                case 'test-strategy':
                case 'test_strategy':
                    this.sendQuickMessage('Suggest a comprehensive testing strategy for this project including unit, integration, and e2e tests with specific frameworks and setup instructions.');
                    break;
                    
                case 'scan-vulnerabilities':
                case 'scan_vulnerabilities':
                    this.sendQuickMessage('Scan the selected files for security vulnerabilities and provide specific remediation steps with code examples.');
                    break;
                    
                case 'check-dependencies':
                case 'check_dependencies':
                    this.sendQuickMessage('Analyze the project dependencies for security vulnerabilities and outdated packages. Suggest specific updates and security improvements.');
                    break;
                    
                case 'review_auth':
                    this.sendQuickMessage('Review authentication and authorization patterns in the code. Identify security issues and provide secure code examples.');
                    break;
                    
                // New actions for applying code changes
                case 'apply_code_fix':
                    if (action.code && this.monacoEditor) {
                        this.applyCodeChanges(action.code, action.description || 'Applied AI suggestion');
                    }
                    break;
                    
                case 'apply_optimization':
                    if (action.code && this.monacoEditor) {
                        this.applyCodeChanges(action.code, 'Applied performance optimization');
                    }
                    break;
                    
                case 'apply_refactor':
                    if (action.code && this.monacoEditor) {
                        this.applyCodeChanges(action.code, 'Applied refactoring suggestion');
                    }
                    break;
                    
                default:
                    console.warn('Unknown action:', action.id);
                    // Try to handle as a general message
                    if (action.label) {
                        this.sendQuickMessage(action.label);
                    }
            }
        },

        // New method to apply code changes directly to Monaco editor
        applyCodeChanges(newCode, description = 'Applied AI changes') {
            if (!this.monacoEditor) {
                console.error('Monaco editor not available');
                return;
            }

            try {
                console.log('Applying code changes:', description);
                
                // Get current content for comparison
                const currentContent = this.monacoEditor.getValue();
                
                // Apply the new code
                this.monacoEditor.setValue(newCode);
                
                // Mark as modified
                this.hasChanges = true;
                
                // Show notification
                this.showNotification?.('success', `✅ ${description}`);
                
                // Add to chat as confirmation
                const confirmationMessage = {
                    id: Date.now(),
                    role: 'assistant',
                    content: `**✅ Code Applied Successfully**\n\n${description}\n\nThe changes have been applied to your editor. You can review them and commit when ready.`,
                    timestamp: new Date()
                };
                this.chatMessages.push(confirmationMessage);
                
                // Scroll chat to bottom
                this.$nextTick(() => {
                    const chatContainer = document.querySelector('.ai-chat-messages');
                    if (chatContainer) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                });
                
                // Focus editor to show changes
                this.monacoEditor.focus();
                
            } catch (error) {
                console.error('Error applying code changes:', error);
                this.showNotification?.('error', `❌ Failed to apply changes: ${error.message}`);
            }
        },

        // Enhanced method to handle different types of AI responses
        handleAIResponse(response) {
            // Check if response contains code to apply
            if (response.code && response.apply_directly) {
                this.applyCodeChanges(response.code, response.description);
                return;
            }
            
            // Check if response contains suggestions with code
            if (response.suggestions) {
                response.suggestions.forEach(suggestion => {
                    if (suggestion.code && suggestion.auto_apply) {
                        this.applyCodeChanges(suggestion.code, suggestion.description);
                    }
                });
            }
            
            // Handle normal message display
            const assistantMessage = {
                id: Date.now(),
                role: 'assistant',
                content: response.content || response.response || 'No response received',
                timestamp: new Date(),
                actions: response.actions || []
            };
            
            this.chatMessages.push(assistantMessage);
        },

        // Utility methods
        autoResizeTextarea(event) {
            const textarea = event.target;
            textarea.style.height = '24px';
            textarea.style.height = Math.min(textarea.scrollHeight, 60) + 'px';
        },

        formatMessage(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        },

        formatTimestamp(timestamp) {
            return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        },

        // Dependency graph methods
        async loadDependencyGraph() {
            if (this.loadingGraph) return;
            
            console.log('=== Loading Dependency Graph ===');
            this.loadingGraph = true;
            
            try {
                // Check cache first
                const cacheKey = `${this.projectId}-${this.currentBranch}`;
                if (this.dependencyCache.has(cacheKey)) {
                    console.log('Loading graph from cache');
                    this.dependencyGraph = this.dependencyCache.get(cacheKey);
                    this.renderMiniGraph();
                    return;
                }
                
                // Fetch dependency analysis from backend
                const response = await fetch(`/gitlab/repository/${this.projectId}/dependencies?branch=${this.currentBranch}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load dependencies: ${response.status}`);
                }
                
                const dependencyData = await response.json();
                console.log('Dependency analysis loaded:', dependencyData);
                
                // Process and cache the dependency graph
                this.dependencyGraph = this.processDependencyData(dependencyData);
                this.dependencyCache.set(cacheKey, this.dependencyGraph);
                
                // Render mini graph
                this.renderMiniGraph();
                
                this.showNotification?.('success', `Dependency graph loaded: ${this.dependencyGraph.nodes.length} files, ${this.dependencyGraph.edges.length} connections`);
                
            } catch (error) {
                console.error('Error loading dependency graph:', error);
                this.showNotification?.('error', `Failed to load dependency graph: ${error.message}`);
            } finally {
                this.loadingGraph = false;
            }
        },

        processDependencyData(data) {
            console.log('Processing dependency data...');
            
            const nodes = [];
            const edges = [];
            const nodeMap = new Map();
            
            // Create nodes for each file
            data.files?.forEach((file, index) => {
                const node = {
                    id: `file-${index}`,
                    name: file.path.split('/').pop(),
                    fullPath: file.path,
                    type: this.getFileLanguage({ name: file.path }),
                    size: file.size || 1,
                    dependencies: file.dependencies || [],
                    exports: file.exports || [],
                    imports: file.imports || [],
                    functions: file.functions || [],
                    classes: file.classes || [],
                    connections: 0
                };
                
                nodes.push(node);
                nodeMap.set(file.path, node);
            });
            
            // Create edges for dependencies
            data.files?.forEach(file => {
                const sourceNode = nodeMap.get(file.path);
                if (!sourceNode) return;
                
                // Import dependencies
                (file.imports || []).forEach(importPath => {
                    const targetNode = nodeMap.get(importPath);
                    if (targetNode && sourceNode.id !== targetNode.id) {
                        edges.push({
                            id: `${sourceNode.id}-${targetNode.id}`,
                            source: sourceNode.id,
                            target: targetNode.id,
                            type: 'import',
                            weight: 1
                        });
                        sourceNode.connections++;
                        targetNode.connections++;
                    }
                });
            });
            
            console.log(`Processed ${nodes.length} nodes and ${edges.length} edges`);
            return { nodes, edges, metadata: data.metadata || {} };
        },

        renderMiniGraph() {
            if (!this.dependencyGraph.nodes.length) return;
            
            const canvas = document.getElementById('dependency-graph-mini');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            
            // Clear canvas
            ctx.fillStyle = '#1f2937';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Simple visualization
            const nodes = this.dependencyGraph.nodes.slice(0, 10);
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(canvas.width, canvas.height) / 3;
            
            // Position nodes in a circle
            nodes.forEach((node, index) => {
                const angle = (index / nodes.length) * 2 * Math.PI;
                node.x = centerX + Math.cos(angle) * radius;
                node.y = centerY + Math.sin(angle) * radius;
            });
            
            // Draw edges
            ctx.strokeStyle = '#4b5563';
            ctx.lineWidth = 1;
            this.dependencyGraph.edges.forEach(edge => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);
                
                if (sourceNode && targetNode) {
                    ctx.beginPath();
                    ctx.moveTo(sourceNode.x, sourceNode.y);
                    ctx.lineTo(targetNode.x, targetNode.y);
                    ctx.stroke();
                }
            });
            
            // Draw nodes
            nodes.forEach(node => {
                const nodeRadius = Math.max(3, Math.min(8, node.connections));
                
                ctx.fillStyle = '#3b82f6';
                ctx.beginPath();
                ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
                ctx.fill();
            });
        },

        openFullGraphView() {
            console.log('Opening full graph view');
            this.showGraphModal = true;
            this.loadingFullGraph = true;
            
            setTimeout(() => {
                this.renderFullGraph();
                this.loadingFullGraph = false;
            }, 100);
        },

        renderFullGraph() {
            // Placeholder for full graph rendering
            console.log('Rendering full graph...');
        },

        // Analysis functionality
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
                    this.showNotification?.('success', 'Changes committed successfully!');
                    await this.loadCommits();
                } else {
                    this.showNotification?.('error', 'Error committing changes: ' + result.error);
                }
                
                this.loading = false;
                
            } catch (error) {
                console.error('Error committing changes:', error);
                this.showNotification?.('error', 'Error committing changes: ' + error.message);
                this.loading = false;
            }
        },

        // Initialize horizontal sidebar tabs functionality
        initializeSidebarTabs() {
            // Set up tab switching logic
            this.$nextTick(() => {
                const tabs = document.querySelectorAll('.sidebar-tab');
                const contents = document.querySelectorAll('.tab-content');
                
                tabs.forEach(tab => {
                    tab.addEventListener('click', () => {
                        const targetContent = tab.dataset.content;
                        
                        // Remove active class from all tabs
                        tabs.forEach(t => t.classList.remove('active'));
                        // Add active class to clicked tab
                        tab.classList.add('active');
                        
                        // Hide all content
                        contents.forEach(content => content.classList.remove('active'));
                        
                        // Show target content
                        const targetElement = document.getElementById(`${targetContent}-content`);
                        if (targetElement) {
                            targetElement.classList.add('active');
                        }
                        
                        // Update active tab state
                        this.activeTab = targetContent;
                        
                        // Load data if needed
                        this.onTabChange(targetContent);
                    });
                });
            });
        },
        
        // Handle tab change events
        onTabChange(tabName) {
            switch (tabName) {
                case 'graph':
                    if (this.dependencyGraph.nodes.length === 0) {
                        this.loadDependencyGraph();
                    }
                    break;
                case 'commits':
                    if (this.commits.length === 0) {
                        this.loadCommits();
                    }
                    break;
                case 'prs':
                    if (this.pullRequests.length === 0) {
                        this.loadPullRequests();
                    }
                    break;
            }
        },
    };
}

// Activity Bar Navigation - Updated for new layout
document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea functionality
    window.autoResizeTextarea = function(event) {
        const textarea = event.target;
        textarea.style.height = '24px';
        textarea.style.height = Math.min(textarea.scrollHeight, 60) + 'px';
    };
}); 