# =============================================================================
# IMPORTS - Libraries we need for our function
# =============================================================================
import azure.functions as func  # Azure Functions SDK - required for all Azure Functions
import logging                  # Built-in Python library for printing log messages
import json                     # Built-in Python library for working with JSON data
import re                       # Built-in Python library for Regular Expressions (pattern matching)
import os                       # Built-in Python library for environment variables
import uuid                     # Built-in Python library for generating unique IDs
from datetime import datetime   # Built-in Python library for working with dates and times
from azure.data.tables import TableClient # Azure Table Storage SDK

# =============================================================================
# CREATE THE FUNCTION APP
# =============================================================================
# This creates our Function App with anonymous access (no authentication required)
# Think of this as the "container" that holds all our functions
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# We'll connect to the database lazily (only when needed)
table_client = None

def get_table_client():
    global table_client
    if not table_client:
        connection_string = os.environ.get("TABLE_STORAGE_CONNECTION_STRING")
        if connection_string:
            try:
                table_client = TableClient.from_connection_string(
                    conn_str=connection_string,
                    table_name="Analyses"
                )
                # Create the table if it doesn't exist
                try:
                    table_client.create_table()
                except Exception:
                    pass # Table likely already exists
            except Exception as e:
                logging.error(f"Error connecting to Table Storage: {e}")
    return table_client

# =============================================================================
# DEFINE THE TEXT ANALYZER FUNCTION
# =============================================================================
# The @app.route decorator tells Azure: "When someone visits /api/TextAnalyzer, run this function"
# This is called a "decorator" - it adds extra behavior to our function
@app.route(route="TextAnalyzer")
def TextAnalyzer(req: func.HttpRequest) -> func.HttpResponse:
    """
    This function analyzes text and returns statistics about it.

    Parameters:
        req: The incoming HTTP request (contains the text to analyze)

    Returns:
        func.HttpResponse: JSON response with analysis results
    """

    # Log a message so we can see in Azure Portal when the function is called
    logging.info('Text Analyzer API was called!')

    # =========================================================================
    # STEP 1: GET THE TEXT INPUT
    # =========================================================================
    # First, try to get 'text' from the URL query string
    # Example URL: /api/TextAnalyzer?text=Hello world
    # req.params.get('text') would return "Hello world"
    text = req.params.get('text')

    # If text wasn't in the URL, try to get it from the request body (JSON)
    if not text:
        try:
            # Try to parse the request body as JSON
            # Example body: {"text": "Hello world"}
            req_body = req.get_json()
            text = req_body.get('text')
        except ValueError:
            # If the body isn't valid JSON, just continue (text stays None)
            pass

    # =========================================================================
    # STEP 2: ANALYZE THE TEXT (if text was provided)
    # =========================================================================
    if text:
        # ----- Word Analysis -----
        # split() breaks the text into a list of words
        # "Hello world" becomes ["Hello", "world"]
        words = text.split()

        # len() counts items in a list
        # ["Hello", "world"] has length 2
        word_count = len(words)

        # ----- Character Analysis -----
        # len() on a string counts characters (including spaces)
        # "Hello world" has 11 characters
        char_count = len(text)

        # replace(" ", "") removes all spaces, then we count
        # "Hello world" becomes "Helloworld" (10 characters)
        char_count_no_spaces = len(text.replace(" ", ""))

        # ----- Sentence Analysis -----
        # re.findall() finds all matches of a pattern
        # r'[.!?]+' means: find any sequence of periods, exclamation marks, or question marks
        # "Hello! How are you?" returns ['!', '?'] (2 sentences)
        # The "or 1" means: if no punctuation found, assume at least 1 sentence
        sentence_count = len(re.findall(r'[.!?]+', text)) or 1

        # ----- Paragraph Analysis -----
        # Paragraphs are separated by blank lines (two newlines: \n\n)
        # split('\n\n') breaks text at blank lines
        # We filter out empty paragraphs with "if p.strip()"
        # strip() removes whitespace - empty strings become "" which is False
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])

        # ----- Reading Time Calculation -----
        # Average reading speed is about 200 words per minute
        # round(x, 1) rounds to 1 decimal place
        # 100 words / 200 wpm = 0.5 minutes
        reading_time_minutes = round(word_count / 200, 1)

        # ----- Average Word Length -----
        # Total characters (no spaces) divided by number of words
        # We check "if word_count > 0" to avoid dividing by zero
        avg_word_length = round(char_count_no_spaces / word_count, 1) if word_count > 0 else 0

        # ----- Find Longest Word -----
        # max() finds the largest item
        # key=len means "compare words by their length"
        # max(["Hi", "Hello", "Hey"], key=len) returns "Hello"
        longest_word = max(words, key=len) if words else ""

        # =====================================================================
        # STEP 3: BUILD THE RESPONSE
        # =====================================================================
        # Create a Python dictionary with all our analysis results
        # This will be converted to JSON format
        
        # Current timestamp
        timestamp = datetime.utcnow().isoformat()
        unique_id = str(uuid.uuid4())

        # For Table Storage, we flatten the structure a bit because it doesn't support nested JSON as well as Cosmos
        # However, we can store the complex analysis as a JSON string if we want, or individual columns.
        # For simplicity and queryability, we'll store key metrics as columns and the full result as a JSON string if needed.
        
        # Data entity for Table Storage
        # Must have PartitionKey and RowKey
        entity = {
            "PartitionKey": "Analysis",
            "RowKey": unique_id,
            "OriginalText": text,
            "WordCount": word_count,
            "AnalyzedAt": timestamp,
            # We can store the full analysis JSON as a string to preserve structure
            "FullAnalysisJson": json.dumps({
                "wordCount": word_count,
            "characterCount": char_count,
            "characterCountNoSpaces": char_count_no_spaces,
            "sentenceCount": sentence_count,
            "paragraphCount": paragraph_count,
            "averageWordLength": avg_word_length,
            "longestWord": longest_word,
            "readingTimeMinutes": reading_time_minutes
            })
        }

        # Response structure (same as before for the API user)
        response_data = {
            "id": unique_id,
            "originalText": text,
            "analysis": {
                "wordCount": word_count,
                "characterCount": char_count,
                "characterCountNoSpaces": char_count_no_spaces,
                "sentenceCount": sentence_count,
                "paragraphCount": paragraph_count,
                "averageWordLength": avg_word_length,
                "longestWord": longest_word,
                "readingTimeMinutes": reading_time_minutes
            },
            "metadata": {
                "analyzedAt": timestamp,
                "textPreview": text[:100] + "..." if len(text) > 100 else text
            }
        }

        # Save to Table Storage (if configured)
        try:
            tc = get_table_client()
            if tc:
                tc.create_entity(entity=entity)
        except Exception as e:
            logging.error(f"Failed to save to Table Storage: {e}")

        # Return a successful HTTP response
        # json.dumps() converts Python dictionary to JSON string
        # indent=2 makes the JSON nicely formatted (2 spaces per indent level)
        # mimetype tells the browser "this is JSON data"
        # status_code=200 means "OK - Success"
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            mimetype="application/json",
            status_code=200
        )

    # =========================================================================
    # STEP 4: HANDLE MISSING TEXT (Error Response)
    # =========================================================================
    else:
        # If no text was provided, return helpful instructions
        instructions = {
            "error": "No text provided",
            "howToUse": {
                "option1": "Add ?text=YourText to the URL",
                "option2": "Send a POST request with JSON body: {\"text\": \"Your text here\"}",
                "example": "https://your-function-url/api/TextAnalyzer?text=Hello world"
            }
        }

        # Return an error response
        # status_code=400 means "Bad Request - client made an error"
        return func.HttpResponse(
            json.dumps(instructions, indent=2),
            mimetype="application/json",
            status_code=400
        )

# =============================================================================
# DEFINE THE HISTORY ENDPOINT
# =============================================================================
@app.route(route="GetAnalysisHistory", auth_level=func.AuthLevel.ANONYMOUS)
def GetAnalysisHistory(req: func.HttpRequest) -> func.HttpResponse:
    """
    Retrieves past analysis results from Table Storage.
    """
    logging.info('GetAnalysisHistory processed a request.')

    try:
        tc = get_table_client()
        if not tc:
             return func.HttpResponse(
                json.dumps({"error": "Database not configured"}, indent=2),
                mimetype="application/json",
                status_code=500
            )
        
        # Get 'limit' from query parameter, default to 10
        limit = req.params.get('limit', '10')
        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        # Query Table Storage
        # We query by PartitionKey and sort locally because Table Storage doesn't support server-side sorting easily
        # For a lab, fetching top N and sorting in Python is fine
        entities = list(tc.query_entities(query_filter="PartitionKey eq 'Analysis'"))
        
        # Sort by AnalyzedAt descending
        entities.sort(key=lambda x: x.get('AnalyzedAt', ''), reverse=True)
        
        # Take the top 'limit'
        recent_items = entities[:limit]
        
        # Clean up for response (remove system properties, parse JSON)
        results = []
        for item in recent_items:
            try:
                 # Try to parse the stored JSON for the full details
                analysis_details = json.loads(item.get("FullAnalysisJson", "{}"))
            except:
                analysis_details = {}

            results.append({
                "id": item.get("RowKey"),
                "originalText": item.get("OriginalText"),
                "analyzedAt": item.get("AnalyzedAt"),
                "analysis": analysis_details
            })

        return func.HttpResponse(
            json.dumps({"count": len(results), "results": results}, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error retrieving history: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, indent=2),
            mimetype="application/json",
            status_code=500
        )

