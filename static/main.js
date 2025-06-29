const chatHistory = document.getElementById('chat-history');
const messageInput = document.getElementById('message-input');
const chatForm = document.getElementById('chat-form');
const sendButton = document.getElementById('send-button');
const sendIcon = document.getElementById('send-icon'); // Changed from sendText
const sendSpinner = document.getElementById('send-spinner');
const schemaDisplay = document.getElementById('schema-display');
const schemaContent = document.getElementById('schema-content');
const schemaToggleBtn = document.getElementById('schema-toggle-btn');
const refreshSchemaBtn = document.getElementById('refresh-schema-btn');
const configToggleBtn = document.getElementById('config-toggle-btn');
const configPopup = document.getElementById('config-popup');
const closeConfigBtn = document.getElementById('close-config-btn');
const configForm = document.getElementById('config-form');
const newChatBtn = document.getElementById('new-chat-btn');

// --- ADDED: Reference to new main content and chat area elements ---
const mainContentWrapper = document.getElementById('main-content-wrapper');
const chatArea = document.getElementById('chat-area');
// --- END ADDED ---

// --- ADDED: Dark Mode Elements ---
const darkModeToggleBtn = document.getElementById('dark-mode-toggle-btn');
const darkModeIconContainer = document.getElementById('dark-mode-icon-container');
// --- END ADDED ---

// --- Autocomplete /run command elements ---
const inputWrapper = document.getElementById('input-wrapper');
const runCommandTag = document.getElementById('run-command-tag');
const removeRunTagBtn = document.getElementById('remove-run-tag-btn');
const slashCommandPopup = document.getElementById('slash-command-popup');
let isRunCommandActive = false;
const originalPlaceholder = "Type your message or /run command...";
const runCommandPlaceholder = "Enter SQL query (e.g., SELECT * FROM users)";
let isInitialState = true; // ADDED: Flag for the initial view

// --- Helper Functions ---

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderMarkdown(text) {
    // Convert Markdown to HTML using marked.js
    const dirtyHtml = marked.parse(text);
    // Sanitize the HTML using DOMPurify to prevent XSS attacks
    const cleanHtml = DOMPurify.sanitize(dirtyHtml);
    return cleanHtml;
}

// ADDED: Helper function to create spinner SVG
function createSpinnerSvg(extraClasses = "w-5 h-5 text-white") {
    return `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="${extraClasses}"><g stroke="currentColor"><circle cx="12" cy="12" r="9.5" fill="none" stroke-linecap="round" stroke-width="3"><animate attributeName="stroke-dasharray" calcMode="spline" dur="1.5s" keySplines="0.42,0,0.58,1;0.42,0,0.58,1;0.42,0,0.58,1" keyTimes="0;0.475;0.95;1" repeatCount="indefinite" values="0 150;42 150;42 150;42 150"/><animate attributeName="stroke-dashoffset" calcMode="spline" dur="1.5s" keySplines="0.42,0,0.58,1;0.42,0,0.58,1;0.42,0,0.58,1" keyTimes="0;0.475;0.95;1" repeatCount="indefinite" values="0;-16;-59;-59"/></circle><animateTransform attributeName="transform" dur="2s" repeatCount="indefinite" type="rotate" values="0 12 12;360 12 12"/></g></svg>
        <span class="sr-only">Loading...</span>
    `;
}

function addMessageToChat(sender, messageHtml, messageType = 'info') {
    const messageDiv = document.createElement('div');
    let alignment;

    if (sender === 'user') {
        // User message style is now handled by pure CSS for easier dark mode adjustments
        alignment = 'ml-auto';
    } else { // Assistant messages
        // Assistant message style is now handled by pure CSS
        alignment = 'mr-auto';
    }

    messageDiv.className = `p-3 rounded-lg max-w-3xl ${alignment} prose prose-sm max-w-none`; // Use prose for markdown styling
    messageDiv.innerHTML = messageHtml; // Use innerHTML as we are injecting HTML
    
    // --- ADDED: Logic to add "Run Query" buttons to SQL code blocks ---
    if (sender === 'assistant') {
        const codeBlocks = messageDiv.querySelectorAll('pre code.language-sql');
        codeBlocks.forEach(codeBlock => {
            const preElement = codeBlock.parentElement;
            if (!preElement) return;

            const query = codeBlock.textContent.trim();

            if (query) {
                // Create a wrapper for relative positioning
                const wrapper = document.createElement('div');
                wrapper.className = 'relative'; // No longer need 'group' for hover

                const runButton = document.createElement('button');
                runButton.className = 'run-query-btn';
                runButton.innerHTML = `<i data-lucide="play" class="h-3 w-3 inline-block mr-1 -ml-1"></i> Run Query`;
                
                runButton.addEventListener('mouseover', () => runButton.style.backgroundColor = 'var(--md-primary-color)');
                runButton.addEventListener('mouseout', () => runButton.style.backgroundColor = 'var(--md-accent-color)');

                runButton.addEventListener('click', () => {
                    showRunCommandTag();
                    messageInput.value = query.replace(/\n/g, ' ');
                    messageInput.focus();
                });

                // Copy button
                const copyButton = document.createElement('button');
                copyButton.className = 'copy-query-btn';
                copyButton.innerHTML = `<i data-lucide="copy" class="h-3 w-3 inline-block mr-1 -ml-1"></i> Copy`;

                copyButton.addEventListener('click', () => {
                    try {
                        navigator.clipboard.writeText(query);
                        showToast('Query copied to clipboard!', 'success', 2000);
                    } catch (err) {
                        showToast('Failed to copy query', 'error', 3000);
                    }
                });

                // Replace the original <pre> with the wrapper containing the <pre> and the button
                if(preElement.parentNode) {
                    preElement.parentNode.replaceChild(wrapper, preElement);
                }
                wrapper.appendChild(preElement);
                wrapper.appendChild(runButton);
                wrapper.appendChild(copyButton);
            }
        });
        // After adding new icons via innerHTML, we must re-run lucide.
        // MOVED: lucide.createIcons();
    }
    // --- END ADDED LOGIC ---

    chatHistory.appendChild(messageDiv);
    // Conditionally auto-scroll only if the user was already near the bottom
    if (isChatScrolledToBottom()) {
        scrollChatToBottom();
    }

    // ADDED: Call lucide.createIcons() AFTER the message is appended to the DOM
    if (sender === 'assistant') {
        lucide.createIcons();
    }
    // Highlight any new code blocks with Prism
    if (window.Prism && typeof Prism.highlightAllUnder === 'function') {
        Prism.highlightAllUnder(messageDiv);
    }
}

function createTableHtml(columns, results) {
    if (!results || results.length === 0) {
        return '<p class="text-sm text-gray-600 italic">Query returned no results.</p>';
    }
    if (!columns || columns.length === 0) {
         return '<p class="text-sm text-red-600">Error: Missing column names for results.</p>';
    }

    let tableHtml = '<div class="results-table"><table><thead><tr>';
    columns.forEach(col => {
        tableHtml += `<th>${escapeHtml(col)}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';

    results.forEach(row => {
        tableHtml += '<tr>';
        // Ensure row is an array or tuple before iterating
        if (Array.isArray(row) || row instanceof Object && typeof row[Symbol.iterator] === 'function') {
             // Check if columns length matches row length
             if (row.length !== columns.length) {
                 console.warn("Row length mismatch:", row, "Columns:", columns);
                 // Add placeholder cells or handle error appropriately
                 tableHtml += `<td colspan="${columns.length}" class="text-red-500 italic">Data format error: row length mismatch</td>`;
             } else {
                row.forEach(cell => {
                    // Handle null or undefined values gracefully
                    const cellContent = cell === null || cell === undefined ? 'NULL' : cell;
                    tableHtml += `<td>${escapeHtml(String(cellContent))}</td>`; // Convert all cells to string before escaping
                });
             }
        } else {
             // Handle cases where row might not be iterable or is a single value
             console.warn("Unexpected row format:", row);
             tableHtml += `<td colspan="${columns.length}" class="text-red-500 italic">Data format error: unexpected row type</td>`;
        }
        tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table></div>';
    if (results.length === 100) {
        tableHtml += '<p class="text-xs text-gray-500 italic mt-1">Displaying up to 100 rows. The actual result set may be larger.</p>';
    }
    return tableHtml;
}

function setLoadingState(isLoading) {
    const sendIcon = document.getElementById('send-icon');
    const sendSpinner = document.getElementById('send-spinner');
    const animationDuration = 150; // ms, matches the CSS animation time

    if (isLoading) {
        // ADDED: Don't disable input on the very first send to allow focus to be maintained during animation
        if (!isInitialState) {
            messageInput.disabled = true;
        }
        sendButton.disabled = true;
        
        sendIcon.classList.add('icon-fade-out');
        
        setTimeout(() => {
            sendIcon.classList.add('hidden');
            sendIcon.classList.remove('icon-fade-out');

            sendSpinner.classList.remove('hidden');
            sendSpinner.classList.add('icon-fade-in');
            sendSpinner.innerHTML = createSpinnerSvg();
        }, animationDuration);

    } else {
        messageInput.disabled = false;
        sendButton.disabled = false;
        
        sendSpinner.classList.add('icon-fade-out');
        
        setTimeout(() => {
            sendSpinner.classList.add('hidden');
            sendSpinner.classList.remove('icon-fade-out');
            sendSpinner.innerHTML = '';

            sendIcon.classList.remove('hidden');
            sendIcon.classList.remove('icon-fade-out'); // Ensure fade-out is not lingering
            sendIcon.classList.add('icon-fade-in');
            
            // Clean up the fade-in class after it has run
            setTimeout(() => {
                sendIcon.classList.remove('icon-fade-in');
            }, animationDuration);

        }, animationDuration);

        if (window.innerWidth > 768) { // Only auto-focus on larger screens
            messageInput.focus({ preventScroll: true });
        }
    }
}

// --- API Interaction ---

// MODIFY fetchSchema to handle nested structure
async function fetchSchema(showLoading = true) {
    // NEW: Record start time for minimum loader display
    let startTime = 0;
    const minLoadingTime = 500; // Minimum loader display time in ms

    if (showLoading) {
         schemaContent.innerHTML = '<div class="flex items-center justify-center p-4"><span class="mr-2">Loading schema...</span>' + createSpinnerSvg("w-4 h-4 text-blue-600") + '</div>';
         startTime = Date.now(); // Record time after loader is shown
    }

    // NEW: Helper function to actually update content and apply animations
    const performVisualUpdate = (htmlToSet, animate) => {
        schemaContent.innerHTML = htmlToSet;
        lucide.createIcons(); // Create icons first

        const items = schemaContent.querySelectorAll('.schema-item');
        const initialDelay = 0; // Small base delay (ms) before the first item starts
        const staggerAmount = 5;  // Delay between each subsequent item (ms)

        if (animate) {
            // Use requestAnimationFrame to ensure initial styles are painted before animation starts
            requestAnimationFrame(() => {
                items.forEach((item, index) => {
                    setTimeout(() => {
                        item.classList.add('visible-item');
                    }, initialDelay + (index * staggerAmount)); 
                });
            });
        } else {
            // If not animating, make them visible immediately (can also be in RAF for consistency)
            requestAnimationFrame(() => {
                items.forEach(item => {
                    item.classList.add('visible-item');
                });
            });
        }
    };

    // REVISED: Helper function to update content after minimum delay
    const updateContentWithDelay = (htmlToSet) => {
        if (showLoading) {
            const elapsedTime = Date.now() - startTime;
            const delayForLoader = Math.max(0, minLoadingTime - elapsedTime); // Ensure delay is not negative
            setTimeout(() => {
                performVisualUpdate(htmlToSet, true); // Animate after loader
            }, delayForLoader);
        } else {
            // If not showing loading (e.g., initial silent load), update immediately without animation for entry
            performVisualUpdate(htmlToSet, false);
        }
    };

     try {
         const response = await fetch('/schema');
         if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try { // Try to get more specific error from backend
                const errData = await response.json();
                // Adjust error path based on potential backend response structure
                errorMsg = errData.detail || (errData.error && errData.error.schema && Array.isArray(errData.error.schema) ? errData.error.schema.join(', ') : errorMsg);
            } catch(e) { /* ignore if body isn't json */ }
            throw new Error(errorMsg);
         }
         const data = await response.json();
         const schema = data.schema; // Expected format: { dbName: { tableName: [columns] } } or { error: { schema: ["message"] } }

         let finalSchemaHtml = ''; // Variable to store the fully constructed HTML

         // Check for the top-level error structure first
         if (schema && typeof schema === 'object' && schema.error && schema.error.schema && Array.isArray(schema.error.schema)) {
            finalSchemaHtml = `<div class="p-4"><p class="text-red-600">Error fetching schema: ${escapeHtml(schema.error.schema.join(', '))}</p></div>`;
         } else if (schema && typeof schema === 'object' && Object.keys(schema).length > 0) {
             let builtSchemaContent = ''; // Temporary string to build schema details
             // Iterate through Databases
             for (const dbName in schema) {
                 if (schema.hasOwnProperty(dbName)) {
                     // ADDED: group class, toggle-icon, and made it initially not expanded
                     builtSchemaContent += `<div class="schema-item schema-database-item group"><i data-lucide="database"></i>${escapeHtml(dbName)}<i data-lucide="chevron-down" class="toggle-icon h-4 w-4 text-gray-400 group-hover:text-gray-600"></i></div>`;
                     // ADDED: Wrapper for all tables and columns under this DB, hidden by default
                     builtSchemaContent += '<div class="database-content-wrapper">';
                      const tables = schema[dbName]; // This could be { tableName: [cols] } or { error: ["msg"] }

                      // Check if the value for the dbName is an error object
                      if (typeof tables === 'object' && tables !== null && tables.error && Array.isArray(tables.error)) {
                          builtSchemaContent += `<div class="schema-item schema-table-item italic text-red-500"><i data-lucide="alert-triangle"></i>Error: ${escapeHtml(tables.error.join(', '))}</div>`;
                      }
                      // Check if it's a valid tables object (and not the error object)
                      else if (typeof tables === 'object' && tables !== null && !tables.error) {
                          if (Object.keys(tables).length > 0) {
                              // Iterate through Tables within the Database
                              for (const tableName in tables) {
                                  if (tables.hasOwnProperty(tableName) && Array.isArray(tables[tableName])) {
                                      // ADDED: group class for hover states on icon, and toggle-icon span
                                      builtSchemaContent += `<div class="schema-item schema-table-item group"><i data-lucide="table-2"></i><strong>${escapeHtml(tableName)}</strong><i data-lucide="chevron-down" class="toggle-icon h-4 w-4 text-gray-400 group-hover:text-gray-600"></i></div>`;
                                       if (tables[tableName].length > 0) {
                                           // ADDED: hidden class to collapse columns by default
                                           builtSchemaContent += '<div class="schema-columns-list">';
                                            tables[tableName].forEach(column => {
                                                builtSchemaContent += `<div class="schema-column">${escapeHtml(column)}</div>`;
                                            });
                                           builtSchemaContent += '</div>';
                                       } else {
                                           builtSchemaContent += '<div class="schema-columns-list italic">No columns found.</div>';
                                       }
                                  }
                              }
                          } else {
                              builtSchemaContent += '<div class="schema-item schema-table-item italic"><i data-lucide="info"></i>No tables found.</div>';
                          }
                      } else {
                          // Handle unexpected format for the database entry
                          builtSchemaContent += '<div class="schema-item schema-table-item italic"><i data-lucide="info"></i>No table data.</div>';
                      }
                  builtSchemaContent += '</div>'; // Close database-content-wrapper
                  }
              }
              finalSchemaHtml = builtSchemaContent || '<div class="p-4 text-gray-500"><i data-lucide="search-x" class="inline-block mr-2"></i>No databases or tables found.</div>';
          } else {
              // This case handles empty schema object {} or other non-error, non-object types
              finalSchemaHtml = '<div class="p-4 text-gray-500"><i data-lucide="database-zap" class="inline-block mr-2"></i>No schema found or unable to fetch.</div>';
          }
          updateContentWithDelay(finalSchemaHtml); // Use the helper to update content
      } catch (error) {
          console.error('Error fetching schema:', error);
          // Ensure error.message is escaped
          const errorHtml = `<div class="p-4 text-red-600"><i data-lucide="alert-circle" class="inline-block mr-2"></i>Failed to load schema. ${escapeHtml(error.message)}</div>`;
          updateContentWithDelay(errorHtml); // Use the helper to update content for errors
      }
}

async function sendMessage(message) {
    addMessageToChat('user', `<p>${escapeHtml(message)}</p>`); // Display user message immediately
    messageInput.value = ''; // Clear input
    setLoadingState(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });

        if (!response.ok) {
             // Try to get error details from response body
             let errorDetail = `HTTP error! status: ${response.status}`;
             try {
                 const errorData = await response.json();
                 errorDetail = errorData.detail || errorData.content || errorDetail;
             } catch (e) { /* Ignore if body isn't JSON */ }
            throw new Error(errorDetail);
        }

        const data = await response.json();
        let assistantMessageHtml = '';

        if (data.type === 'result') {
            assistantMessageHtml += `<p class="font-semibold">Generated SQL:</p><pre><code class="language-sql">${escapeHtml(data.query || '')}</code></pre>`;
            assistantMessageHtml += createTableHtml(data.columns, data.results);
            if (data.insights) {
                // Render insights as Markdown
                assistantMessageHtml += renderMarkdown(data.insights);
            }
        } else if (data.type === 'info') {
             // Render info potentially containing markdown (like code blocks)
             assistantMessageHtml += renderMarkdown(data.content);
        } else if (data.type === 'error') {
             // Render error potentially containing markdown (like code blocks)
             assistantMessageHtml += renderMarkdown(data.content);
             if (data.ai_explanation) {
                assistantMessageHtml += renderMarkdown(data.ai_explanation); // Render AI explanation as Markdown
             }
        } else if (data.type === 'confirm_execution') {
            // This case is now handled by addConfirmationMessageToChat
            // It will set loading state to false to re-enable input while confirm buttons are visible.
            addConfirmationMessageToChat(data.message, data.query);
            return; // Return early as we don't want to call addMessageToChat or setLoadingState(false) again here
        } else {
            assistantMessageHtml = `<p>${escapeHtml(String(data.content || 'Received unexpected response format.'))}</p>`;
        }

        addMessageToChat('assistant', assistantMessageHtml, data.type);

    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToChat('assistant', `<p>Sorry, I encountered an error: ${escapeHtml(error.message)}</p>`, 'error');
    } finally {
        setLoadingState(false);
    }
}

// --- ADDED: Functions for handling query confirmation ---
function addConfirmationMessageToChat(messageText, queryToConfirm) {
    const messageDiv = document.createElement('div');
    // Using a distinct style for confirmation prompts
    messageDiv.className = `p-3 rounded-lg max-w-3xl mr-auto prose prose-sm max-w-none shadow`;

    let htmlContent = `<p class="font-semibold">${escapeHtml(messageText)}</p>`;
    htmlContent += `<pre class="p-2 rounded mt-2"><code class="language-sql">${escapeHtml(queryToConfirm)}</code></pre>`;
    htmlContent += `<div class="mt-3 flex space-x-2">
                        <button class="confirm-execute-btn font-semibold py-1.5 px-4 rounded text-sm shadow-sm transition-colors duration-150" data-query="${escapeHtml(queryToConfirm)}">Execute</button>
                        <button class="cancel-execute-btn font-semibold py-1.5 px-4 rounded text-sm shadow-sm transition-colors duration-150">Cancel</button>
                     </div>`;

    messageDiv.innerHTML = htmlContent;
    chatHistory.appendChild(messageDiv);
    // Restore event listeners for the Execute / Cancel buttons
    const confirmBtn = messageDiv.querySelector('.confirm-execute-btn');
    const cancelBtn = messageDiv.querySelector('.cancel-execute-btn');

    if (confirmBtn) {
        confirmBtn.addEventListener('click', async function() {
            const query = this.dataset.query;
            // Update the current message to "Executing..."
            const parentMessageBubble = this.closest('.p-3.rounded-lg');
            if (parentMessageBubble) {
                parentMessageBubble.innerHTML = `<p class="font-semibold text-blue-700">Executing query:</p><pre class="bg-blue-50 p-2 rounded mt-2 border border-blue-200"><code class="language-sql text-blue-900">${escapeHtml(query)}</code></pre><p class="mt-2 text-sm text-gray-600 italic">Please wait...</p>`;
            }
            if (isChatScrolledToBottom()) {
                scrollChatToBottom();
            }

            await executeConfirmedQuery(query); // This will add a *new* message with the result

            // Update the original confirmation bubble after execution
            if (parentMessageBubble) {
                parentMessageBubble.innerHTML = `<p class="text-sm text-gray-600 italic">The confirmed query execution has been processed. See result in the new message below.</p>`;
                parentMessageBubble.className = `p-3 rounded-lg bg-gray-50 border border-gray-200 text-gray-500 max-w-3xl mr-auto prose prose-sm max-w-none shadow-sm`;
            }

            if (isChatScrolledToBottom()) {
                scrollChatToBottom();
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            const parentMessageBubble = this.closest('.p-3.rounded-lg');
            if (parentMessageBubble) {
                parentMessageBubble.className = `p-3 rounded-lg bg-gray-100 text-gray-600 max-w-3xl mr-auto prose prose-sm max-w-none italic shadow`;
                parentMessageBubble.innerHTML = `<p>Execution cancelled by user.</p>`;
            }
            if (isChatScrolledToBottom()) {
                scrollChatToBottom();
            }
        });
    }

    // Conditionally auto-scroll only if the user was already near the bottom
    if (isChatScrolledToBottom()) {
        scrollChatToBottom();
    }
    setLoadingState(false); // Ensure main input is usable while confirmation is shown
}

async function executeConfirmedQuery(query) {
    // setLoadingState(true); // Main input is already re-enabled by addConfirmationMessageToChat, keep it that way.
                         // We want the user to be able to type a new query if they wish, while the confirmed one executes.
                         // However, we should show a specific loading indicator for this execution if possible, or rely on the message update.
    // For now, the message update to "Executing..." will serve as the primary indicator.

    try {
        const response = await fetch('/execute_confirmed_sql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        if (!response.ok) {
            let errorDetail = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.content || errorData.detail || errorDetail;
            } catch (e) { /* Ignore if body isn't JSON */ }
            throw new Error(errorDetail);
        }

        const data = await response.json();
        let resultMessageHtml = '';

        // Process response from /execute_confirmed_sql (similar to /chat)
        // The 'assistant' will now deliver the outcome of the confirmed query.
        if (data.type === 'info') {
            resultMessageHtml = renderMarkdown(data.content);
        } else if (data.type === 'error') {
            resultMessageHtml = renderMarkdown(data.content); // Error messages can also contain markdown (like code blocks)
            if (data.ai_explanation) {
                resultMessageHtml += renderMarkdown(data.ai_explanation); // Render AI explanation as Markdown
            }
        } else if (data.type === 'result') { // Should be rare for this flow but handle
            resultMessageHtml += `<p class="font-semibold">Query Executed:</p><pre><code class="language-sql">${escapeHtml(data.query || '')}</code></pre>`;
            resultMessageHtml += createTableHtml(data.columns, data.results);
            if (data.insights) {
                resultMessageHtml += renderMarkdown(data.insights);
            }
        } else {
            resultMessageHtml = `<p>${escapeHtml(String(data.content || 'Received unexpected response format.'))}</p>`;
        }
        // Add this result as a new message from the assistant
        addMessageToChat('assistant', resultMessageHtml, data.type);

    } catch (error) {
        console.error('Error executing confirmed query:', error);
        addMessageToChat('assistant', `<p>Sorry, I encountered an error during the confirmed execution: ${escapeHtml(error.message)}</p>`, 'error');
    } finally {
        // setLoadingState(false); // No need to call setLoadingState(false) here as it wasn't set to true at the start of this func.
    }
}
// --- END: Functions for handling query confirmation ---

// --- ADDED: Toast Notification Function ---
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('Toast container not found!');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`; // e.g., toast toast-success

    const content = document.createElement('div');
    content.className = 'toast-content';
    content.textContent = message;

    const closeButton = document.createElement('button');
    closeButton.className = 'toast-close';
    closeButton.innerHTML = '<i data-lucide="x" class="h-4 w-4"></i>'; // Use a centered SVG icon
    closeButton.onclick = () => {
        toast.classList.add('toast-remove');
        toast.addEventListener('animationend', () => {
            if (container.contains(toast)) { // Check if still a child before removing
                container.removeChild(toast);
            }
        });
    };

    toast.appendChild(content);
    toast.appendChild(closeButton);
    container.appendChild(toast);

    lucide.createIcons(); // Render the new icon

    // Auto-remove after duration
    setTimeout(() => {
        // Check if toast is still in DOM (user might have closed it manually)
        if (container.contains(toast) && !toast.classList.contains('toast-remove')) {
            toast.classList.add('toast-remove');
            toast.addEventListener('animationend', () => {
                 if (container.contains(toast)) { // Double check before removing
                    container.removeChild(toast);
                 }
            });
        }
    }, duration);
}
// --- END: Toast Notification Function ---

// --- Configuration Popup Functions ---

async function saveConfig(config) {
    // Set loading state
    const saveBtn = document.getElementById('config-save-btn');
    const saveText = document.getElementById('config-save-text'); 
    const saveSpinner = document.getElementById('config-save-spinner');
    
    saveBtn.disabled = true;
    saveText.classList.add('opacity-75');
    saveSpinner.classList.remove('hidden');
    saveSpinner.innerHTML = createSpinnerSvg("w-4 h-4 text-white"); // Use helper with specific classes
    
    try {
        // Send configuration to backend
        const response = await fetch('/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mysql_host: config.mysqlHost,
                mysql_user: config.mysqlUser,
                mysql_password: config.mysqlPassword,
                gemini_api_key: config.geminiApiKey
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // REMOVED: No longer saving to localStorage
        // localStorage.setItem('sqlAssistantConfig', JSON.stringify(config));
        
        if (data.status === 'success') {
            const connectionWarnings = [];
            if (data.mysql_connection !== 'success') {
                connectionWarnings.push(`MySQL connection warning: ${data.mysql_connection}`);
            }
            if (data.gemini_api !== 'success') {
                connectionWarnings.push(`Gemini API warning: ${data.gemini_api}`);
            }
            
            if (connectionWarnings.length > 0) {
                showToast(`Configuration saved with warnings:\n${connectionWarnings.join('\n')}\n\nChanges have been applied and .env file updated.`, 'warning');
            } else {
                showToast('Configuration successfully saved and applied! No restart required.', 'success');
            }
            
            // Reload schema to reflect any database connection changes
            fetchSchema(true);
            // ADDED: Re-fetch config to update the form state (e.g., placeholder for password)
            fetchAndApplyConfig(); 
        } else {
            showToast(`Configuration status: ${data.message}`, 'info');
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        showToast(`Error saving configuration: ${error.message}. Please try again.`, 'error');
        // REMOVED: No longer saving to localStorage as a fallback
        // localStorage.setItem('sqlAssistantConfig', JSON.stringify(config));
    } finally {
        // Reset button state
        saveBtn.disabled = false;
        saveText.classList.remove('opacity-75');
        saveSpinner.classList.add('hidden');
        saveSpinner.innerHTML = ""; // Clear spinner
    }
}

async function fetchAndApplyConfig() {
    try {
        const response = await fetch('/config_status');
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        const config = await response.json();
        
        document.getElementById('mysql-host').value = config.mysql_host || '';
        document.getElementById('mysql-user').value = config.mysql_user || '';
        
        const passwordInput = document.getElementById('mysql-password');
        const passwordLabel = document.querySelector('label[for="mysql-password"]');
        if (config.mysql_password_set) {
            passwordInput.value = '';
            passwordInput.placeholder = ' '; // Keep placeholder empty for label
            passwordLabel.textContent = 'MySQL Password (already set)';
        } else {
            passwordInput.value = '';
            passwordInput.placeholder = ' '; // Use a space for floating label to work
            passwordLabel.textContent = 'MySQL Password';
        }

        const geminiInput = document.getElementById('gemini-api-key');
        const geminiLabel = document.querySelector('label[for="gemini-api-key"]');
        if (config.gemini_api_key_set) {
            geminiInput.value = '';
            geminiInput.placeholder = ' '; // Keep placeholder empty for label
            geminiLabel.textContent = 'Gemini API Key (already set)';
        } else {
            geminiInput.value = '';
            geminiInput.placeholder = ' '; // Use a space for floating label to work
            geminiLabel.textContent = 'Gemini API Key';
        }

    } catch (error) {
        console.error('Error fetching configuration status:', error);
        showToast(`Could not fetch server configuration: ${error.message}`, 'error');
    }
}

// --- Autocomplete and /run Tag Functions ---
function showRunCommandTag() {
    runCommandTag.classList.remove('hidden');
    messageInput.placeholder = runCommandPlaceholder;
    isRunCommandActive = true;
    messageInput.value = '';
    hideSlashCommandPopup();
    messageInput.focus();
}

function hideRunCommandTag() {
    runCommandTag.classList.add('hidden');
    messageInput.placeholder = originalPlaceholder;
    isRunCommandActive = false;
    // DO NOT clear the input value here, allowing the query to be preserved.
    messageInput.focus();
}

function showSlashCommandPopup() {
    const inputValue = messageInput.value;
    // Only show the popup if the input *starts with* a slash,
    // but don't hide it just because there's text after it.
    if (!inputValue.startsWith('/')) {
        hideSlashCommandPopup();
        return;
    }

    // Filter commands based on what's typed after the slash.
    const commandFragment = inputValue.substring(1).toLowerCase();
    const potentialCommands = ['run'];
    const matchingCommands = potentialCommands.filter(cmd => cmd.startsWith(commandFragment));

    if (matchingCommands.length > 0) {
        slashCommandPopup.innerHTML = ''; // Clear previous suggestions
        matchingCommands.forEach(cmd => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.textContent = `/${cmd}`;
            suggestionDiv.dataset.command = `/${cmd}`;
            suggestionDiv.addEventListener('click', () => {
                showRunCommandTag();
            });
            slashCommandPopup.appendChild(suggestionDiv);
        });
        slashCommandPopup.classList.remove('hidden');
    } else {
        hideSlashCommandPopup();
    }
}

function hideSlashCommandPopup() {
    slashCommandPopup.classList.add('hidden');
    slashCommandPopup.innerHTML = '';
}

// --- Event Listeners ---

document.getElementById('terminal-btn').addEventListener('click', () => {
    // If the initial animation hasn't run, clicking the terminal button should also trigger it.
    if (isInitialState) {
        chatArea.classList.remove('initial-state');
        isInitialState = false;
    }
    showRunCommandTag();
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const queryPart = messageInput.value.trim();
    let messageToSend;

    // --- ADDED: Handle transition from initial state ---
    if (isInitialState) {
        if (!queryPart) return; // Don't submit empty on initial view
        chatArea.classList.remove('initial-state');
        isInitialState = false;
    }
    // --- END ADDED ---

    if (isRunCommandActive) {
        if (queryPart) {
            messageToSend = "/run " + queryPart;
        } else {
            showToast("Please enter an SQL query to run.", "warning", 3000);
            messageInput.focus();
            return;
        }
    } else {
        messageToSend = queryPart;
    }

    if (messageToSend) {
        sendMessage(messageToSend);
        if (isRunCommandActive) {
            hideRunCommandTag();
        }
    }
});

schemaToggleBtn.addEventListener('click', () => {
    const isOpen = schemaDisplay.classList.contains('open');
    const dbIcon = document.getElementById('schema-db-icon');
    const upIcon = document.getElementById('schema-up-icon');
    const schemaText = document.getElementById('schema-text');

    // Prevent re-triggering animations if already in progress by cleaning up
    dbIcon.classList.remove('schema-icon-animate-out', 'schema-icon-animate-in');
    upIcon.classList.remove('schema-icon-animate-out', 'schema-icon-animate-in');
    dbIcon.style.opacity = '';
    dbIcon.style.transform = '';
    upIcon.style.opacity = '';
    upIcon.style.transform = '';

    if (!isOpen) { // Schema is opening
        schemaDisplay.classList.add('open');
        // REMOVED: No longer shifting the main content
        // if (window.innerWidth > 768) {
        //     chatArea.style.marginRight = '320px'; 
        // }
        schemaText.textContent = 'Hide Schema';

        // Animate out dbIcon
        dbIcon.classList.add('schema-icon-animate-out');
        dbIcon.addEventListener('animationend', function handleDbAnimOut() {
            dbIcon.classList.add('hidden');
            dbIcon.classList.remove('schema-icon-animate-out'); // Clean up animation class

            // Animate in upIcon
            upIcon.classList.remove('hidden');
            void upIcon.offsetWidth; // Force reflow before adding new animation class
            upIcon.classList.add('schema-icon-animate-in');
            upIcon.addEventListener('animationend', function handleUpAnimIn() {
                upIcon.classList.remove('schema-icon-animate-in'); // Clean up animation class
            }, { once: true });
        }, { once: true });
        
        const currentHTML = schemaContent.innerHTML;
        const trimmedContent = currentHTML.trim();

        const isEmptyOrPlaceholder = trimmedContent.startsWith("<!--") || trimmedContent === "";
        const isLoading = currentHTML.includes('Loading schema...');
        const hasFailedOrIsEmptyBackend = currentHTML.includes('Failed to load schema') ||
                          currentHTML.includes('Error fetching schema') ||
                          currentHTML.includes('No databases or tables found, or unable to fetch schema') ||
                          currentHTML.includes('No databases or tables found.');

        const needsFetching = isEmptyOrPlaceholder || isLoading || hasFailedOrIsEmptyBackend;
        if (needsFetching) {
           fetchSchema();
        }
    } else {
        // Start slide-out animation then hide panel after it finishes
        schemaDisplay.classList.remove('open');
        schemaDisplay.classList.add('closing');
        schemaText.textContent = 'View Schema';

        // After animation ends remove the closing class so CSS display:none takes over
        setTimeout(() => {
            schemaDisplay.classList.remove('closing');
        }, 300);
        // REMOVED: No longer resetting the margin
        // chatArea.style.marginRight = '0';
        schemaText.textContent = 'View Schema';

        // Animate out upIcon
        upIcon.classList.add('schema-icon-animate-out');
        upIcon.addEventListener('animationend', function handleUpAnimOut() {
            upIcon.classList.add('hidden');
            upIcon.classList.remove('schema-icon-animate-out');

            // Animate in dbIcon
            dbIcon.classList.remove('hidden');
            void dbIcon.offsetWidth; // Force reflow
            dbIcon.classList.add('schema-icon-animate-in');
            dbIcon.addEventListener('animationend', function handleDbAnimIn() {
                dbIcon.classList.remove('schema-icon-animate-in');
            }, { once: true });
        }, { once: true });
    }
});

refreshSchemaBtn.addEventListener('click', () => {
    fetchSchema(true);
});

configToggleBtn.addEventListener('click', () => {
    const settingsIcon = document.getElementById('settings-icon');
    
    if (configPopup.classList.contains('visible')) {
        configPopup.classList.remove('visible');
        
        settingsIcon.classList.remove('settings-icon-rotate-cw');
        settingsIcon.classList.add('settings-icon-rotate-ccw');
    } else {
        configPopup.classList.add('visible');
        
        settingsIcon.classList.remove('settings-icon-rotate-ccw');
        settingsIcon.classList.add('settings-icon-rotate-cw');
        
        // REMOVED: loadConfig();
    }
});

closeConfigBtn.addEventListener('click', () => {
    configPopup.classList.remove('visible');
});

// MODIFIED: Changed from 'submit' event on form to 'click' event on button
document.getElementById('config-save-btn').addEventListener('click', async () => {
    const config = {
        mysqlHost: document.getElementById('mysql-host').value || "localhost",
        mysqlUser: document.getElementById('mysql-user').value || "root",
        mysqlPassword: document.getElementById('mysql-password').value || "root",
        geminiApiKey: document.getElementById('gemini-api-key').value || ""
    };
    await saveConfig(config);
    configPopup.classList.remove('visible');
});

messageInput.addEventListener('input', () => {
    const inputValue = messageInput.value;
    if (isRunCommandActive) {
        hideSlashCommandPopup();
        return;
    }

    // If the user types "/run" and a space, or just "/run", activate the tag.
    if (inputValue.startsWith('/run ')) {
        const restOfQuery = inputValue.substring(5); // Get text after "/run "
        showRunCommandTag();
        messageInput.value = restOfQuery; // Put the rest of the query back
        return; 
    }
    
    if (inputValue.startsWith('/')) {
        showSlashCommandPopup();
    } else {
        hideSlashCommandPopup();
    }
});

removeRunTagBtn.addEventListener('click', () => {
    hideRunCommandTag();
});

document.addEventListener('click', function(event) {
    if (!slashCommandPopup.classList.contains('hidden')) {
        const isClickInsidePopup = slashCommandPopup.contains(event.target);
        const isClickOnInput = messageInput.contains(event.target);
        if (!isClickInsidePopup && !isClickOnInput) {
            hideSlashCommandPopup();
        }
    }
});

// --- ADDED: Event listener for schema table toggling ---
schemaContent.addEventListener('click', function(event) {
    const dbItem = event.target.closest('.schema-database-item');

    if (dbItem) {
        dbItem.classList.toggle('expanded');
        const dbContentWrapper = dbItem.nextElementSibling;
        if (dbContentWrapper && dbContentWrapper.classList.contains('database-content-wrapper')) {
            if (dbContentWrapper.style.maxHeight && dbContentWrapper.style.maxHeight !== '0px') {
                // Collapse the database content
                dbContentWrapper.style.maxHeight = '0px';
            } else {
                // Expand the database content to its own scroll height
                dbContentWrapper.style.maxHeight = dbContentWrapper.scrollHeight + 'px';
            }
        }
    } else {
        const tableItem = event.target.closest('.schema-table-item');
        if (tableItem) {
            tableItem.classList.toggle('expanded');
            const columnsList = tableItem.nextElementSibling;
            if (columnsList && columnsList.classList.contains('schema-columns-list')) {
                const parentWrapper = tableItem.closest('.database-content-wrapper');

                if (columnsList.style.maxHeight && columnsList.style.maxHeight !== '0px') {
                    // Collapse the column list
                    const listHeight = columnsList.scrollHeight;
                    columnsList.style.maxHeight = '0px';
                    // Adjust parent wrapper's height
                    if (parentWrapper && parentWrapper.style.maxHeight !== '0px') {
                        parentWrapper.style.maxHeight = (parseInt(parentWrapper.style.maxHeight) - listHeight) + 'px';
                    }
                } else {
                    // Expand the column list
                    const listHeight = columnsList.scrollHeight;
                    columnsList.style.maxHeight = listHeight + 'px';
                    // Adjust parent wrapper's height
                    if (parentWrapper && parentWrapper.style.maxHeight !== '0px') {
                        parentWrapper.style.maxHeight = (parseInt(parentWrapper.style.maxHeight) + listHeight) + 'px';
                    }
                }
            }
        }
    }
    // Ensure icons are rendered/updated after any DOM change that might affect them.
    lucide.createIcons(); 
});
// --- END ADDED ---

// --- ADDED: Event listeners for dynamic placeholders in config ---
function setupDynamicPlaceholder(inputId, placeholderText) {
    const inputElement = document.getElementById(inputId);
    if (inputElement) {
        inputElement.addEventListener('focus', function() {
            const label = document.querySelector(`label[for="${inputId}"]`);
            // Only add the placeholder if the label indicates the value is already set
            if (label && label.textContent.includes('(already set)')) {
                this.placeholder = placeholderText;
            }
        });
        inputElement.addEventListener('blur', function() {
            // Always clear the placeholder on blur to allow the label to float back down
            this.placeholder = ' ';
        });
    }
}

setupDynamicPlaceholder('mysql-password', 'Enter new password to update');
setupDynamicPlaceholder('gemini-api-key', 'Enter new key to update');
// --- END ADDED ---

// --- Initial Setup ---

lucide.createIcons();

// Page load animation for header icon
document.addEventListener('DOMContentLoaded', () => {
    fetchAndApplyConfig(); // Fetch config on page load

    // --- ADDED: Initialize dark mode from system preference ---
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(prefersDark);
    // --- END ADDED ---

    // === ADDED: Apply ripple effect to main buttons ===
    const buttonsForRipple = document.querySelectorAll('.header-btn, #send-button, #refresh-schema-btn, #config-save-btn, #close-config-btn, #terminal-btn, #scroll-bottom-btn');
    buttonsForRipple.forEach(button => {
        button.classList.add('ripple-container');
        button.addEventListener('click', createRipple);
    });
    // === END ADDED ===

    const headerDbIcon = document.getElementById('header-db-icon');
    if (headerDbIcon) {
        headerDbIcon.classList.add('icon-rotate-onload');
        headerDbIcon.addEventListener('animationend', () => {
            headerDbIcon.classList.remove('icon-rotate-onload');
        }, { once: true });
    }
    setGreeting(); // ADDED
    updateScrollBottomButton(); // ADDED
});

// --- Event Listeners ---

// ADDED: Event listener for password visibility toggles
document.querySelectorAll('.toggle-password').forEach(button => {
    button.addEventListener('click', function() {
        const targetInputId = this.dataset.target;
        const targetInput = document.getElementById(targetInputId);
        
        if (targetInput) {
            if (targetInput.type === 'password') {
                targetInput.type = 'text';
                // Replace the icon inside the button
                this.innerHTML = '<i data-lucide="eye-off" class="h-4 w-4"></i>';
            } else {
                targetInput.type = 'password';
                // Replace it back
                this.innerHTML = '<i data-lucide="eye" class="h-4 w-4"></i>';
            }
            // Tell Lucide to create the new icon
            lucide.createIcons();
        }
    });
});

function addWelcomeMessage() {
    // This function is no longer needed to add the initial message bubble,
    // as it is handled by the initial view. It can be kept for other purposes
    // or if the chat reset needs to add a bubble back in a non-initial state.
    if (isInitialState) return;

    const welcomeHtml = `<div class="p-3 rounded-lg max-w-xl mr-auto">
            <p class="text-sm">Curious about your data? Ask a question or type <code class="bg-gray-200 text-gray-700 px-1 rounded text-xs">/run</code> to execute a direct SQL query.</p>
        </div>`;
    chatHistory.innerHTML = welcomeHtml; // Use innerHTML to replace content
}

async function resetChat() {
    try {
        const response = await fetch('/reset_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        const data = await response.json();
        if (data.status === 'success') {
            chatHistory.innerHTML = ''; // Clear the chat history display
            
            // ADDED: Reset to initial view state
            isInitialState = true;
            chatArea.classList.add('initial-state');
            setGreeting(); // Update greeting in case the time of day changed

            showToast('New chat started.', 'success', 3000);
        } else {
            throw new Error(data.message || 'Failed to reset chat on server.');
        }
    } catch (error) {
        console.error('Error resetting chat:', error);
        showToast(`Could not start new chat: ${error.message}`, 'error');
    }
}

newChatBtn.addEventListener('click', () => {
    resetChat();
});

function addWelcomeMessage() {
    const welcomeHtml = `<div class="p-3 rounded-lg max-w-xl mr-auto">
            <p class="text-sm">Curious about your data? Ask a question or type <code class="bg-blue-200 text-gray-700 px-1 rounded text-xs">/run</code> to execute a direct SQL query.</p>
        </div>`;
    chatHistory.innerHTML = welcomeHtml; // Use innerHTML to replace content
}

// === ADDED: Ripple Effect Logic ===
function createRipple(event) {
    // Only create ripple in dark mode
    if (!document.documentElement.classList.contains('dark')) {
        return;
    }

    const button = event.currentTarget;
    
    const circle = document.createElement("span");
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    const rect = button.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - rect.left - radius}px`;
    circle.style.top = `${event.clientY - rect.top - radius}px`;
    circle.classList.add("ripple");
    
    // Remove any previous ripple to avoid build-up
    const oldRipple = button.querySelector(".ripple");
    if (oldRipple) {
        oldRipple.remove();
    }

    button.appendChild(circle);

    // Clean up after animation
    circle.addEventListener('animationend', () => {
        if (circle.parentElement) {
            circle.remove();
        }
    });
}
// === END ADDED ===

// === ADDED: Greeting Function ===
function setGreeting() {
    const greetingEl = document.getElementById('greeting');
    if (!greetingEl) return;

    const hour = new Date().getHours();
    let greetingText = "Good Evening";
    if (hour >= 5 && hour < 12) {
        greetingText = "Good Morning";
    } else if (hour >= 12 && hour < 16) {
        greetingText = "Good Afternoon";
    }
    greetingEl.textContent = greetingText;
}
// === END ADDED ===

// === Scroll helpers ===

// Returns true if the user is already viewing (or very close to) the bottom of the chat history
function isChatScrolledToBottom(thresholdPx = 20) {
    return chatHistory.scrollHeight - chatHistory.scrollTop - chatHistory.clientHeight < thresholdPx;
}

// Scrolls the chat history container to the bottom (safely and smoothly)
function scrollChatToBottom(forceSmooth = false) {
    // If the scroll distance is short, allow smooth scroll
    const distanceToBottom = chatHistory.scrollHeight - chatHistory.scrollTop - chatHistory.clientHeight;

    const useSmooth = forceSmooth || distanceToBottom < 200;

    if (chatHistory && typeof chatHistory.scrollTo === 'function') {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: useSmooth ? 'smooth' : 'auto'
        });
    } else {
        chatHistory.scrollTop = chatHistory.scrollHeight; // Fallback
    }
}

// === Go-to-bottom button logic ===
const scrollBottomBtn = document.getElementById('scroll-bottom-btn');

// Hide/show the button based on how far user is from the bottom
function updateScrollBottomButton() {
    if (!scrollBottomBtn) return;
    scrollBottomBtn.classList.toggle('hidden', isChatScrolledToBottom());
}

// Throttle the scroll event listener (important for performance)
let scrollTimeout = null;
chatHistory.addEventListener('scroll', () => {
    if (scrollTimeout) return;
    scrollTimeout = setTimeout(() => {
        updateScrollBottomButton();
        scrollTimeout = null;
    }, 100); // adjust delay as needed
});

if (scrollBottomBtn) {
    scrollBottomBtn.addEventListener('click', () => {
        scrollChatToBottom(true); // force smooth on button click
        updateScrollBottomButton();
    });
}

// === End Go-to-bottom button logic ===

// --- ADDED: Dark Mode Functions ---
function setDarkMode(isDark) {
    if (isDark) {
        document.documentElement.classList.add('dark');
        darkModeIconContainer.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sun-icon lucide-sun"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>';
    } else {
        document.documentElement.classList.remove('dark');
        darkModeIconContainer.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-moon-icon lucide-moon"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';
    }
    lucide.createIcons();
}
// --- END: Dark Mode Functions ---

// --- ADDED: Dark Mode Toggle Event Listener ---
darkModeToggleBtn.addEventListener('click', (e) => {
    const isDarkMode = document.documentElement.classList.contains('dark');
    createThemeToggleRipple(e, !isDarkMode);
});
// --- END ADDED ---

// === ADDED: Theme Toggle Ripple Logic (merged from theme.js) ===
function createThemeToggleRipple(event, toDarkMode) {
    // Create overlay ripple element
    const ripple = document.createElement('span');
    ripple.className = 'theme-toggle-ripple';

    // Position the ripple at the click location
    const x = event.clientX;
    const y = event.clientY;
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';

    // Use the target theme's background colour for the ripple
    ripple.style.backgroundColor = toDarkMode ? '#121212' : '#ffffff';

    // Ensure the ripple is large enough to cover the entire viewport
    const maxDim = Math.max(window.innerWidth, window.innerHeight);
    const size = maxDim * 2; // extra to ensure coverage
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.marginLeft = `-${size / 2}px`;
    ripple.style.marginTop = `-${size / 2}px`;

    document.body.appendChild(ripple);

    // Toggle the theme shortly after the ripple starts so the change happens under the overlay
    setTimeout(() => {
        setDarkMode(toDarkMode);
    }, 50);

    // Clean up after animation completes
    ripple.addEventListener('animationend', () => {
        ripple.remove();
    });
}
// === END THEME TOGGLE RIPPLE ===

// === ADDED: Fix 100vh issue on mobile browsers (merged from theme.js) ===
function setAppHeight() {
    const doc = document.documentElement;
    doc.style.setProperty('--app-height', `${window.innerHeight}px`);
}
window.addEventListener('resize', setAppHeight);
document.addEventListener('DOMContentLoaded', setAppHeight);
// === END 100vh FIX ===