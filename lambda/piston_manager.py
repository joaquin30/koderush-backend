import requests
import os

class UnsupportedLanguageError(Exception):
    def __init__(self, language):
        self.language = language
        super().__init__(f"Language '{language}' is not supported.")

class PistonManager:
    def __init__(self):
        self.piston_url = os.environ.get('PISTON_EXECUTE_URL', None)
        self.supported_lang = {
            "python": "3.10.0",
            "c++": "10.2.0",
            "javascript": "18.15.0"
        }

    def _execute_code(self, code, input_data, language):
        if language not in self.supported_lang:
            raise UnsupportedLanguageError(language)
        
        payload = {
            "language": language,
            "version": self.supported_lang[language],
            "files": [{
                "content": code
            }],
            "stdin": input_data if input_data else ""
        }

        try:
            response = requests.post(self.piston_url, json=payload)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            output = data.get('run', {}).get('output', '').strip()
            return output if output else None
        
        except requests.exceptions.RequestException as e:
            return None
        
    def validate_solution(self, problem, solution, language):
        veredict = "accepted"

        for test in problem['examples']:
            output = self._execute_code(solution, test['input'], language)
            if output is None:
                veredict = "runtime error"
                break
            if output.strip() != test['output'].strip():
                veredict = "wrong answer"
                break
        return veredict