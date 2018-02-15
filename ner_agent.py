import os
import json
import copy
import traceback
import requests
from glob import glob
import nltk

from ner.network import NER
from ner.corpus import Corpus
from ner.utils import md5_hashsum, download_untar
from ner.utils import tokenize, lemmatize


class NerAgent:
    def __init__(self, config):
        self.config = copy.deepcopy(config)
        self.kpi_name = self.config['kpi_name']
        self.agent = None
        self.session_id = None
        self.numtasks = None
        self.tasks = None
        self.observations = None
        self.agent_params = None
        self.predictions = None
        self.answers = None
        self.score = None
        self.response_code = None

    def init_agent(self):
        model_dir = self.config['kpis'][self.kpi_name]['settings_agent']['model_dir']
        update_model = bool(self.config['kpis'][self.kpi_name]['settings_agent']['update_model'])

        if update_model:
            glob_arg = os.path.join('{}/*'.format(model_dir))
            if md5_hashsum(glob(glob_arg)) != 'f25fe8e1297154077fc4d3bf65ed888e':
                download_url = 'http://lnsigo.mipt.ru/export/ner/ner_model_total_rus.tar.gz'
                download_path = model_dir
                download_untar(download_url, download_path)

        params_path = os.path.join(model_dir, 'params.json')
        with open(params_path) as f:
            network_params = json.load(f)

        dicts_path = os.path.join('model/dict.txt')
        corpus = Corpus(dicts_filepath=dicts_path)
        network = NER(corpus, verbouse=False, pretrained_model_filepath='model/ner_model', **network_params)
        self.agent = network

    def _set_numtasks(self, numtasks):
        self.numtasks = numtasks

    def _get_tasks(self):
        get_url = self.config['kpis'][self.kpi_name]['settings_kpi']['rest_url']
        if self.numtasks in [None, 0]:
            test_tasks_number = self.config['kpis'][self.kpi_name]['settings_kpi']['test_tasks_number']
        else:
            test_tasks_number = self.numtasks
        get_params = {'stage': 'netest', 'quantity': test_tasks_number}
        get_response = requests.get(get_url, params=get_params)
        tasks = json.loads(get_response.text)
        return tasks

    def _make_observations(self, tasks, human_input=False):
        observations = []
        if human_input:
            question = self._preprocess_humaninput(tasks[0])
            observations.append({
                'id': 'dummy',
                'input': nltk.tokenize.wordpunct_tokenize(tasks[0]),
                'question': question})
        else:
            for task in tasks['qas']:
                question = self._preprocess_task(task['question'])
                observations.append({
                    'id': task['id'],
                    'input': task['question'].split(' '),
                    'question': question})
        return observations

    def _preprocess_humaninput(self, task):
        tokens = nltk.tokenize.wordpunct_tokenize(task)
        tokens_lemmas = lemmatize(tokens)
        return tokens_lemmas

    def _preprocess_task(self, task):
        # tokens = tokenize(task)
        tokens = task.split(' ')
        tokens_lemmas = lemmatize(tokens)
        return tokens_lemmas

    def _get_predictions(self, observations):
        predictions = []
        for observation in observations:
            predict = self.agent.predict_for_token_batch([observation['question']])[0]
            # predict = ' '.join(self.agent.predict_for_token_batch([observation['question']])[0])
            predictions.append(predict)
        return predictions

    def _make_answers(self, observations, predictions, human_input=False):
        print(observations)
        print(predictions)
        answers = {}
        observ_predict = list(zip(observations, predictions))
        if human_input:
            for obs, pred in observ_predict:
                answers[obs['id']] = list(zip(obs['input'], pred))
            return answers['dummy']
        else:
            for obs, pred in observ_predict:
                answers[obs['id']] = ' '.join(pred)
            tasks = copy.deepcopy(self.tasks)
            tasks['answers'] = answers
            return tasks

    def _get_score(self, answers):
        post_headers = {'Accept': '*/*'}
        rest_response = requests.post(self.config['kpis'][self.kpi_name]['settings_kpi']['rest_url'],
                                      json=answers,
                                      headers=post_headers)
        return {'text': rest_response.text, 'status_code': rest_response.status_code}

    def _run_test(self):
        tasks = self._get_tasks()
        session_id = tasks['id']
        numtasks = tasks['total']
        self.tasks = tasks
        self.session_id = session_id
        self.numtasks = numtasks

        observations = self._make_observations(tasks)
        self.observations = observations

        predictions = self._get_predictions(observations)
        self.predictions = predictions

        answers = self._make_answers(observations, predictions)
        self.answers = answers

        score_response = self._get_score(answers)
        self.score = score_response['text']
        self.response_code = score_response['status_code']

    def _run_score(self, observation):
        observations = self._make_observations(observation, human_input=True)
        self.observations = observations
        predictions = self._get_predictions(observations)
        self.predictions = predictions
        answers = self._make_answers(observations, predictions, human_input=True)
        self.answers = answers

    def answer(self, input_task):
        try:
            if isinstance(input_task, list):
                print("%s human input mode..." % self.kpi_name)
                self._run_score(input_task)
                result = copy.deepcopy(self.answers)
                print("%s action result:  %s" % (self.kpi_name, result))
                return result
            elif isinstance(input_task, int):
                print("%s API mode..." % self.kpi_name)
                self._set_numtasks(input_task)
                self._run_test()
                print("%s score: %s" % (self.kpi_name, self.score))
                result = copy.deepcopy(self.tasks)
                result.update(copy.deepcopy(self.answers))
                return result
            else:
                return {"ERROR": "{} parameter error - {} belongs to unknown type".format(self.kpi_name,
                                                                                          str(input_task))}
        except Exception as e:
            return {"ERROR": "{}".format(traceback.extract_stack())}
