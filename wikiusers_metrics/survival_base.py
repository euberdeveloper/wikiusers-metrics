from datetime import datetime
from json import dumps, loads
from pathlib import Path
from typing import Callable, Tuple, Union
import matplotlib.pyplot as plt
import numpy as np

from wikiusers import settings as wu_settings
from wikiusers import logger

import settings
from utils import Batcher, get_today_month_date, get_month_date_from_key, get_diff_in_months, get_no_ghost, get_key_from_date





class SurvivalMetricher:

    def __is_user_dead(self, user: dict) -> bool:
        today = get_today_month_date()
        dead_date = user['activity']['total']['last_event_timestamp']
        return get_diff_in_months(today, dead_date) > self.dropoff_month_threshold

    def __iterate_user(self, user: dict, group: str) -> bool:
        dead_date = user['activity']['total']['last_event_timestamp']

        activity_per_month = user['activity']['per_month']
        for year in sorted(activity_per_month.keys(), reverse=True):
            year_obj = activity_per_month[year]

            for month in sorted(year_obj.keys(), reverse=True):
                month_obj = year_obj[month]
                survived_months = get_diff_in_months(dead_date, get_month_date_from_key(f'{year}-{month}'))
                extracted_val = self.extractor(month_obj)

                try:
                    self.result[group][survived_months]['tot'] += extracted_val
                    self.result[group][survived_months]['count'] += 1
                except:
                    self.result[group][survived_months] = { 'tot': extracted_val, 'count': 1 }

    def __postprocess(self) -> None:
        for group in self.result:
            for survived_months, obj in self.result[group].items():
                self.result[group][survived_months] = obj['tot'] / obj['count']

    def __process_user(self, user: dict) -> None:
        if self.__is_user_dead(user):
            group = self.discriminator(user)

            if not group in self.result:
                self.result[group] = {}
            
            self.__iterate_user(user, group)

    def __init__(
        self,
        name = 'survival',
        lang: str = wu_settings.DEFAULT_LANGUAGE,
        database: str = wu_settings.DEFAULT_DATABASE_PREFIX,
        batch_size: str = wu_settings.DEFAULT_BATCH_SIZE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR,
        dropoff_month_threshold: int = settings.DEFAULT_DROPOFF_MONTH_THRESHOLD,
        discriminator: Callable[[dict], str] = lambda: 'all',
        extractor: Callable[[dict], float] = lambda: 0
    ):
        self.name = name
        self.lang = lang
        self.database = database
        self.batch_size = batch_size
        self.metrics_path = Path(metrics_path)
        self.dropoff_month_threshold = dropoff_month_threshold
        self.discriminator = discriminator
        self.extractor = extractor

        query_filter = {**get_no_ghost()}
        self.batcher = Batcher(self.database, self.lang, self.batch_size, query_filter)
        self.result = {}

    def compute(self) -> None:
        logger.info(f'Start computing', lang=self.lang)
        for i, users_batch in enumerate(self.batcher):
            logger.debug(f'Computing batch {i}', lang=self.lang)
            for user in users_batch:
                self.__process_user(user)
        self.__postprocess()
        logger.succ(f'Finished computing', lang=self.lang)

    def save_json(self) -> None:
        logger.info(f'Start saving json', lang=self.lang)

        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'{self.name}')
        path_root.mkdir(exist_ok=True, parents=True)
        path = path_root.joinpath(f'{self.name}.json')
        json_text = dumps(self.result, sort_keys=True)
        with open(path, 'w') as out_file:
            out_file.write(json_text)

        logger.succ(f'Finished saving json', lang=self.lang)

    def save_graphs(
        self
    ) -> None:

        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'{self.name}')
        path_root.mkdir(exist_ok=True, parents=True)
        path_json = path_root.joinpath(f'{self.name}.json')
        path = path_root.joinpath(f'{self.name}.png')

        with open(path_json) as json_file:
            data = loads(json_file.read())

        fig, axs = plt.subplots(len(data.keys()), 1, figsize=(18, 18))

        # TODO: remove fixed arr
        # for i, activity_level in enumerate(['inactive', '5_active', '15_active', '30_active', '60_active', '120_active']):
        for i, activity_level in enumerate(sorted(data.keys())):
            obj = data[activity_level]
            x_values = obj.keys()
            y_values = obj.values()
            axs[i].set_ylabel('Dropoff count')
            axs[i].plot(x_values, y_values)
            axs[i].set_title(f'Activity level is {activity_level}')

        fig.savefig(path, bbox_inches='tight')



