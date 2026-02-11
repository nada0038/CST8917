# Database Choice: Azure Table Storage

## Selected Database
**Azure Table Storage**

## Justification

I chose Azure Table Storage for this project for the following reasons:

1. **Cost-Effective**: Table Storage is significantly cheaper than Cosmos DB, making it ideal for a lab project with limited budget.

2. **Simple NoSQL Storage**: The text analysis results are simple key-value pairs with JSON data. Table Storage's PartitionKey/RowKey model is sufficient for storing and retrieving these records.

3. **Easy Integration**: Azure Functions has excellent SDK support for Table Storage through the azure-data-tables library, making implementation straightforward.

4. **No Complex Queries Needed**: The application only needs to store analyses and retrieve recent history - no complex queries or indexing required.

## Alternatives Considered

- **Azure Cosmos DB**: More powerful but significantly more expensive. Overkill for this simple use case.
- **Azure SQL Database**: Requires schema definition and is optimized for relational data, not JSON documents.
- **Azure Blob Storage**: Good for file storage but lacks querying capabilities needed for the history endpoint.

## Implementation

The Table Storage schema uses:
- **PartitionKey**: "Analysis" (groups all analyses together)
- **RowKey**: Unique UUID for each analysis
- **Additional fields**: OriginalText, WordCount, AnalyzedAt, FullAnalysisJson
