from json import dumps, loads
from pathlib import Path
from typing import Union
from matplotlib import pyplot as plt

from wikiusers import settings as wu_settings
from wikiusers import logger

import settings
from utils import Batcher


class Metricher:

    def __process_user(self, user: dict) -> None:
        activity_total = user['activity']['total']

        active_days = str(activity_total['n_activity_days'])
        total_events = activity_total['events']['total']['total']

        for ns, events_counts in activity_total['events']['per_namespace'].items():
            if ns not in self.result:
                self.result[ns] = {}

            if active_days not in self.result[ns]:
                self.result[ns][active_days] = {'tot': 0, 'count': 0}

            self.result[ns][active_days]['tot'] += events_counts['total'] / total_events
            self.result[ns][active_days]['count'] += 1

    def __process_final(self) -> None:
        for ns in self.result.keys():
            ns_obj = self.result[ns]

            for days in ns_obj.keys():
                ns_obj[days] = ns_obj[days]['tot'] / ns_obj[days]['count']

    def __init__(
        self,
        lang: str = wu_settings.DEFAULT_LANGUAGE,
        database: str = wu_settings.DEFAULT_DATABASE_PREFIX,
        batch_size: str = wu_settings.DEFAULT_BATCH_SIZE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR
    ):
        self.lang = lang
        self.database = database
        self.batch_size = batch_size
        self.metrics_path = Path(metrics_path)

        query_filter = {'groups.ever_had': 'sysop',  'activity.per_month': {'$ne': {}}}
        query_projector = {'activity.per_year': False, 'activityper_month': False}

        self.batcher = Batcher(self.database, self.lang, self.batch_size, query_filter, query_projector)
        self.result = {}

    def compute(self) -> None:
        logger.info(f'Start computing', lang=self.lang)
        for i, users_batch in enumerate(self.batcher):
            logger.debug(f'Computing batch {i}', lang=self.lang)
            for user in users_batch:
                self.__process_user(user)
            self.__process_final()
        logger.succ(f'Finished computing', lang=self.lang)

    def save_json(self) -> None:
        logger.info(f'Start saving json', lang=self.lang)
        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'admins_n_activity_days_over_ns')
        path_root.mkdir(exist_ok=True, parents=True)
        path = path_root.joinpath('data.json')
        json_text = dumps(self.result, sort_keys=True)
        with open(path, 'w') as out_file:
            out_file.write(json_text)

        logger.succ(f'Finished saving json', lang=self.lang)

    def save_graph(
        self,
    ) -> None:
        path_root = self.metrics_path.joinpath(self.lang).joinpath(f'admins_n_activity_days_over_ns')
        path_root.mkdir(exist_ok=True, parents=True)
        json_path = path_root.joinpath('data.json')
        png_path = path_root.joinpath('graph.png')

        with open(json_path) as jsonfile:
            rawdata = jsonfile.read()
            data = loads(rawdata)

            for ns, ns_vals in data.items():
                if ns in ['n0', 'n1', 'n2', 'n3']:
                    ns_vals = ns_vals

                    sorted_keys = sorted(ns_vals.keys())
                    x_values = sorted([int(key) for key in sorted_keys])
                    y_values = [ns_vals[key] for key in sorted_keys]
                    plt.plot(x_values, y_values, label=ns)

            plt.title('mah')
            plt.ylabel('My graph')
            plt.legend()
            plt.savefig(png_path, bbox_inches='tight')


if __name__ == '__main__':
    metricher = Metricher(lang='de')
    metricher.compute()
    metricher.save_json()
    metricher.save_graph()
