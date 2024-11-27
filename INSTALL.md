# INSTALL.md

## Getting Started & Installation

### Prerequisites

- Download [Python 3.x](https://www.python.org/downloads/).

### Installation

If you downloaded Python `3.10.12` or any other version, follow these steps to set up the environment:

#### 1. Set up Virtual Environment

- Create a virtual environment:

    ```bash
    python3.10 -m venv test_env
    ```

- Activate the virtual environment:

    - On macOS/Linux:
      ```bash
      source test_env/bin/activate
      ```

    - On Windows:
      ```bash
      test_env\Scripts\activate
      ```

#### 2. Install Dependencies

- Navigate to your project directory and install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

---

## Run Instructions

**To run/test the site locally:**

1. Clone the [WolfTrack GitHub repository](https://github.com/SE-Group-95/WolfTrack7.0).

2. Navigate to the project directory.

    ```bash
    cd WolfTrack7.0
    ```

3. Run the application:

    ```bash
    python app.py
    ```

    or, if you're using `python3`:

    ```bash
    python3 app.py
    ```

4. The site will be hosted locally at:
   ```
    http://127.0.0.1:5000/
   ```

---

## API Setup

### 1. Sign up for RapidAPI and Subscribe to JSearch API

1. Go to the [RapidAPI website](https://rapidapi.com/).
   
2. Search for **JSearch API** in the RapidAPI marketplace.

3. Sign up or log in to your RapidAPI account.

4. Subscribe to the **JSearch API**. You may need to choose a plan (free or paid, depending on your requirements).

5. Once you have subscribed, obtain the **API key** from your RapidAPI dashboard.


### 2. Set Up the Environment Variable for the API Key

1. Export the API key to your environment variables:

    - On macOS/Linux:
      ```bash
      export RAPIDAPI_KEY="YOUR_RAPIDAPI_KEY"
      ```

    - On Windows (Command Prompt):
      ```cmd
      set RAPIDAPI_KEY="YOUR_RAPIDAPI_KEY"
      ```

    - On Windows (PowerShell):
      ```powershell
      $env:RAPIDAPI_KEY="YOUR_RAPIDAPI_KEY"
      ```


### 3. Set up OpenAI API Key

1. Sign up or log in to your [OpenAI account](https://platform.openai.com/signup/).

2. Go to the **API Keys** section in your account settings and create a new API key.

3. Export the API key to your environment variables:

    - On macOS/Linux:
      ```bash
      export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
      ```

    - On Windows (Command Prompt):
      ```cmd
      set OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
      ```

    - On Windows (PowerShell):
      ```powershell
      $env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
      ```

4. To avoid hitting the API quota limits, load at least $5 credit to your OpenAI account for smooth usage.

---

### Troubleshooting

If you encounter an error when trying to download NLTK stopwords, follow these steps:

1. Search for `Install Certificates.command` in your Finder (for macOS).
2. Open the script and run it. This will install the necessary certificates for NLTK.
3. Try running the application again.

---

With these steps, your environment should be set up, and the site should be running locally with the JSearch API integrated.
