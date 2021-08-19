from survival_base import SurvivalMetricher

from utils import Batcher, get_today_month_date, get_month_date_from_key, get_diff_in_months, get_no_ghost, get_key_from_date


def active_discriminator(user: dict) -> str:
    all_groups = user['groups']['ever_had']

    if 'sysop' in all_groups:
        return 'sysop'

    if 'autopatrolled' in all_groups:
        return 'autopatrolled'

    return 'none'


def retriever(month_activity: dict) -> float:
    try:
        return month_activity['events']['total']['total']
    except:
        return 0


if __name__ == '__main__':
    metricher = SurvivalMetricher(name='for_role_edits_total_survived_months', lang='it', dropoff_month_threshold=24, discriminator=active_discriminator, extractor=retriever)
    metricher.compute()
    metricher.save_json()
    metricher.save_graphs()