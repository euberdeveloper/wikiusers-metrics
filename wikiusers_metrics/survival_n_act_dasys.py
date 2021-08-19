from survival_base import SurvivalMetricher


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


def retriever(month_activity: dict) -> float:
    try:
        return month_activity['n_of_activity_days']
    except:
        return 0


if __name__ == '__main__':
    metricher = SurvivalMetricher(name='activity_days_over_survived_months', dropoff_month_threshold=24, lang='ca', discriminator=active_discriminator, extractor=retriever)
    metricher.compute()
    metricher.save_json()
    metricher.save_graphs()