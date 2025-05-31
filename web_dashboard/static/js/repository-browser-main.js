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
            insights: true,
            dependencies: false
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
        showGraphModal: false,
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
        },

        // === DEPENDENCY GRAPH SYSTEM ===
        
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
                
                this.showNotification('success', `Dependency graph loaded: ${this.dependencyGraph.nodes.length} files, ${this.dependencyGraph.edges.length} connections`);
                
            } catch (error) {
                console.error('Error loading dependency graph:', error);
                this.showNotification('error', `Failed to load dependency graph: ${error.message}`);
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
            data.files.forEach((file, index) => {
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
            data.files.forEach(file => {
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
                
                // Function call dependencies
                (file.function_calls || []).forEach(funcCall => {
                    const targetNode = Array.from(nodeMap.values()).find(n => 
                        n.functions.some(f => f.name === funcCall.function)
                    );
                    if (targetNode && sourceNode.id !== targetNode.id) {
                        edges.push({
                            id: `${sourceNode.id}-${targetNode.id}-func`,
                            source: sourceNode.id,
                            target: targetNode.id,
                            type: 'function_call',
                            weight: 0.5
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
            
            // Check if we should use vis-network or canvas fallback
            if (window.visNetworkLoaded === true) {
                // Use vis-network for interactive mini graph
                this.renderMiniGraphWithVis(canvas);
            } else {
                // Use canvas fallback for simple visualization
                this.renderMiniGraphWithCanvas(canvas);
            }
        },
        
        renderMiniGraphWithCanvas(canvas) {
            const ctx = canvas.getContext('2d');
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width;
            canvas.height = rect.height;
            
            // Clear canvas
            ctx.fillStyle = '#1f2937';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Simple force-directed layout for mini preview
            const nodes = this.dependencyGraph.nodes.slice(0, 20); // Limit for performance
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
                
                // Node color based on type
                const colors = {
                    'Python': '#3b82f6',
                    'JavaScript': '#f59e0b',
                    'TypeScript': '#6366f1',
                    'JSON': '#10b981',
                    'CSS': '#ec4899'
                };
                
                ctx.fillStyle = colors[node.type] || '#6b7280';
                ctx.beginPath();
                ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
                ctx.fill();
                
                // Highlight highly connected nodes
                if (node.connections > 3) {
                    ctx.strokeStyle = '#fbbf24';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });
        },
        
        renderMiniGraphWithVis(canvas) {
            // Convert canvas to a div for vis-network
            const container = canvas.parentNode;
            const visDiv = document.createElement('div');
            visDiv.id = 'dependency-graph-mini-vis';
            visDiv.style.width = '100%';
            visDiv.style.height = '100%';
            
            container.replaceChild(visDiv, canvas);
            
            try {
                const nodes = new vis.DataSet(this.dependencyGraph.nodes.slice(0, 15).map(node => ({
                    id: node.id,
                    label: node.name.length > 10 ? node.name.substring(0, 10) + '...' : node.name,
                    size: Math.max(5, Math.min(15, node.connections * 2)),
                    color: this.getNodeColor(node).background,
                    font: { color: '#e5e7eb', size: 8 }
                })));
                
                const edges = new vis.DataSet(this.dependencyGraph.edges.filter(edge => {
                    const sourceExists = nodes.get(edge.source);
                    const targetExists = nodes.get(edge.target);
                    return sourceExists && targetExists;
                }).slice(0, 20).map(edge => ({
                    from: edge.source,
                    to: edge.target,
                    color: this.getEdgeColor(edge.type),
                    width: 1
                })));
                
                const data = { nodes, edges };
                const options = {
                    layout: { randomSeed: 2 },
                    physics: { enabled: false },
                    interaction: { dragNodes: false, dragView: false, zoomView: false },
                    nodes: { borderWidth: 0, font: { size: 8 } },
                    edges: { smooth: false }
                };
                
                this.miniGraphInstance = new vis.Network(visDiv, data, options);
            } catch (error) {
                console.error('Error rendering mini graph with vis:', error);
                // Fall back to canvas if vis fails
                const newCanvas = document.createElement('canvas');
                newCanvas.id = 'dependency-graph-mini';
                newCanvas.className = 'w-full h-full cursor-pointer';
                newCanvas.addEventListener('click', () => this.openFullGraphView());
                container.replaceChild(newCanvas, visDiv);
                this.renderMiniGraphWithCanvas(newCanvas);
            }
        },
        
        openFullGraphView() {
            console.log('Opening full graph view');
            
            // Check if we have dependency data
            if (!this.dependencyGraph.nodes.length) {
                this.showNotification('warning', 'No dependency data available. Please load the dependency graph first.');
                return;
            }
            
            // Open modal regardless of vis-network status
            this.showGraphModal = true;
            this.loadingFullGraph = true;
            
            // Wait for vis-network to be ready (or fallback to be ready)
            const renderGraph = () => {
                this.renderFullGraph();
                this.loadingFullGraph = false;
            };
            
            if (window.visNetworkLoaded) {
                // Already loaded (either real or fallback)
                setTimeout(renderGraph, 100);
            } else {
                // Wait for vis-network to load
                const timeout = setTimeout(() => {
                    console.log('Timeout waiting for vis-network, using fallback');
                    renderGraph();
                }, 3000);
                
                window.addEventListener('visNetworkReady', () => {
                    clearTimeout(timeout);
                    renderGraph();
                }, { once: true });
            }
        },
        
        renderFullGraph() {
            const container = document.getElementById('dependency-graph-full');
            if (!container || !this.dependencyGraph.nodes.length) return;
            
            // Clear previous instance
            if (this.fullGraphInstance) {
                try {
                    this.fullGraphInstance.destroy();
                } catch (e) {
                    console.warn('Error destroying previous graph instance:', e);
                }
                this.fullGraphInstance = null;
            }
            
            // Check vis-network availability and render accordingly
            if (window.visNetworkLoaded === true) {
                this.renderFullGraphWithVis(container);
            } else if (window.visNetworkLoaded === 'fallback') {
                this.renderFullGraphFallback(container);
            } else {
                this.renderFullGraphFallback(container);
            }
        },
        
        renderFullGraphWithVis(container) {
            try {
                // Initialize vis.js network with correct API
                const nodes = new vis.DataSet(this.dependencyGraph.nodes.map(node => ({
                    id: node.id,
                    label: node.name,
                    title: `${node.fullPath}\nType: ${node.type}\nConnections: ${node.connections}`,
                    size: Math.max(10, Math.min(30, node.connections * 3)),
                    color: this.getNodeColor(node),
                    font: { color: '#e5e7eb', size: 12 },
                    borderWidth: 2,
                    borderColor: '#374151'
                })));
                
                const edges = new vis.DataSet(this.dependencyGraph.edges.map(edge => ({
                    id: edge.id,
                    from: edge.source,
                    to: edge.target,
                    color: this.getEdgeColor(edge.type),
                    width: edge.weight * 2,
                    arrows: 'to',
                    smooth: { type: 'continuous' }
                })));
                
                const data = { nodes, edges };
                const options = {
                    layout: {
                        improvedLayout: true,
                        clusterThreshold: 150
                    },
                    physics: {
                        enabled: true,
                        stabilization: { iterations: 100 }
                    },
                    interaction: {
                        hover: true,
                        selectConnectedEdges: false
                    },
                    nodes: {
                        shape: 'dot',
                        scaling: { min: 10, max: 30 }
                    },
                    edges: {
                        smooth: true,
                        scaling: { min: 1, max: 5 }
                    }
                };
                
                this.fullGraphInstance = new vis.Network(container, data, options);
                
                // Add event listeners
                this.fullGraphInstance.on('selectNode', (params) => {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        this.selectedNode = this.dependencyGraph.nodes.find(n => n.id === nodeId);
                    }
                });
                
                this.fullGraphInstance.on('deselectNode', () => {
                    this.selectedNode = null;
                });
                
                console.log('Full dependency graph rendered successfully with vis-network');
                
            } catch (error) {
                console.error('Error rendering full graph with vis:', error);
                this.renderFullGraphFallback(container);
            }
        },
        
        renderFullGraphFallback(container) {
            console.log('Using fallback graph visualization');
            
            // Create a comprehensive fallback interface
            container.innerHTML = `
                <div class="h-full bg-gray-800 p-6 overflow-y-auto">
                    <div class="text-center mb-6">
                        <i class="fas fa-project-diagram text-4xl mb-4 text-blue-400"></i>
                        <h3 class="text-xl font-medium text-white mb-2">Dependency Analysis</h3>
                        <p class="text-sm text-gray-400">Interactive visualization unavailable - showing data view</p>
                    </div>
                    
                    <!-- Statistics -->
                    <div class="grid grid-cols-2 gap-4 mb-6">
                        <div class="bg-gray-700 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-blue-400">${this.dependencyGraph.nodes.length}</div>
                            <div class="text-sm text-gray-300">Files Analyzed</div>
                        </div>
                        <div class="bg-gray-700 rounded-lg p-4 text-center">
                            <div class="text-2xl font-bold text-green-400">${this.dependencyGraph.edges.length}</div>
                            <div class="text-sm text-gray-300">Dependencies Found</div>
                        </div>
                    </div>
                    
                    <!-- Top Connected Files -->
                    <div class="mb-6">
                        <h4 class="text-lg font-medium text-white mb-3 flex items-center">
                            <i class="fas fa-star mr-2 text-yellow-400"></i>
                            Most Connected Files
                        </h4>
                        <div class="space-y-2">
                            ${this.getTopConnectedFiles().map(file => `
                                <div class="bg-gray-700 rounded p-3 flex justify-between items-center">
                                    <div>
                                        <div class="font-mono text-sm text-white">${file.name}</div>
                                        <div class="text-xs text-gray-400">Type: ${this.dependencyGraph.nodes.find(n => n.id === file.id)?.type || 'Unknown'}</div>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-lg font-bold text-blue-400">${file.connections}</div>
                                        <div class="text-xs text-gray-400">connections</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- File List -->
                    <div>
                        <h4 class="text-lg font-medium text-white mb-3 flex items-center">
                            <i class="fas fa-list mr-2 text-green-400"></i>
                            All Files (${this.dependencyGraph.nodes.length})
                        </h4>
                        <div class="space-y-1 max-h-96 overflow-y-auto">
                            ${this.dependencyGraph.nodes.map(node => `
                                <div class="bg-gray-700 rounded p-2 flex justify-between items-center hover:bg-gray-600 cursor-pointer"
                                     onclick="this.classList.toggle('bg-gray-600')">
                                    <div class="flex items-center space-x-2">
                                        <div class="w-3 h-3 rounded-full" style="background-color: ${this.getNodeColor(node).background}"></div>
                                        <span class="font-mono text-sm text-white">${node.name}</span>
                                        <span class="text-xs text-gray-400">(${node.type})</span>
                                    </div>
                                    <div class="text-xs text-blue-400">${node.connections} deps</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            console.log('Fallback graph visualization rendered');
        },
        
        getNodeColor(node) {
            const typeColors = {
                'Python': { background: '#3b82f6', border: '#1e40af' },
                'JavaScript': { background: '#f59e0b', border: '#d97706' },
                'TypeScript': { background: '#6366f1', border: '#4f46e5' },
                'JSON': { background: '#10b981', border: '#059669' },
                'CSS': { background: '#ec4899', border: '#db2777' },
                'HTML': { background: '#f97316', border: '#ea580c' },
                'Markdown': { background: '#6b7280', border: '#4b5563' }
            };
            
            return typeColors[node.type] || { background: '#6b7280', border: '#4b5563' };
        },
        
        getEdgeColor(type) {
            const edgeColors = {
                'import': '#10b981',
                'function_call': '#3b82f6',
                'class_inheritance': '#8b5cf6',
                'export': '#f59e0b'
            };
            
            return edgeColors[type] || '#6b7280';
        },
        
        // Graph utility methods
        getTopConnectedFiles() {
            if (!this.dependencyGraph.nodes.length) return [];
            
            return this.dependencyGraph.nodes
                .sort((a, b) => b.connections - a.connections)
                .slice(0, 5)
                .map(node => ({
                    id: node.id,
                    name: node.name,
                    connections: node.connections
                }));
        },
        
        getNodeConnections(node) {
            if (!node || !this.dependencyGraph.edges.length) return [];
            
            const connections = [];
            this.dependencyGraph.edges.forEach(edge => {
                if (edge.source === node.id) {
                    const targetNode = this.dependencyGraph.nodes.find(n => n.id === edge.target);
                    if (targetNode) {
                        connections.push({
                            id: targetNode.id,
                            name: targetNode.name,
                            type: edge.type
                        });
                    }
                }
                if (edge.target === node.id) {
                    const sourceNode = this.dependencyGraph.nodes.find(n => n.id === edge.source);
                    if (sourceNode) {
                        connections.push({
                            id: sourceNode.id,
                            name: sourceNode.name,
                            type: edge.type
                        });
                    }
                }
            });
            
            return connections;
        },
        
        getConnectionTypeColor(type) {
            const colors = {
                'import': 'text-green-400',
                'function_call': 'text-blue-400',
                'class_inheritance': 'text-purple-400',
                'export': 'text-yellow-400'
            };
            return colors[type] || 'text-gray-400';
        },
        
        getAverageConnections() {
            if (!this.dependencyGraph.nodes.length) return '0.0';
            const total = this.dependencyGraph.nodes.reduce((sum, node) => sum + node.connections, 0);
            return (total / this.dependencyGraph.nodes.length).toFixed(1);
        },
        
        getMaxConnections() {
            if (!this.dependencyGraph.nodes.length) return 0;
            return Math.max(...this.dependencyGraph.nodes.map(node => node.connections));
        },
        
        // Graph controls
        toggleGraphFilter(filterType) {
            this.graphFilters[filterType] = !this.graphFilters[filterType];
            if (this.fullGraphInstance) {
                this.renderFullGraph(); // Re-render with new filters
            }
        },
        
        updateGraphLayout() {
            if (!this.fullGraphInstance) return;
            
            const layoutOptions = {
                force: { physics: { enabled: true } },
                hierarchical: { 
                    layout: { hierarchical: { direction: 'UD', sortMethod: 'directed' } },
                    physics: { enabled: false }
                },
                circular: {
                    layout: { randomSeed: 2 },
                    physics: { enabled: false }
                },
                grid: {
                    layout: { randomSeed: undefined },
                    physics: { enabled: false }
                }
            };
            
            this.fullGraphInstance.setOptions(layoutOptions[this.graphLayout] || layoutOptions.force);
        },
        
        centerGraph() {
            if (this.fullGraphInstance) {
                this.fullGraphInstance.fit();
            }
        },
        
        exportGraph() {
            const graphData = {
                nodes: this.dependencyGraph.nodes,
                edges: this.dependencyGraph.edges,
                metadata: {
                    project: this.projectName,
                    branch: this.currentBranch,
                    exported: new Date().toISOString()
                }
            };
            
            const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.projectName}-dependency-graph.json`;
            a.click();
            URL.revokeObjectURL(url);
        },
        
        refreshDependencyCache() {
            const cacheKey = `${this.projectId}-${this.currentBranch}`;
            this.dependencyCache.delete(cacheKey);
            this.loadDependencyGraph();
        },
        
        // === MULTI-FILE EDIT SUPPORT ===
        
        getConnectedFiles(filePath) {
            if (!this.dependencyGraph.nodes.length) return [];
            
            const currentNode = this.dependencyGraph.nodes.find(n => n.fullPath === filePath);
            if (!currentNode) return [];
            
            const connectedFiles = this.getNodeConnections(currentNode);
            return connectedFiles.map(conn => ({
                path: this.dependencyGraph.nodes.find(n => n.id === conn.id)?.fullPath,
                type: conn.type,
                name: conn.name
            })).filter(f => f.path);
        },
        
        async updateMultipleFiles(changes) {
            // This will be called when AI makes changes to multiple connected files
            console.log('Updating multiple connected files:', changes);
            
            const results = [];
            for (const change of changes) {
                try {
                    const result = await this.updateSingleFile(change.path, change.content, change.message);
                    results.push({ ...change, success: true, result });
                } catch (error) {
                    results.push({ ...change, success: false, error: error.message });
                }
            }
            
            return results;
        },
        
        async updateSingleFile(filePath, content, commitMessage) {
            const response = await fetch(`/gitlab/repository/${this.projectId}/commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_path: filePath,
                    branch: this.currentBranch,
                    content: content,
                    commit_message: commitMessage || `Update ${filePath}`
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update ${filePath}: ${response.status}`);
            }
            
            return response.json();
        }
    };
} 