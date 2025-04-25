# Credit-Recommendation Chatbot

A conversational assistant that recommends the best U.S. credit card for a user based on credit score, income bracket, length of employment, and DTI ratio. Built with Rasa 3, Python, and includes a lightweight eligibility classifier and a custom web interface.

## Setup (One-Time)

1.  **Clone/Download:** Get the project files onto your local machine.
2.  **Navigate to Project Root:** Open your terminal and change into the project's root directory:
    ```bash
    cd <path-to-your-project>/Credit-Recommendation-Chatbot
    ```
3.  **Create Virtual Environment:** Create a dedicated Python environment for the project (requires Python 3.9+):
    ```bash
    python3 -m venv venv
    ```
4.  **Activate Virtual Environment:**
    * On macOS/Linux: `source venv/bin/activate`
    * On Windows (Git Bash/WSL): `source venv/bin/activate`
    * On Windows (CMD/PowerShell): `.\venv\Scripts\activate`
5.  **Install Dependencies:** Install all required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
6.  **Install Honcho (for Option 3 Running):** Install the process manager:
    ```bash
    pip install honcho
    ```
    *(Optional but recommended: Add `honcho` to `requirements.txt` by running `pip freeze > requirements.txt` after installing it).*
7.  **Create Procfile (for Option 3 Running):** In the project root directory (`<path-to-your-project>/Credit-Recommendation-Chatbot`), create a file named exactly `Procfile` (no extension) with the following content:
    ```Procfile
    # Procfile for Rasa Credit Bot
    # Run with: honcho start (after activating venv)

    actions: rasa run actions
    rasa: rasa run --enable-api --cors "*"
    webui: python3 -m http.server 8080 --directory ./chatbot-ui
    ```
8.  **Train Rasa Model:** Train the NLU and Core models (needed initially and after changing NLU/domain/stories/config):
    ```bash
    rasa train
    ```

## Running the Chatbot

You have three options to interact with the bot:

### Option 1: Custom Web Interface (Using Honcho - Recommended)

This uses the graphical chat interface and manages all server processes in **one** terminal window using Honcho (requires Setup steps 6 & 7 to be completed).

1.  **Navigate to Project Root:**
    ```bash
    cd <path-to-your-project>/Credit-Recommendation-Chatbot
    ```
2.  **Activate Virtual Environment:**
    ```bash
    source venv/bin/activate
    ```
3.  **Start All Processes:**
    ```bash
    honcho start
    ```
    * Honcho will run the `actions`, `rasa`, and `webui` commands defined in your `Procfile`. You will see interleaved logs from all processes.

4.  **Access the UI:**
    * Open your web browser and go to: `http://localhost:8080` (or the port specified in your `Procfile` for `webui`).

### Option 2: Command Line Interface (`rasa shell`)

This uses Rasa's built-in text interface. You'll need **two** separate terminal windows/tabs.

1.  **Terminal 1: Start Action Server**
    * Navigate to the project root.
    * Activate the virtual environment.
    * Run: `rasa run actions`
    * *Keep this terminal running.*

2.  **Terminal 2: Start Rasa Shell**
    * Navigate to the project root.
    * Activate the virtual environment.
    * Run: `rasa shell`
    * *Interact with the bot in this terminal.*

### Option 3: Custom Web Interface (Manual Terminals)

This uses the graphical chat interface in your browser, requiring manual management of three terminals.

1.  **Terminal 1: Start Action Server**
    * Navigate to the project root.
    * Activate the virtual environment.
    * Run: `rasa run actions`
    * *Keep this terminal running.*

2.  **Terminal 2: Start Rasa Server (API Enabled)**
    * Navigate to the project root.
    * Activate the virtual environment.
    * Run: `rasa run --enable-api --cors "*"`
    * *Keep this terminal running.*

3.  **Terminal 3: Serve Frontend UI**
    * Navigate to the UI subdirectory: `cd <path-to-your-project>/Credit-Recommendation-Chatbot/chatbot-ui`
    * Start Python's simple web server: `python3 -m http.server 8080`
        * *(If port 8080 is busy, try another port).*
    * *Keep this terminal running.*

4.  **Access the UI:**
    * Open your web browser and go to: `http://localhost:8080` (or the port you used).


**Stopping the Servers:**

* If using Option 1 or 2, press `Ctrl + C` in each terminal window.
* If using Option 3 (Honcho), press `Ctrl + C` in the single terminal where `honcho start` is running.

## Docker Instructions (Optional)

If you prefer using Docker:

1.  **Build the Image:**
    ```bash
    docker build -t credit-bot .
    ```
2.  **Run the Container:** This runs Rasa and the Action Server together.
    ```bash
    # Exposes the Rasa server port 5005
    docker run -p 5005:5005 credit-bot
    ```
   *Note: This default Docker setup runs the Rasa server. To interact, you would typically use the REST API (e.g., via the custom web UI pointing to `http://localhost:5005`, or tools like Postman). It doesn't automatically serve the custom UI files; modifying the Docker setup would be needed for that.*

## What to Ask?

See the `InputExamples.md` file for a comprehensive list of example inputs, or try these:

**Starting the Recommendation:**

* "Can you recommend me a credit card?"
* "I need help finding a card"
* "Suggest some cards"

*(The bot will then ask for your income, credit score, DTI, and employment length.)*

**After Getting Recommendations:**

*(Replace `[Card Name]` with a name recommended by the bot)*

* **General Details:**
    * "Tell me more about the first one."
    * "What are the details for the second card?"
    * "More info on the last recommendation."
    * "Tell me about [Card Name]."
* **Specific Features (Examples):**
    * "What is the signup bonus for the first one?"
    * "Does the second card have foreign transaction fees?" (Try typos like "forigen transaciton" too!)
    * "Tell me about the travel insurance on the third recommendation."
    * "What are the rewards details for [Card Name]?" (Try "reward details" too!)
    * "Is there an intro APR for balance transfers on the second one?"
    * "What's the annual fee for the last card?"
    * "What score do I need for the first card?"
    * "Any introductory APR on the second recommendation?"
    * "Who issues the [Card Name]?"
    * "What is the welcome offer for the first card?"
    * "Does [Card Name] have cell phone protection?"
    * "How do I apply for the second card?"
    * "Any bonus on the first card?"
    * "Interest rate for the second option?"
    * "Does the last one cost anything per year?"
* **Ending:**
    * "Thanks!"
    * "Goodbye"