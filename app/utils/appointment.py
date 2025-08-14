from datetime import date, timedelta, time
from typing import List


def get_available_dates(start_date: date, days: int = 30) -> List[date]:
    dates = []
    current_date = start_date
    for _ in range(days):
        if current_date.weekday() != 6:  # Exclude Sundays
            dates.append(current_date)
        current_date += timedelta(days=1)
    return dates

# Time slots configuration
TIME_SLOTS_CONFIG = {
    "buyer": {
        "virtual": {"times": [time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                             time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                             time(14, 0), time(14, 30)], "time_zone": "EST"},
        "offline": {
            "USA Office – HQ": {"times": [time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                                         time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                                         time(15, 0), time(15, 30)], "time_zone": "EST"},
            "Kashmir India": {"times": [time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                                       time(13, 0), time(13, 30), time(14, 0), time(14, 30)],
                              "time_zone": "IST"}
        }
    },
    "vendor": {
        "virtual": {"times": [time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                             time(12, 0), time(12, 30), time(13, 0), time(13, 30),
                             time(14, 0), time(14, 30), time(15, 0), time(15, 30)],
                    "time_zone": "IST"},
        "offline": {
            "USA Office – HQ": {"times": [time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                                         time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                                         time(15, 0), time(15, 30)], "time_zone": "EST"},
            "Kashmir India": {"times": [time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                                       time(13, 0), time(13, 30), time(14, 0), time(14, 30)],
                              "time_zone": "IST"}
        }
    },
    "guest": {
        "USA": {
            "virtual": {"times": [time(9, 0), time(9, 30), time(10, 0), time(10, 30),
                                 time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                                 time(14, 0), time(14, 30)], "time_zone": "EST"},
            "offline": {
                "USA Office – HQ": {"times": [time(10, 0), time(10, 30), time(11, 0), time(11, 30),
                                             time(12, 0), time(12, 30), time(14, 0), time(14, 30),
                                             time(15, 0), time(15, 30)], "time_zone": "EST"}
            }
        },
        "India": {
            "virtual": {"times": [time(13, 0), time(13, 30), time(14, 0), time(14, 30)],
                        "time_zone": "IST"},
            "offline": {
                "Kashmir India": {"times": [time(11, 0), time(11, 30), time(12, 0), time(12, 30),
                                           time(13, 0), time(13, 30), time(14, 0), time(14, 30)],
                                  "time_zone": "IST"}
            }
        }
    }
}
