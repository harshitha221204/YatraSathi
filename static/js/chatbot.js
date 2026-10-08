document.addEventListener("DOMContentLoaded", function () {

    const chatbotButton = document.getElementById("chatbotButton");
    const chatbotBox = document.getElementById("chatbotBox");
    const closeChatbot = document.getElementById("closeChatbot");

    const chatMessages = document.getElementById("chatMessages");
    const chatInput = document.getElementById("chatInput");
    const sendButton = document.getElementById("sendMessage");

    // =========================
    // OPEN CHATBOT
    // =========================
    if (chatbotButton) {
        chatbotButton.addEventListener("click", function () {
            chatbotBox.classList.add("show-chatbot");
            chatInput.focus();
        });
    }

    // =========================
    // CLOSE CHATBOT
    // =========================
    if (closeChatbot) {
        closeChatbot.addEventListener("click", function () {
            chatbotBox.classList.remove("show-chatbot");
        });
    }

    // =========================
    // ADD MESSAGE
    // =========================
    function addMessage(message, type) {

        const messageDiv = document.createElement("div");

        messageDiv.classList.add("chat-message");

        if (type === "user") {
            messageDiv.classList.add("user-message");
        } else {
            messageDiv.classList.add("bot-message");
        }

        messageDiv.textContent = message;

        chatMessages.appendChild(messageDiv);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // =========================
    // SEND MESSAGE
    // =========================
    async function sendMessage() {

        const message = chatInput.value.trim();

        if (message === "") {
            return;
        }

        addMessage(message, "user");

        chatInput.value = "";

        // Show typing
        const typing = document.createElement("div");

        typing.classList.add(
            "chat-message",
            "bot-message",
            "typing-message"
        );

        typing.textContent = "YatraSathi AI is typing...";

        chatMessages.appendChild(typing);

        chatMessages.scrollTop =
            chatMessages.scrollHeight;

        try {

            // Language from your language selector
            const languageSelector =
                document.getElementById("languageSelect");

            const language = languageSelector
                ? languageSelector.value
                : "en";

            const response = await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message,
                    language: language
                })
            });

            const data = await response.json();

            typing.remove();

            if (response.ok) {

                addMessage(
                    data.reply || "I could not generate a response.",
                    "bot"
                );

            } else {

                addMessage(
                    data.reply ||
                    "Sorry, something went wrong.",
                    "bot"
                );
            }

        } catch (error) {

            typing.remove();

            console.error(
                "Chatbot Error:",
                error
            );

            addMessage(
                "Sorry, I could not connect to the YatraSathi assistant.",
                "bot"
            );
        }
    }

    // =========================
    // SEND BUTTON
    // =========================
    if (sendButton) {

        sendButton.addEventListener(
            "click",
            sendMessage
        );
    }

    // =========================
    // ENTER KEY
    // =========================
    if (chatInput) {

        chatInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    event.preventDefault();

                    sendMessage();
                }
            }
        );
    }

});