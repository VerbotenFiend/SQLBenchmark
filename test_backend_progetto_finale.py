"""
NON CAMBIARE QUESTO SCRIPT DI TEST.
USEREMO ESATTAMENTE QUESTO SCRIPT PER VALIDARE IL VOSTRO CODICE
(+ un breve test manuale del frontend web).
DOVETE ESEGUIRE QUESTO TEST DA FUORI DAL DOCKER.
"""
import argparse
from typing import Set, Dict, Any, Optional, List
from urllib.parse import urljoin
import requests
import copy


class BackendTester():
    def __init__(self, url: str):
        self.url = url

        self.sql_queries = {
            "movies_of_year": "SELECT movies.titolo, movies.anno FROM movies WHERE movies.anno = {year}",
        }

    def test_database_schema_format(self) -> None:
        urlpath = urljoin(self.url, "schema_summary")
        response = requests.get(urlpath)
        assert response.status_code == 200, f"Expected status code 200 but got {response.status_code} for URL {urlpath}"
        result = response.json()

        assert isinstance(result, list), f"Expected result type list but got {type(result)}"
        for index, column_dict in enumerate(result):
            assert isinstance(column_dict, dict), f"Expected each element to be a dict but element at index {index} is {type(column_dict)}"
            assert column_dict.get("table_name") is not None, f"Each dictionary of the schema summary must have a 'table_name', got: {column_dict}"
            assert column_dict.get("table_column") is not None, f"Each dictionary of the schema summary must have a 'table_column', got: {column_dict}"

        table_names = [x["table_name"] for x in result]
        assert "movies" in table_names, (
            f"Expected one of the tables to be 'movies' but got table names: {table_names}. "
            "You can use other tables if you want."
        )
        print(f"PASS: the database schema summary is correctly formatted and contains the 'movies' table.\n")

    def test_sql_query_response(self, sql_query_to_test: str, expected_validation_status: str) -> None:
        """
        Tests the /sql_search endpoint with a given SQL query and checks the validation status.
        If expected_validation_status is "unsafe" or "invalid", it also checks that results are None.
        """
        urlpath = urljoin(self.url, "sql_search")
        payload = {"sql_query": sql_query_to_test}
        print(f"  POST {urlpath} with JSON body: {payload}")
        response = requests.post(urlpath, json=payload)

        assert response.status_code == 200, \
            f"For SQL query '{sql_query_to_test}', expected HTTP status 200 but got: {response.status_code} {response.text}."

        response_data = response.json()

        assert "sql_validation" in response_data, f"Response missing 'sql_validation' field for query: '{sql_query_to_test}'"
        assert response_data["sql_validation"] == expected_validation_status, \
            f"For SQL query '{sql_query_to_test}', expected 'sql_validation' to be '{expected_validation_status}' but got '{response_data['sql_validation']}'"

        assert "results" in response_data, f"Response missing 'results' field for query: '{sql_query_to_test}'"
        if expected_validation_status in ["unsafe", "invalid"]:
            assert response_data["results"] is None, \
                f"For SQL query '{sql_query_to_test}' with validation '{expected_validation_status}', expected 'results' to be None but got {type(response_data['results'])}"
        else:
            self._extract_names_and_validate_results(actual_results=response_data["results"],
                                                          expected_item_type="...",
                                                          query_for_error=sql_query_to_test,
                                                          verbose=True,
                                                          do_check_itemtype=False)
        print(f"PASS: SQL query '{sql_query_to_test}' correctly resulted in validation status '{expected_validation_status}'.\n")
        
    def _extract_names_and_validate_results(self, actual_results: List, expected_item_type: str, query_for_error: str,
                                            verbose=False, do_check_itemtype=True):
        names = set()
        for idx, item in enumerate(actual_results):
            assert isinstance(item, dict), (
                f"Expected each item in 'results' to be a dict but got {type(item)} at index {idx} for SQL query: '{query_for_error}'"
            )
            actual_item_type = item.get("item_type")
            if do_check_itemtype:
                assert actual_item_type == expected_item_type, (
                f"Expected item_type to be '{expected_item_type}' but got '{actual_item_type}' "
                f"at index {idx} for SQL query: '{query_for_error}'"
            )
            properties = item.get("properties", [])
            item_name = None
            for prop in properties:
                if prop.get("property_name") == "name":
                    item_name = prop.get("property_value")
                    if item_name is not None:
                         names.add(item_name)
                    break
            assert item_name is not None, f"Item at index {idx} missing 'name' property (or mapped equivalent) for SQL query: '{query_for_error}'. Properties found: {properties}"


        if verbose:
            print(f"  -> Extracted names: {names}")
        return names

    def _run_search_and_extract(self, sql_query: str, expected_item_type: str) -> set:
        """
        Executes a SQL search request expected to be valid and extracts item names.
        """
        urlpath = urljoin(self.url, "sql_search")
        payload = {"sql_query": sql_query}
        print(f"  POST {urlpath} with JSON body: {payload}")
        response = requests.post(urlpath, json=payload)

        assert response.status_code == 200, (
            f"Request failed for SQL query: '{sql_query}'. Expected status code 200 but got {response.status_code}. Response: {response.text}"
        )

        response_data = response.json()

        assert response_data.get("sql_validation") == "valid", \
            f"SQL query '{sql_query}' was expected to be 'valid' but got validation status '{response_data.get('sql_validation')}'. Response: {response.text}"

        actual_results: Optional[List[Dict[str, Any]]] = response_data.get("results")

        if actual_results is None:
            actual_results = []

        assert isinstance(actual_results, list), (
            f"Expected 'results' field to be a list but got {type(actual_results)} for SQL query: '{sql_query}'"
        )
        
        names =  self._extract_names_and_validate_results(actual_results=actual_results,
                                                          expected_item_type=expected_item_type,
                                                          query_for_error=sql_query,
                                                          verbose=True)
        
        return names

    def test_question_1_movies_of_year(self, year: str, expected_titles: Set[str]) -> None:
        print(f"Testing: Question 1 - Movies of year {year} (SQL)...")
        sql_query = self.sql_queries["movies_of_year"].format(year=int(year))
        returned_titles = self._run_search_and_extract(sql_query, "film")
        assert returned_titles == expected_titles, (
            f"FAIL: For year {year}, expected movie titles {expected_titles} but got {returned_titles}"
        )
        print(f"PASS: Question 1 - Movies of year {year}.\n")

    def add_movie_line(self, data_line_string: str) -> None:
        """
        Sends the pre-formatted comma-separated data_line string to the POST /add endpoint.
        The expected format is: Titolo,Regista,Età_Autore,Anno,Genere,Piattaforma_1,Piattaforma_2
        Con Piattaforma_1 e Piattaforma_2 che possono essere 
        """
        urlpath = urljoin(self.url, "add") # Use the /add endpoint

        # Prepare the JSON payload: {"data_line": "..."}
        # The input argument 'data_line_string' is used directly
        payload = {"data_line": data_line_string}

        print(f"  POST {urlpath} with JSON body: {payload}")
        response = requests.post(urlpath, json=payload) # Send payload as JSON

        # Check for success (200 OK according to spec example, or 422 error)
        if response.status_code == 422:
             raise AssertionError(
                 f"Failed to add movie line '{data_line_string}'. Expected status code 200 but got 422. "
                 f"This might indicate an invalid format according to the backend. Response: {response.text}"
             )
        assert response.status_code == 200, (
            f"Failed to add movie line '{data_line_string}'. Expected status code 200 but got {response.status_code}. "
            f"Response: {response.text}"
        )
        # Check the response body matches {"status": "ok"}
        try:
            response_json = response.json()
            assert response_json == {"status": "ok"}, \
                f"Expected response body {{'status': 'ok'}} but got {response_json}"
        except requests.exceptions.JSONDecodeError:
            raise AssertionError(f"Response for adding movie line '{data_line_string}' was not valid JSON. Response text: {response.text}")

        print(f"  -> backend acknowledged add request for line: '{data_line_string}' (Status: {response.status_code}).\n")

    def test_add_movie_of_2010_year(self) -> None:
        print("Testing: Add Movie - The Social Network (/add)...")
        data_line = "The Social Network,David Fincher,62,2010,Drama,Netflix,Amazon Prime Video"
        self.add_movie_line(data_line)
        print("PASS: Add Movie - The Social Network (/add).\n")

    def test_invalid_add(self, wrong_add_line: str):
        """Tests sending an invalidly formatted line to the /add endpoint."""
        print("Testing: Invalid Add Movie Line (/add)...")
        invalid_data_string = wrong_add_line # Example of an invalid format
        urlpath = urljoin(self.url, "add")
        payload = {"data_line": invalid_data_string}
        print(f"  POST {urlpath} with JSON body: {payload}")
        response = requests.post(urlpath, json=payload)
        assert response.status_code == 422, f"After sending invalid data line '{invalid_data_string}', expected 422 error code but got: {response.status_code} {response.text}."
        print(f"PASS: after sending invalid data line '{invalid_data_string}', correctly got 422 error code.\n")

    def _validate_search_response_format(self, response_part: dict, context_description: str):
        """
        Validates the structure of a dictionary expected to match SqlSearchResponse.
        Args:
            response_part: The dictionary part to validate.
            context_description: A string describing the context (e.g., "attempt_1", "search response") for error messages.
            required_sql: Is the SQL field required in the output?
        """
        assert isinstance(response_part, dict), \
            f"Expected response part ({context_description}) to be a dict, but got {type(response_part)}."
            
        
        assert "sql" in response_part, f"Response missing 'sql' field in {context_description}. Response part: {response_part}"
        assert isinstance(response_part["sql"], str), \
            f"Expected 'sql' field to be a string in {context_description}, but got {type(response_part['sql'])}."
        print(f"  [{context_description}] SQL: {response_part['sql']}")

        assert "sql_validation" in response_part, f"Response missing 'sql_validation' field in {context_description}. Response part: {response_part}"
        valid_statuses = ["valid", "invalid", "unsafe"]
        assert response_part["sql_validation"] in valid_statuses, \
            f"Expected 'sql_validation' in {context_description} to be one of {valid_statuses}, but got '{response_part['sql_validation']}'."
        print(f"  [{context_description}] SQL Validation Status: {response_part['sql_validation']}")

        assert "results" in response_part, f"Response missing 'results' field in {context_description}. Response part: {response_part}"

        actual_results = response_part["results"]
        if response_part["sql_validation"] == "valid":
            assert isinstance(actual_results, list), \
                (f"For 'sql_validation' == 'valid' in {context_description}, expected 'results' to be a list, "
                 f"but got {type(actual_results)}.")

            if not actual_results:
                print(f"  [{context_description}] Received empty list for results, which is a valid format for 'sql_validation: valid'.")
            else:
                print(f"  [{context_description}] Received {len(actual_results)} items in results. Checking format...")
                for idx, item in enumerate(actual_results):
                    assert isinstance(item, dict), \
                        f"Expected item at index {idx} in 'results' ({context_description}) to be a dict, but got {type(item)}."
                    assert "item_type" in item, f"Item at index {idx} in 'results' ({context_description}) missing 'item_type'. Response: {item}"
                    assert isinstance(item["item_type"], str), \
                        f"Expected 'item_type' to be str in item at index {idx} ({context_description}), got {type(item['item_type'])}. Response: {item}"
                    assert "properties" in item, f"Item at index {idx} in 'results' ({context_description}) missing 'properties'. Response: {item}"
                    assert isinstance(item["properties"], list), \
                        f"Expected 'properties' to be list in item at index {idx} ({context_description}), got {type(item['properties'])}. Response: {item}"
                    for prop_idx, prop_item in enumerate(item["properties"]):
                        assert isinstance(prop_item, dict), \
                            f"Property at index {prop_idx} (item {idx}, {context_description}) not a dict. Got {type(prop_item)}. Response: {prop_item}"
                        assert "property_name" in prop_item, f"Property at {prop_idx} (item {idx}, {context_description}) missing 'property_name'. Response: {prop_item}"
                        assert "property_value" in prop_item, f"Property at {prop_idx} (item {idx}, {context_description}) missing 'property_value'. Response: {prop_item}"
        else:
            assert actual_results is None, \
                (f"For 'sql_validation' == '{response_part['sql_validation']}' in {context_description}, expected 'results' to be None, "
                 f"but got {type(actual_results)}.")
            print(f"  [{context_description}] 'results' is None, consistent with 'sql_validation: {response_part['sql_validation']}'.")

    def test_natural_language_search_format(self, question: str, model_name: str) -> None:
        """
        Tests the format of the POST /search endpoint response.
        Content of results depends on LLM and is not strictly validated here.
        Includes optional 'model' parameter in payload.
        """
        context_desc = f"search response for question '{question}'" + (f" with model '{model_name}'" if model_name else "")
        print(f"Testing: Natural Language Search - '{question}'{(' using model '+model_name) if model_name else ''} (Format Check via POST)...")

        urlpath = urljoin(self.url, "search")
        payload = {"question": question}
        
        payload["model"] = model_name

        print(f"  POST {urlpath} with JSON body: {payload}")

        try:
            response = requests.post(urlpath, json=payload, timeout=180)
        except requests.exceptions.Timeout:
            raise AssertionError(f"Request to {urlpath} with payload {payload} timed out. The LLM service might be slow or unresponsive.")

        if response.status_code != 200:
            raise AssertionError(
                f"For question '{question}' (via POST), expected HTTP status 200 for a SqlSearchResponse, but got: {response.status_code} {response.text}. "
                f"Check backend logs for errors (LLM service, DB connection, etc.)."
            )

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise AssertionError(f"Response for question '{question}' (via POST) was not valid JSON. Response text: {response.text}")

        self._validate_search_response_format(response_data, context_desc)

        print(f"PASS: Natural Language Search - '{question}'{(' using model '+model_name) if model_name else ''} (via POST) response format is valid (SqlSearchResponse).\n")

    def test_natural_language_search_format_with_retry(self, question: str, model_name: str) -> None:
        """
        Tests the format of the POST /search_with_retry endpoint response.
        This endpoint is expected for groups of 3.
        Checks for attempt_1 and attempt_2 keys, each matching SqlSearchResponse format.
        """
        print(f"Testing: Natural Language Search with Retry - '{question}' using model '{model_name}' (Format Check via POST)...")

        urlpath = urljoin(self.url, "search_with_retry")
        payload = {"question": question, "model": model_name}

        print(f"  POST {urlpath} with JSON body: {payload}")

        try:
            response = requests.post(urlpath, json=payload, timeout=360)
        except requests.exceptions.Timeout:
            raise AssertionError(f"Request to {urlpath} with payload {payload} timed out. The LLM service with retry might be slow or unresponsive.")

        if response.status_code != 200:
            if response.status_code == 404:
                 raise AssertionError(
                    f"Endpoint {urlpath} returned 404 Not Found. "
                    f"This endpoint (/search_with_retry) is only required for groups of 3. "
                    f"If you are a group of 2, this test failure is expected run this script with --group-size=2. "
                    f"If you are a group of 3, ensure the endpoint is correctly implemented in your backend."
                 )
            else:
                raise AssertionError(
                    f"For question '{question}' with retry (via POST), expected HTTP status 200, but got: {response.status_code} {response.text}. "
                    f"Check backend logs for errors."
                )

        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise AssertionError(f"Response for question '{question}' with retry (via POST) was not valid JSON. Response text: {response.text}")

        assert isinstance(response_data, dict), \
            f"Expected response for retry endpoint to be a dict, but got {type(response_data)} for question '{question}'."
        assert "attempt_1" in response_data, f"Response missing 'attempt_1' key for question '{question}' with retry. Keys found: {list(response_data.keys())}"
        assert "attempt_2" in response_data, f"Response missing 'attempt_2' key for question '{question}' with retry. Keys found: {list(response_data.keys())}"

        print("\n  Validating attempt_1 format...")
        self._validate_search_response_format(
            response_data["attempt_1"],
            f"attempt_1 for question '{question}' with model '{model_name}'"
        )

        print("\n  Validating attempt_2 format...")
        if response_data["attempt_2"] is not None:
            self._validate_search_response_format(
            response_data["attempt_2"],
            f"attempt_2 for question '{question}' with model '{model_name}'"
        )

        print(f"PASS: Natural Language Search with Retry - '{question}' using model '{model_name}' (via POST) response format is valid.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run backend tests for the final project.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--group-size",
        type=int,
        required=True,
        choices=[2, 3],
        help="Number of people in the group (2 or 3). Determines if retry tests are run."
    )
    args = parser.parse_args()
    group_size = args.group_size
    print(f"--- Running tests for group size: {group_size} ---")

    URL = "http://localhost:8003"
    assert URL == "http://localhost:8003", "Do not change the URL, you must expose the backend on port 8003"
    tester = BackendTester(URL)

    print("--- Phase 1: Testing Initial State ---")
    tester.test_database_schema_format()

    original_2010_movies = {"Inception", "Shutter Island"}
    tester.test_question_1_movies_of_year("2010", original_2010_movies)
    tester.test_question_1_movies_of_year("1998", {"Saving Private Ryan"})


    print("\n--- Testing SQL Query Validation (/sql_search) ---")
    tester.test_sql_query_response("SELECT * FROM WeirdPasta", "invalid")
    tester.test_sql_query_response("DROP TABLE Film", "unsafe")
    tester.test_sql_query_response("UPDATE Film SET anno = 2000 WHERE titolo = 'Inception'", "unsafe")
    tester.test_sql_query_response("SELECT * FROM movies WHERE anno = 2000", "valid")

    print("\n--- Testing Natural Language Search (/search Format Only) ---")
    default_model = "gemma3:1b-it-qat"
    tester.test_natural_language_search_format("Elenca tutti i film.", default_model)

    if group_size == 3:
        print("\n--- Testing Natural Language Search with Retry (/search_with_retry Format Only) ---")
        try:
            tester.test_natural_language_search_format_with_retry("Elenca i film di fantascienza usciti dopo il 2015.", "gemma3:1b-it-qat")
        except AssertionError as e:
             print(f"ERROR: Test for /search_with_retry failed unexpectedly for group size 3: {e}")
             raise
    else:
        print("\n--- Skipping Natural Language Search with Retry test (Group size is 2) ---")


    print("\n--- Phase 2: Adding New Movies (via /add endpoint) ---")
    tester.test_add_movie_of_2010_year()

    tester.test_invalid_add("hello,world")
    tester.test_invalid_add("a,b,c_not_an_int,d,e,f,g")
    tester.test_invalid_add("a,b,10,not_a_year,e,f,g")
    tester.test_invalid_add(",b,10,2000,e,f,g")
    tester.test_invalid_add("a,,10,2000,e,f,g")


    print("\n--- Phase 3: Testing State After Additions (via /sql_search) ---")
    updated_expected_titles_2010 = copy.deepcopy(original_2010_movies)
    updated_expected_titles_2010.add("The Social Network")
    tester.test_question_1_movies_of_year("2010", updated_expected_titles_2010)


    print("\n--- Re-testing Unchanged Queries (Sanity Check via /sql_search) ---")
    tester.test_question_1_movies_of_year("1998", {"Saving Private Ryan"})


    print("\n-----------------------------------------------------")
    print("ALL TESTS PASS!")
    print("(Check manually the frontend webpage UI before handing in the project)")
    print("-----------------------------------------------------")

if __name__ == "__main__":
    main()