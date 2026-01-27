import hashlib
import json
import logging
import os
from pathlib import Path

import openai
from openai import OpenAI

from prog_params import ProgParams as prog_params


class LLM(object):
    def __init__(self, model=('deepseek-chat', 'https://api.deepseek.com'), api_key=None,
                 cache_folder=None, load_from_cache=True, save_to_cache=True):
        self.model, self.base_url = model
        openai.base_url = self.base_url
        self.api_key = api_key
        self.cache_folder = cache_folder
        self.load_from_cache = load_from_cache
        self.save_to_cache = save_to_cache
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

    def call(self, prompt, num_of_samples=1, prefix=None, max_tokens=8192):

        response = None
        call_params = self.get_call_params(prompt, num_of_samples)
        cache_file_path = self.get_cache_file_path(prompt, num_of_samples, prefix)

        if self.load_from_cache and self.cache_folder is not None:
            if Path(cache_file_path).is_file():
                with open(cache_file_path, "r") as file:
                    logging.info(f"Loading LLM's response from cache...")
                    try:
                        json_to_load = json.load(file)
                        response = json_to_load['response']
                    except Exception:
                        logging.warning("Failed to load LLM's response from cache.")

        if response is None:
            try:
                logging.info(f"Calling the LLM with prompt: {prompt}")

                #response = openai.ChatCompletion.create(**call_params)

                client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=prompt,
                    n=1,
                    stream=False,
                    temperature=1,
                    max_tokens=max_tokens
                ).model_dump_json()
            except openai.OpenAIError as e:
                response = {
                    'error': "context_length_exceeded",
                    'error_message': e.with_traceback(None),
                    'choices': [ {'message': {'content': ""}} ],
                    'usage': {'total_tokens': prog_params.model_token_limit}
                    }

            if self.save_to_cache and self.cache_folder is not None:
                with open(cache_file_path, "w") as file:
                    json_to_save = LLM.get_json_to_save(call_params, response)
                    file.write(json.dumps(json_to_save, indent=4, sort_keys=True))

        if type(response) is str:
            response = json.loads(response)
        if 'error' in response:
            if response['error'] == "context_length_exceeded":
                raise openai.OpenAIError(response['error_message'], None)
            
        response_message = [choice['message']['content'] for choice in response['choices']]
        response_token_usage = response['usage']['total_tokens']

        completion_token_usage = response['usage']['completion_tokens']
        prompt_token_usage = response['usage']['prompt_tokens']

        logging.info(f"Responses are fetched. Token usage: {response_token_usage}")

        return response_message, completion_token_usage, prompt_token_usage
    
    def get_call_params(self, prompt, num_of_samples=1):
        return {
            "model": self.model,
            "messages": prompt,
            "n": num_of_samples,
            "temperature": 1,
            "top_p": 1,
        }

    def get_call_hash(self, prompt, num_of_samples=1):
        call_params = self.get_call_params(prompt, num_of_samples=num_of_samples)
        call_params=LLM.get_sorted_json_str(call_params)
        return hashlib.md5(call_params.encode('utf-8')).hexdigest()

    @staticmethod
    def get_sorted_json_str(data):
        if isinstance(data, list):
            sorted_list = sorted([LLM.get_sorted_json_str(item) if isinstance(item, (dict, list)) else item for item in data])
            json_str = json.dumps(sorted_list, sort_keys=True)
        elif isinstance(data, dict):
            sorted_dict = {k: LLM.get_sorted_json_str(v) for k, v in sorted(data.items())}
            json_str = json.dumps(sorted_dict, sort_keys=True)
        else:
            json_str = json.dumps(data)

        return json_str
    
    def get_cache_file_path(self, prompt, num_of_samples=1, prefix=None):
        call_hash = self.get_call_hash(prompt, num_of_samples)
        if prefix is not None:
            return f"{self.cache_folder}/{prefix}_{call_hash}.json"
        return f"{self.cache_folder}/{call_hash}.json"

    @staticmethod
    def get_json_to_save(call_params, response):
        return {
            "call": call_params,
            "response": response
        }
