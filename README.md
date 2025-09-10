# Intelligent Email Agent

An intelligent AI-powered agent for Gmail that leverages Python and Google Gemini to automatically classify, manage, and reply to unread emails. This project helps users automate email triage and response, saving time and enhancing productivity.

---

## Features

- **Automatic Email Classification:**  
  Uses AI to categorize incoming emails (e.g., Promotions, Updates, Personal, Important).

- **Smart Auto-Reply:**  
  Drafts and sends contextually appropriate replies to unread emails.

- **Custom Email Management:**  
  Can archive, flag, or delete emails based on custom rules or AI predictions.

- **Google Gemini Integration:**  
  Integrates with Google Gemini LLM for advanced natural language understanding and generation.

- **Configurable Workflows:**  
  Adapt rules and actions to fit your personal or organizational needs.

---

## Architecture

- **Python-based Core:**  
  Handles Gmail API interactions, email parsing, and communication with Gemini.

- **Gmail API:**  
  Securely connects to a Gmail account using OAuth2 for reading and managing emails.

- **Gemini API:**  
  Sends email content/context to Gemini for classification and reply generation.

---

## Getting Started

### Prerequisites

- Python 3.8 or newer
- Gmail API enabled and OAuth2 credentials (see setup instructions)
- Google Gemini API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tamilmani-murugan/intelligent-email-agent.git
   cd intelligent-email-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Gmail API credentials:**
   - Visit [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project, enable the Gmail API, and create OAuth2 credentials.
   - Download the credentials JSON and place it in the project directory as `credentials.json`.

4. **Set up Gemini API credentials:**
   - Obtain an API key from [Google Gemini](https://ai.google.dev/gemini-api/docs).
   - Store the API key in your environment, e.g.:
     ```bash
     export GEMINI_API_KEY='your-api-key'
     ```

---

## Usage

1. **Run the agent:**
   ```bash
   python main.py
   ```

2. **Configuration:**
   - Customize rules, labels, or response templates in `config.yaml` (if provided).
   - To run periodically, schedule with cron or Windows Task Scheduler.

---

## Example Code

```python
from intelligent_email_agent import Agent

agent = Agent()
agent.process_unread_emails()
```

---

## Project Structure

```
intelligent-email-agent/
├── main.py                  # Entry point for running the agent
├── agent.py                 # Core logic for email fetching, classifying, and replying
├── gmail_service.py         # Gmail API authentication and operations
├── gemini_service.py        # Gemini API integration
├── config.yaml              # Configuration (rules, thresholds, etc)
├── requirements.txt         # Python dependencies
├── credentials.json         # Your Gmail OAuth2 credentials (DO NOT COMMIT)
└── README.md                # Project documentation
```

---

## Security & Privacy

- Your credentials (`credentials.json` and Gemini API key) are kept local and never shared.
- The agent acts only on your Gmail account as authorized via OAuth2.
- Always keep your API keys and OAuth credentials secure.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Open a pull request describing your changes.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [Google Gmail API](https://developers.google.com/gmail/api)
- [Google Gemini](https://ai.google.dev/gemini-api/docs)

---

## Contact

For questions, feature requests, or support:  
Open an issue or contact [tamilmani-murugan](https://github.com/tamilmani-murugan).
