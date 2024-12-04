document.addEventListener('DOMContentLoaded', (event) => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesDiv = document.getElementById('messages');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value;

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        const newMessage = document.createElement('div');
        newMessage.textContent = data.response;
        newMessage.classList.add('message');
        messagesDiv.appendChild(newMessage);

        messageInput.value = '';
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom
    });
});