// theme.js
export function createTheme() {
    return {
        base: 'vs-dark',
        inherit: true,
        rules: [
            // Python syntax highlighting
            { token: 'keyword', foreground: '#C586C0' },
            { token: 'type', foreground: '#4EC9B0' },
            { token: 'string', foreground: '#CE9178' },
            { token: 'number', foreground: '#B5CEA8' },
            { token: 'comment', foreground: '#6A9955' },
            { token: 'operator', foreground: '#D4D4D4' },
            { token: 'function', foreground: '#DCDCAA' },
            { token: 'variable', foreground: '#9CDCFE' },
            { token: 'parameter', foreground: '#9CDCFE' },
            { token: 'class', foreground: '#4EC9B0' },
            { token: 'decorator', foreground: '#DCDCAA' },
            
            // Diff specific colors
            { token: 'diff.deleted', foreground: '#ff6b6b', fontStyle: 'italic' },
            { token: 'diff.inserted', foreground: '#51cf66', fontStyle: 'bold' },
            { token: 'diff.header', foreground: '#569CD6', fontStyle: 'italic' }
        ],
        colors: {
            // Editor colors
            'editor.background': '#1E1E1E',
            'editor.foreground': '#D4D4D4',
            'editor.lineHighlightBackground': '#2A2D2E',
            'editor.selectionBackground': '#264F78',
            'editor.inactiveSelectionBackground': '#3A3D41',
            
            // Diff editor colors
            'diffEditor.insertedTextBackground': '#51cf6633',
            'diffEditor.removedTextBackground': '#ff6b6b33',
            'diffEditor.insertedLineBackground': '#51cf6619',
            'diffEditor.removedLineBackground': '#ff6b6b19',
            
            // Gutter colors
            'editorGutter.background': '#1E1E1E',
            'editorGutter.modifiedBackground': '#51cf66',
            'editorGutter.addedBackground': '#51cf66',
            'editorGutter.deletedBackground': '#ff6b6b',
            
            // Line number colors
            'editorLineNumber.foreground': '#858585',
            'editorLineNumber.activeForeground': '#C6C6C6',
            
            // Suggestion widget colors
            'editorSuggestWidget.background': '#252526',
            'editorSuggestWidget.foreground': '#D4D4D4',
            'editorSuggestWidget.selectedBackground': '#062F4A',
            'editorSuggestWidget.highlightForeground': '#51cf66',
            
            // Error and warning colors
            'editorError.foreground': '#F14C4C',
            'editorWarning.foreground': '#CCA700',
            'editorInfo.foreground': '#3794FF',
            
            // Bracket pair colors
            'editorBracketMatch.background': '#0D3A58',
            'editorBracketMatch.border': '#888888'
        }
    };
} 