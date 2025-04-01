from core.variables import days_week


def day_to_number_converter(value: str):
    for key, day in days_week.items():
        if day == value:
            return key
