# import re
# import logging

# # Regex pattern to match dates in various common formats
# DATE_PATTERN = r'\b(?:\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|' \
#                r'\d{1,2}\s(?:Jan|January|Feb|February|Mar|March|Apr|April|' \
#                r'May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|' \
#                r'Nov|November|Dec|December)\s\d{2,4})\b'

# def extract_date_windows(page_text, pattern=DATE_PATTERN, before=20, after=10):
#     """
#     For a given page, find all date occurrences and extract a window of characters
#     around each match.
    
#     Args:
#       page_text (str): Text from one page.
#       pattern (str): Regex pattern to match dates.
#       before (int): Number of characters to include before the date.
#       after (int): Number of characters to include after the date.
    
#     Returns:
#       list: A list of context snippets (windows) where date info was found.
#     """
#     windows = []
#     for match in re.finditer(pattern, page_text, re.IGNORECASE):
#         start_idx = max(0, match.start() - before)
#         end_idx = min(len(page_text), match.end() + after)
#         windows.append(page_text[start_idx:end_idx])
#     return windows

# def extract_period_date(nims_lim, documents):
#     """
#     For each document (each represented as a list of page texts), this function:
#       1. Uses regex to locate pages with date info and extracts a small window around each date.
#       2. Concatenates all the windows into a single text.
#       3. Sends that text to the LLM to ask: "Which of the following is the period date?"
#          The LLM must return a JSON output in the format:
#          { "risk_inception": start_date, "risk_expiry": end_date }
    
#     Args:
#       nims_lim: An LLM client instance with a .getresponse() method.
#       documents (list): A list of documents, where each document is a list of page strings.
    
#     Returns:
#       list: A list of responses from the LLM (one per document). If no date info is found
#             in a document, it returns {"risk_inception": None, "risk_expiry": None}.
#     """
#     results = []
    
#     for doc_pages in documents:
#         # Accumulate context snippets from pages with date info.
#         context_windows = []
#         for page in doc_pages:
#             windows = extract_date_windows(page)
#             print(windows)
#             if windows:
#                 context_windows.extend(windows)
        
#         if context_windows:
#             concatenated_context = " ".join(context_windows)
#             # Build the LLM prompt.
#             prompt = (
#                 "Extract the period date from the following text. "
#                 "Return the result as a JSON object in the format: "
#                 '{ "risk_inception": start_date, "risk_expiry": end_date }.\n'
#                 f"Text: {concatenated_context}"
#             )
#             messages = [
#                 {"role": "user", "content": prompt},
#                 {"role": "assistant", "content": "350N Output:"}
#             ]
#             print(messages)
#             try:
#                 response = nims_lim.getresponse(messages)
#             except Exception as e:
#                 logging.info(f"Error in getting endpoint response: {e}")
#                 response = { "risk_inception": None, "risk_expiry": None }
#             results.append(response)
#         else:
#             results.append({ "risk_inception": None, "risk_expiry": None })
    
#     return results

# # Example usage:
# if __name__ == "__main__":
#     # Example: each document is a list of page texts.
#     documents = [
#         [
#             "This is some header \n1 June 2024 without dates.",
#             "The project started on 5 January 2025. More info follows.",
#             "and ended on 10 February 2025 after some extensions."
#         ],
       
#     ]
    
#     # Assume nims_lim is your LLM client instance.
#     class DummyLLM:
#         def getresponse(self, messages):
#             # This dummy function pretends to extract period dates.
#             # In real usage, this should call your actual LLM API.
#             # For our dummy response, we assume the first document has valid period dates.
#             if "5 January 2025" in messages[0]["content"]:
#                 return { "risk_inception": "2025-01-05", "risk_expiry": "2025-02-10" }
#             else:
#                 return { "risk_inception": None, "risk_expiry": None }
    
#     nims_lim = DummyLLM()
    
#     period_dates = extract_period_date(nims_lim, documents)
#     for doc_result in period_dates:
#         print(doc_result)
import re
import logging
import pandas as pd

# Updated regex pattern to handle various date formats
DATE_PATTERN = (
    r'\b(?:'
    r'\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}'                            # Matches numeric formats like YYYY-MM-DD, DD.MM.YYYY, etc.
    r'|'                                                         
    r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'                              # Matches DD/MM/YYYY, MM/DD/YYYY, etc.
    r'|'                                                         
    r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'                                # Matches YYYY/MM/DD, etc.
    r'|'                                                         
    r'(?:\d{1,2}(?:st|nd|rd|th)?'                                  # Ordinal day (1st, 2nd, 3rd, 4th...)
    r'(?:\s+day(?:\s+of)?)?\s+'                                   # Optional "day" or "day of"
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|'
    r'Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|'
    r'Nov(?:ember)?|Dec(?:ember)?)'
    r'(?:,\s*\d{4})?'                                             # Optional comma before year
    r')'
    r')\b'
)

def extract_date_windows(pages, pattern=DATE_PATTERN, before=20, after=10):
    """
    Extract date-related context snippets along with page numbers.
    
    Args:
        pages (dict): A dictionary where keys are page numbers and values are page texts.
        pattern (str): Regex pattern to match dates.
        before (int): Characters to include before the date.
        after (int): Characters to include after the date.

    Returns:
        list: A list of dictionaries containing {"page_no": int, "text_window": str}.
    """
    extracted_data = []

    for page_no, text in pages.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start_idx = max(0, match.start() - before)
            end_idx = min(len(text), match.end() + after)
            extracted_data.append({
                "page_no": page_no,
                "text_window": text[start_idx:end_idx]
            })
    
    return extracted_data


def extract_period_date(nims_lim, documents):
    """
    Extracts period dates from multi-page documents using regex & LLM.

    Args:
        nims_lim: LLM client instance with a `.getresponse()` method.
        documents (list): List of documents, where each document is a dict of {page_no: text}.

    Returns:
        DataFrame: Columns -> ["page_no", "risk_inception", "risk_expiry"]
    """
    results = []

    for doc_pages in documents:
        # Extract date windows with page numbers
        date_windows = extract_date_windows(doc_pages)

        if date_windows:
            # Concatenate all extracted text windows
            concatenated_context = " ".join([entry["text_window"] for entry in date_windows])

            # Construct LLM prompt
            prompt = (
                "Extract the period date from the following text. "
                "Return the result as a JSON object in the format: "
                '{ "risk_inception": start_date, "risk_expiry": end_date }.'
                f"Text: {concatenated_context}"
            )
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "350N Output:"}
            ]

            try:
                response = nims_lim.getresponse(messages)
            except Exception as e:
                logging.info(f"Error in LLM response: {e}")
                response = { "risk_inception": None, "risk_expiry": None }
        else:
            response = { "risk_inception": None, "risk_expiry": None }

        for entry in date_windows:
            results.append({
                "page_no": entry["page_no"],
                "risk_inception": response["risk_inception"],
                "risk_expiry": response["risk_expiry"]
            })

    # Convert results to DataFrame
    return pd.DataFrame(results)


# Example Usage
if __name__ == "__main__":
    # Example input: List of documents (each document is a dictionary of page_no -> text)
    documents = [
        {  # Document 1
            1: "Some header information, no dates here.",
            2: "The project started on 5 January 2025. Additional details follow.",
            3: "It ended on 10 February 2025 after some discussions."
        },
        
    ]

    # Dummy LLM client
    class DummyLLM:
        def getresponse(self, messages):
            if "5 January 2025" in messages[0]["content"]:
                return { "risk_inception": "2025-01-05", "risk_expiry": "2025-02-10" }
            return { "risk_inception": None, "risk_expiry": None }

    nims_lim = DummyLLM()

    # Get period dates as DataFrame
    period_dates_df = extract_period_date(nims_lim, documents)
    print(period_dates_df)
