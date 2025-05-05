import sqlite3
from pathlib import Path
import os
import logging
import re # Import regex for parsing key-value pairs
import json # For debugging parser output if needed

# --- Attempt to import the Markdown parser ---
try:
    # --- CHOOSE AND UNCOMMENT YOUR PARSER LIBRARY ---
    from markdown_to_data import Markdown
    # Or: from some_other_library import MarkdownParser as Markdown # Adapt as needed
    # --- Make sure the chosen library is installed (e.g., pip install markdown-to-data) ---

except ImportError:
    print("ERROR: Required Markdown parsing library not found.")
    print("Please ensure 'markdown_to_data' (or your chosen library) is installed")
    print("and that the script imports it correctly.")
    exit(1) # Exit if the parser is not available

# --- Configuration ---
# Use absolute paths or ensure relative paths are correct from where you RUN the script
MARKDOWN_DIR = Path('../assets/Parks') # Use Path object early
DATABASE_PATH = Path('./national_parks.db') # Use Path object
LOG_DIR = Path('./logs')
LOG_FILE = LOG_DIR / 'processing.log'

# --- Logging Setup ---
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        # Change to INFO for less verbose output once working, DEBUG for detailed tracing
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
        filename=LOG_FILE,
        filemode='w' # Use 'w' (write) mode to start log fresh each run
    )
    # Add a handler to also print INFO level messages to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger().addHandler(console_handler)

except OSError as e:
    print(f"Error setting up logging directory/file: {e}")
    # Fallback basic config if file setup fails
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Function Definitions ---

def setup_database(db_path: Path) -> tuple[sqlite3.Connection | None, sqlite3.Cursor | None]:
    """Connects to DB, enables FKs, creates tables if they don't exist."""
    logging.info(f"Setting up database at: {db_path.resolve()}")
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        con = sqlite3.connect(db_path)
        con.execute("PRAGMA foreign_keys = ON;")
        cur = con.cursor()
        # Combined table creation script
        create_tables_sql = """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS parks (
                park_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS details (
                detail_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                park_ID INTEGER NOT NULL,
                location TEXT,
                established INTEGER,
                size_acres INTEGER,
                ecosystems TEXT,
                unique_feature TEXT,
                description TEXT,
                FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS camping (
                camping_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                park_ID INTEGER NOT NULL,
                type TEXT,
                capacity TEXT,
                amenities TEXT,
                notes TEXT,
                FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS fees (
                fee_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                park_ID INTEGER NOT NULL,
                category TEXT,
                cost TEXT,
                notes TEXT,
                FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS seasons (
                season_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                park_ID INTEGER NOT NULL,
                season_name TEXT,
                dates TEXT,
                characteristics TEXT,
                FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS attractions (
                attraction_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                park_ID INTEGER NOT NULL,
                attraction_name TEXT,
                description TEXT,
                notes TEXT,
                FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE
            );
        """
        cur.executescript(create_tables_sql)
        con.commit()
        logging.info("Database setup complete.")
        return con, cur
    except (sqlite3.Error, OSError) as e:
        logging.error(f"Database setup failed: {e}", exc_info=True)
        if 'con' in locals() and con:
            con.close()
        return None, None

def find_markdown_files(directory: Path) -> list[Path]:
    """Recursively finds all .md files."""
    logging.info(f"Searching for Markdown files in: {directory.resolve()}")
    if not directory.is_dir():
        logging.error(f"Directory not found or not a directory: {directory.resolve()}")
        return []
    files = list(directory.rglob('*.md'))
    logging.info(f"Found {len(files)} Markdown files.")
    return files

def read_file_content(file_path: Path) -> str | None:
    """Reads text content from a file."""
    logging.debug(f"Attempting to read content from: {file_path}")
    try:
        content = file_path.read_text(encoding='utf-8')
        logging.debug(f"Successfully read content from: {file_path}.")
        return content
    except Exception as e:
        logging.error(f"Failed to read file {file_path}: {e}", exc_info=True)
        return None

def parse_markdown_content(markdown_string: str, file_path: Path) -> list | dict | None:
    """Parses Markdown string using the chosen library."""
    logging.debug(f"Attempting to parse Markdown content from: {file_path}")
    try:
        # --- Adapt this based on your parser ---
        # Assumes your parser class is named Markdown and returns data via .md_list
        md_parser = Markdown(markdown_string)
        parsed_data = md_parser.md_list
        # --- End Adapt ---

        if not parsed_data:
            logging.warning(f"Parser returned no data for {file_path}.")
            return None

        # Optional: Uncomment to log the full parsed structure for debugging
        # logging.debug(f"Parser Output Structure for {file_path}:\n{json.dumps(parsed_data, indent=2)}")

        logging.debug(f"Successfully parsed Markdown content from: {file_path}.")
        return parsed_data
    except Exception as e:
        # Catch potential errors during parsing itself
        logging.error(f"Failed to parse Markdown from {file_path}: {e}", exc_info=True)
        return None

def extract_data_from_parsed(parsed_content: list | dict, file_path: Path) -> dict | None:
    """
    Extracts structured data from parsed content.
    Assumes parser returns list of blocks.
    Handles key:value pairs after H1.
    Handles tables assuming item['table'] is a DICTIONARY of COLUMNS (header: [col_data]).
    """
    logging.debug(f"Extracting structured data from parsed content of: {file_path}")

    # Expecting a list of dictionaries from the parser
    if not isinstance(parsed_content, list) or not parsed_content:
        logging.warning(f"Parsed content is not a list or is empty for {file_path}. Cannot extract.")
        return None

    extracted_data = {
        'name': None,
        'details': {},
        'description': '',
        'camping': [],
        'fees': [],
        'seasons': [],
        'attractions': []
    }
    current_section_key = None # Tracks context (camping, fees, etc.) based on H2
    details_parsing_active = False # Flag to capture key:value pairs after H1

    # Maps H2 titles (lowercase) to keys in extracted_data
    section_mapping = {
        "park description": "description",
        "camping information": "camping",
        "fees & passes": "fees",
        "seasonal operations": "seasons",
        "key attractions": "attractions"
    }

    try:
        for item_index, item in enumerate(parsed_content):
            logging.debug(f"Processing parsed item {item_index}: {str(item)[:100]}...") # Log start of item

            if not isinstance(item, dict):
                logging.warning(f"Skipping non-dict item #{item_index} in parsed content: {item}")
                continue

            # --- Header Processing ---
            if 'header' in item:
                header_info = item['header']
                level = header_info.get('level')
                content = header_info.get('content', '').strip()
                logging.debug(f"Item {item_index} is H{level}: {content}")

                if level == 1 and not extracted_data['name']: # Found H1 (Park Name)
                    extracted_data['name'] = content
                    details_parsing_active = True # Start looking for details
                    logging.debug(f"Extracted Park Name: {content}. Activating details parsing.")
                elif level == 2: # Found H2 (Section Header)
                    details_parsing_active = False # Stop looking for details
                    current_section_key = None # Reset current section
                    normalized_content = content.lower()
                    logging.debug(f"Deactivating details parsing. Checking H2 '{content}' against section map.")
                    # Map H2 title to a known section key
                    for title, key in section_mapping.items():
                        if title in normalized_content:
                            current_section_key = key
                            logging.debug(f"Identified section: {content} -> mapped to '{key}'")
                            break
                    if not current_section_key:
                        logging.warning(f"Unmapped H2 header found: {content}")

            # --- Paragraph Processing (Details / Description) ---
            elif 'paragraph' in item:
                text = item['paragraph'].strip()
                logging.debug(f"Item {item_index} is Paragraph: '{text[:80]}...'")

                # If between H1 and first H2, look for **Key:** Value pairs
                if details_parsing_active:
                    logging.debug(f"Attempting to parse details from paragraph: '{text}'")
                    # Regex to capture bolded key and the value after colon
                    match = re.match(r"\*\*(.+?):\*?\*?\s*(.*)", text)
                    if match:
                        key_raw = match.group(1).strip().lower()
                        value = match.group(2).strip()
                        key = key_raw.replace(' ', '_') # Convert to snake_case key
                        logging.debug(f"Regex matched! key_raw='{key_raw}', value='{value}' -> key='{key}'")

                        # Store value, converting specific keys if possible
                        if key == 'established':
                           try: extracted_data['details'][key] = int(value); logging.debug(f"Stored Detail: {key} = {extracted_data['details'][key]}")
                           except ValueError: logging.warning(f"Could not convert 'established' year to int: {value}"); extracted_data['details'][key] = value; logging.debug(f"Stored Detail: {key} = {extracted_data['details'][key]}")
                        elif key == 'size' and 'acres' in value.lower():
                            try: size_str = re.sub(r'[,\sacres]', '', value, flags=re.IGNORECASE); extracted_data['details']['size_acres'] = int(size_str); logging.debug(f"Stored Detail: size_acres = {extracted_data['details']['size_acres']}")
                            except (ValueError, IndexError): logging.warning(f"Could not parse 'size_acres' to int: {value}"); extracted_data['details']['size_raw'] = value; logging.debug(f"Stored Detail: size_raw = {extracted_data['details']['size_raw']}")
                        else: # Store other details as text
                           extracted_data['details'][key] = value; logging.debug(f"Stored Detail: {key} = {extracted_data['details'][key]}")
                    else:
                        logging.debug("Regex did not match for details.")

                # If inside a 'description' section, append the text
                elif current_section_key == 'description':
                    logging.debug(f"Appending paragraph to description for section '{current_section_key}'")
                    extracted_data['description'] += text + "\n" # Append paragraphs

            # --- Table Processing (Column-Oriented Dictionary Logic) ---
            elif 'table' in item and current_section_key:
                 logging.debug(f"Item {item_index} is Table for section '{current_section_key}'")

                 table_data = item['table'] # Get the value associated with 'table' key

                 # Check if it's a non-empty dictionary (columnar format)
                 if isinstance(table_data, dict) and table_data:
                     logging.debug(f"Table data is a dictionary (column-oriented). Keys: {list(table_data.keys())}")

                     headers = list(table_data.keys())
                     if not headers:
                         logging.warning(f"Table dictionary for section '{current_section_key}' has no headers (keys).")
                         continue

                     # Determine number of rows from the length of the first column's list
                     try:
                         # Check if the value for the first header is indeed a list
                         first_col_data = table_data[headers[0]]
                         if not isinstance(first_col_data, list):
                              logging.warning(f"Data for first column '{headers[0]}' in table '{current_section_key}' is not a list. Type: {type(first_col_data)}. Skipping table.")
                              continue
                         num_rows = len(first_col_data)
                         logging.debug(f"Determined {num_rows} rows based on first column '{headers[0]}'.")
                     except (KeyError, TypeError) as e:
                         logging.warning(f"Could not determine row count for table in section '{current_section_key}'. Error accessing first column data: {e}. Headers: {headers}")
                         continue

                     if num_rows == 0:
                         logging.warning(f"Table for section '{current_section_key}' has headers but no data rows.")
                         continue

                     # Check if target key exists and is a list
                     if current_section_key not in extracted_data or not isinstance(extracted_data[current_section_key], list):
                         logging.warning(f"Target key '{current_section_key}' not found or not a list in extracted_data.")
                         continue

                     # Reconstruct rows (list of dictionaries)
                     final_rows = []
                     valid_row_count = 0
                     for i in range(num_rows): # Iterate through row indices
                         new_row = {}
                         processing_row_ok = True
                         for header in headers: # Iterate through column headers
                             try:
                                 # Check if column data exists and is a list before accessing index
                                 column_list = table_data[header]
                                 if not isinstance(column_list, list):
                                      logging.warning(f"Data for column '{header}' in table '{current_section_key}' is not a list (at row index {i}). Type: {type(column_list)}. Skipping rest of table.")
                                      processing_row_ok = False; break
                                 if i >= len(column_list):
                                     logging.warning(f"Inconsistent column length in table '{current_section_key}'. Row index {i} out of bounds for header '{header}' (length {len(column_list)}). Setting value to None.")
                                     value = None # Handle potentially shorter columns gracefully
                                 else:
                                     value = column_list[i] # Get value for row i, column header

                                 # Map the original MD header to the DB key
                                 # Define header maps for each section
                                 if current_section_key == 'camping': header_map = {'Type': 'type', 'Capacity': 'capacity', 'Amenities': 'amenities', 'Notes': 'notes'}
                                 elif current_section_key == 'fees': header_map = {'Category': 'category', 'Cost': 'cost', 'Notes': 'notes'}
                                 elif current_section_key == 'seasons': header_map = {'Season': 'season_name', 'Dates': 'dates', 'Characteristics': 'characteristics'}
                                 elif current_section_key == 'attractions': header_map = {'Attraction': 'attraction_name', 'Description': 'description', 'NOTES': 'notes'} # Match exact case
                                 else: header_map = {}

                                 # Get DB key, defaulting to lowercased header
                                 db_key = header_map.get(header, header.lower().replace(' ', '_'))
                                 new_row[db_key] = str(value).strip() if value is not None else None # Store value with DB key

                             except KeyError as e_key:
                                  logging.warning(f"Header key '{e_key}' not found while processing row {i} for section '{current_section_key}'. Should not happen if headers list is correct. Skipping rest of table.")
                                  processing_row_ok = False; break
                             except Exception as e_cell:
                                 logging.warning(f"Error processing cell for header '{header}' at row index {i} for section '{current_section_key}': {e_cell}. Skipping rest of table.")
                                 processing_row_ok = False; break

                         if not processing_row_ok: # If error occurred processing columns for this row
                             break # Stop processing this table

                         # If row processed without column errors, add it
                         final_rows.append(new_row)
                         valid_row_count += 1

                     if final_rows: # Add successfully processed rows
                          extracted_data[current_section_key].extend(final_rows)
                          logging.debug(f"Successfully processed and stored {valid_row_count} rows for section '{current_section_key}'")
                     # else: # Logged if loop broken early or no rows processed
                          # logging.warning(f"Could not reconstruct any valid rows for table in section '{current_section_key}'.")

                 else: # Handle case where item['table'] is not a non-empty dict
                     logging.warning(f"Table data for section '{current_section_key}' is not in the expected format (non-empty dictionary). Type: {type(table_data)}. Content: {str(table_data)[:200]}")

            # --- End Table Processing ---
            else: # Handle other unexpected element types if needed
                 element_type = next(iter(item.keys()), 'Unknown')
                 logging.debug(f"Item {item_index} is Type '{element_type}', not processed by current logic.")

        # Clean up description field
        extracted_data['description'] = extracted_data['description'].strip()

        # Final validation before returning
        if extracted_data.get('name'):
            logging.info(f"Successfully extracted data for park: {extracted_data['name']}")
            # Optional: Log the full structured data before insertion
            # logging.debug(f"Full extracted data: {json.dumps(extracted_data, indent=2)}")
            return extracted_data
        else:
             logging.error(f"Extraction failed for {file_path}, no park name found.")
             return None

    except Exception as e:
        # Catch-all for unexpected errors during extraction
        logging.error(f"Failed to extract data from parsed content of {file_path}: {e}", exc_info=True)
        return None

def insert_park_data(cur: sqlite3.Cursor, con: sqlite3.Connection, park_data: dict, file_path: Path) -> bool:
    """
    Inserts or updates extracted park data into the database.
    If park exists, deletes old child data and inserts new data.
    """
    park_name = park_data.get('name', f'Unknown Park ({file_path.name})')
    logging.debug(f"Attempting to insert/update data for '{park_name}' from {file_path}")

    park_id = None
    try:
        # --- Check if Park Exists ---
        cur.execute("SELECT park_ID FROM parks WHERE name = ?", (park_name,))
        result = cur.fetchone()

        if result:
            # --- Park Exists: Update ---
            park_id = result[0]
            logging.info(f"Park '{park_name}' (ID: {park_id}) already exists. Deleting old data and inserting new data.")

            # Delete existing child records for this park_id to prevent duplicates
            child_tables = ['details', 'camping', 'fees', 'seasons', 'attractions']
            for table in child_tables:
                cur.execute(f"DELETE FROM {table} WHERE park_ID = ?", (park_id,))
            logging.debug(f"Deleted existing child data for park_ID {park_id}.")

        else:
            # --- Park Doesn't Exist: Insert New ---
            cur.execute("INSERT INTO parks (name) VALUES (?)", (park_name,))
            park_id = cur.lastrowid
            logging.info(f"Inserted new park '{park_name}' with ID: {park_id}")

        # --- Insert Child Table Data (Runs for both New and Existing Parks) ---
        if park_id is None: # Should have a valid park_id by now
             logging.error(f"Failed to get or create park_ID for '{park_name}'. Aborting child data insertion.")
             return False # Indicate failure

        # Insert Details (only one row expected)
        details = park_data.get('details', {})
        description = park_data.get('description', details.get('description', '')) # Use extracted desc, fallback to detail's desc, then empty
        cur.execute("""
            INSERT INTO details (park_ID, location, established, size_acres, ecosystems, unique_feature, description) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (park_id, details.get('location'), details.get('established'), details.get('size_acres'), details.get('ecosystems'), details.get('unique_feature'), description))
        logging.debug(f"Inserted details for park_ID {park_id}.")

        # Insert data for other tables (potentially multiple rows) dynamically
        section_to_table_map = {
            'camping': ('camping', '(park_ID, type, capacity, amenities, notes)', '(?, ?, ?, ?, ?)'),
            'fees': ('fees', '(park_ID, category, cost, notes)', '(?, ?, ?, ?)'),
            'seasons': ('seasons', '(park_ID, season_name, dates, characteristics)', '(?, ?, ?, ?)'),
            'attractions': ('attractions', '(park_ID, attraction_name, description, notes)', '(?, ?, ?, ?)')
        }

        for section_key, (table_name, columns_sql, values_sql) in section_to_table_map.items():
            table_data = park_data.get(section_key, []) # Get the list of row dictionaries
            if table_data:
                logging.debug(f"Inserting {len(table_data)} rows into '{table_name}' for park_ID {park_id}.")
                inserted_count = 0
                for row in table_data: # Each 'row' is a dictionary extracted previously
                    try:
                        # Get column values in the correct order based on the mapped keys
                        # Keys in 'row' should match lowercase DB keys from extract_data_from_parsed
                        if section_key == 'camping': values = (park_id, row.get('type'), row.get('capacity'), row.get('amenities'), row.get('notes'))
                        elif section_key == 'fees': values = (park_id, row.get('category'), row.get('cost'), row.get('notes'))
                        elif section_key == 'seasons': values = (park_id, row.get('season_name'), row.get('dates'), row.get('characteristics'))
                        elif section_key == 'attractions': values = (park_id, row.get('attraction_name'), row.get('description'), row.get('notes'))
                        else: continue # Skip if section key somehow doesn't match

                        # Construct and execute the SQL
                        sql = f"INSERT INTO {table_name} {columns_sql} VALUES {values_sql}"
                        cur.execute(sql, values)
                        inserted_count += 1
                    except sqlite3.Error as e_insert:
                        logging.error(f"Failed to insert row into {table_name} for park_ID {park_id}. Error: {e_insert}. Row data: {row}", exc_info=True)
                    except Exception as e_insert_gen:
                         logging.error(f"Unexpected error inserting row into {table_name} for park_ID {park_id}. Error: {e_insert_gen}. Row data: {row}", exc_info=True)

                logging.debug(f"Finished inserting. Attempted: {len(table_data)}, Succeeded: {inserted_count} rows for '{table_name}'.")
            else:
                logging.debug(f"No data found for section '{section_key}' for park_ID {park_id}.")

        # Commit transaction after all insertions for this park
        con.commit()
        logging.info(f"Successfully committed all data for '{park_name}' (ID: {park_id})")
        return True

    except sqlite3.Error as e:
        logging.error(f"Database error during insert/update transaction for '{park_name}' (park_ID: {park_id}): {e}", exc_info=True)
        con.rollback() # Rollback transaction on error
        return False
    except Exception as e:
        logging.error(f"Unexpected error during insert/update transaction for '{park_name}' (park_ID: {park_id}): {e}", exc_info=True)
        con.rollback() # Rollback transaction on error
        return False

# --- Main Execution Logic ---
def main():
    """Main function to orchestrate the Markdown to SQLite pipeline."""
    logging.info("="*20 + " Starting Markdown to SQLite processing pipeline " + "="*20)
    connection, cursor = setup_database(DATABASE_PATH)
    files_processed = 0
    files_succeeded = 0
    total_files_found = 0

    if not (connection and cursor):
        logging.critical("Database setup failed. Exiting.")
        return # Cannot proceed without DB connection

    try:
        markdown_files = find_markdown_files(MARKDOWN_DIR)
        total_files_found = len(markdown_files)

        if not markdown_files:
             logging.warning(f"No Markdown files found in {MARKDOWN_DIR.resolve()}. Exiting.")
             return # Exit gracefully if no files found

        for file_path in markdown_files:
            logging.info(f"--- Processing file: {file_path.name} ---")
            files_processed += 1
            content = read_file_content(file_path)
            if not content:
                logging.warning(f"Skipping file {file_path.name} due to read error.")
                continue # Go to next file

            parsed_content = parse_markdown_content(content, file_path)
            if not parsed_content:
                logging.warning(f"Skipping file {file_path.name} due to parsing error or no data.")
                continue # Go to next file

            # Extract structured data using the refined logic
            extracted_data = extract_data_from_parsed(parsed_content, file_path)
            if not extracted_data:
                logging.warning(f"Skipping file {file_path.name} due to data extraction failure.")
                continue # Go to next file

            # Insert or update data in the database
            if insert_park_data(cursor, connection, extracted_data, file_path):
                files_succeeded += 1 # Count success if insert/update didn't raise error
            else:
                 # Error logged within insert_park_data
                 logging.error(f"Failed to process database operations for file: {file_path.name}")

    except Exception as e:
        # Catch any unexpected errors during the main loop
        logging.critical(f"An uncaught exception occurred during processing: {e}", exc_info=True)
    finally:
        # Ensure database connection is closed
        if connection:
            connection.close()
            logging.info("Database connection closed.")

    # Log summary statistics
    logging.info("="*20 + " Processing Summary " + "="*20)
    logging.info(f"Total files found: {total_files_found}")
    logging.info(f"Files attempted processing: {files_processed}")
    logging.info(f"Files successfully processed (inserted/updated/skipped OK): {files_succeeded}")
    logging.info(f"Files failed during processing: {files_processed - files_succeeded}")
    logging.info(f"Processing pipeline finished. Check '{LOG_FILE.resolve()}' for detailed logs.")
    # Also print log file location to console
    print(f"\nProcessing finished. See '{LOG_FILE.resolve()}' for details.")

# --- Script Entry Point ---
if __name__ == "__main__":
    main()