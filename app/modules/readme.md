# HR recruiter agent 🚀

This project is supporting a recruitment process to a Python developer role.

## 🌟 Key Features

- **Schedule:** Schedule a call with the candidate based on his and the recruiter availability.
- **Info:** Supply information about the Python developer rule to the candidate.
- **Exit:** Decides if the conversation should be ended or continued.

## 🛠️ Tech Stack & Prerequisites

List the main languages, frameworks, or tools required to run your project:
- **Language:** Python 3.12+ 
- **Framework:** Langchain
- **API Dependencies:** 

## 🚀 Getting Started

Follow these steps to set up the project locally.

### 1. Clone the Repository
```bash
git clone https://github.com/ronweinberg1-web/New-Repository.git


### 2. Prepare the DB

Connect to the DB and run the following scripts:
1. db_Tech.sql - will create the tech DB tech and Schedule table
2. .\app\modules\prepDB.sql - creates a view to be used by the Schedule agent, and update the Schedule data to current dates
3. Create a DB user to be used later on when connecting to the database, parameters will be set in the .env file

### 3. Prepare the .env file

The following parameters needs to be set:

OPENAI_API_KEY - the KEY to Open AI API 
DB_SERVER - the DB server name
DATABASE - the DB name, i.e. tech
DRIVER - the driver to be used, i.e. ODBC+Driver+17+for+SQL+Server
DB_USERNAME - the user that was set in the DB 
DB_PASSWORD - the password set for the DB user


### 4. Run the project
```bash
cd New-Repository
cd .\app\modules\
streamlit run .\Streamlit1.py
