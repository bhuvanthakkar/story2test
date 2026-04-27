# 🚀 Story2Test - Automation Engine

> Transform Jira stories into fully automated test execution pipelines using AI.

Story2Test is an autonomous QA automation engine that converts user stories from Jira into executable Playwright tests, runs them, and posts results back to the same story, all with zero manual scripting.

---

## 🧠 What Problem Does This Solve?

Early-stage startups and new projects often struggle with:

* Manual test case creation slowing down development
* Lack of automation coverage in early phases
* Inconsistent QA processes
* Time spent writing and maintaining test scripts

**Story2Test eliminates this gap by automating the entire QA lifecycle directly from your Jira stories.**

---

## 📌 Prerequisites

Before Story2Test starts processing a Jira story, the following condition must be met:

* Once development of a UI web application feature is completed, the Jira story must be labeled as **`AUTO_QA`**

### 🔖 What does `AUTO_QA` mean?

`AUTO_QA` indicates that:

* Development is complete
* The feature is ready for testing
* The story contains sufficient details for test generation

### ⚡ Trigger Mechanism

Story2Test begins execution **only when a story is tagged with `AUTO_QA`**.

If the label is missing:

* The pipeline will not start
* The story will be ignored by the automation engine

---

## ⚙️ How It Works

1. Once the development is completed > user creates a story in Jira for the testing by adding all the necessary description
2. Story is marked with `AUTO_QA` label
3. Story2Test detects the eligible story
4. AI analyzes the description and extracts requirements
5. Test cases are automatically generated
6. Test cases are converted into Playwright scripts (Python)
7. Tests are executed locally
8. Results are posted back to the Jira story as a comment
9. Story is moved to **Done** (if successful)

---

## 🔁 Intelligent Validation Flow

* If the story description is incomplete or unclear:

  * AI stops execution
  * Posts a comment in Jira requesting more details
  * Prevents invalid or low-quality test generation

---

## ✨ Key Features

* 🤖 AI-powered test case generation using Claude
* ⚡ Zero manual scripting required
* 🔍 End-to-end traceability from story to test results
* 🔁 Retry and failure handling with actionable feedback
* 📝 Rich formatted reporting directly in Jira comments
* 🧩 Seamless Jira integration

---

## 🛠 Tech Stack

* **AI Engine:** Claude API
* **Automation Framework:** Playwright (Python)
* **Backend:** Python
* **Integration:** Jira REST API
* **Execution:** Local machine (Windows supported)

---

## 📦 Installation

```bash
git clone <your-repo-url>
cd story2test
```

### 🔑 Environment Setup

Create a `.env` file and add:

```
JIRA_API_KEY=your_jira_api_key
ANTHROPIC_API_KEY=your_claude_api_key
APP_URL=https://www.saucedemo.com
& more, refer .env.example for more info!
```

Ensure your Claude account has sufficient balance:
https://platform.claude.com/

---

## ▶️ Running the Engine

```bash
python orchestrator.py
```

The system will start monitoring Jira stories and trigger the pipeline automatically.

---

## 🧾 Output

* Test results are posted as **comments on the Jira story**

Includes:

* Pass / Fail status
* Failure reasons
* AI-generated insights
* Suggested fixes (if applicable)

---

## ⚠️ Limitations

* Requires well-structured and detailed Jira stories
* Incomplete descriptions will halt execution
* Currently supports local execution only
* Windows environment supported (macOS & GitHub Actions support planned)

---

## 🛣 Roadmap

* 🚀 GitHub Actions integration (CI/CD support)
* 🧠 Self-healing test scripts
* 🍎 macOS execution support
* 🔄 Enhanced AI validation and smarter retries

---

## 🎯 Target Users

* Startups building products from scratch
* Teams with little to no QA automation
* Developers who want instant test coverage from requirements

---

## 💡 Vision

To fully automate the journey from:

**requirement → test → execution → feedback**

Making QA effortless and integrated into everyday development workflows.

---

## 🤝 Contributing

Contributions, ideas, and improvements are welcome. Feel free to open issues or submit pull requests.

---

## 📬 Feedback

If the AI asks for better descriptions, it means your story needs clarity 😉
