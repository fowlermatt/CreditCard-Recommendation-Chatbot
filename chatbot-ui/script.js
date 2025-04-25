const chatMessages = document.getElementById('chat-messages');
const chatInputForm = document.getElementById('chat-input-form');
const userInputField = document.getElementById('user-input');
const typingIndicator = document.getElementById('typing-indicator');

const RASA_SERVER_URL = 'http://localhost:5005/webhooks/rest/webhook';

let senderId = localStorage.getItem('rasa-sender-id');
if (!senderId) {
    senderId = generateUUID();
    localStorage.setItem('rasa-sender-id', senderId);
}
console.log("Using senderId:", senderId);

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function displayMessage(text, senderType, contentElement = null) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message', senderType === 'user' ? 'user-message' : 'bot-message');

    if (text) {
        const textDiv = document.createElement('div');
        textDiv.textContent = text;
        messageContainer.appendChild(textDiv);
    }

    if (contentElement) {
        messageContainer.appendChild(contentElement);
    }

    if (text || contentElement) {
        chatMessages.insertBefore(messageContainer, typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        console.warn("Attempted to display an empty message.");
    }

}

async function sendMessageToRasa(messageText) {
    typingIndicator.style.display = 'block';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(RASA_SERVER_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender: senderId,
                message: messageText,
            }),
        });

        typingIndicator.style.display = 'none';

        if (!response.ok) {
            console.error("Rasa server returned an error:", response.status, response.statusText);
            displayMessage("Sorry, I'm having trouble connecting to the server.", 'bot');
            return;
        }

        const botResponses = await response.json();
        console.log("Rasa response:", botResponses);

        if (botResponses && botResponses.length > 0) {
            botResponses.forEach(botMsg => {
                let contentElement = null;

                if (botMsg.image) {
                    contentElement = document.createElement('img');
                    contentElement.src = botMsg.image;
                    contentElement.alt = 'Bot image response';
                    contentElement.classList.add('chat-image');
                    displayMessage(botMsg.text || '', 'bot', contentElement);

                } else if (botMsg.buttons && botMsg.buttons.length > 0) {
                    contentElement = document.createElement('div');
                    contentElement.classList.add('chat-buttons');

                    botMsg.buttons.forEach(button => {
                        const buttonElement = document.createElement('button');
                        buttonElement.textContent = button.title;
                        buttonElement.addEventListener('click', () => {
                            displayMessage(button.title, 'user');
                            sendMessageToRasa(button.payload);
                        });
                        contentElement.appendChild(buttonElement);
                    });
                    displayMessage(botMsg.text || '', 'bot', contentElement);

                } else if (botMsg.text) {
                    displayMessage(botMsg.text, 'bot');
                }
            });
        } else {
            console.log("Received empty response from Rasa.");
            displayMessage("I didn't get a specific response. Can you try rephrasing?", 'bot');
        }

    } catch (error) {
        console.error("Error sending message to Rasa:", error);
        displayMessage("Sorry, there was an error sending your message.", 'bot');
        typingIndicator.style.display = 'none';
    } finally {
         typingIndicator.style.display = 'none';
    }
}

chatInputForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const messageText = userInputField.value.trim();
    if (messageText) {
        displayMessage(messageText, 'user');
        sendMessageToRasa(messageText);
        userInputField.value = '';
    }
});