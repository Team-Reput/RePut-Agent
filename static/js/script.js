document.addEventListener('DOMContentLoaded', () => {
    const chatArea = document.getElementById('chat-area');
    const messagesContainer = document.getElementById('messages-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const suggestions = document.getElementById('suggestions');

    // Auto-focus input
    userInput.focus();

    function scrollToBottom() {
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        // Convert newlines to <br> for bot messages if needed, or just text
        // For bot, we might want to parse markdown later, but for now simple text
        // We can use a simple replacement for newlines
        const formattedText = text.replace(/\n/g, '<br>');
        messageDiv.innerHTML = formattedText;

        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'bot', 'typing-indicator-container');
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    function showContactForm() {
        const formDiv = document.createElement('div');
        formDiv.classList.add('message', 'bot', 'contact-form-container');

        formDiv.innerHTML = `
            <form id="contact-form" class="contact-form">
                <div class="form-group">
                    <label for="contact-name">Name</label>
                    <input type="text" id="contact-name" required placeholder="Your Name">
                </div>
                <div class="form-group">
                    <label for="contact-phone">Phone</label>
                    <input type="tel" id="contact-phone" required placeholder="Your Phone Number">
                </div>
                <div class="form-group">
                    <label for="contact-email">Email (Optional)</label>
                    <input type="email" id="contact-email" placeholder="Your Email">
                </div>
                <button type="submit" class="submit-btn">Submit</button>
            </form>
        `;

        messagesContainer.appendChild(formDiv);
        scrollToBottom();

        const form = formDiv.querySelector('#contact-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = form.querySelector('#contact-name').value;
            const phone = form.querySelector('#contact-phone').value;
            const email = form.querySelector('#contact-email').value;

            // Disable button
            const btn = form.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'Sending...';

            try {
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, phone, email })
                });

                const resData = await response.json();

                if (response.ok) {
                    formDiv.innerHTML = `<div class="success-message"><i class="fa-solid fa-check-circle"></i> Thanks ${name}! Our support team will reach you shortly.</div>`;
                } else {
                    btn.textContent = 'Try Again';
                    btn.disabled = false;
                    alert(resData.error || 'Error sending details');
                }
            } catch (err) {
                console.error(err);
                btn.textContent = 'Try Again';
                btn.disabled = false;
            }
        });
    }

    let chatHistory = [];

    async function sendMessage(text) {
        if (!text.trim()) return;

        // Add user message
        addMessage(text, 'user');
        chatHistory.push({ role: 'user', content: text });
        userInput.value = '';

        // Hide suggestions after first interaction (optional, but cleaner)
        if (suggestions) {
            suggestions.style.display = 'none';
        }

        // Show typing
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    history: chatHistory.slice(-10) // Send last 10 messages context
                })
            });

            const data = await response.json();

            removeTypingIndicator();

            if (data.error) {
                addMessage('Sorry, something went wrong. Please try again.', 'bot');
            } else {
                let answerText = data.answer;
                let showForm = false;

                if (answerText.includes('|||SHOW_CONTACT_FORM|||')) {
                    answerText = answerText.replace('|||SHOW_CONTACT_FORM|||', '');
                    showForm = true;
                }

                addMessage(answerText, 'bot');
                chatHistory.push({ role: 'assistant', content: answerText });

                if (showForm) {
                    showContactForm();
                }

                // Update suggestions if available
                if (data.suggested_questions && data.suggested_questions.length > 0) {
                    const suggestionsDiv = document.getElementById('suggestions');
                    if (suggestionsDiv) {
                        suggestionsDiv.innerHTML = ''; // Clear old suggestions
                        data.suggested_questions.forEach(q => {
                            const btn = document.createElement('button');
                            btn.classList.add('suggestion-chip');
                            btn.textContent = q;
                            btn.onclick = () => window.sendSuggestion(q);
                            suggestionsDiv.appendChild(btn);
                        });
                        suggestionsDiv.style.display = 'flex'; // Make sure it's visible

                        // Scroll to bottom to show suggestions if they are at the bottom
                        setTimeout(scrollToBottom, 100);
                    }
                }
            }

        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('Sorry, I seem to be having trouble connecting. Please check your connection.', 'bot');
        }
    }

    // Event Listeners
    sendBtn.addEventListener('click', () => {
        sendMessage(userInput.value);
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage(userInput.value);
        }
    });

    // Expose for global access (for suggestion chips)
    window.sendSuggestion = (text) => {
        sendMessage(text);
    };

    // Initial greeting
    addMessage("Hello! \nHow can I help you with RePut, sustainability, traceability, or ESG data management?", 'bot');
});
