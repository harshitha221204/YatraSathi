/* ==========================================================
   YatraSathi Voice + Smart Assistant
   Works with the existing translator and chatbot on home.html
========================================================== */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        const root = document.getElementById("ysAssistant");
        const panel = document.getElementById("ysAssistantPanel");
        const toggleButton = document.getElementById("ysAssistantButton");
        const assistantLanguage = document.getElementById("assistantLanguage");
        const mainLanguage = document.getElementById("languageSelector");
        const voiceCommandButton = document.getElementById("ysVoiceCommand");
        const speakButton = document.getElementById("ysSpeakPage");
        const stopButton = document.getElementById("ysStopSpeaking");
        const chatButton = document.getElementById("ysOpenChat");
        const weatherButton = document.getElementById("ysOpenWeather");
        const nearMeButton = document.getElementById("ysOpenNearMe");
        const status = document.getElementById("ysVoiceStatus");

        if (!root || !panel || !toggleButton) {
            return;
        }

        function currentLanguage() {
            return (assistantLanguage && assistantLanguage.value) ||
                   (mainLanguage && mainLanguage.value) ||
                   localStorage.getItem("yatrasathi_language") ||
                   "en";
        }

        function setStatus(message) {
            if (status) status.textContent = message;
        }

        function openPanel() {
            panel.classList.add("active");
            toggleButton.setAttribute("aria-expanded", "true");
        }

        function closePanel() {
            panel.classList.remove("active");
            toggleButton.setAttribute("aria-expanded", "false");
        }

        toggleButton.setAttribute("aria-expanded", "false");
        toggleButton.addEventListener("click", function (event) {
            event.stopPropagation();
            panel.classList.toggle("active");
            toggleButton.setAttribute(
                "aria-expanded",
                panel.classList.contains("active") ? "true" : "false"
            );
        });

        document.addEventListener("click", function (event) {
            if (!root.contains(event.target)) closePanel();
        });

        panel.addEventListener("click", function (event) {
            event.stopPropagation();
        });

        /* ---------------- Language sync + website translation ---------------- */
        const savedLanguage = localStorage.getItem("yatrasathi_language") || "en";
        if (assistantLanguage) assistantLanguage.value = savedLanguage;

        if (assistantLanguage) {
            assistantLanguage.addEventListener("change", function () {
                const language = this.value;
                localStorage.setItem("yatrasathi_language", language);

                if (mainLanguage) {
                    mainLanguage.value = language;
                    mainLanguage.dispatchEvent(new Event("change", { bubbles: true }));
                } else if (typeof window.translatePage === "function") {
                    window.translatePage(language);
                }

                const messages = {
                    en: "Website language changed to English.",
                    hi: "वेबसाइट की भाषा हिन्दी कर दी गई है।",
                    kn: "ವೆಬ್‌ಸೈಟ್ ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಿಸಲಾಗಿದೆ."
                };
                setStatus(messages[language] || messages.en);
            });
        }

        if (mainLanguage) {
            mainLanguage.addEventListener("change", function () {
                if (assistantLanguage) assistantLanguage.value = this.value;
            });
        }

        /* ---------------- Speak the visible page ---------------- */
        function speakPage() {
            if (!("speechSynthesis" in window)) {
                setStatus("Speech output is not supported in this browser.");
                return;
            }

            window.speechSynthesis.cancel();

            const source = document.querySelector("main") || document.body;
            const readable = source.cloneNode(true);
            readable.querySelectorAll(
                "script, style, .ys-assistant, #ys-chat-window, #ys-chat-button"
            ).forEach(function (item) { item.remove(); });

            let text = (readable.innerText || readable.textContent || "")
                .replace(/\s+/g, " ")
                .trim();

            if (!text) {
                setStatus("There is no readable text on this page.");
                return;
            }

            // Keep browser speech responsive on long pages.
            text = text.slice(0, 4500);

            const utterance = new SpeechSynthesisUtterance(text);
            const language = currentLanguage();
            utterance.lang = language === "kn" ? "kn-IN" : language === "hi" ? "hi-IN" : "en-IN";
            utterance.rate = 0.95;
            utterance.pitch = 1;
            utterance.volume = 1;

            utterance.onstart = function () { setStatus("YatraSathi is reading this page..."); };
            utterance.onend = function () { setStatus("Finished speaking."); };
            utterance.onerror = function () { setStatus("Speech could not be played. Try again."); };

            window.speechSynthesis.speak(utterance);
        }

        if (speakButton) speakButton.addEventListener("click", speakPage);

        if (stopButton) {
            stopButton.addEventListener("click", function () {
                if ("speechSynthesis" in window) window.speechSynthesis.cancel();
                setStatus("Voice stopped.");
            });
        }

        /* ---------------- Existing chatbot integration ---------------- */
        function openChat(message) {
            const floatingChatButton = document.getElementById("ys-chat-button");
            const chatWindow = document.getElementById("ys-chat-window");
            const input = document.getElementById("ys-message-input");
            const send = document.getElementById("ys-send-button");

            if (chatWindow) {
                // Use the exact class used by the existing chatbot.
                chatWindow.classList.add("ys-open");
            } else if (floatingChatButton) {
                floatingChatButton.click();
            }

            if (message && input) {
                input.value = message;
                input.focus();
                if (send) {
                    setTimeout(function () { send.click(); }, 150);
                }
            } else if (input) {
                input.focus();
            }

            closePanel();
        }

        if (chatButton) chatButton.addEventListener("click", function () { openChat(); });

        if (weatherButton) {
            weatherButton.addEventListener("click", function () {
                window.location.href = root.dataset.weatherUrl;
            });
        }

        if (nearMeButton) {
            nearMeButton.addEventListener("click", function () {
                window.location.href = root.dataset.nearMeUrl;
            });
        }

        /* ---------------- Voice commands ---------------- */
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            if (voiceCommandButton) {
                voiceCommandButton.addEventListener("click", function () {
                    setStatus("Voice commands need Google Chrome or Microsoft Edge.");
                });
            }
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        function commandLanguage() {
            const language = currentLanguage();
            return language === "kn" ? "kn-IN" : language === "hi" ? "hi-IN" : "en-IN";
        }

        function hasAny(text, words) {
            return words.some(function (word) { return text.includes(word); });
        }

        function handleVoiceCommand(transcript) {
            const text = transcript.toLowerCase().trim();
            setStatus("Heard: “" + transcript + "”");

            if (hasAny(text, ["weather", "ಮಳೆ", "ಹವಾಮಾನ", "मौसम", "बारिश"])) {
                window.location.href = root.dataset.weatherUrl;
                return;
            }

            if (hasAny(text, ["near me", "current location", "my location", "ಹತ್ತಿರ", "ನನ್ನ ಸ್ಥಳ", "पास", "लोकेशन"])) {
                window.location.href = root.dataset.nearMeUrl;
                return;
            }

            if (hasAny(text, ["explore", "destinations", "places", "ಅನ್ವೇಷಿಸಿ", "ಸ್ಥಳಗಳು", "घूमने", "स्थान"])) {
                window.location.href = root.dataset.exploreUrl;
                return;
            }

            if (hasAny(text, ["plan trip", "planner", "itinerary", "ಪ್ರವಾಸ ಯೋಜನೆ", "यात्रा योजना"])) {
                window.location.href = root.dataset.plannerUrl;
                return;
            }

            if (hasAny(text, ["login", "ಲಾಗಿನ್", "लॉगिन"])) {
                window.location.href = root.dataset.loginUrl;
                return;
            }

            if (hasAny(text, ["speak page", "read page", "ಓದಿ", "पढ़ो", "पढ़ो"])) {
                speakPage();
                return;
            }

            if (hasAny(text, ["stop speaking", "stop voice", "ನಿಲ್ಲಿಸು", "बंद करो"])) {
                if ("speechSynthesis" in window) window.speechSynthesis.cancel();
                setStatus("Voice stopped.");
                return;
            }

            // Anything else is treated as a tourism question for the existing chatbot.
            openChat(transcript);
        }

        if (voiceCommandButton) {
            voiceCommandButton.addEventListener("click", function () {
                recognition.lang = commandLanguage();
                try {
                    recognition.start();
                    toggleButton.classList.add("listening");
                    setStatus("Listening... speak now.");
                } catch (error) {
                    setStatus("Voice recognition is already listening.");
                }
            });
        }

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            handleVoiceCommand(transcript);
        };

        recognition.onend = function () {
            toggleButton.classList.remove("listening");
        };

        recognition.onerror = function (event) {
            toggleButton.classList.remove("listening");
            if (event.error === "not-allowed") {
                setStatus("Microphone permission is blocked. Allow microphone access in the browser.");
            } else if (event.error === "no-speech") {
                setStatus("No speech was detected. Try again.");
            } else {
                setStatus("Voice recognition error: " + event.error);
            }
        };

        openPanel();
        setTimeout(closePanel, 1400);
    });
})();
