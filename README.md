# Text Analyzer - Azure Functions Lab
## Akash Nadackanal Vinod

A simple serverless API that analyzes text and stores results in Azure Table Storage.

## Features

- Analyzes text (word count, character count, sentences, etc.)
- Stores analysis history in Azure Table Storage
- Retrieves past analyses

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `local.settings.json`:
   ```json
   {
     "Values": {
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "TABLE_STORAGE_CONNECTION_STRING": "your-connection-string"
     }
   }
   ```

3. Start the function:
   ```bash
   func start
   ```

## Deployment

```bash
func azure functionapp publish <func-lab1-akash>
```

## Technologies

- Azure Functions (Python 3.11)
- Azure Table Storage
