let conversations = [];
let currentConversation = null;
let ws;
let updateThrottle = null;
let currentMemoryType = "buffer";
let memoryStats = null;

const messagesDiv = document.getElementById("messages");
const input = document.getElementById("messageInput");
const form = document.getElementById("chatForm");
const convList = document.getElementById("convList");

// --- Render ---
function renderMessages() {
  messagesDiv.innerHTML = "";
  if (!currentConversation) return;
  for (const m of currentConversation.messages) {
    const div = document.createElement("div");
    div.className = "msg " + m.role;
    div.innerText = m.content;
    messagesDiv.appendChild(div);
  }
}

function renderConversations() {
  convList.innerHTML = "";
  conversations.forEach(c => {
    const li = document.createElement("li");
    li.innerText = c.id;
    li.onclick = () => { currentConversation = c; renderMessages(); };
    convList.appendChild(li);
  });
}

// --- Load convs from backend ---
async function loadConversations() {
  const token = document.getElementById("apiKey").value;
  if (!token) return;
  const res = await fetch("/api/conversations", {
    headers: { Authorization: "Bearer " + token }
  });
  const data = await res.json();
  conversations = data;
  if (conversations.length > 0) currentConversation = conversations[0];
  renderConversations();
  renderMessages();
}

// --- Auto-load conversations on page load ---
document.addEventListener('DOMContentLoaded', () => {
  // Load conversations automatically with default token
  loadConversations();
  
  // Reload conversations when token changes
  document.getElementById("apiKey").addEventListener("input", () => {
    loadConversations();
  });
  
  // Update memory type when selector changes
  const memoryTypeSelect = document.getElementById('memoryType');
  if (memoryTypeSelect) {
    memoryTypeSelect.addEventListener('change', updateMemoryType);
    // Initialize memory type
    updateMemoryType();
  }
});

// --- SSE send ---
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  
  // Clear input and disable form
  input.value = "";
  input.style.height = "auto";
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="button-icon">⏳</span><span class="button-text">Envoi...</span>';
  
  // Show typing indicator
  showTypingIndicator();
  
  if (!currentConversation) currentConversation = { id: crypto.randomUUID(), messages: [] };
  currentConversation.messages.push({ role: "user", content: text });
  renderMessages();

  try {
    const token = document.getElementById("apiKey").value.trim();
    const lang = document.getElementById("lang").value;
    
    // Validate token before sending request
    if (!token) {
      throw new Error("Veuillez entrer un token valide dans le champ 'Token utilisateur'");
    }
    
    console.log("Sending request to /api/chat/stream with:", {
      message: text,
      conversation: currentConversation,
      lang: lang,
      token: "***" // Always show as masked for security
    });
    
    const res = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token
      },
      body: JSON.stringify({ 
        message: text, 
        conversation: currentConversation, 
        lang: lang,
        memory_type: currentMemoryType
      })
    });

    console.log("Response status:", res.status, res.statusText);
    console.log("Response headers:", Object.fromEntries(res.headers.entries()));

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const reader = res.body.getReader();
    let decoder = new TextDecoder();
    let buffer = "";
    let streamingMessage = null;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value);
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.content && !data.done) {
              // Streaming chunk
              if (!streamingMessage) {
                // Create new streaming message
                streamingMessage = { role: "assistant", content: "", streaming: true };
                currentConversation.messages.push(streamingMessage);
                // Render the new message container
                renderMessages();
                // Hide typing indicator when first chunk arrives
                hideTypingIndicator();
              } else {
                // Update only the streaming message content
                streamingMessage.content += data.content;
                updateStreamingMessage(streamingMessage);
              }
            } else if (data.done) {
              // Streaming complete
              if (streamingMessage) {
                streamingMessage.streaming = false;
                updateStreamingMessage(streamingMessage);
                streamingMessage = null;
              }
              
              // Handle memory stats if provided
              if (data.memory_stats) {
                handleMemoryStats(data.memory_stats);
              }
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e, line);
          }
        }
      }
    }
  } catch (error) {
    console.error("Error sending message:", error);
    // Add error message with more details
    const errorMsg = `Erreur: ${error.message}. Vérifiez que le serveur est démarré et que votre token est valide.`;
    currentConversation.messages.push({ role: "assistant", content: errorMsg });
    renderMessages();
  } finally {
    // Hide typing indicator and re-enable form
    hideTypingIndicator();
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
});

// --- WebSocket send ---
document.getElementById("sendWs").addEventListener("click", () => {
  const text = input.value.trim();
  if (!text) return;
  
  const token = document.getElementById("apiKey").value.trim();
  const lang = document.getElementById("lang").value;
  
  // Validate token before sending request
  if (!token) {
    alert("Veuillez entrer un token valide dans le champ 'Token utilisateur'");
    return;
  }
  
  // Clear input and disable buttons
  input.value = "";
  input.style.height = "auto";
  const wsBtn = document.getElementById("sendWs");
  const stopBtn = document.getElementById("stopWs");
  const originalWsText = wsBtn.innerHTML;
  
  wsBtn.disabled = true;
  wsBtn.innerHTML = '<span class="button-icon">⏳</span><span class="button-text">Connexion...</span>';
  stopBtn.disabled = false;
  
  // Show typing indicator
  showTypingIndicator();
  
  ws = new WebSocket(`ws://${window.location.host}/ws?token=${token}&lang=${lang}&memory_type=${currentMemoryType}`);

  ws.onopen = () => {
    wsBtn.innerHTML = '<span class="button-icon">📡</span><span class="button-text">Envoi...</span>';
    if (!currentConversation) currentConversation = { id: crypto.randomUUID(), messages: [] };
    currentConversation.messages.push({ role: "user", content: text });
    renderMessages();
    ws.send(JSON.stringify({ 
      type: "user_message", 
      text, 
      conversation: currentConversation,
      memory_type: currentMemoryType
    }));
  };

  let streamingMessage = null;
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
      if (data.type === "chunk") {
        // Streaming chunk
        if (!streamingMessage) {
          // Create new streaming message
          streamingMessage = { role: "assistant", content: "", streaming: true };
          currentConversation.messages.push(streamingMessage);
          // Render the new message container
          renderMessages();
          // Hide typing indicator when first chunk arrives
          hideTypingIndicator();
        } else {
          // Update only the streaming message content
          streamingMessage.content += data.content;
          updateStreamingMessage(streamingMessage);
        }
    } else if (data.type === "final") {
      // Streaming complete
      if (streamingMessage) {
        streamingMessage.streaming = false;
        updateStreamingMessage(streamingMessage);
        streamingMessage = null;
      }
      
      // Handle memory stats if provided
      if (data.memory_stats) {
        handleMemoryStats(data.memory_stats);
      }
      
      // Hide typing indicator and reset buttons
      hideTypingIndicator();
      wsBtn.disabled = false;
      wsBtn.innerHTML = originalWsText;
      stopBtn.disabled = true;
    }
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    hideTypingIndicator();
    wsBtn.disabled = false;
    wsBtn.innerHTML = originalWsText;
    stopBtn.disabled = true;
  };
  
  ws.onclose = () => {
    hideTypingIndicator();
    wsBtn.disabled = false;
    wsBtn.innerHTML = originalWsText;
    stopBtn.disabled = true;
  };
});

// --- Stop streaming ---
document.getElementById("stopWs").addEventListener("click", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "stop" }));
  }
  // Hide typing indicator when stopping
  hideTypingIndicator();
});

// --- Theme toggle ---
document.getElementById("themeToggle").addEventListener("click", () => {
  document.body.classList.toggle("dark");
  const themeIcon = document.querySelector(".theme-icon");
  themeIcon.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";
});

// --- Mobile sidebar toggle ---
document.getElementById("sidebarToggle").addEventListener("click", () => {
  document.getElementById("sidebar").classList.add("open");
});

document.getElementById("sidebarClose").addEventListener("click", () => {
  document.getElementById("sidebar").classList.remove("open");
});

// Close sidebar when clicking outside on mobile
document.addEventListener("click", (e) => {
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");
  
  if (window.innerWidth <= 768 && 
      sidebar.classList.contains("open") && 
      !sidebar.contains(e.target) && 
      !sidebarToggle.contains(e.target)) {
    sidebar.classList.remove("open");
  }
});

// --- Auto-resize textarea ---
const messageInput = document.getElementById("messageInput");
messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 8 * 24) + "px";
});

// --- Loading overlay ---
function showLoading() {
  document.getElementById("loadingOverlay").classList.add("show");
}

function hideLoading() {
  document.getElementById("loadingOverlay").classList.remove("show");
}

// --- Enhanced Markdown renderer with syntax highlighting ---
function renderMarkdown(text) {
  // Escape HTML first
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  
  // Code blocks (```language\ncode```)
  html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text';
    const highlightedCode = highlightCode(code.trim(), language);
    return `<pre class="code-block" data-language="${language}"><code class="language-${language}">${highlightedCode}</code></pre>`;
  });
  
  // Inline code (`code`)
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
  
  // Bold (**text**)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic (*text*)
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  
  return html;
}

// --- Syntax highlighting function ---
function highlightCode(code, language) {
  // Simple syntax highlighting based on language
  switch (language.toLowerCase()) {
    case 'python':
      return highlightPython(code);
    case 'javascript':
    case 'js':
      return highlightJavaScript(code);
    case 'bash':
    case 'shell':
    case 'sh':
    case 'zsh':
    case 'fish':
      return highlightBash(code);
    case 'powershell':
    case 'ps1':
      return highlightPowerShell(code);
    case 'cmd':
    case 'batch':
      return highlightBatch(code);
    case 'sql':
      return highlightSQL(code);
    case 'html':
      return highlightHTML(code);
    case 'css':
      return highlightCSS(code);
    case 'json':
      return highlightJSON(code);
    case 'yaml':
    case 'yml':
      return highlightYAML(code);
    case 'markdown':
    case 'md':
      return highlightMarkdown(code);
    default:
      return escapeHtml(code);
  }
}

// --- Python syntax highlighting ---
function highlightPython(code) {
  return code
    .replace(/\b(def|class|if|elif|else|for|while|try|except|finally|with|import|from|return|yield|lambda|and|or|not|in|is|True|False|None)\b/g, '<span class="keyword">$1</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/#.*$/gm, '<span class="comment">$&</span>')
    .replace(/\b(__\w+__)\b/g, '<span class="builtin">$1</span>');
}

// --- JavaScript syntax highlighting ---
function highlightJavaScript(code) {
  return code
    .replace(/\b(const|let|var|function|class|if|else|for|while|do|switch|case|break|continue|return|try|catch|finally|throw|new|this|super|extends|import|export|default|async|await|static|public|private|protected)\b/g, '<span class="keyword">$1</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>')
    .replace(/(["'`])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/\/\/.*$/gm, '<span class="comment">$&</span>')
    .replace(/\/\*[\s\S]*?\*\//g, '<span class="comment">$&</span>')
    .replace(/\b(console|document|window|Array|Object|String|Number|Boolean|Date|Math|JSON|Promise|fetch)\b/g, '<span class="builtin">$1</span>');
}

// --- Bash/Shell syntax highlighting ---
function highlightBash(code) {
  return code
    .replace(/^(\s*)(#.*)$/gm, '$1<span class="comment">$2</span>')
    .replace(/\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|break|continue|echo|printf|read|cd|ls|pwd|mkdir|rm|cp|mv|grep|sed|awk|chmod|chown|sudo|apt|pip|npm|git|docker|kubectl|curl|wget|tar|zip|unzip|ssh|scp|rsync|find|locate|which|whereis|ps|top|htop|kill|killall|systemctl|service|journalctl|tail|head|cat|less|more|vim|nano|emacs|python|python3|node|npm|yarn|composer|bundle|gem|cargo|go|rustc|javac|java|gcc|g\+\+|make|cmake|configure|install|uninstall|update|upgrade|dist-upgrade|autoremove|clean|search|show|list|info|version|help|--help|-h)\b/g, '<span class="command">$1</span>')
    .replace(/(\$[a-zA-Z_][a-zA-Z0-9_]*)/g, '<span class="variable">$1</span>')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/^(\s*)([a-zA-Z_][a-zA-Z0-9_]*=)/gm, '$1<span class="assignment">$2</span>')
    .replace(/(\$\{[^}]+\})/g, '<span class="variable">$1</span>')
    .replace(/(\$\d+)/g, '<span class="variable">$1</span>')
    .replace(/(\|\||&&|;|&)/g, '<span class="operator">$1</span>')
    .replace(/(\-\w+)/g, '<span class="option">$1</span>')
    .replace(/(\-\-\w+)/g, '<span class="option">$1</span>');
}

// --- PowerShell syntax highlighting ---
function highlightPowerShell(code) {
  return code
    .replace(/^(\s*)(#.*)$/gm, '$1<span class="comment">$2</span>')
    .replace(/\b(if|else|elseif|for|foreach|while|do|until|switch|case|default|break|continue|return|function|param|begin|process|end|try|catch|finally|throw|Get-|Set-|New-|Remove-|Add-|Clear-|Copy-|Move-|Rename-|Test-|Where-|Select-|Sort-|Group-|Measure-|Out-|Write-|Read-|Import-|Export-|ConvertTo-|ConvertFrom-|Invoke-|Start-|Stop-|Restart-|Suspend-|Resume-|Wait-|Receive-|Send-|Connect-|Disconnect-|Register-|Unregister-|Enable-|Disable-|Show-|Hide-|Open-|Close-|Save-|Load-|Update-|Install-|Uninstall-|Get-Content|Set-Content|Add-Content|Clear-Content|Copy-Item|Move-Item|New-Item|Remove-Item|Rename-Item|Test-Path|Where-Object|Select-Object|Sort-Object|Group-Object|Measure-Object|Out-File|Write-Host|Write-Output|Write-Warning|Write-Error|Read-Host|Import-Module|Export-ModuleMember|ConvertTo-Html|ConvertTo-Json|ConvertTo-Xml|ConvertFrom-Json|ConvertFrom-Xml|Invoke-Command|Invoke-Expression|Invoke-WebRequest|Start-Process|Start-Service|Stop-Service|Restart-Service|Suspend-Service|Resume-Service|Wait-Process|Receive-Job|Send-MailMessage|Connect-PSSession|Disconnect-PSSession|Register-PSSessionConfiguration|Unregister-PSSessionConfiguration|Enable-PSRemoting|Disable-PSRemoting|Show-Command|Hide-Command|Open-File|Close-File|Save-File|Load-File|Update-Help|Install-Module|Uninstall-Module)\b/g, '<span class="command">$1</span>')
    .replace(/(\$[a-zA-Z_][a-zA-Z0-9_]*)/g, '<span class="variable">$1</span>')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/^(\s*)([a-zA-Z_][a-zA-Z0-9_]*\s*=)/gm, '$1<span class="assignment">$2</span>')
    .replace(/(\$\{[^}]+\})/g, '<span class="variable">$1</span>')
    .replace(/(\|\||&&|;|&)/g, '<span class="operator">$1</span>')
    .replace(/(\-\w+)/g, '<span class="option">$1</span>')
    .replace(/(\-\-\w+)/g, '<span class="option">$1</span>');
}

// --- Batch/CMD syntax highlighting ---
function highlightBatch(code) {
  return code
    .replace(/^(\s*)(REM.*|::.*)$/gm, '$1<span class="comment">$2</span>')
    .replace(/\b(if|else|for|while|do|goto|call|start|echo|set|cd|dir|copy|move|del|ren|md|rd|type|find|findstr|sort|more|pause|exit|cls|color|title|prompt|path|ver|vol|date|time|chkdsk|format|diskpart|sfc|dism|bcdedit|reg|regedit|net|netstat|ipconfig|ping|tracert|nslookup|telnet|ftp|sc|tasklist|taskkill|wmic|systeminfo|driverquery|shutdown|restart|logoff|msg|net|share|use|subst|attrib|xcopy|robocopy|fc|comp|expand|extract|makecab|iexpress|certutil|bitsadmin|wget|curl|powershell|cmd|command|batch|bat)\b/gi, '<span class="command">$1</span>')
    .replace(/(%[a-zA-Z_][a-zA-Z0-9_]*%)/g, '<span class="variable">$1</span>')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/^(\s*)([a-zA-Z_][a-zA-Z0-9_]*\s*=)/gm, '$1<span class="assignment">$2</span>')
    .replace(/(\|\||&&|;|&)/g, '<span class="operator">$1</span>')
    .replace(/(\-\w+)/g, '<span class="option">$1</span>')
    .replace(/(\-\-\w+)/g, '<span class="option">$1</span>');
}

// --- SQL syntax highlighting ---
function highlightSQL(code) {
  return code
    .replace(/\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|HAVING|INSERT|INTO|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|PRIMARY|KEY|FOREIGN|REFERENCES|UNIQUE|NOT|NULL|DEFAULT|AUTO_INCREMENT|LIMIT|OFFSET|UNION|DISTINCT|COUNT|SUM|AVG|MIN|MAX)\b/gi, '<span class="keyword">$1</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/--.*$/gm, '<span class="comment">$&</span>')
    .replace(/\/\*[\s\S]*?\*\//g, '<span class="comment">$&</span>');
}

// --- HTML syntax highlighting ---
function highlightHTML(code) {
  return code
    .replace(/&lt;(\/?)([a-zA-Z][a-zA-Z0-9]*)\b([^&]*?)&gt;/g, (match, closing, tag, attrs) => {
      const tagClass = closing ? 'tag-closing' : 'tag-opening';
      return `&lt;${closing}<span class="tag">${tag}</span>${highlightHTMLAttributes(attrs)}&gt;`;
    })
    .replace(/&lt;!--[\s\S]*?--&gt;/g, '<span class="comment">$&</span>');
}

function highlightHTMLAttributes(attrs) {
  return attrs.replace(/\b([a-zA-Z-]+)(=)(["'][^"']*["'])/g, '<span class="attr-name">$1</span><span class="attr-equals">$2</span><span class="attr-value">$3</span>');
}

// --- CSS syntax highlighting ---
function highlightCSS(code) {
  return code
    .replace(/([.#]?[a-zA-Z-]+)\s*\{/g, '<span class="selector">$1</span> {')
    .replace(/\b([a-zA-Z-]+)\s*:/g, '<span class="property">$1</span>:')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="string">$1$2$1</span>')
    .replace(/\b(\d+\.?\d*[a-zA-Z%]*)\b/g, '<span class="value">$1</span>')
    .replace(/\/\*[\s\S]*?\*\//g, '<span class="comment">$&</span>');
}

// --- JSON syntax highlighting ---
function highlightJSON(code) {
  return code
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1(\s*:)/g, '<span class="json-key">$1$2$1</span>$3')
    .replace(/:\s*(\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
    .replace(/:\s*(true|false|null)/g, ': <span class="json-boolean">$1</span>')
    .replace(/:\s*(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, ': <span class="json-string">$1$2$1</span>');
}

// --- YAML syntax highlighting ---
function highlightYAML(code) {
  return code
    .replace(/^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:/gm, '$1<span class="yaml-key">$2</span>:')
    .replace(/(["'])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span class="yaml-string">$1$2$1</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="yaml-number">$1</span>')
    .replace(/\b(true|false|null|yes|no|on|off)\b/g, '<span class="yaml-boolean">$1</span>')
    .replace(/#.*$/gm, '<span class="comment">$&</span>');
}

// --- Markdown syntax highlighting ---
function highlightMarkdown(code) {
  return code
    .replace(/^#{1,6}\s+(.+)$/gm, '<span class="md-header">$&</span>')
    .replace(/\*\*(.+?)\*\*/g, '<span class="md-bold">**$1**</span>')
    .replace(/\*(.+?)\*/g, '<span class="md-italic">*$1*</span>')
    .replace(/`([^`]+)`/g, '<span class="md-code">`$1`</span>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<span class="md-link">[$1]($2)</span>');
}

// --- Utility function to escape HTML ---
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// --- Enhanced message rendering with timestamps and Markdown ---
function renderMessages() {
  messagesDiv.innerHTML = "";
  if (!currentConversation) return;
  
  for (const m of currentConversation.messages) {
    const div = document.createElement("div");
    div.className = "msg " + m.role + (m.streaming ? " streaming" : "");
    div.setAttribute("data-message-id", m.id || currentConversation.messages.indexOf(m));
    
    const content = document.createElement("div");
    if (m.role === "assistant") {
      content.innerHTML = renderMarkdown(m.content);
      
      // Add copy functionality to code blocks
      const codeBlocks = content.querySelectorAll('.code-block');
      codeBlocks.forEach(block => {
        block.addEventListener('click', () => copyCodeToClipboard(block));
        block.style.cursor = 'pointer';
        block.title = 'Click to copy code';
      });
      
      // Add typing indicator for streaming messages
      if (m.streaming) {
        const typingIndicator = document.createElement("span");
        typingIndicator.className = "typing-indicator";
        typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        content.appendChild(typingIndicator);
      }
    } else {
      content.textContent = m.content;
    }
    div.appendChild(content);
    
    // Add timestamp
    const timestamp = document.createElement("div");
    timestamp.className = "timestamp";
    timestamp.textContent = new Date().toLocaleTimeString();
    timestamp.style.fontSize = "0.75rem";
    timestamp.style.opacity = "0.7";
    timestamp.style.marginTop = "0.5rem";
    div.appendChild(timestamp);
    
    messagesDiv.appendChild(div);
  }
  
  // Scroll to bottom
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// --- Efficient streaming message update ---
function updateStreamingMessage(message) {
  const messageIndex = currentConversation.messages.indexOf(message);
  const messageElement = messagesDiv.querySelector(`[data-message-id="${messageIndex}"]`);
  
  if (!messageElement) return;
  
  const contentElement = messageElement.querySelector('div');
  if (!contentElement) return;
  
  // Throttle updates to prevent excessive re-rendering
  if (updateThrottle) {
    clearTimeout(updateThrottle);
  }
  
  updateThrottle = setTimeout(() => {
    // Update content with smooth animation
    contentElement.innerHTML = renderMarkdown(message.content);
    
    // Re-add copy functionality to code blocks
    const codeBlocks = contentElement.querySelectorAll('.code-block');
    codeBlocks.forEach(block => {
      block.addEventListener('click', () => copyCodeToClipboard(block));
      block.style.cursor = 'pointer';
      block.title = 'Click to copy code';
    });
    
    // Update typing indicator
    if (message.streaming) {
      const existingIndicator = contentElement.querySelector('.typing-indicator');
      if (!existingIndicator) {
        const typingIndicator = document.createElement("span");
        typingIndicator.className = "typing-indicator";
        typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        contentElement.appendChild(typingIndicator);
      }
    } else {
      // Remove typing indicator when streaming is complete
      const existingIndicator = contentElement.querySelector('.typing-indicator');
      if (existingIndicator) {
        existingIndicator.remove();
      }
      // Remove streaming class
      messageElement.classList.remove('streaming');
    }
    
    // Smooth scroll to bottom (throttled for performance)
    requestAnimationFrame(() => {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
    
    updateThrottle = null;
  }, 50); // Update every 50ms instead of on every chunk
}

// --- Enhanced copy code to clipboard functionality ---
async function copyCodeToClipboard(codeBlock) {
  const codeElement = codeBlock.querySelector('code');
  if (!codeElement) return;
  
  try {
    // Extract plain text from the highlighted code
    const textToCopy = codeElement.textContent || codeElement.innerText;
    await navigator.clipboard.writeText(textToCopy);
    
    // Enhanced visual feedback
    showCopyFeedback(codeBlock, '✓ Copied!', '#50fa7b');
    
    // Add a subtle animation
    codeBlock.classList.add('animated');
    setTimeout(() => {
      codeBlock.classList.remove('animated');
    }, 3000);
    
  } catch (err) {
    console.error('Failed to copy code: ', err);
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = codeElement.textContent || codeElement.innerText;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    showCopyFeedback(codeBlock, '✓ Copied!', '#50fa7b');
  }
}

// --- Typing Indicator Functions ---
function showTypingIndicator() {
  const typingIndicator = document.getElementById('typingIndicator');
  if (typingIndicator) {
    typingIndicator.style.display = 'flex';
    // Scroll to bottom to show the typing indicator
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }
}

function hideTypingIndicator() {
  const typingIndicator = document.getElementById('typingIndicator');
  if (typingIndicator) {
    typingIndicator.style.display = 'none';
  }
}

// --- Memory Management Functions ---
function updateMemoryType() {
  const memoryTypeSelect = document.getElementById('memoryType');
  if (memoryTypeSelect) {
    currentMemoryType = memoryTypeSelect.value;
    updateMemoryInfo();
  }
}

function updateMemoryInfo() {
  const memoryInfo = document.getElementById('memoryInfo');
  const memoryTypeValue = document.getElementById('currentMemoryType');
  const memoryCountValue = document.getElementById('currentMemoryCount');
  
  if (memoryInfo && memoryTypeValue && memoryCountValue) {
    // Show memory info if we have stats
    if (memoryStats) {
      memoryInfo.style.display = 'block';
      memoryTypeValue.textContent = getMemoryTypeDisplayName(currentMemoryType);
      memoryTypeValue.setAttribute('data-type', currentMemoryType);
      memoryCountValue.textContent = memoryStats.message_count || 0;
    } else {
      memoryInfo.style.display = 'none';
    }
  }
}

function getMemoryTypeDisplayName(type) {
  const names = {
    'buffer': 'Buffer complet',
    'summary': 'Résumé intelligent', 
    'token_buffer': 'Buffer limité'
  };
  return names[type] || type;
}

function handleMemoryStats(stats) {
  memoryStats = stats;
  updateMemoryInfo();
  
  // Log memory stats for debugging
  console.log('Memory stats:', stats);
}

// --- Enhanced copy feedback ---
function showCopyFeedback(codeBlock, message, color) {
  // Create feedback overlay
  const feedback = document.createElement('div');
  feedback.style.cssText = `
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.9);
    color: ${color};
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
    font-weight: 600;
    font-size: 0.9rem;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    border: 1px solid ${color};
    animation: fadeInOut 1.5s ease-in-out;
  `;
  feedback.textContent = message;
  
  // Add animation keyframes if not already added
  if (!document.querySelector('#copy-feedback-styles')) {
    const style = document.createElement('style');
    style.id = 'copy-feedback-styles';
    style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
      }
    `;
    document.head.appendChild(style);
  }
  
  codeBlock.style.position = 'relative';
  codeBlock.appendChild(feedback);
  
  // Remove feedback after animation
  setTimeout(() => {
    if (feedback.parentNode) {
      feedback.parentNode.removeChild(feedback);
    }
  }, 1500);
}

// --- Enhanced conversation rendering ---
function renderConversations() {
  convList.innerHTML = "";
  conversations.forEach(c => {
    const li = document.createElement("li");
    
    // Format the date
    const date = new Date(c.updated_at || c.created_at);
    const dateStr = date.toLocaleDateString();
    const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    li.innerHTML = `
      <div class="conv-title">${c.title || 'New Conversation'}</div>
      <div class="conv-preview">
        <span class="conv-meta">${c.message_count || c.messages.length} messages</span>
        <span class="conv-date">${dateStr} ${timeStr}</span>
      </div>
    `;
    li.onclick = () => { 
      currentConversation = c; 
      renderMessages();
      // Close sidebar on mobile after selection
      if (window.innerWidth <= 768) {
        document.getElementById("sidebar").classList.remove("open");
      }
    };
    convList.appendChild(li);
  });
}

// --- New conversation functionality ---
document.getElementById("newConversationBtn").addEventListener("click", () => {
  currentConversation = { id: crypto.randomUUID(), messages: [] };
  renderMessages();
  // Close sidebar on mobile after creating new conversation
  if (window.innerWidth <= 768) {
    document.getElementById("sidebar").classList.remove("open");
  }
});

// --- Init ---
document.getElementById("apiKey").addEventListener("change", loadConversations);

// Initialize theme icon
const themeIcon = document.querySelector(".theme-icon");
themeIcon.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";

// --- Code Editor Functions ---
let currentCodeEditor = null;

function openCodeEditor(code, language = 'text') {
  const modal = document.getElementById('codeEditorModal');
  const textarea = document.getElementById('codeEditorTextarea');
  const languageBadge = document.getElementById('codeEditorLanguage');
  const linesCount = document.getElementById('codeEditorLines');
  const charsCount = document.getElementById('codeEditorChars');
  
  // Set the code content
  textarea.value = code;
  languageBadge.textContent = language;
  
  // Update counts
  updateEditorCounts();
  
  // Show modal
  modal.classList.add('active');
  modal.setAttribute('aria-hidden', 'false');
  
  // Focus on textarea
  setTimeout(() => {
    textarea.focus();
  }, 100);
  
  // Store current editor state
  currentCodeEditor = {
    code: code,
    language: language,
    originalCode: code
  };
  
  // Prevent body scroll
  document.body.style.overflow = 'hidden';
}

function closeCodeEditor() {
  const modal = document.getElementById('codeEditorModal');
  
  modal.classList.remove('active');
  modal.setAttribute('aria-hidden', 'true');
  
  // Restore body scroll
  document.body.style.overflow = '';
  
  // Clear current editor state
  currentCodeEditor = null;
}

function updateEditorCounts() {
  const textarea = document.getElementById('codeEditorTextarea');
  const linesCount = document.getElementById('codeEditorLines');
  const charsCount = document.getElementById('codeEditorChars');
  
  const text = textarea.value;
  const lines = text.split('\n').length;
  const chars = text.length;
  
  linesCount.textContent = `${lines} line${lines !== 1 ? 's' : ''}`;
  charsCount.textContent = `${chars} character${chars !== 1 ? 's' : ''}`;
}

function copyCodeFromEditor() {
  const textarea = document.getElementById('codeEditorTextarea');
  const code = textarea.value;
  
  navigator.clipboard.writeText(code).then(() => {
    showCopyFeedback('Code copied to clipboard!');
  }).catch(err => {
    console.error('Failed to copy code:', err);
    showCopyFeedback('Failed to copy code', 'error');
  });
}

function downloadCodeFromEditor() {
  const textarea = document.getElementById('codeEditorTextarea');
  const languageBadge = document.getElementById('codeEditorLanguage');
  const code = textarea.value;
  const language = languageBadge.textContent.toLowerCase();
  
  // Determine file extension
  const extensions = {
    'python': 'py',
    'javascript': 'js',
    'typescript': 'ts',
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'xml': 'xml',
    'sql': 'sql',
    'bash': 'sh',
    'shell': 'sh',
    'yaml': 'yml',
    'markdown': 'md',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'c',
    'rust': 'rs',
    'go': 'go',
    'php': 'php',
    'ruby': 'rb',
    'swift': 'swift',
    'kotlin': 'kt',
    'scala': 'scala',
    'r': 'r',
    'matlab': 'm',
    'text': 'txt'
  };
  
  const extension = extensions[language] || 'txt';
  const filename = `code.${extension}`;
  
  const blob = new Blob([code], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  showCopyFeedback(`Code downloaded as ${filename}!`);
}

function formatCodeInEditor() {
  const textarea = document.getElementById('codeEditorTextarea');
  const languageBadge = document.getElementById('codeEditorLanguage');
  const language = languageBadge.textContent.toLowerCase();
  
  let formattedCode = textarea.value;
  
  // Basic formatting based on language
  switch (language) {
    case 'javascript':
    case 'typescript':
    case 'json':
      // Basic JSON formatting
      if (language === 'json') {
        try {
          const parsed = JSON.parse(formattedCode);
          formattedCode = JSON.stringify(parsed, null, 2);
        } catch (e) {
          showCopyFeedback('Invalid JSON format', 'error');
          return;
        }
      } else {
        // Basic JS/TS formatting (indentation)
        formattedCode = formattedCode
          .replace(/\{/g, '{\n  ')
          .replace(/\}/g, '\n}')
          .replace(/;/g, ';\n')
          .replace(/,\n/g, ',\n  ');
      }
      break;
      
    case 'html':
      // Basic HTML formatting
      formattedCode = formattedCode
        .replace(/></g, '>\n<')
        .replace(/^\s+/gm, '  ');
      break;
      
    case 'css':
      // Basic CSS formatting
      formattedCode = formattedCode
        .replace(/\{/g, ' {\n  ')
        .replace(/\}/g, '\n}\n')
        .replace(/;/g, ';\n  ');
      break;
      
    case 'python':
      // Basic Python formatting (just ensure proper indentation)
      const lines = formattedCode.split('\n');
      let indentLevel = 0;
      formattedCode = lines.map(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('def ') || trimmed.startsWith('class ') || trimmed.startsWith('if ') || 
            trimmed.startsWith('for ') || trimmed.startsWith('while ') || trimmed.startsWith('with ')) {
          const result = '  '.repeat(indentLevel) + trimmed;
          indentLevel++;
          return result;
        } else if (trimmed === '' || trimmed.startsWith('#')) {
          return '  '.repeat(indentLevel) + trimmed;
        } else {
          indentLevel = Math.max(0, indentLevel - 1);
          return '  '.repeat(indentLevel) + trimmed;
        }
      }).join('\n');
      break;
      
    default:
      showCopyFeedback('Formatting not available for this language', 'warning');
      return;
  }
  
  textarea.value = formattedCode;
  updateEditorCounts();
  showCopyFeedback('Code formatted!');
}

function saveCodeFromEditor() {
  if (!currentCodeEditor) return;
  
  const textarea = document.getElementById('codeEditorTextarea');
  const newCode = textarea.value;
  
  // Update the original code block if it exists
  const codeBlocks = document.querySelectorAll('.code-block');
  codeBlocks.forEach(block => {
    const codeElement = block.querySelector('code');
    if (codeElement && codeElement.textContent.trim() === currentCodeEditor.originalCode.trim()) {
      codeElement.textContent = newCode;
      // Re-highlight the code
      if (window.hljs) {
        hljs.highlightElement(codeElement);
      }
    }
  });
  
  currentCodeEditor.code = newCode;
  showCopyFeedback('Code saved!');
}

function addEditorButtonToCodeBlocks() {
  const codeBlocks = document.querySelectorAll('.code-block');
  
  codeBlocks.forEach(block => {
    // Check if editor button already exists
    if (block.querySelector('.editor-btn')) return;
    
    const editorBtn = document.createElement('button');
    editorBtn.className = 'editor-btn';
    editorBtn.innerHTML = '<span class="btn-icon">✏️</span><span class="btn-text">Edit</span>';
    editorBtn.title = 'Open in code editor';
    
    editorBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const codeElement = block.querySelector('code');
      const language = block.getAttribute('data-language') || 'text';
      
      if (codeElement) {
        openCodeEditor(codeElement.textContent, language);
      }
    });
    
    block.appendChild(editorBtn);
  });
}

// Indentation functions
function insertIndentation(textarea, spaces = 2) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = textarea.value;
  
  // If there's a selection, indent the selected lines
  if (start !== end) {
    const lines = text.split('\n');
    const startLine = text.substring(0, start).split('\n').length - 1;
    const endLine = text.substring(0, end).split('\n').length - 1;
    
    for (let i = startLine; i <= endLine; i++) {
      if (lines[i].trim() !== '') {
        lines[i] = ' '.repeat(spaces) + lines[i];
      }
    }
    
    textarea.value = lines.join('\n');
    
    // Restore selection
    const newStart = start + spaces;
    const newEnd = end + (spaces * (endLine - startLine + 1));
    textarea.setSelectionRange(newStart, newEnd);
  } else {
    // Insert spaces at cursor position
    const beforeCursor = text.substring(0, start);
    const afterCursor = text.substring(end);
    
    textarea.value = beforeCursor + ' '.repeat(spaces) + afterCursor;
    textarea.setSelectionRange(start + spaces, start + spaces);
  }
  
  updateEditorCounts();
}

function removeIndentation(textarea, spaces = 2) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = textarea.value;
  
  // If there's a selection, unindent the selected lines
  if (start !== end) {
    const lines = text.split('\n');
    const startLine = text.substring(0, start).split('\n').length - 1;
    const endLine = text.substring(0, end).split('\n').length - 1;
    
    for (let i = startLine; i <= endLine; i++) {
      if (lines[i].trim() !== '') {
        // Remove up to 'spaces' characters from the beginning
        const indentToRemove = Math.min(spaces, lines[i].match(/^ */)[0].length);
        lines[i] = lines[i].substring(indentToRemove);
      }
    }
    
    textarea.value = lines.join('\n');
    
    // Restore selection
    const newStart = Math.max(0, start - spaces);
    const newEnd = Math.max(0, end - (spaces * (endLine - startLine + 1)));
    textarea.setSelectionRange(newStart, newEnd);
  } else {
    // Remove spaces before cursor
    const beforeCursor = text.substring(0, start);
    const afterCursor = text.substring(end);
    
    // Find the last line before cursor
    const lines = beforeCursor.split('\n');
    const currentLine = lines[lines.length - 1];
    
    // Remove up to 'spaces' characters from the end of the line
    const indentToRemove = Math.min(spaces, currentLine.match(/ *$/)[0].length);
    const newBeforeCursor = beforeCursor.substring(0, beforeCursor.length - indentToRemove);
    
    textarea.value = newBeforeCursor + afterCursor;
    textarea.setSelectionRange(start - indentToRemove, start - indentToRemove);
  }
  
  updateEditorCounts();
}

function autoIndent(textarea) {
  const start = textarea.selectionStart;
  const text = textarea.value;
  const lines = text.split('\n');
  const currentLineIndex = text.substring(0, start).split('\n').length - 1;
  const currentLine = lines[currentLineIndex];
  
  // Get the previous line's indentation
  let prevLineIndent = 0;
  if (currentLineIndex > 0) {
    const prevLine = lines[currentLineIndex - 1];
    prevLineIndent = prevLine.match(/^ */)[0].length;
    
    // Check if previous line ends with opening bracket/parenthesis
    const trimmedPrevLine = prevLine.trim();
    if (trimmedPrevLine.endsWith('{') || trimmedPrevLine.endsWith('(') || 
        trimmedPrevLine.endsWith('[') || trimmedPrevLine.endsWith(':')) {
      prevLineIndent += 2; // Add extra indentation
    }
  }
  
  // Set cursor position with proper indentation
  const newPosition = start + prevLineIndent;
  textarea.value = text.substring(0, start) + ' '.repeat(prevLineIndent) + text.substring(start);
  textarea.setSelectionRange(newPosition, newPosition);
  
  updateEditorCounts();
}

function handleEditorKeydown(e) {
  const textarea = e.target;
  
  // Tab key for indentation
  if (e.key === 'Tab') {
    e.preventDefault();
    if (e.shiftKey) {
      removeIndentation(textarea, 2);
    } else {
      insertIndentation(textarea, 2);
    }
  }
  
  // Enter key for auto-indentation
  if (e.key === 'Enter') {
    // Let the default behavior happen first, then adjust indentation
    setTimeout(() => {
      autoIndent(textarea);
    }, 0);
  }
  
  // Ctrl+] and Ctrl+[ for indentation (common in editors)
  if (e.ctrlKey) {
    if (e.key === ']') {
      e.preventDefault();
      insertIndentation(textarea, 2);
    } else if (e.key === '[') {
      e.preventDefault();
      removeIndentation(textarea, 2);
    }
  }
}

// Event listeners for code editor
document.addEventListener('DOMContentLoaded', () => {
  // Close editor on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('codeEditorModal').classList.contains('active')) {
      closeCodeEditor();
    }
  });
  
  // Close editor on backdrop click
  document.getElementById('codeEditorModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
      closeCodeEditor();
    }
  });
  
  // Editor button event listeners
  document.getElementById('closeCodeEditor').addEventListener('click', closeCodeEditor);
  document.getElementById('copyCodeBtn').addEventListener('click', copyCodeFromEditor);
  document.getElementById('downloadCodeBtn').addEventListener('click', downloadCodeFromEditor);
  document.getElementById('formatCodeBtn').addEventListener('click', formatCodeInEditor);
  document.getElementById('saveCodeBtn').addEventListener('click', saveCodeFromEditor);
  
  // Indentation button event listeners
  document.getElementById('indentBtn').addEventListener('click', () => {
    const textarea = document.getElementById('codeEditorTextarea');
    insertIndentation(textarea, 2);
    textarea.focus();
  });
  
  document.getElementById('unindentBtn').addEventListener('click', () => {
    const textarea = document.getElementById('codeEditorTextarea');
    removeIndentation(textarea, 2);
    textarea.focus();
  });
  
  // Update counts on textarea change
  document.getElementById('codeEditorTextarea').addEventListener('input', updateEditorCounts);
  
  // Add indentation keyboard shortcuts
  document.getElementById('codeEditorTextarea').addEventListener('keydown', handleEditorKeydown);
  
  // Add editor buttons to existing code blocks
  addEditorButtonToCodeBlocks();
});

// Override the renderMessages function to add editor buttons to new code blocks
const originalRenderMessages = renderMessages;
renderMessages = function() {
  originalRenderMessages.call(this);
  // Add editor buttons to any new code blocks
  setTimeout(() => {
    addEditorButtonToCodeBlocks();
  }, 100);
};
