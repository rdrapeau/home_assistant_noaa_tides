from datetime import datetime, timedelta
import math

import noaa_coops as nc

TIME_FORMAT = "%m/%d/%Y %I:%M %p"


class CustomNOAASensor(object):
    def __init__(self, station_id, timezone, unit_system):
        self._station_id = station_id
        self._timezone = timezone
        self._unit_system = unit_system
        self._station = None
        self._data = None


    def get_state_from_raw_data(self):
        if self._data is None:
            return

        now = datetime.now()
        tides = [(time, tuple(tide)) for time, tide in self._data.iterrows()]
        
        next_tide_index = None
        for i in range(len(tides)):
            time, _ = tides[i]
            if time > now:
                next_tide_index = i
                break

        if next_tide_index is None or next_tide_index == 0:
            return None

        next_tide_time, next_tide = tides[next_tide_index]
        previous_tide_time, previous_tide = tides[next_tide_index - 1]

        predicted_period = (next_tide_time - previous_tide_time).seconds
        if next_tide[1] == "H":
            low_tide_level = previous_tide[0]
            high_tide_level = next_tide[0]
            tide_factor = 50 - (50 * math.cos((now - previous_tide_time).seconds * math.pi / predicted_period))
        else:
            low_tide_level = next_tide[0]
            high_tide_level = previous_tide[0]
            tide_factor = 50 + (50 * math.cos((now - previous_tide_time).seconds * math.pi / predicted_period))

        current_tide_estimate = round(low_tide_level + (tide_factor / 100.0) * (high_tide_level - low_tide_level), 3)

        return {
            "next_tide_time": next_tide_time.strftime(TIME_FORMAT),
            "next_tide_level": next_tide[0],
            "next_tide_type": next_tide[1],
            "last_tide_time": previous_tide_time.strftime(TIME_FORMAT),
            "last_tide_level": previous_tide[0],
            "last_tide_type": previous_tide[1],
            "raw_tide_times": ','.join([time.strftime(TIME_FORMAT) for time, _ in tides]),
            "raw_tide_levels": ','.join([str(tide[0]) for _, tide in tides]),
            "current_tide_estimate": current_tide_estimate,
            "tide_factor": tide_factor
        }


    def needs_refresh(self):
        if self._station is None or self._data is None:
            return True

        next_day = datetime.now() + timedelta(hours=20)
        for time, _ in self._data.iterrows():
            if time >= next_day:
                return False

        return True


    def refresh(self):
        if self._station is None:
            self._station = nc.Station(self._station_id)

        begin = datetime.now() - timedelta(hours=24)
        end = begin + timedelta(hours=48)
        self._data = self._station.get_data(
            begin_date=begin.strftime("%Y%m%d %H:%M"),
            end_date=end.strftime("%Y%m%d %H:%M"),
            product="predictions",
            datum="MLLW",
            interval="hilo",
            units=self._unit_system,
            time_zone=self._timezone,
        )


station_id = '9446025'
sensor = CustomNOAASensor(station_id, 'lst_ldt', 'english')
print(sensor.needs_refresh())
sensor.refresh()
print(sensor.needs_refresh())

print(sensor.get_state_from_raw_data())