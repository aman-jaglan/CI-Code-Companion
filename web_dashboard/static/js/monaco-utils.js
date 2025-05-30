// Monaco Editor Language Support and Configuration
function monacoLanguageUtils() {
    return {
        getMonacoLanguage(filename) {
            if (!filename || typeof filename !== 'string') {
                console.warn('[getMonacoLanguage] Invalid filename provided:', filename);
                return 'plaintext';
            }
            
            const parts = filename.split('.');
            const ext = parts.length > 1 ? parts.pop().toLowerCase() : null;
            const basename = parts.join('.');
            
            if (!ext) {
                // Handle files without extensions by name
                const nameMap = {
                    'dockerfile': 'dockerfile',
                    'makefile': 'makefile',
                    'vagrantfile': 'ruby',
                    'gemfile': 'ruby',
                    'rakefile': 'ruby',
                    'gruntfile': 'javascript',
                    'gulpfile': 'javascript'
                };
                return nameMap[basename.toLowerCase()] || 'plaintext';
            }

            const langMap = {
                // Web Technologies
                'html': 'html',
                'htm': 'html',
                'xhtml': 'html',
                'css': 'css',
                'scss': 'scss',
                'sass': 'scss',
                'less': 'less',
                'js': 'javascript',
                'jsx': 'jsx',
                'ts': 'typescript',
                'tsx': 'typescript',
                'vue': 'vue',
                'svelte': 'svelte',
                
                // Backend Languages
                'py': 'python',
                'pyw': 'python',
                'pyi': 'python',
                'java': 'java',
                'class': 'java',
                'kt': 'kotlin',
                'scala': 'scala',
                'rb': 'ruby',
                'php': 'php',
                'go': 'go',
                'rs': 'rust',
                'swift': 'swift',
                'cs': 'csharp',
                'vb': 'vb',
                'fs': 'fsharp',
                'cpp': 'cpp',
                'cxx': 'cpp',
                'cc': 'cpp',
                'c': 'c',
                'h': 'c',
                'hpp': 'cpp',
                'hxx': 'cpp',
                
                // Data & Config
                'json': 'json',
                'jsonc': 'json',
                'yaml': 'yaml',
                'yml': 'yaml',
                'toml': 'toml',
                'ini': 'ini',
                'cfg': 'ini',
                'conf': 'ini',
                'xml': 'xml',
                'xsl': 'xml',
                'xslt': 'xml',
                'svg': 'xml',
                
                // Documentation
                'md': 'markdown',
                'markdown': 'markdown',
                'mdown': 'markdown',
                'mkd': 'markdown',
                'rst': 'restructuredtext',
                'txt': 'plaintext',
                'rtf': 'plaintext',
                'tex': 'latex',
                'latex': 'latex',
                
                // Database
                'sql': 'sql',
                'mysql': 'mysql',
                'pgsql': 'pgsql',
                'plsql': 'plsql',
                
                // Shell & Scripts
                'sh': 'shell',
                'bash': 'shell',
                'zsh': 'shell',
                'fish': 'shell',
                'ps1': 'powershell',
                'psm1': 'powershell',
                'bat': 'bat',
                'cmd': 'bat',
                
                // DevOps & Infrastructure
                'dockerfile': 'dockerfile',
                'tf': 'hcl',
                'hcl': 'hcl',
                'nomad': 'hcl',
                'k8s': 'yaml',
                'kube': 'yaml',
                
                // Other common languages
                'r': 'r',
                'matlab': 'matlab',
                'jl': 'julia',
                'pl': 'perl',
                'pm': 'perl',
                'tcl': 'tcl',
                'awk': 'awk',
                'vim': 'vim',
                'vimrc': 'vim',
                'dart': 'dart',
                'm': 'objective-c',
                'mm': 'objective-cpp',
                'glsl': 'glsl',
                'hlsl': 'hlsl',
                'shader': 'glsl'
            };
            
            // Handle compound extensions (e.g., .test.js, .spec.ts)
            if (parts.length > 1) {
                const secondExt = parts[parts.length - 1]?.toLowerCase();
                const compoundKey = `${secondExt}.${ext}`;
                const compoundMap = {
                    'test.js': 'javascript',
                    'spec.js': 'javascript',
                    'test.ts': 'typescript',
                    'spec.ts': 'typescript',
                    'test.py': 'python',
                    'spec.py': 'python',
                    'd.ts': 'typescript', // TypeScript declaration files
                    'min.js': 'javascript',
                    'min.css': 'css'
                };
                
                if (compoundMap[compoundKey]) {
                    return compoundMap[compoundKey];
                }
            }
            
            return langMap[ext] || 'plaintext';
        },

        getEditorOptions(language, content) {
            const baseOptions = {
                value: content,
                language: language,
                theme: 'vs-dark',
                automaticLayout: true,
                minimap: { enabled: true },
                renderLineHighlight: 'all',
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                fontSize: 14,
                tabSize: this.getTabSize(language),
                insertSpaces: true,
                detectIndentation: true,
                folding: true,
                foldingStrategy: 'auto',
                showFoldingControls: 'mouseover',
                bracketPairColorization: { enabled: true },
                guides: {
                    indentation: true,
                    bracketPairs: true
                }
            };
            
            // Language-specific options
            const languageOptions = this.getLanguageSpecificOptions(language);
            
            return { ...baseOptions, ...languageOptions };
        },
        
        getLanguageSpecificOptions(language) {
            switch (language) {
                case 'python':
                    return {
                        tabSize: 4,
                        rulers: [79, 100], // PEP 8 line length guides
                        wordWrap: 'off',
                        semanticHighlighting: { enabled: true }
                    };
                case 'javascript':
                case 'typescript':
                    return {
                        tabSize: 2,
                        rulers: [120],
                        formatOnPaste: true,
                        formatOnType: true,
                        suggest: {
                            includeWordBasedSuggestions: true
                        }
                    };
                case 'json':
                    return {
                        tabSize: 2,
                        formatOnPaste: true,
                        validate: true,
                        allowComments: false
                    };
                case 'markdown':
                    return {
                        tabSize: 2,
                        wordWrap: 'on',
                        rulers: [80],
                        minimap: { enabled: false },
                        lineNumbers: 'off',
                        glyphMargin: false,
                        folding: true,
                        links: true,
                        colorDecorators: true
                    };
                case 'yaml':
                    return {
                        tabSize: 2,
                        insertSpaces: true,
                        rulers: [120]
                    };
                case 'css':
                case 'scss':
                case 'less':
                    return {
                        tabSize: 2,
                        formatOnPaste: true,
                        colorDecorators: true
                    };
                case 'html':
                    return {
                        tabSize: 2,
                        formatOnPaste: true,
                        suggest: {
                            html5: true
                        }
                    };
                default:
                    return {
                        tabSize: 4,
                        rulers: [120]
                    };
            }
        },
        
        getTabSize(language) {
            const tabSizes = {
                'python': 4,
                'javascript': 2,
                'typescript': 2,
                'jsx': 2,
                'tsx': 2,
                'json': 2,
                'yaml': 2,
                'yml': 2,
                'css': 2,
                'scss': 2,
                'less': 2,
                'html': 2,
                'xml': 2,
                'markdown': 2,
                'sql': 4,
                'shell': 4,
                'bash': 4,
                'dockerfile': 4
            };
            return tabSizes[language] || 4;
        },

        configureLanguageFeatures(language) {
            switch (language) {
                case 'python':
                    this.configurePythonFeatures();
                    break;
                case 'javascript':
                case 'typescript':
                    this.configureJavaScriptFeatures();
                    break;
                case 'json':
                    this.configureJsonFeatures();
                    break;
                case 'markdown':
                    this.configureMarkdownFeatures();
                    break;
                case 'yaml':
                    this.configureYamlFeatures();
                    break;
                case 'html':
                    this.configureHtmlFeatures();
                    break;
                case 'css':
                    this.configureCssFeatures();
                    break;
            }
        },

        configurePythonFeatures() {
            // Python-specific IntelliSense and validation
            monaco.languages.registerCompletionItemProvider('python', {
                provideCompletionItems: (model, position) => {
                    const suggestions = [
                        {
                            label: 'import',
                            kind: monaco.languages.CompletionItemKind.Keyword,
                            insertText: 'import ${1:module}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'def',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'def ${1:function_name}(${2:args}):\n    ${3:pass}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                            documentation: 'Define a function'
                        },
                        {
                            label: 'class',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'class ${1:ClassName}:\n    def __init__(self${2:, args}):\n        ${3:pass}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                            documentation: 'Define a class'
                        },
                        {
                            label: 'if __name__ == "__main__"',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'if __name__ == "__main__":\n    ${1:main()}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        }
                    ];
                    return { suggestions };
                }
            });
        },
        
        configureJavaScriptFeatures() {
            // JavaScript/TypeScript-specific features
            monaco.languages.registerCompletionItemProvider('javascript', {
                provideCompletionItems: (model, position) => {
                    const suggestions = [
                        {
                            label: 'function',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'function ${1:functionName}(${2:params}) {\n    ${3:// TODO: implement}\n}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'arrow function',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'const ${1:functionName} = (${2:params}) => {\n    ${3:// TODO: implement}\n};',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'async function',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'async function ${1:functionName}(${2:params}) {\n    ${3:// TODO: implement}\n}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'try-catch',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'try {\n    ${1:// code}\n} catch (${2:error}) {\n    ${3:console.error(error);}\n}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        }
                    ];
                    return { suggestions };
                }
            });
        },
        
        configureJsonFeatures() {
            // JSON validation and formatting
            monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                validate: true,
                allowComments: false,
                schemas: [],
                enableSchemaRequest: true
            });
        },
        
        configureMarkdownFeatures() {
            // Markdown-specific features
            monaco.languages.registerCompletionItemProvider('markdown', {
                provideCompletionItems: (model, position) => {
                    const suggestions = [
                        {
                            label: 'heading1',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '# ${1:Heading}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'heading2',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '## ${1:Heading}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'code block',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '```${1:language}\n${2:code}\n```',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'link',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '[${1:text}](${2:url})',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'image',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '![${1:alt text}](${2:image url})',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'table',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '| ${1:Header 1} | ${2:Header 2} |\n|----------|----------|\n| ${3:Cell 1} | ${4:Cell 2} |',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        }
                    ];
                    return { suggestions };
                }
            });
        },
        
        configureYamlFeatures() {
            // YAML-specific features
            monaco.languages.registerCompletionItemProvider('yaml', {
                provideCompletionItems: (model, position) => {
                    const suggestions = [
                        {
                            label: 'docker-compose service',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: '${1:service_name}:\n  image: ${2:image_name}\n  ports:\n    - "${3:port}:${4:port}"\n  environment:\n    - ${5:ENV_VAR}=${6:value}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        },
                        {
                            label: 'github action',
                            kind: monaco.languages.CompletionItemKind.Snippet,
                            insertText: 'name: ${1:Action Name}\non: [${2:push, pull_request}]\njobs:\n  ${3:job_name}:\n    runs-on: ${4:ubuntu-latest}\n    steps:\n      - uses: actions/checkout@v2\n      - name: ${5:Step Name}\n        run: ${6:command}',
                            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                        }
                    ];
                    return { suggestions };
                }
            });
        },
        
        configureHtmlFeatures() {
            // HTML-specific features
            monaco.languages.html.htmlDefaults.setOptions({
                format: {
                    tabSize: 2,
                    insertSpaces: true,
                    wrapLineLength: 120,
                    unformatted: 'default"',
                    contentUnformatted: 'pre,code,textarea',
                    indentInnerHtml: false,
                    preserveNewLines: true,
                    maxPreserveNewLines: 2,
                    indentHandlebars: false,
                    endWithNewline: false,
                    extraLiners: 'head, body, /html',
                    wrapAttributes: 'auto'
                },
                suggest: {
                    html5: true,
                    angular1: false,
                    ionic: false
                }
            });
        },
        
        configureCssFeatures() {
            // CSS-specific features
            monaco.languages.css.cssDefaults.setOptions({
                validate: true,
                lint: {
                    compatibleVendorPrefixes: 'ignore',
                    vendorPrefix: 'warning',
                    duplicateProperties: 'warning',
                    emptyRules: 'warning',
                    importStatement: 'ignore',
                    boxModel: 'ignore',
                    universalSelector: 'ignore',
                    zeroUnits: 'ignore',
                    fontFaceProperties: 'warning',
                    hexColorLength: 'error',
                    argumentsInColorFunction: 'error',
                    unknownProperties: 'warning',
                    ieHack: 'ignore',
                    unknownVendorSpecificProperties: 'ignore',
                    propertyIgnoredDueToDisplay: 'warning',
                    important: 'ignore',
                    float: 'ignore',
                    idSelector: 'ignore'
                }
            });
        },

        setupLanguageShortcuts(language) {
            // Add language-specific keyboard shortcuts
            if (!this.monacoEditor) return;
            
            // Universal shortcuts
            this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
                this.saveFile();
            });
            
            this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
                this.formatDocument();
            });
            
            // Language-specific shortcuts
            switch (language) {
                case 'python':
                    this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
                        this.runPythonCode();
                    });
                    break;
                case 'javascript':
                case 'typescript':
                    this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
                        this.runJavaScriptCode();
                    });
                    break;
                case 'markdown':
                    this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB, () => {
                        this.insertMarkdownBold();
                    });
                    this.monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyI, () => {
                        this.insertMarkdownItalic();
                    });
                    break;
            }
        },

        validateContent(language, content) {
            // Perform language-specific validation
            switch (language) {
                case 'json':
                    this.validateJson(content);
                    break;
                case 'yaml':
                    this.validateYaml(content);
                    break;
                case 'python':
                    this.validatePython(content);
                    break;
            }
        },
        
        validateJson(content) {
            try {
                JSON.parse(content);
                this.clearValidationErrors();
            } catch (error) {
                this.showValidationError('JSON', error.message);
            }
        },
        
        validateYaml(content) {
            // Basic YAML validation
            if (content.includes('\t')) {
                this.showValidationError('YAML', 'YAML files should use spaces, not tabs for indentation');
            } else {
                this.clearValidationErrors();
            }
        },
        
        validatePython(content) {
            // Basic Python syntax checking
            const lines = content.split('\n');
            let errors = [];
            
            lines.forEach((line, index) => {
                const trimmed = line.trim();
                if (trimmed && !trimmed.startsWith('#')) {
                    const indent = line.length - line.trimStart().length;
                    if (indent % 4 !== 0) {
                        errors.push(`Line ${index + 1}: Inconsistent indentation (should be multiples of 4)`);
                    }
                }
            });
            
            if (errors.length > 0) {
                this.showValidationError('Python', errors[0]);
            } else {
                this.clearValidationErrors();
            }
        },

        formatDocument() {
            if (this.monacoEditor) {
                this.monacoEditor.trigger('anyString', 'editor.action.formatDocument');
            }
        },
        
        showValidationError(language, message) {
            // You can implement a proper error display here
            console.warn(`${language} validation error:`, message);
        },
        
        clearValidationErrors() {
            // Clear any validation error displays
            console.log('Validation passed');
        },
        
        // Mock keyboard shortcut implementations
        saveFile() {
            if (this.hasChanges) {
                this.commitChanges();
            }
        },
        
        runPythonCode() {
            this.showNotification('info', 'Python execution feature coming soon!');
        },
        
        runJavaScriptCode() {
            this.showNotification('info', 'JavaScript execution feature coming soon!');
        },
        
        insertMarkdownBold() {
            const selection = this.monacoEditor.getSelection();
            const text = this.monacoEditor.getModel().getValueInRange(selection);
            this.monacoEditor.executeEdits('bold', [{
                range: selection,
                text: `**${text}**`
            }]);
        },
        
        insertMarkdownItalic() {
            const selection = this.monacoEditor.getSelection();
            const text = this.monacoEditor.getModel().getValueInRange(selection);
            this.monacoEditor.executeEdits('italic', [{
                range: selection,
                text: `*${text}*`
            }]);
        }
    };
} 