from survival_base import SurvivalMetricher

from utils import Batcher, get_today_month_date, get_month_date_from_key, get_diff_in_months, get_no_ghost, get_key_from_date


def active_discriminator(user: dict, thresholds: list[int] = [5, 15, 30, 60, 120]) -> str:
    sorted_thresholds = sorted(thresholds, reverse=True)
    active_thresholds = [False] * len(sorted_thresholds)

    per_month = user['activity']['per_month']
    for _, year_obj in per_month.items():
        for _, month_obj in year_obj.items():
            for i, thr in enumerate(sorted_thresholds):
                if month_obj['events']['total']['total'] >= thr:
                    active_thresholds[i] = True

    for i, is_active in enumerate(active_thresholds):
        if is_active:
            return f'{sorted_thresholds[i]}_active'

    return 'inactive'


def retrieve_page_entropy(month_activity: dict) -> float:
    try:
        return month_activity['pages_activity']['entropy']
    except:
        return 0


if __name__ == '__main__':
    metricher = SurvivalMetricher(name='pages_entropy_over_survived_months', lang='ca', dropoff_month_threshold=24, discriminator=active_discriminator, extractor=retrieve_page_entropy)
    metricher.compute()
    metricher.save_json()
    metricher.save_graphs()