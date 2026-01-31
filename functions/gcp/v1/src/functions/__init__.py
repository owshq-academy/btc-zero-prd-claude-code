"""Cloud Run functions for the invoice processing pipeline.

Functions:
- tiff_to_png: Convert TIFF invoices to PNG format
- invoice_classifier: Classify vendor type and validate quality
- data_extractor: Extract structured data using Gemini
- bigquery_writer: Persist extracted data to BigQuery
- dlq_processor: Handle failed messages from dead-letter queues
"""
