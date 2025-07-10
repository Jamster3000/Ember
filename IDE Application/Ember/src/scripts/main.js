import { browser } from '$app/environment';

// Initialize global variables and functions immediately
let openFiles = new Map();
let currentFile = null;
let fileCounter = 0;
let tauriInvoke = null;

// Performance optimization variables
let isProcessingLargeOperation = false;
let pendingUpdate = null;

// Initialize Tauri API first
async function initializeTauri() {
    console.log('Initializing Tauri...');
    
    // Try to import Tauri API (modern approach)
    try {
        const { invoke } = await import('@tauri-apps/api/core');
        console.log('Tauri API imported successfully');
        tauriInvoke = invoke;
        return true;
    } catch (error) {
        console.log('Failed to import Tauri API:', error);
    }
    
    // Try modern Tauri 2.0 API
    if (typeof window !== 'undefined' && window.__TAURI_TAURI__) {
        console.log('Tauri 2.0 API found');
        tauriInvoke = window.__TAURI_TAURI__.invoke;
        return true;
    }
    
    // Fallback to legacy API
    if (typeof window !== 'undefined' && window.__TAURI__) {
        console.log('Tauri legacy API found');
        tauriInvoke = window.__TAURI__.tauri.invoke;
        return true;
    }
    
    // Wait for API to be available
    for (let i = 0; i < 50; i++) {
        if (window.__TAURI_TAURI__) {
            console.log('Tauri 2.0 API found after', i, 'attempts');
            tauriInvoke = window.__TAURI_TAURI__.invoke;
            return true;
        }
        if (window.__TAURI__) {
            console.log('Tauri legacy API found after', i, 'attempts');
            tauriInvoke = window.__TAURI__.tauri.invoke;
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    console.log('Tauri API not available');
    return false;
}

// Initialize functions that work without Tauri
function initializeFunctions() {
    console.log('Initializing functions...');

    // Menu functionality
    document.addEventListener('click', function(e) {
        const menuItem = e.target.closest('.menu-item');
        if (menuItem) {
            const dropdown = menuItem.querySelector('.dropdown');
            if (dropdown) {
                const isOpen = dropdown.classList.contains('show');
                
                // Close all dropdowns
                document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
                document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
                
                // Toggle current dropdown
                if (!isOpen) {
                    dropdown.classList.add('show');
                    menuItem.classList.add('active');
                }
            }
        } else if (!e.target.closest('.dropdown')) {
            // Close all dropdowns if clicking outside
            document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('show'));
            document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
        }
    });

    // Use Rust for large files, JavaScript for small ones
    async function updateLineNumbers() {
        const editor = document.getElementById('editor');
        const lineNumbers = document.getElementById('lineNumbers');
        if (!editor || !lineNumbers) return;
        
        const text = editor.value;
        const lineCount = text.split('\n').length;
        
        // Use Rust for files with 1000+ lines
        if (tauriInvoke && lineCount > 1000) {
            try {
                const numbers = await tauriInvoke('get_line_numbers', { line_count: lineCount });
                lineNumbers.textContent = numbers.join('\n');
            } catch (error) {
                console.error('Rust line numbers failed, using fallback:', error);
                fallbackUpdateLineNumbers();
            }
        } else {
            fallbackUpdateLineNumbers();
        }
        
        // Sync scroll
        lineNumbers.scrollTop = editor.scrollTop;
    }

    function fallbackUpdateLineNumbers() {
        const editor = document.getElementById('editor');
        const lineNumbers = document.getElementById('lineNumbers');
        if (!editor || !lineNumbers) return;
        
        const lineCount = editor.value.split('\n').length;
        const lineNumbersText = Array.from({length: lineCount}, (_, i) => (i + 1).toString().padStart(3, ' ')).join('\n');
        lineNumbers.textContent = lineNumbersText;
    }

    // Use Rust for large files
    async function updateStatusBar() {
        const editor = document.getElementById('editor');
        const statusPosition = document.getElementById('statusPosition');
        if (!editor || !statusPosition) return;
        
        const text = editor.value;
        const cursorPos = editor.selectionStart;
        
        // Use Rust for files with 5000+ characters
        if (tauriInvoke && text.length > 5000) {
            try {
                const [line, column] = await tauriInvoke('calculate_cursor_position', { 
                    text: text, 
                    cursor_pos: cursorPos 
                });
                statusPosition.textContent = `Line ${line}, Column ${column}`;
            } catch (error) {
                console.error('Rust cursor calculation failed, using fallback:', error);
                fallbackUpdateStatusBar();
            }
        } else {
            fallbackUpdateStatusBar();
        }
    }

    function fallbackUpdateStatusBar() {
        const editor = document.getElementById('editor');
        const statusPosition = document.getElementById('statusPosition');
        if (!editor || !statusPosition) return;
        
        const lines = editor.value.split('\n');
        const currentLine = editor.value.substr(0, editor.selectionStart).split('\n').length;
        const currentColumn = editor.selectionStart - editor.value.lastIndexOf('\n', editor.selectionStart - 1);
        
        statusPosition.textContent = `Line ${currentLine}, Column ${currentColumn}`;
    }

    // Smart update scheduler
    function scheduleUpdate() {
        if (isProcessingLargeOperation) return;
        
        if (pendingUpdate) {
            clearTimeout(pendingUpdate);
        }
        
        pendingUpdate = setTimeout(async () => {
            await updateLineNumbers();
            await updateStatusBar();
            pendingUpdate = null;
        }, 16); // 60fps update rate
    }

    // Immediate update for small operations
    function immediateUpdate() {
        if (isProcessingLargeOperation) return;
        
        const editor = document.getElementById('editor');
        if (!editor) return;
        
        // For small files, update immediately
        if (editor.value.length < 5000) {
            updateLineNumbers();
            updateStatusBar();
        } else {
            // For larger files, schedule update
            scheduleUpdate();
        }
    }

    function getFileIcon(fileName) {
        const ext = fileName.split('.').pop().toLowerCase();
        switch(ext) {
            case 'emb': return 'EB';
            case 'js': return 'JS';
            case 'html': return 'HT';
            case 'css': return 'CS';
            case 'json': return 'JS';
            case 'md': return 'MD';
            case 'txt': return 'TX';
            default: return 'FI';
        }
    }

    function getFileStatus(fileName) {
        const file = openFiles.get(fileName);
        if (!file) return '';
        if (!file.saved) return '●';
        return '';
    }

    function newFile() {
        console.log('newFile called');
        
        const newFileName = `untitled${++fileCounter}.emb`;
        
        openFiles.set(newFileName, {
            content: '',
            saved: false,
            path: null
        });
        
        addFileToExplorer(newFileName);
        openTab(newFileName, newFileName);
        hideWelcomeScreen();
    }

    function hideWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
        }
    }

    function showWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        if (welcomeScreen) {
            welcomeScreen.style.display = 'flex';
        }
    }

    async function openFile() {
        console.log('openFile called, tauriInvoke:', !!tauriInvoke);
        
        if (!tauriInvoke) {
            console.log('Tauri not available, attempting to initialize...');
            const tauriAvailable = await initializeTauri();
            if (!tauriAvailable) {
                addToOutput('File operations require Tauri API (not available in browser)');
                return;
            }
        }
        
        try {
            const result = await tauriInvoke('open_file_dialog');
            console.log('Open file dialog result:', result);
            
            if (result) {
                const fileName = result.split('/').pop();
                const content = await tauriInvoke('read_file', { path: result });
                
                openFiles.set(fileName, {
                    content: content,
                    saved: true,
                    path: result
                });
                
                addFileToExplorer(fileName);
                openTab(fileName, fileName);
                hideWelcomeScreen();
            }
        } catch (error) {
            console.error('Error opening file:', error);
            addToOutput(`Error opening file: ${error}`);
        }
    }

    async function saveFile() {
        console.log('saveFile called, currentFile:', currentFile);
        console.log('tauriInvoke available:', !!tauriInvoke);
        
        if (!currentFile) {
            console.log('No current file');
            return;
        }
        
        const file = openFiles.get(currentFile);
        console.log('File object:', file);
        
        if (!file) {
            console.log('File not found in openFiles');
            return;
        }
        
        if (!tauriInvoke) {
            console.log('Tauri not available, attempting to initialize...');
            const tauriAvailable = await initializeTauri();
            if (!tauriAvailable) {
                addToOutput('File operations require Tauri API (not available in browser)');
                return;
            }
        }
        
        console.log('Tauri available, file.path:', file.path);
        
        try {
            // If file has a path, save directly. If not, open save dialog
            if (file.path) {
                console.log('Saving to existing path:', file.path);
                await tauriInvoke('write_file', { path: file.path, content: file.content });
                file.saved = true;
                updateTabTitle(currentFile);
                updateFileExplorerItem(currentFile);
                addToOutput(`File saved: ${currentFile}`);
            } else {
                console.log('New file, opening save dialog...');
                let result = await tauriInvoke('save_file_dialog');
                console.log('Save dialog result:', result);
                
                if (result) {
                    // Ensure .emb extension (JavaScript fallback)
                    if (!result.endsWith('.emb') && !result.includes('.')) {
                        result += '.emb';
                    }
                    
                    console.log('Writing file to:', result);
                    await tauriInvoke('write_file', { path: result, content: file.content });
                    file.path = result;
                    file.saved = true;
                    
                    // Update the file name in the tab and explorer
                    const newFileName = result.split('/').pop();
                    console.log('New file name:', newFileName);
                    
                    // Update openFiles map
                    openFiles.delete(currentFile);
                    openFiles.set(newFileName, file);
                    
                    // Update current file reference
                    const oldFileName = currentFile;
                    currentFile = newFileName;
                    
                    // Update tab
                    const tab = document.querySelector(`[data-file="${oldFileName}"]`);
                    if (tab) {
                        tab.setAttribute('data-file', newFileName);
                        const span = tab.querySelector('span:nth-child(2)');
                        if (span) {
                            span.textContent = newFileName;
                        }
                        const icon = tab.querySelector('.tab-icon');
                        if (icon) {
                            icon.textContent = getFileIcon(newFileName);
                        }
                    }
                    
                    // Update file explorer
                    const fileItem = document.querySelector(`[data-file-item="${oldFileName}"]`);
                    if (fileItem) {
                        fileItem.setAttribute('data-file-item', newFileName);
                        const nameSpan = fileItem.querySelector('.file-name');
                        if (nameSpan) {
                            nameSpan.textContent = newFileName;
                        }
                        const iconSpan = fileItem.querySelector('.file-icon');
                        if (iconSpan) {
                            iconSpan.textContent = getFileIcon(newFileName);
                        }
                        const statusSpan = fileItem.querySelector('.file-status');
                        if (statusSpan) {
                            statusSpan.textContent = '';
                        }
                        fileItem.classList.remove('unsaved');
                    }
                    
                    addToOutput(`File saved: ${newFileName}`);
                } else {
                    console.log('Save dialog cancelled');
                    addToOutput('Save cancelled');
                }
            }
        } catch (error) {
            console.error('Error saving file:', error);
            addToOutput(`Error saving file: ${error}`);
        }
    }

    async function saveAsFile() {
        if (!currentFile) return;
        
        const file = openFiles.get(currentFile);
        if (!file) return;
        
        if (!tauriInvoke) {
            console.log('Tauri not available, attempting to initialize...');
            const tauriAvailable = await initializeTauri();
            if (!tauriAvailable) {
                addToOutput('File operations require Tauri API (not available in browser)');
                return;
            }
        }
        
        try {
            // Always open save dialog for "Save As"
            const result = await tauriInvoke('save_file_dialog');
            if (result) {
                await tauriInvoke('write_file', { path: result, content: file.content });
                
                // For "Save As", we create a new file entry
                const newFileName = result.split('/').pop();
                
                // Create new file entry
                openFiles.set(newFileName, {
                    content: file.content,
                    saved: true,
                    path: result
                });
                
                // Add to explorer and open in new tab
                addFileToExplorer(newFileName);
                openTab(newFileName, newFileName);
                
                addToOutput(`File saved as: ${newFileName}`);
            } else {
                addToOutput('Save As cancelled');
            }
        } catch (error) {
            console.error('Error saving file as:', error);
            addToOutput(`Error saving file: ${error}`);
        }
    }

    async function runCode() {
        console.log('runCode called');
        
        if (!currentFile) {
            addToOutput('No file open to run');
            return;
        }
        
        const file = openFiles.get(currentFile);
        if (!file) {
            addToOutput('No file content to run');
            return;
        }
        
        if (!tauriInvoke) {
            const tauriAvailable = await initializeTauri();
            if (!tauriAvailable) {
                addToOutput('Cannot run code - Tauri API not available');
                return;
            }
        }
        
        try {
            // Show output panel
            showOutput();
            
            // Clear previous output
            clearOutput();
            
            // Add running indicator
            addToOutput('Running Emberon code...\n');
            
            // Send code to Rust backend for execution
            const result = await tauriInvoke('run_emberon_code', { 
                code: file.content,
                filename: currentFile 
            });
            
            // Display results
            addToOutput('=== LEXER OUTPUT ===');
            addToOutput(result.lexer_output || 'No lexer output');
            addToOutput('\n=== PARSER OUTPUT ===');
            addToOutput(result.parser_output || 'No parser output');
            addToOutput('\n=== EXECUTION OUTPUT ===');
            addToOutput(result.execution_output || 'No execution output');
            
            if (result.error) {
                addToOutput('\n=== ERROR ===');
                addToOutput(result.error);
            }
            
        } catch (error) {
            console.error('Error running code:', error);
            addToOutput(`Error running code: ${error}`);
        }
    }

    function openTab(fileName, displayName) {
        currentFile = fileName;
        console.log('Opening tab, currentFile set to:', currentFile);
        
        // Update tabs
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        
        let tab = document.querySelector(`[data-file="${fileName}"]`);
        if (!tab) {
            tab = createTab(fileName, displayName);
        }
        
        tab.classList.add('active');
        
        // Create or update editor
        createEditor(fileName);
        
        // Update file explorer
        updateFileExplorerSelection(fileName);
    }

    function createEditor(fileName) {
        const container = document.getElementById('editorContainer');
        
        // Remove existing editor
        const existingEditor = container.querySelector('.editor-with-numbers');
        if (existingEditor) {
            existingEditor.remove();
        }
        
        // Create new editor
        const editorWrapper = document.createElement('div');
        editorWrapper.className = 'editor-with-numbers';
        editorWrapper.innerHTML = `
            <div class="line-numbers" id="lineNumbers">1</div>
            <div class="editor-scroll">
                <textarea class="editor" id="editor" placeholder="Start coding in Emberonon..." wrap="off"></textarea>
            </div>
        `;
        
        container.appendChild(editorWrapper);
        
        const editor = document.getElementById('editor');
        const lineNumbers = document.getElementById('lineNumbers');
        const file = openFiles.get(fileName);
        
        if (file) {
            editor.value = file.content;
            immediateUpdate();
        }
        
        // Optimized event listeners
        editor.addEventListener('input', function() {
            // Update file content immediately (this is always fast)
            if (openFiles.has(currentFile)) {
                openFiles.get(currentFile).content = editor.value;
                openFiles.get(currentFile).saved = false;
                updateTabTitle(currentFile);
                updateFileExplorerItem(currentFile);
            }
            
            // Smart UI updates
            immediateUpdate();
        });
        
        // Special handling for large pastes
        editor.addEventListener('paste', async function(e) {
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            
            // For very large pastes, use Rust processing
            if (pastedText.length > 10000) {
                isProcessingLargeOperation = true;
                const statusPosition = document.getElementById('statusPosition');
                
                if (statusPosition) {
                    statusPosition.textContent = 'Processing large paste...';
                }
                
                // Let the paste complete first
                setTimeout(async () => {
                    try {
                        if (tauriInvoke) {
                            // Process with Rust
                            const processedText = await tauriInvoke('process_large_text', { text: editor.value });
                            
                            // Update line numbers with Rust
                            const numbers = await tauriInvoke('get_line_numbers', { line_count: processedText.line_count });
                            lineNumbers.textContent = numbers.join('\n');
                            
                            // Update status
                            const [line, column] = await tauriInvoke('calculate_cursor_position', { 
                                text: editor.value, 
                                cursor_pos: editor.selectionStart 
                            });
                            statusPosition.textContent = `Line ${line}, Column ${column} (${processedText.line_count} lines, ${processedText.char_count} chars)`;
                        } else {
                            // Fallback to JavaScript
                            fallbackUpdateLineNumbers();
                            fallbackUpdateStatusBar();
                        }
                    } catch (error) {
                        console.error('Error processing large paste:', error);
                        // Fallback to JavaScript
                        fallbackUpdateLineNumbers();
                        fallbackUpdateStatusBar();
                    } finally {
                        isProcessingLargeOperation = false;
                    }
                }, 50); // Small delay to let paste complete
            } else {
                // Small pastes, update normally
                setTimeout(immediateUpdate, 16);
            }
        });
        
        // Sync line numbers scroll with editor
        editor.addEventListener('scroll', function() {
            if (!isProcessingLargeOperation) {
                lineNumbers.scrollTop = editor.scrollTop;
            }
        });
        
        editor.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
                
                // Update content
                if (openFiles.has(currentFile)) {
                    openFiles.get(currentFile).content = this.value;
                    openFiles.get(currentFile).saved = false;
                    updateTabTitle(currentFile);
                    updateFileExplorerItem(currentFile);
                }
                
                immediateUpdate();
            }
        });
        
        editor.addEventListener('click', immediateUpdate);
        editor.addEventListener('keyup', immediateUpdate);
        
        editor.focus();
    }

    function createTab(fileName, displayName) {
        const tab = document.createElement('div');
        tab.className = 'tab';
        tab.setAttribute('data-file', fileName);
        tab.innerHTML = `
            <span class="tab-icon">${getFileIcon(fileName)}</span>
            <span>${displayName}</span>
            <button class="tab-close" onclick="closeTab(event, '${fileName}')">×</button>
        `;
        tab.addEventListener('click', (e) => {
            if (!e.target.classList.contains('tab-close')) {
                openTab(fileName, displayName);
            }
        });
        
        document.getElementById('tabs').appendChild(tab);
        return tab;
    }

    function closeTab(event, fileName) {
        event.stopPropagation();
        
        const tab = document.querySelector(`[data-file="${fileName}"]`);
        if (tab) {
            tab.remove();
        }
        
        // Remove from explorer
        const fileItem = document.querySelector(`[data-file-item="${fileName}"]`);
        if (fileItem) {
            fileItem.remove();
        }
        
        openFiles.delete(fileName);
        
        // Handle current file change
        if (currentFile === fileName) {
            const remainingTabs = document.querySelectorAll('.tab');
            if (remainingTabs.length > 0) {
                const newFileName = remainingTabs[0].getAttribute('data-file');
                openTab(newFileName, newFileName);
            } else {
                currentFile = null;
                const container = document.getElementById('editorContainer');
                container.innerHTML = `
                    <div class="welcome-screen" id="welcomeScreen">
                        <div class="welcome-Emberon">○</div>
                        <div class="welcome-title">Welcome to Emberon IDE</div>
                        <div class="welcome-subtitle">A powerful IDE for the Emberon programming language</div>
                        <div class="welcome-actions">
                            <div class="welcome-action" onclick="newFile()">
                                <div class="icon">📄</div>
                                <div class="title">New File</div>
                                <div class="subtitle">Create a new .emb file</div>
                            </div>
                            <div class="welcome-action" onclick="openFile()">
                                <div class="icon">📂</div>
                                <div class="title">Open File</div>
                                <div class="subtitle">Open an existing file</div>
                            </div>
                        </div>
                    </div>
                `;
                updateFileExplorer();
            }
        }
    }

    function updateTabTitle(fileName) {
        const file = openFiles.get(fileName);
        const tab = document.querySelector(`[data-file="${fileName}"]`);
        if (tab && file) {
            const span = tab.querySelector('span:nth-child(2)');
            if (span) {
                span.textContent = file.saved ? fileName : fileName + ' ●';
            }
        }
    }

    function addFileToExplorer(fileName) {
        const fileExplorer = document.getElementById('fileExplorer');
        if (!fileExplorer) return;
        
        // Remove empty state
        const emptyState = fileExplorer.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.setAttribute('data-file-item', fileName);
        fileItem.innerHTML = `
            <span class="file-icon">${getFileIcon(fileName)}</span>
            <span class="file-name">${fileName}</span>
            <span class="file-status">${getFileStatus(fileName)}</span>
        `;
        fileItem.addEventListener('click', () => openTab(fileName, fileName));
        
        fileExplorer.appendChild(fileItem);
    }

    function updateFileExplorerItem(fileName) {
        const fileItem = document.querySelector(`[data-file-item="${fileName}"]`);
        if (fileItem) {
            const statusSpan = fileItem.querySelector('.file-status');
            const file = openFiles.get(fileName);
            
            if (statusSpan && file) {
                statusSpan.textContent = file.saved ? '' : '●';
                if (file.saved) {
                    fileItem.classList.remove('unsaved');
                } else {
                    fileItem.classList.add('unsaved');
                }
            }
        }
    }

    function updateFileExplorerSelection(fileName) {
        document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
        const fileItem = document.querySelector(`[data-file-item="${fileName}"]`);
        if (fileItem) {
            fileItem.classList.add('active');
        }
    }

    function updateFileExplorer() {
        const fileExplorer = document.getElementById('fileExplorer');
        if (!fileExplorer) return;
        
        if (openFiles.size === 0) {
            fileExplorer.innerHTML = `
                <div class="empty-state">
                    <div class="Emberon-icon">○</div>
                    <div>No files open</div>
                    <div style="font-size: 12px; margin-top: 8px;">Create a new file to get started</div>
                </div>
            `;
        }
    }

    function toggleOutput() {
        const outputPanel = document.getElementById('outputPanel');
        if (outputPanel) {
            outputPanel.classList.toggle('hidden');
        }
    }

    function showOutput() {
        const outputPanel = document.getElementById('outputPanel');
        if (outputPanel) {
            outputPanel.classList.remove('hidden');
        }
    }

    function addToOutput(message) {
        const outputContent = document.getElementById('outputContent');
        if (!outputContent) return;
        const timestamp = new Date().toLocaleTimeString();
        outputContent.textContent += `[${timestamp}] ${message}\n`;
        outputContent.scrollTop = outputContent.scrollHeight;
    }

    function clearOutput() {
        const outputContent = document.getElementById('outputContent');
        if (outputContent) {
            outputContent.textContent = '';
        }
    }

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('hidden');
        }
    }

    function closeCurrentFile() {
        if (currentFile) {
            const tab = document.querySelector(`[data-file="${currentFile}"]`);
            if (tab) {
                const closeButton = tab.querySelector('.tab-close');
                if (closeButton) {
                    closeButton.click();
                }
            }
        }
    }

    // Make functions global
    window.newFile = newFile;
    window.openFile = openFile;
    window.saveFile = saveFile;
    window.saveAsFile = saveAsFile;
    window.runCode = runCode;
    window.toggleOutput = toggleOutput;
    window.toggleSidebar = toggleSidebar;
    window.closeCurrentFile = closeCurrentFile;
    window.clearOutput = clearOutput;
    window.closeTab = closeTab;
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'n':
                    e.preventDefault();
                    newFile();
                    break;
                case 'o':
                    e.preventDefault();
                    openFile();
                    break;
                case 's':
                    e.preventDefault();
                    if (e.shiftKey) {
                        saveAsFile();
                    } else {
                        saveFile();
                    }
                    break;
                case 'r':
                    e.preventDefault();
                    runCode();
                    break;
                case 'w':
                    e.preventDefault();
                    closeCurrentFile();
                    break;
                case 'b':
                    e.preventDefault();
                    toggleSidebar();
                    break;
                case '`':
                    e.preventDefault();
                    toggleOutput();
                    break;
            }
        }
    });

    // Add F5 keyboard shortcut
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F5') {
            e.preventDefault();
            runCode();
        }
    });

    console.log('Functions initialized');
}

// Initialize functions immediately
initializeFunctions();

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Content Loaded - initializing Tauri...');
    
    const tauriAvailable = await initializeTauri();
    
    const statusPosition = document.getElementById('statusPosition');
    if (statusPosition) {
        if (tauriAvailable) {
            statusPosition.textContent = 'Tauri Ready';
            console.log('Tauri initialized successfully');
        } else {
            statusPosition.textContent = 'Browser Mode';
            console.log('Running in browser mode');
        }
    }
});