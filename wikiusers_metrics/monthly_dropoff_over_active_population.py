from datetime import datetime
from json import dumps, loads
from pathlib import Path
from typing import Tuple, Union
import matplotlib.pyplot as plt

from wikiusers import settings as wu_settings
from wikiusers import logger

import settings
from utils import Batcher, get_today_month_date, get_month_date_from_key, get_diff_in_months, get_no_ghost, get_key_from_date


class Metricher:
    def __was_user_active(self, user: dict) -> None:
        result = [False] * len(self.active_per_month_thr)

        per_month = user['activity']['per_month']
        for _, year_obj in per_month.items():
            for _, month_obj in year_obj.items():
                for i, thr in enumerate(self.active_per_month_thr):
                    if month_obj['events']['total']['total'] >= thr:
                        result[i] = True

        return result

    def __process_user(self, user: dict) -> None:
        was_user_actives = self.__was_user_active(user)

        for i, was_it in enumerate(was_user_actives):
            if was_it:
                last_event: datetime = user['activity']['total']['last_event_timestamp']
                year_month = get_key_from_date(last_event)

                curr_thr = self.active_per_month_thr[i]

                if curr_thr not in self.result:
                    self.result[curr_thr] = {}

                try:
                    self.result[curr_thr][year_month] += 1
                except:
                    self.result[curr_thr][year_month] = 1

    def __filter_for_threshold(self) -> None:
        today_month_date = get_today_month_date()

        for thr in list(self.result.keys()):
            thr_obj = self.result[thr]

            for key in list(thr_obj):
                key_month_date = get_month_date_from_key(key)
                if get_diff_in_months(today_month_date, key_month_date) <= self.dropoff_month_threshold:
                    thr_obj.pop(key)

    def __init__(
        self,
        lang: str = wu_settings.DEFAULT_LANGUAGE,
        database: str = wu_settings.DEFAULT_DATABASE_PREFIX,
        batch_size: str = wu_settings.DEFAULT_BATCH_SIZE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR,
        dropoff_month_threshold: int = settings.DEFAULT_DROPOFF_MONTH_THRESHOLD,
        active_per_month_thr: list[int] = [settings.DEFAULT_ACTIVE_PER_MONTH_THRESHOLD]
    ):
        self.lang = lang
        self.database = database
        self.batch_size = batch_size
        self.metrics_path = Path(metrics_path)
        self.dropoff_month_threshold = dropoff_month_threshold
        self.active_per_month_thr = active_per_month_thr

        query_filter = {**get_no_ghost()}
        self.batcher = Batcher(self.database, self.lang, self.batch_size, query_filter)
        self.result = {}

    def compute(self) -> None:
        logger.info(f'Start computing', lang=self.lang)
        for i, users_batch in enumerate(self.batcher):
            logger.debug(f'Computing batch {i}', lang=self.lang)
            for user in users_batch:
                self.__process_user(user)
        self.__filter_for_threshold()
        logger.succ(f'Finished computing', lang=self.lang)

    def save_json(self) -> None:
        logger.info(f'Start saving json', lang=self.lang)

        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'monthly_dropoff_over_active_population')
        path_root.mkdir(exist_ok=True, parents=True)

        for thr, val in self.result.items():
            json_text = dumps(val, sort_keys=True)
            path = path_root.joinpath(f'{self.dropoff_month_threshold}_{thr}.json')

            with open(path, 'w') as out_file:
                out_file.write(json_text)
        logger.succ(f'Finished saving json', lang=self.lang)

    def save_graphs(
        self
    ) -> None:
        fig, axs = plt.subplots(len(self.active_per_month_thr), 1, figsize=(18, 18))

        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'monthly_dropoff_over_active_population')
        path_root.mkdir(exist_ok=True, parents=True)

        for i, thr in enumerate(self.active_per_month_thr):
            json_path = path_root.joinpath(f'{self.dropoff_month_threshold}_{thr}.json')
            with open(json_path) as input_file:
                raw_data = loads(input_file.read())
                x_values = [datetime(2001, 1, 1)] + [get_month_date_from_key(key) for key in raw_data.keys()]
                y_values = [0] + list(raw_data.values())
                axs[i].set_ylabel('Dropoff count')
                axs[i].plot(x_values, y_values)
                axs[i].set_title(f'At least a month with {thr} events, died since {self.dropoff_month_threshold} months')

        path = path_root.joinpath(f'{self.dropoff_month_threshold}_{self.active_per_month_thr}.png')
        fig.savefig(path, bbox_inches='tight')

    @staticmethod
    def show_graph_perc(
        thresholds: list[Tuple[int, int]],
        lang: str = wu_settings.DEFAULT_LANGUAGE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR
    ) -> None:
        fig, axs = plt.subplots(len(thresholds), 1, figsize=(18, 18))

        metrics_path = Path(metrics_path)
        for i, thrs in enumerate(thresholds):
            diethr, actthr, color = thrs

            path = Path(metrics_path).joinpath(lang).joinpath(
                f'monthly_dropoff_with_threshold_{diethr}_over_active_population_{"".join(actthr)}.json')
            with open(path) as input_file:
                raw_data = loads(input_file.read())
                x_values = [get_month_date_from_key(key) for key in raw_data.keys()]
                y_values = raw_data.values()
                axs[i].set_ylabel('Dropoff count')
                axs[i].plot(x_values, y_values, color=color)
                axs[i].set_title(f'At least a month with {actthr} events, died since {diethr} months')

        fig.savefig('result.png', bbox_inches='tight')


if __name__ == '__main__':
    metricher = Metricher(lang='it', active_per_month_thr=[5, 15, 50, 200, 1000])
    metricher.compute()
    metricher.save_json()
    metricher.save_graphs()